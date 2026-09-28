"""인물 초상 폴백 가공 (v2.4.0, back_and_forth D-0029 작업 5, 07 §3.4, 19 부록 D prep3 `mono, normalize_portrait`).

라이브러리(`assets/library/people/`)에 없는 인물의 긴급 폴백 경로다. 정석은 저장소 공방(codex imagegen)이다(07 §3.4 한계).

    python tools/portrait_fallback.py cutout SRC.jpg DEST.png [--style v3|engraving]
    python tools/portrait_fallback.py library PID DEST.png        # 라이브러리 가공본 → 뱃지용 머리-어깨 정규화

- `v3`(기본): rembg `u2net_human_seg` → 알파 GaussianBlur(0.8) → `mono()` S자 대비 → `normalize_portrait()` 폭 420.
  v3 호르무즈 초상과 같은 바이트(재현성 — Phase 4 md5)를 내도록 prep3 코드를 그대로 옮겼다.
- `engraving`: 라이브러리 24인과 같은 판화 질감(`workers/engraving_stylizer.stylize_mono`)으로 흑백화. 알파는 rembg 것을 쓴다.
- 원본·도구·파라미터를 권리 레지스트리 `processing` 에 남긴다(C9, G4-10). 사실 텍스트는 넣지 않는다(코드 렌더).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REMBG_MODEL = "u2net_human_seg"
ALPHA_BLUR = 0.8
PORTRAIT_W = 420
HEAD_RATIO = 1.22       # 머리-어깨 구도: 높이 ≤ 폭 × 1.22
ALPHA_BBOX_MIN = 40


def mono(im: Image.Image) -> Image.Image:
    """v3 흑백화: autocontrast(1.2%) + UnsharpMask(2, 90, 2) + tanh S자 곡선(07 §3.4)."""
    a = im.getchannel("A")
    g = ImageOps.autocontrast(ImageOps.grayscale(im.convert("RGB")), cutoff=1.2).filter(ImageFilter.UnsharpMask(2, 90, 2))
    arr = np.asarray(g, np.float32) / 255
    arr = 0.5 + np.tanh((arr - 0.52) * 2.6) / (2 * np.tanh(1.3))
    g = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "L")
    return Image.merge("RGBA", (g, g, g, a))


def normalize_portrait(im: Image.Image, out_w: int = PORTRAIT_W) -> Image.Image:
    """알파 bbox 위에서부터 높이 ≤ 폭×1.22 로 자르고 폭 420 으로 맞춘다."""
    a = np.asarray(im.getchannel("A"))
    ys, xs = np.where(a > ALPHA_BBOX_MIN)
    if len(xs) == 0:
        raise ValueError("알파가 빈 이미지 — 배경 제거 실패")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w = x1 - x0
    h = min(y1 - y0, int(w * HEAD_RATIO))
    c = im.crop((x0, y0, x1, y0 + h))
    return c.resize((out_w, int(c.height * out_w / c.width)), Image.LANCZOS)


_sessions: dict[str, object] = {}


def cutout(img: Image.Image) -> Image.Image:
    """rembg 배경 제거(최초 실행 시 모델 ~170MB). 알파 가장자리 부드럽게."""
    from rembg import new_session, remove  # noqa: PLC0415 — 무거운 의존성

    if REMBG_MODEL not in _sessions:
        _sessions[REMBG_MODEL] = new_session(REMBG_MODEL)
    cut = remove(img.convert("RGB"), session=_sessions[REMBG_MODEL]).convert("RGBA")
    cut.putalpha(cut.getchannel("A").filter(ImageFilter.GaussianBlur(ALPHA_BLUR)))
    return cut


def engraving(cut: Image.Image) -> Image.Image:
    """라이브러리 판화 질감(engraving_stylizer.stylize_mono) + rembg 알파."""
    from workers.engraving_stylizer import stylize_mono  # noqa: PLC0415

    res = stylize_mono(cut.convert("RGB"))
    out = res.image.convert("RGBA").resize(cut.size, Image.LANCZOS)
    out.putalpha(cut.getchannel("A"))
    return out


def process(src: Path, dest: Path, style: str = "v3") -> dict:
    """사진 → 뱃지 초상. 돌려주는 dict 는 권리 레지스트리 `processing` 에 그대로 들어간다."""
    cut = cutout(Image.open(src))
    styled = mono(cut) if style == "v3" else engraving(cut)
    dest.parent.mkdir(parents=True, exist_ok=True)
    normalize_portrait(styled).save(dest)
    return {"tool": "tools/portrait_fallback.py", "style": style, "rembg_model": REMBG_MODEL, "alpha_blur": ALPHA_BLUR,
            "width": PORTRAIT_W, "head_ratio": HEAD_RATIO, "source_file": src.name}


def library_portrait(pid: str, dest: Path, manifest: Path | None = None) -> dict:
    """라이브러리 가공본(첫 변형) → 머리-어깨 정규화. 권리 항목(src=repo_library)을 돌려준다."""
    manifest = manifest or REPO / "assets" / "library" / "library_manifest.json"
    lib = {p["person_id"]: p for p in json.loads(manifest.read_text(encoding="utf-8"))["people"]}
    if pid not in lib:
        raise KeyError(f"라이브러리에 없는 인물: {pid}")
    p = lib[pid]
    dest.parent.mkdir(parents=True, exist_ok=True)
    normalize_portrait(Image.open(REPO / p["variants"][0]["path"]).convert("RGBA")).save(dest)
    return {"source": p["source"], "variant": p["variants"][0]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cutout")
    c.add_argument("src", type=Path)
    c.add_argument("dest", type=Path)
    c.add_argument("--style", choices=("v3", "engraving"), default="v3")
    lb = sub.add_parser("library")
    lb.add_argument("pid")
    lb.add_argument("dest", type=Path)
    a = ap.parse_args(argv)
    out = process(a.src, a.dest, a.style) if a.cmd == "cutout" else library_portrait(a.pid, a.dest)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

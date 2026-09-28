"""패널 프리뷰 갤러리 (D-0032 작업 5·7) — 예시 데이터(prompts/examples/panels)를 실제 렌더러로 그려 한 장씩 + 격자.

    python tools/panel_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phase6/panels

배경은 프로젝트 첫 카메라의 지도(패널 덮개가 그 위에 깔린다). 이미지(국기·인물·휘장)는 프로젝트 자산을 쓴다.
각 패널은 등장이 다 끝난 시각(t1 − 1초)에 찍는다. 문구·수치는 예시다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cairo
import yaml
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.project import load_project  # noqa: E402
from engine.projection import View  # noqa: E402
from engine.registry import resolve, validate_events  # noqa: E402
from engine.style import H_OUT, W_OUT  # noqa: E402

KINDS: tuple[str, ...] = ("dots", "gantt", "dual_line", "fork", "checklist", "network")
EXAMPLES = Path(__file__).resolve().parent.parent / "prompts" / "examples" / "panels"


def render_panel(P, ev: dict, t: float) -> Image.Image:  # noqa: ANN001
    A = P.R.assets  # noqa: N806
    im = View(P.cams[0], A.tiers, A.base).base()
    buf = bytearray(im.tobytes("raw", "BGRX"))
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W_OUT, H_OUT, W_OUT * 4)
    ctx = cairo.Context(surf)
    resolve(ev).render(ctx, P.R, t, ev)
    surf.flush()
    return Image.frombuffer("RGBA", (W_OUT, H_OUT), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proj", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--extra", nargs="*", default=[], help="추가 예시 YAML(label=path)")
    args = ap.parse_args(argv)
    P = load_project(args.proj)  # noqa: N806
    args.out.mkdir(parents=True, exist_ok=True)
    items: list[tuple[str, Path]] = [(k, EXAMPLES / f"{k}.yaml") for k in KINDS]
    for x in args.extra:
        name, _, path = x.partition("=")
        items.append((name, Path(path)))
    shots: list[tuple[str, Image.Image]] = []
    for name, path in items:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))["event"]
        ev = validate_events([raw])[0]
        im = render_panel(P, ev, ev["t1"] - 1.0)
        im.save(args.out / f"{name}.png")
        shots.append((name, im))
        print(f"{name}: {args.out / (name + '.png')}")
    sc, cols, lab = 0.5, 2, 22
    w, h = int(W_OUT * sc), int(H_OUT * sc)
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, (h + lab) * rows), (12, 14, 20))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
    except OSError:
        font = ImageFont.load_default()
    for i, (name, im) in enumerate(shots):
        x, y = (i % cols) * w, (i // cols) * (h + lab)
        d.text((x + 6, y + 3), name, fill=(230, 230, 230), font=font)
        sheet.paste(im.resize((w, h)), (x, y + lab))
    sheet.save(args.out.parent / "panels_gallery.jpg", quality=90)
    print(args.out.parent / "panels_gallery.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

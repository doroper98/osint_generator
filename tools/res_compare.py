"""해상도 비교 — 1080p 골든 25컷 → Lanczos 854×480 축소 → 480p 와 MAD (v3.6.0, back_and_forth D-0066 작업 4 · D-0067 요건 4).

    python tools/res_compare.py projects/hormuz_korea --out docs/handoff/reports/phase10 [--res 1080p]

먼저 두 프로파일의 골든 프리뷰가 있어야 한다:
    python -m engine.render <proj> --preview golden                 → prev/
    python -m engine.render <proj> --preview golden --res 1080p     → prev_1080p/

판정: 컷마다 축소 MAD ≤ rules `golden.res_compare_mad_max`(설계 좌표가 같으니 남는 차이는 래스터 선명도·글자 힌팅뿐).
위치: 두 폴더 frames.json 이 같고(시각·문장·활성 이벤트), place_over 상자(뱃지·마커)가 두 프로파일에서 같다.
참고: 480p·1080p 축소를 골든 PNG(docs/handoff/golden)와도 잰다(판정 아님 — 골든은 v3 원본, expected_deltas 는 golden_compare 몫).
출력: res_compare.json, v480_vs_1080.jpg(컷마다 480p | 1080p 축소), res1080_crop_NN_*.jpg(1080p 원본 3컷 1920×1080, JPEG 92, 글자 판독 육안).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.sheet import grid  # noqa: E402
from rules import load_rules  # noqa: E402

GOLDEN = REPO / "docs" / "handoff" / "golden"
CROP_CUTS = ("p_0038.45.png", "p_0164.59.png", "p_0214.46.png")   # 지도 라벨·패널 글자·기사 카드 — 판독 육안용


def _rgb(p: Path, size: tuple[int, int] | None = None) -> np.ndarray:
    im = Image.open(p).convert("RGB")
    if size is not None and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, np.float32)


def mad(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a - b).mean() / 255)


def positions(proj: Path, res: str) -> dict:
    """place_over 상자 — 두 프로파일에서 뱃지·마커마다 표시 구간 가운데 시각."""
    import cairo  # noqa: PLC0415

    from engine.checks import place_over  # noqa: PLC0415
    from engine.project import load_project  # noqa: PLC0415
    from engine.style import output_profile  # noqa: PLC0415

    a, b = load_project(proj), load_project(proj, out=output_profile(res))
    c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    rows, diff = 0, []
    for e in a.events:
        if e["type"] not in ("badge", "marker"):
            continue
        t = (e["t0"] + e["t1"]) / 2
        pa, pb = place_over(a, c, e, t), place_over(b, c, e, t)
        rows += 1
        if pa != pb:
            diff.append({"label": e.get("label"), "t": round(t, 2), "480p": pa, res: pb})
    return {"compared": rows, "different": diff}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="480p ↔ 1080p 축소 비교")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--res", default="1080p")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    lo, hi = proj / "prev", proj / f"prev_{args.res}"
    thr = load_rules().golden.res_compare_mad_max
    fl, fh = (json.loads((d / "frames.json").read_text(encoding="utf-8"))["frames"] for d in (lo, hi))
    cuts, cells = [], []
    for fr in fl:
        name = fr["file"]
        a = _rgb(lo / name)
        big = hi / name
        b = _rgb(big, (a.shape[1], a.shape[0]))
        gold = GOLDEN / name.replace("p_", "frame_")
        row = {"png": name, "label": fr["label"], "mad": round(mad(a, b), 5),
               "device": list(Image.open(big).size)}
        if gold.exists():
            g = _rgb(gold)
            row["golden_ref"] = {"480p": round(mad(a, g), 5), args.res: round(mad(b, g), 5)}
        row["pass"] = row["mad"] <= thr
        cuts.append(row)
        cells += [(Image.open(lo / name), f"{len(cuts):02d} 480p {name}"), (Image.open(big), f"{len(cuts):02d} {args.res}→854 MAD {row['mad']:.4f}")]
    pos = positions(proj, args.res)
    res = {"schema_version": 1, "project": proj.name, "res": args.res, "threshold": thr,
           "frames_json_equal": fl == fh, "positions": pos,
           "mad_mean": round(float(np.mean([c["mad"] for c in cuts])), 5), "mad_max": max(c["mad"] for c in cuts),
           "passed": all(c["pass"] for c in cuts) and fl == fh and not pos["different"], "cuts": cuts}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "res_compare.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    grid(cells, 4, args.out / "v480_vs_1080.jpg")
    for i, n in enumerate(CROP_CUTS, 1):
        if (hi / n).exists():
            Image.open(hi / n).convert("RGB").save(args.out / f"res1080_crop_{i:02d}_{Path(n).stem}.jpg", quality=92)
    print(json.dumps({k: res[k] for k in ("mad_mean", "mad_max", "threshold", "frames_json_equal", "passed")}
                     | {"positions_compared": pos["compared"], "positions_different": len(pos["different"])}, ensure_ascii=False))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""배경 사진 가독 스윕 시트 — stage_backdrop 블러·덮개 변형별로 같은 컷을 그려 한 장에 (v5.2.0, back_and_forth D-0129 §A).

규칙 파일은 바꾸지 않는다 — 이 프로세스 안에서만 BACKDROP 값을 바꾸고 배경 표면 캐시를 비운 뒤 render_frame 으로 그린다.
행 = 컷(시각), 열 = 변형. 사용자가 한 열을 고르면 그 값이 규칙 값이 된다(사람 승인, 15 P11).

    python tools/backdrop_sweep.py projects/fed_policy_2026 --t 20.5 --t 120 --t 250 \\
        --v 4:0.30 --v 6:0.38 --v 10:0.45 --out sweep.jpg
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

from engine.project import load_project  # noqa: E402
from engine.render import render_frame  # noqa: E402
from engine.sheet import grid  # noqa: E402
from engine.style import BACKDROP, FPS  # noqa: E402


def parse_variant(s: str) -> tuple[float, ...]:
    """'blur:dim' 또는 'blur:dim:desaturate' → (blur_px, dim[, desaturate]). desaturate 를 빼면 규칙 값."""
    return tuple(float(v) for v in s.split(":"))


def sweep(proj: Path, times: list[float], variants: list[tuple[float, ...]], dest: Path) -> dict:
    """times × variants 컷을 그려 dest(JPEG 격자)와 dest 옆 PNG 들을 남긴다. 기록 dict(변형·컷 파일)를 돌려준다."""
    P = load_project(proj)  # noqa: N806
    keep = (BACKDROP.blur_px, BACKDROP.dim, BACKDROP.desaturate)
    cells: list[tuple[Image.Image, str]] = []
    rows: list[dict] = []
    png_dir = dest.with_suffix("")
    png_dir.mkdir(parents=True, exist_ok=True)
    try:
        for t in times:
            for v in variants:
                b, d = v[0], v[1]
                BACKDROP.blur_px, BACKDROP.dim = b, d   # 이 프로세스 안에서만(규칙 파일은 그대로)
                BACKDROP.desaturate = v[2] if len(v) > 2 else keep[2]
                P.R.cache.pop("backdrop_surf", None)
                s, _ = render_frame(P, min(P.n_frames - 1, int(t * FPS)))
                ds = BACKDROP.desaturate
                p = png_dir / f"t{t:07.2f}_b{b:g}_d{d:g}_s{ds:g}.png"
                s.write_to_png(str(p))
                cells.append((Image.open(p), f"t={t:.2f}  blur {b:g} · dim {d:g} · desat {ds:g}"))
                rows.append({"t": t, "blur_px": b, "dim": d, "desaturate": ds, "file": p.name})
    finally:
        BACKDROP.blur_px, BACKDROP.dim, BACKDROP.desaturate = keep
    grid(cells, len(variants), dest)
    rec = {"schema_version": 1, "project": proj.name, "variants": [list(v) for v in variants],
           "times": times, "sheet": dest.name, "cells": rows}
    dest.with_suffix(".json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="stage_backdrop 블러·덮개 스윕 시트")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--t", type=float, action="append", required=True, help="컷 시각(초), 여러 번")
    ap.add_argument("--v", type=parse_variant, action="append", required=True, help="blur:dim[:desaturate] 변형, 여러 번")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    rec = sweep(args.proj.resolve(), args.t, args.v, args.out.resolve())
    print(json.dumps({"sheet": str(args.out), "cells": len(rec["cells"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

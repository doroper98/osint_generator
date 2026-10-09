"""미사일 발사 사건 스케치 CLI(D-0140 §3).

    python -m sketch.missile projects/<pid>                 # 2D → out/sketch_2d.mp4 · sketch_2d_sheet.jpg · sketch_provenance.json
    python -m sketch.missile projects/<pid> --globe         # 3D 전환편 → out/sketch_globe.mp4 · 시트 · provenance
    python -m sketch.missile projects/<pid> --frames 5,27   # 정지 화면
    python -m sketch.missile projects/<pid> --check         # 렌더 없이 검사만
"""

from __future__ import annotations

import sys

from sketch.common.cli import base_parser

NOT_YET = 2   # 종료 코드 — 이식 전 단계(조용히 옛 스크립트로 폴백하지 않는다, P6)


def main(argv: list[str] | None = None) -> int:
    ap = base_parser("python -m sketch.missile", "미사일 발사 사건 화면 스케치 — EEZ·탐지 자산·궤적·착탄·고도 단면(2D), 지구본 전환(3D)")
    ap.add_argument("--globe", action="store_true", help="2D → 3D 지구본 전환편")
    ap.parse_args(argv)
    print("sketch.missile: 2D 이식은 Phase S1, 3D 는 S2 에서 들어온다(D-0140 §5) — 아직 렌더할 수 없다", file=sys.stderr)
    return NOT_YET


if __name__ == "__main__":
    raise SystemExit(main())

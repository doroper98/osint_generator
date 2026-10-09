"""전황 작전도 스케치 CLI(D-0140 §3).

    python -m sketch.campaign projects/<pid>                # → out/sketch_campaign.mp4 · 시트 · sketch_provenance.json
    python -m sketch.campaign projects/<pid> --frames 6,20  # 정지 화면
    python -m sketch.campaign projects/<pid> --check        # 렌더 없이 검사만
"""

from __future__ import annotations

import sys

from sketch.common.cli import base_parser

NOT_YET = 2   # 종료 코드 — 이식 전 단계(조용히 옛 스크립트로 폴백하지 않는다, P6)


def main(argv: list[str] | None = None) -> int:
    ap = base_parser("python -m sketch.campaign", "전황 작전도 화면 스케치 — 국가·제대별 부대 부호, 날짜별 전선, 진격 화살표, 포위망")
    ap.parse_args(argv)
    print("sketch.campaign: 이식은 Phase S3 에서 들어온다(D-0140 §5) — 아직 렌더할 수 없다", file=sys.stderr)
    return NOT_YET


if __name__ == "__main__":
    raise SystemExit(main())

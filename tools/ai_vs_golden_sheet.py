"""골든(사람 연출) 컷과 AI 연출 컷을 나란히 (v3.1.0, back_and_forth D-0047 작업 10 (c) `v3_vs_ai.jpg`).

    python tools/ai_vs_golden_sheet.py <골든 프레임 폴더> <AI 프로젝트> <출력.jpg>

두 쪽 모두 `--preview golden`(골든 25 앵커)으로 만든 컷을 시각순으로 짝짓는다. 한 줄 = [골든 | AI] × 2 앵커.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.golden import golden_times  # noqa: E402
from engine.sheet import grid  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    from PIL import Image  # noqa: PLC0415

    a = argv if argv is not None else sys.argv[1:]
    gold_dir, proj, dest = Path(a[0]), Path(a[1]), Path(a[2])
    gold = sorted(gold_dir.glob("*.png"))
    plan = json.loads((proj / "plan.json").read_text(encoding="utf-8"))
    anchors = golden_times(plan)
    ai = [proj / "prev" / f"p_{t:07.2f}.png" for _, t in anchors]
    missing = [str(p) for p in ai if not p.exists()]
    if len(gold) != len(anchors) or missing:
        print(f"컷 수 불일치: 골든 {len(gold)} · 앵커 {len(anchors)} · AI 없음 {missing[:3]}", file=sys.stderr)
        return 1
    cells = []
    for (label, _), g, p in zip(anchors, gold, ai):
        cells += [(Image.open(g), f"v3  {label}"), (Image.open(p), f"AI  {label}")]
    grid(cells, 4, dest)
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())

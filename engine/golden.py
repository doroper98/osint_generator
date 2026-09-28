"""골든 앵커 시각 (v3.0.0, back_and_forth D-0041 — `engine.render --preview golden`).

`docs/handoff/golden/golden_frames.json` 25 앵커(문장 id·TITLE·END + 오프셋)를 plan 시각으로 바꾼다.
`tools/golden_compare.py` 도 이 함수를 쓴다(중복 없음, 하드코딩 없음).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO / "docs" / "handoff" / "golden"


def load_golden() -> dict:
    return json.loads((GOLDEN_DIR / "golden_frames.json").read_text(encoding="utf-8"))


def anchor_time(anchor: str, offset: float, plan: dict) -> float:
    """앵커 → 절대 시각(초)."""
    if anchor == "TITLE":
        return next(c["t0"] for c in plan["cards"] if c["kind"] == "title") + offset
    if anchor == "END":
        return float(plan["total"]) + offset
    for s in plan["sentences"]:
        if s["sid"] == anchor:
            return float(s["t0"]) + offset
    raise KeyError(f"plan.json 에 앵커 없음: {anchor}")


def golden_times(plan: dict) -> list[tuple[str, float]]:
    """[(라벨, 시각)] — 골든 25 앵커."""
    return [(f"{f['anchor']}{float(f['offset']):+g}", anchor_time(f["anchor"], float(f["offset"]), plan))
            for f in load_golden()["frames"]]

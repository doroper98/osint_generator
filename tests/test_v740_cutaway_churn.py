"""v7.4.0 back_and_forth D-0229 §2.3(UF-110) — [cutaway-churn]: 기사 → 지도 0.1초 → 기사 같은 성급한 전면 전환은 hard.

재현: diesel_road_2026 v1 연출(direction.v1·현 direction.yaml)의 오프닝 기사 카드 두 장(cold_4 끝 ~ cold_5) 사이 지도 복귀가 짧다.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from engine.checks import cutaway_churn
from engine.direction import build, load_direction_doc
from engine.stage import MercatorStage
from engine.timebase import Timebase
from rules import load_rules
from script.schema import Plan

REPO = Path(__file__).resolve().parent.parent
PROJ = REPO / "projects" / "diesel_road_2026"
HOLD = load_rules().shot_grammar.shot_min_hold_sec


def _ev(t0: float, t1: float, typ: str = "article", mid: str = "a") -> dict:
    return dict(type=typ, t0=t0, t1=t1, mid=mid)


class UnitTest(unittest.TestCase):
    def test_short_map_return_is_hard(self) -> None:
        self.assertEqual(len(cutaway_churn([_ev(0, 5), _ev(5.1, 9, mid="b")])), 1)

    def test_long_map_return_ok(self) -> None:
        self.assertEqual(cutaway_churn([_ev(0, 5), _ev(5 + HOLD + 0.1, 15, mid="b")]), [])

    def test_contiguous_is_one_scene(self) -> None:
        self.assertEqual(cutaway_churn([_ev(0, 5), _ev(5.0, 9, mid="b")]), [])

    def test_boxed_media_not_full(self) -> None:
        self.assertEqual(cutaway_churn([_ev(0, 5), _ev(5.5, 9, typ="photo")]), [])


class V1FixtureTest(unittest.TestCase):
    def test_v1_opening_fails(self) -> None:
        doc = load_direction_doc(PROJ / "direction.v1.yaml" if (PROJ / "direction.v1.yaml").exists() else PROJ / "direction.yaml")
        free = lambda xs: [x for x in xs if "word" not in json.dumps(x if isinstance(x, dict) else x.model_dump())]  # noqa: E731 — 정렬 없는 컨테이너
        doc_arts = doc.model_copy(update={"events": [e for e in free(doc.events) if e.get("type") == "article"],
                                          "shots": free(doc.shots), "sound": None})
        plan = Plan.model_validate(json.loads((PROJ / "plan.json").read_text(encoding="utf-8")))
        _keys, events, _ = build(doc_arts, Timebase(plan), MercatorStage())
        hits = cutaway_churn(events)
        self.assertTrue(any(h for h in hits), hits)
        t_title = next(c.t0 for c in plan.cards if c.kind == "title")
        self.assertTrue(any(float(h.split("(~")[1].split(")")[0]) < t_title for h in hits), hits)   # 오프닝(제목 카드 전)에서 걸린다


if __name__ == "__main__":
    unittest.main()

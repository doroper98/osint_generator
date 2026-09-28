"""연표 자동 층 배치 (D-0032 작업 3·6, 08 §11-3)."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

import cairo
import yaml

from engine.events import PanelTimeline
from engine.panels import timeline

FIX = Path(__file__).resolve().parent / "fixtures" / "preview" / "panel_timeline.yaml"


def _ctx() -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


class TimelineLayerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = yaml.safe_load(FIX.read_text(encoding="utf-8"))["event"]

    def _auto(self) -> dict:
        a = copy.deepcopy(self.raw)
        for x in a["events"]:
            x.pop("side", None)
        return PanelTimeline.model_validate(a).model_dump()

    def test_explicit_sides_kept(self) -> None:
        """데이터가 준 층은 코드가 바꾸지 않는다(P8) — v3 연표 컷 무변경의 근거."""
        e = PanelTimeline.model_validate(self.raw).model_dump()
        sides, warns = timeline.assign_sides(e, _ctx())
        self.assertEqual(sides, [x["side"] for x in self.raw["events"]])
        self.assertEqual(warns, [])
        self.assertEqual(timeline.lint(e), [])

    def test_auto_no_overlap_and_deterministic(self) -> None:
        e = self._auto()
        s1, w1 = timeline.assign_sides(e, _ctx())
        s2, _ = timeline.assign_sides(e, _ctx())
        self.assertEqual(s1, s2)
        self.assertEqual(w1, [])
        self.assertEqual(timeline.lint(dict(e, events=[dict(x, side=s) for x, s in zip(e["events"], s1)])), [])
        self.assertEqual(s1[0], -1)   # 첫 사건은 축 위부터

    def test_close_dates_get_different_layers(self) -> None:
        e = self._auto()
        e["events"] = [dict(e["events"][0], date="2026-05-01", label="가까운 사건 하나"),
                       dict(e["events"][0], date="2026-05-02", label="가까운 사건 둘"),
                       dict(e["events"][0], date="2026-06-20", label="먼 사건"),
                       dict(e["events"][0], date="2026-06-24", label="먼 사건 옆")]
        sides, warns = timeline.assign_sides(e, _ctx())
        self.assertEqual(sides, [-1, 1, -1, 1])   # 가까운 둘은 위·아래로 갈린다
        self.assertEqual(warns, [])

    def test_explicit_overlap_warns(self) -> None:
        e = PanelTimeline.model_validate(self.raw).model_dump()
        e["events"][2]["side"] = -1   # 4.7 을 4.13 과 같은 쪽 1층으로 — 2.28 과는 떨어져도 4.13(+2)와 무관
        e["events"][3]["side"] = -1   # 4.13 을 4.7 과 같은 층에 → 라벨 겹침
        self.assertTrue(any("timeline-overlap" in w for w in timeline.lint(e)))

    def test_no_free_layer_is_loud(self) -> None:
        e = self._auto()
        e["events"] = [dict(e["events"][0], date="2026-05-01", label=f"같은 날 사건 {i}") for i in range(8)]
        _, warns = timeline.assign_sides(e, _ctx())
        self.assertTrue(any("timeline-no-free-layer" in w for w in warns))


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 back_and_forth D-0329 ② — 덮인 배지는 없는 요소(P6). 전면 덮개(기사 카드·인용) 아래 배지는 덮개 끝으로 미루고, 계획 구간 중
안 보인 비율이 rules badge.covered_max_ratio 를 넘으면 [badge-covered] hard. 발견: showcase_geo 트럼프 배지 206.84~211.88 ↔ 기사 카드 206.64~211.78."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from engine.reserved import FULL_COVER_TYPES, delay_covered_badges


def _badge(t0: float, t1: float, **kw) -> dict:  # noqa: ANN003
    return {"type": "badge", "t0": t0, "t1": t1, "label": "b", **kw}


class DelayTest(unittest.TestCase):
    def test_delay_past_chained_covers(self) -> None:
        b = _badge(10.0, 20.0)
        rec = delay_covered_badges([{"type": "article", "t0": 9.0, "t1": 12.0}, {"type": "quote", "t0": 11.5, "t1": 14.0}, b])
        self.assertEqual((b["t0"], b["t0_planned"]), (14.0, 10.0))
        self.assertEqual(rec, [{"label": "b", "t0_planned": 10.0, "t0": 14.0, "delay": 4.0}])

    def test_panel_and_over_panel_untouched(self) -> None:
        self.assertNotIn("panel", FULL_COVER_TYPES)   # 패널 덮개는 over_panel 배지 규칙(D-0104)
        b, o = _badge(10.0, 20.0), _badge(10.0, 20.0, over_panel=True)
        self.assertEqual(delay_covered_badges([{"type": "panel", "t0": 9.0, "t1": 12.0}, {"type": "article", "t0": 9.0, "t1": 12.0}, b, o])[0]["label"], "b")
        self.assertEqual(o["t0"], 10.0)


class CoveredCheckTest(unittest.TestCase):
    def _P(self, events: list[dict]) -> NS:  # noqa: N802
        return NS(events=events, R=NS(assets=NS(media_assets={})))

    def test_mostly_delayed_is_hard(self) -> None:
        b = _badge(10.0, 20.0)
        evs = [{"type": "article", "t0": 9.0, "t1": 18.0}, b]
        delay_covered_badges(evs)
        with mock.patch.object(checks, "place_over", return_value=(0.0, (0, 0, 10, 10))):
            out = checks.check_badge_covered(self._P(evs))
        self.assertEqual(len(out), 1)
        self.assertIn("[badge-covered]", out[0])
        self.assertIn("badge_covered", checks.HARD)

    def test_short_delay_passes(self) -> None:
        b = _badge(10.0, 20.0)
        evs = [{"type": "article", "t0": 9.0, "t1": 12.0}, b]
        delay_covered_badges(evs)
        with mock.patch.object(checks, "place_over", return_value=(0.0, (0, 0, 10, 10))):
            self.assertEqual(checks.check_badge_covered(self._P(evs)), [])

    def test_rule_keys(self) -> None:
        B = checks.R_.layout_480p.badge  # noqa: N806
        self.assertEqual((B.covered_max_ratio, B.covered_box_ratio), (0.5, 0.5))


if __name__ == "__main__":
    unittest.main()

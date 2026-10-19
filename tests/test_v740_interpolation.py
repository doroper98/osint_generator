"""v7.4.0 back_and_forth D-0247(사용자 결정 UF-128 "그래프가 중간에 끊기지 않도록 중간 보간을 해서 그래프를 표기하도록 해") —
dual_line 빈 달 점선 보간: 실측 사이만(외삽 없음)·보간 점 라벨·점 없음·출처 줄 보간 표기·정직성 hard."""

from __future__ import annotations

import unittest

from engine.honesty import ChartMeta, chart_honesty
from engine.panels import dual_line as D


def _e(vals: list, sub: str = "하루 천 배럴") -> dict:
    return {"subtitle": sub, "series": [{"label": "x", "col": "ru", "values": vals}]}


class GapTest(unittest.TestCase):
    def test_middle_gaps_linear(self) -> None:
        self.assertEqual(D.gap_pairs([1, None, 3]), [(0, 2)])
        self.assertEqual(D.gap_pairs([1, None, None, 4, 5]), [(0, 3)])
        self.assertEqual(D.interpolated_idx(_e([1, None, None, 4])), [[1, 2]])

    def test_edges_not_extrapolated(self) -> None:
        self.assertEqual(D.gap_pairs([None, 2, 3, None]), [])
        self.assertEqual(D.interpolated_idx(_e([None, 2, None, 4, None])), [[2]])

    def test_gap_note_only_when_interpolated(self) -> None:
        self.assertEqual(D.gap_subtitle(_e([1, 2, 3])), "하루 천 배럴")
        self.assertTrue(D.gap_subtitle(_e([1, None, 3])).endswith(D.L.gap_note))

    def test_style_rules(self) -> None:
        self.assertEqual(D.L.gap_policy, "interpolate")
        ist = D.L.interpolated_style
        self.assertFalse(ist.point)                     # 보간 점에 점 표식 없음
        self.assertLess(ist.alpha, 1)
        self.assertGreaterEqual(len(ist.dash), 2)


class HonestyTest(unittest.TestCase):
    def _m(self, **kw) -> ChartMeta:  # noqa: ANN003
        return ChartMeta(ref="t", axis="value", kind="dual_line", **kw)

    def test_hard_cases(self) -> None:
        self.assertEqual(chart_honesty(self._m(interpolated=2)), [])
        self.assertTrue(chart_honesty(self._m(interpolated=2, interp_distinct=False))[0].startswith("[interp-style]"))
        self.assertTrue(chart_honesty(self._m(interpolated=2, interp_noted=False))[0].startswith("[interp-unmarked]"))
        self.assertTrue(chart_honesty(self._m(extrapolated=1))[0].startswith("[interp-extrapolated]"))


if __name__ == "__main__":
    unittest.main()

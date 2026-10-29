"""v7.4.0 back_and_forth D-0263 — 시간축 레인 값 범위를 데이터에 맞춘다(사용자 의견 UF-140).

UF-140 원문: "그리고 금리 같이 변동이 크지 않은 데이터나 차트의 가로축을 그렇개 늘려버리면 그냥 가로로 펼쳐진 직선으로밖에 안보인다."
- lane_range fit: 무대 기간 안 데이터 [최소 − pad, 최대 + pad], 최소 폭(단위별), 눈금 반올림, 0 이 아닌 시작이면 출처 줄 표기.
- [flat-lane] hard: 카메라가 보여 준 구간의 세로 폭 ÷ 레인 범위 < flat_lane_min_ratio.
"""

from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace as NS

import numpy as np

from engine import checks, honesty
from engine.layers.series import axis_range_note, axis_values, lane_range
from engine.stage_timeline import TimelineStage
from engine.style import ISLAND, TIMELINE

LR = TIMELINE.lane_range
SER = [{"type": "series", "lane": "policy_rate", "series_id": "FEDFUNDS", "t0": 0.0, "t1": 9.0}]


def _stage(start: str) -> TimelineStage:
    st = TimelineStage(config={"start": start, "end": "2026-12-31",
                               "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"},
                                         {"id": "events", "label": "사건", "kind": "pins"}]})
    st.fit_frame(tuple(TIMELINE.frame.box), ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
    return st


def _P(st: TimelineStage, center: str = "2025-12-15", w: float = 400.0) -> NS:  # noqa: N802
    x = st.x_of(center)
    cams = np.tile(np.array([x, 1.0, w]), (24 * 10, 1))
    return NS(R=NS(stage=st, cache={"series_range": {"policy_rate": lane_range(SER, "policy_rate", st)}}), cams=cams, n_frames=24 * 10, events=SER)


class LaneRangeFitTest(unittest.TestCase):
    def test_rule_values(self) -> None:
        self.assertEqual((LR.mode, LR.min_span["%"], LR.flat_lane_min_ratio), ("fit", 1.0, 0.35))

    def test_fit_to_stage_period(self) -> None:
        lo, hi = lane_range(SER, "policy_rate", _stage("2025-01-01"))   # 2025~ 실효금리 3.63~4.33
        self.assertGreater(lo, 0)
        self.assertLessEqual(lo, 3.63)
        self.assertGreaterEqual(hi, 4.33)
        self.assertLess(hi - lo, 4.0)   # 옛 0~최대(0~4.33) 보다 좁다
        vals = axis_values((lo, hi))
        self.assertEqual((vals[0], vals[-1]), (lo, hi))
        self.assertLessEqual(len(vals) - 2, LR.ticks_max)
        self.assertIn("축 범위", axis_range_note((lo, hi), "%") or "")

    def test_min_span_floor(self) -> None:
        st = _stage("2026-01-01")   # 2026 은 3.63~3.64 — 0.01 폭을 절벽처럼 늘리지 않는다
        lo, hi = lane_range(SER, "policy_rate", st)
        self.assertGreaterEqual(hi - lo, LR.min_span["%"])

    def test_flat_lane_hard_when_stage_wider_than_view(self) -> None:
        """무대 2019~(0.05~5.33%) 인데 카메라는 2025~2026(3.63~4.33)만 → 화면에서 직선 = hard. 무대를 보이는 구간에 맞추면 통과."""
        out = checks.check_flat_lane(_P(_stage("2019-01-01")))
        self.assertEqual(len(out), 1)
        self.assertIn("[flat-lane]", out[0])
        self.assertIn("flat_lane", checks.HARD)
        self.assertEqual(checks.check_flat_lane(_P(_stage("2025-01-01"))), [])

    def test_axis_range_note_required(self) -> None:
        m = honesty.ChartMeta(ref="r", axis="value", kind="line", unit_label="%", axis_offset=True, axis_range_noted=False)
        self.assertTrue(any("[axis-range-unmarked]" in s for s in honesty.units_visible(m)))
        self.assertEqual(honesty.units_visible(m.model_copy(update={"axis_range_noted": True})), [])

    def test_zero_baseline_data_keeps_zero(self) -> None:
        self.assertEqual(lane_range(SER, "policy_rate", _stage("2019-01-01"))[0], 0.0)   # 데이터 최소 0.05 ≥ 0 → 아래 끝 0


if __name__ == "__main__":
    unittest.main()

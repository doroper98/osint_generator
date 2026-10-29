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


class IslandPathTest(unittest.TestCase):
    """v7.4.0 — 차트 아일랜드(사진 배경 + 시간축 차트) 경로에도 같은 장치(C12 §3): [flat-lane](UF-140)·시리즈 레인 덮개(UF-129).
    showcase_econ 연출 v4(backdrop + island)에서 금리 선이 0~7.5% 레인에 평평하게 그려지고 점도표가 차트를 덮었는데 두 검사가 돌지 않았다."""

    def _P(self, start: str) -> NS:  # noqa: N802
        from engine.island import island_box  # noqa: PLC0415

        cst = TimelineStage(config={"start": start, "end": "2026-12-31",
                                    "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"},
                                              {"id": "events", "label": "사건", "kind": "pins"}]})
        box = island_box({"box": "left"})
        cst.fit_island(box[3], ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        cams = np.tile(np.array([cst.x_of("2025-12-15"), 1.0, 400.0]), (24 * 10, 1))
        isl = {"type": "island", "kind": "chart", "box": "left", "t0": 0.0, "t1": 9.0}
        chart = {"stage": cst, "cams": cams, "events": SER}
        return NS(R=NS(stage=NS(name="backdrop"), cache={"island_chart": chart, "series_range": {"policy_rate": lane_range(SER, "policy_rate", cst)}}),
                  cams=None, n_frames=24 * 10, events=[isl])

    def test_flat_lane_on_island(self) -> None:
        self.assertEqual(len(checks.check_flat_lane(self._P("2019-01-01"))), 1)
        self.assertEqual(checks.check_flat_lane(self._P("2025-01-01")), [])   # 무대를 보이는 구간 쪽으로 — 3.63~4.33 / 3~5% = 0.35

    def test_cover_on_island_series_lane(self) -> None:
        P = self._P("2025-09-01")
        P.events.append({"type": "primitive", "id": "dot_plot", "tag": "점도표", "t0": 2.0, "t1": 6.0})
        rects = checks.series_lane_rects(P, 3.0)
        self.assertEqual([r[0] for r in rects], ["policy_rate"])
        box = rects[0][1]
        got = checks.timeline_lanes_covered(P, lambda e, t: [(box[0] + 10, box[1] + 2, box[0] + 80, box[3] - 2)])
        self.assertEqual([(g[0]["tag"], g[1]) for g in got], [("점도표", "policy_rate")])

    def test_island_markers_not_measured_on_main_stage(self) -> None:
        """아일랜드 안 핀(in_island)은 주 무대 좌표로 offscreen·label_collision 을 재지 않는다(econ v5 — 주 무대 좌표로 재면 가짜 화면 밖·겹침)."""
        from unittest import mock  # noqa: PLC0415

        P = NS(events=[{"type": "marker", "in_island": True, "label": "핀", "t0": 0.0, "t1": 5.0, "world": (0.0, 0.0)}])
        with mock.patch.object(checks, "place_over", side_effect=AssertionError("주 무대 좌표로 재면 안 된다")):
            self.assertEqual(checks.offscreen_hits(P), [])
        self.assertEqual(checks._place_label_boxes(None, NS(events=P.events, R=NS(cache={})), None, 1.0), [])
        with mock.patch.object(checks, "place_over", side_effect=AssertionError("주 무대 좌표로 재면 안 된다")):
            self.assertEqual(checks.check_label_collision(NS(events=P.events)), [])


class IslandPinCollisionTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0267 §2 — 아일랜드 기록 레인 핀 라벨 겹침(econ v5 52초 "10월 29일 인하"·"12월 10일 인하"): 반대쪽으로 옮기고,
    그래도 겹치면 [island-pin-collision] hard."""

    def _chart(self, dates: list[str]) -> tuple[list[dict], dict]:
        from engine.island import island_box  # noqa: PLC0415

        cst = TimelineStage(config={"start": "2025-06-01", "end": "2026-12-31",
                                    "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"},
                                              {"id": "events", "label": "기록", "kind": "pins"}]})
        cst.fit_island(island_box({"box": "left"})[3], ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        cams = np.tile(np.array([cst.x_of("2026-01-01"), 1.0, 420.0]), (24 * 12, 1))
        pins = [{"type": "marker", "label": f"{d[5:7]}월 {d[8:]}일 인하", "sub": "3.75~4%", "side": "right", "date": d, "lane": "events",
                 "t0": 1.0 + k + k / 24, "t1": 11.0, "world": cst.to_world(date=d, lane="events")} for k, d in enumerate(dates)]
        isl = {"type": "island", "kind": "chart", "box": "left", "t0": 0.0, "t1": 12.0}
        return [isl, *pins], {"stage": cst, "cams": cams, "events": pins}

    def test_close_pins_get_opposite_sides(self) -> None:
        from engine.island import assign_pin_sides, label_check  # noqa: PLC0415

        events, chart = self._chart(["2025-10-29", "2025-12-10"])
        self.assertEqual(len(label_check(events, chart)["pin_collision"]), 1)   # 옮기기 전 = 겹침
        moved = assign_pin_sides(events, chart)
        self.assertTrue(moved)
        self.assertEqual(label_check(events, chart)["pin_collision"], [])

    def test_label_over_other_dot_counts(self) -> None:
        """라벨끼리는 안 겹쳐도 한 핀 라벨이 다른 핀의 점을 덮으면 겹침(econ 콘티 판 v2 56초)."""
        from engine.island import _pin_hit  # noqa: PLC0415

        a_text, a_dot = (10, 0, 100, 20), (0, 3, 14, 17)
        b_text, b_dot = (120, 0, 200, 20), (90, 3, 104, 17)   # a 라벨이 b 점(90~104) 위
        self.assertTrue(_pin_hit(a_text, a_dot, b_text, b_dot))
        self.assertFalse(_pin_hit(a_text, a_dot, (220, 0, 300, 20), (205, 3, 219, 17)))
        self.assertTrue(_pin_hit(a_text, a_dot, (101, 0, 180, 20), (186, 3, 200, 17)))   # 1px 떨어져 맞닿은 라벨도 겹침(간격 하한)

    def test_unavoidable_collision_is_hard(self) -> None:
        from engine.island import assign_pin_sides, label_check  # noqa: PLC0415

        events, chart = self._chart(["2025-11-01", "2025-11-03", "2025-11-05"])   # 셋이 붙어 있으면 반대쪽으로도 겹친다
        assign_pin_sides(events, chart)
        rows = label_check(events, chart)["pin_collision"]
        self.assertTrue(rows)
        P = NS(R=NS(cache={"island_check": {"pin_collision": rows}}))
        self.assertTrue(checks.check_island_pin_collision(P)[0].startswith("[island-pin-collision]"))
        self.assertIn("island_pin_collision", checks.HARD)


class IslandLeftTallTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0268 — left_tall 상자(레인 둘이면 금리 값 영역 ≥ 60px). 기존 left·center·right 는 그대로."""

    def test_left_tall_value_area(self) -> None:
        x, y, w, h = ISLAND.boxes["left_tall"]
        self.assertEqual((x, y, w, h), (24, 52, 540, 344))
        self.assertEqual(ISLAND.boxes["left"][3], 298)
        S = TIMELINE.series  # noqa: N806
        lane = (h - ISLAND.chart.pad_top - ISLAND.chart.pad_bottom) / 2
        self.assertGreaterEqual(min(lane, ISLAND.chart.lane_h_max) * (1 - S.lane_pad_top - S.lane_pad_bottom), 60)

    def test_island_cap_independent_of_main_stage(self) -> None:
        """D-0269 — 아일랜드 레인 상한(island.chart.lane_h_max)은 fit_island 만, 주 무대(stage_timeline.lane_h) 와 독립."""
        cfg = {"start": "2025-06-01", "end": "2026-12-31", "lanes": [{"id": "policy_rate", "label": "금리", "kind": "step", "unit": "%"},
                                                                     {"id": "events", "label": "기록", "kind": "pins"}]}
        isl = TimelineStage(config=cfg)
        isl.fit_island(ISLAND.boxes["left_tall"][3], ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        main = TimelineStage(config=cfg)
        self.assertEqual(isl.y_px_per_unit, ISLAND.chart.lane_h_max)
        self.assertEqual(main.y_px_per_unit, TIMELINE.lane_h)
        self.assertGreater(ISLAND.chart.lane_h_max, TIMELINE.lane_h)

    def test_ticks_half_step_and_label_skip(self) -> None:
        """D-0268 §2 — ticks_max 3: 범위 2%p 는 간격 0.5(4 구간). 라벨 간격이 axis_label_min_gap_px 미만이면 중간 라벨 생략."""
        from engine.layers.series import axis_label_values, nice_step  # noqa: PLC0415

        self.assertEqual(LR.ticks_max, 3)
        self.assertEqual(nice_step(2.0), 0.5)
        self.assertEqual(axis_values((3.0, 5.0)), [3.0, 3.5, 4.0, 4.5, 5.0])
        st = _stage("2025-01-01")
        v = _P(st).cams[0]
        from engine.projection import View  # noqa: PLC0415

        view = View(st, v)
        labs = axis_label_values(view, st, "policy_rate", (3.0, 5.0))
        self.assertEqual((labs[0], labs[-1]), (3.0, 5.0))
        ys = [view.to_screen(0.0, __import__("engine.layers.series", fromlist=["value_y"]).value_y(st, "policy_rate", (3.0, 5.0), x))[1] for x in labs]
        self.assertTrue(all(abs(a - b) >= TIMELINE.series.axis_label_min_gap_px for a, b in zip(ys, ys[1:])))


if __name__ == "__main__":
    unittest.main()

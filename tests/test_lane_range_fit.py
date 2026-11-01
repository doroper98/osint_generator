"""v7.4.0 back_and_forth D-0263 — 시간축 레인 값 범위를 데이터에 맞춘다(사용자 의견 UF-140).

UF-140 원문: "그리고 금리 같이 변동이 크지 않은 데이터나 차트의 가로축을 그렇개 늘려버리면 그냥 가로로 펼쳐진 직선으로밖에 안보인다."
- lane_range fit: 무대 기간 안 데이터 [최소 − pad, 최대 + pad], 최소 폭(단위별), 눈금 반올림, 0 이 아닌 시작이면 출처 줄 표기.
- [flat-lane] hard: 카메라가 보여 준 구간의 세로 폭 ÷ 레인 범위 < flat_lane_min_ratio.
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock
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
                               "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"}]})
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


class AxisEmptyBandTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0277 §3(정정) — 끝 값은 반 눈금 단위로 내림·올림, [axis-empty-band] hard.
    showcase_econ 금리 레인(목표 범위 띠 + 실효금리 + SEP 점도표, 무대 2025-06~2028): 데이터 3.125~4.5 → 옛 3~5(위 빈 띠 25 %) → 3~4.75(14 %)."""

    EV = [{"type": "series", "lane": "policy_rate", "series_id": "DFEDTARL", "upper_id": "DFEDTARU", "t0": 0.0, "t1": 9.0},
          {"type": "series", "lane": "policy_rate", "series_id": "FEDFUNDS", "t0": 0.0, "t1": 9.0},
          {"type": "series", "lane": "policy_rate", "series_id": "SEP_20260916", "style": "projection", "t0": 0.0, "t1": 9.0}]

    def _st(self) -> TimelineStage:
        st = TimelineStage(config={"start": "2025-06-01", "end": "2028-12-31",
                                   "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"}]})
        st.fit_frame(tuple(TIMELINE.frame.box), ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        return st

    def test_econ_range(self) -> None:
        rng = lane_range(self.EV, "policy_rate", self._st())
        self.assertEqual(rng, (3.0, 4.75))   # D-0277 §3 정정 — 끝 값 반 눈금(0.25) 올림
        self.assertEqual(axis_values(rng), [3.0, 3.5, 4.0, 4.5, 4.75])   # 중간 눈금은 0.5 배수
        self.assertEqual(LR.end_round, "half_step")

    def test_empty_band_hard(self) -> None:
        st = self._st()
        P = NS(R=NS(stage=st, cache={"series_range": {"policy_rate": (3.0, 5.0)}}), cams=np.tile(np.array([st.x_of("2026-06-01"), 1.0, 420.0]), (24, 1)),
               n_frames=24, events=self.EV)
        out = checks.check_axis_empty_band(P)
        self.assertTrue(out and "[axis-empty-band]" in out[0] and "위" in out[0])   # 4.5~5.0 = 25 % > 15 %
        self.assertIn("axis_empty_band", checks.HARD)
        P.R.cache["series_range"]["policy_rate"] = lane_range(self.EV, "policy_rate", st)
        self.assertEqual(checks.check_axis_empty_band(P), [])


class IslandPathTest(unittest.TestCase):
    """v7.4.0 — 차트 아일랜드(사진 배경 + 시간축 차트) 경로에도 같은 장치(C12 §3): [flat-lane](UF-140)·시리즈 레인 덮개(UF-129).
    showcase_econ 연출 v4(backdrop + island)에서 금리 선이 0~7.5% 레인에 평평하게 그려지고 점도표가 차트를 덮었는데 두 검사가 돌지 않았다."""

    def _P(self, start: str) -> NS:  # noqa: N802
        from engine.island import island_box  # noqa: PLC0415

        cst = TimelineStage(config={"start": start, "end": "2026-12-31",
                                    "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"}]})
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
    """v7.4.0 back_and_forth D-0274 §1②(UF-143 "차트에 글씨가 너무 겹치네") — 값 레인 위 핀 라벨은 선 위·아래 두 단(+1·+2·−1·−2) 중
    교차 0 인 첫 단. 넷 다 막히면 점만(dropped). 교차가 남으면 [island-pin-collision] hard."""

    def _scene(self, dates: list[str], gap_sec: float = 1.0) -> tuple[list[dict], object]:
        from engine.island import island_box, island_view_at  # noqa: PLC0415
        from engine.pin_labels import PinScene  # noqa: PLC0415
        from engine.project import pins_on_series  # noqa: PLC0415

        cst = TimelineStage(config={"start": "2025-06-01", "end": "2026-12-31",
                                    "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"}]})
        cst.fit_island(island_box({"box": "left_tall"})[3], ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        cams = np.tile(np.array([cst.x_of("2026-01-01"), 1.0, 420.0]), (24 * 12, 1))
        ser = {"type": "series", "lane": "policy_rate", "series_id": "FEDFUNDS", "style": "step", "grow": False, "t0": 0.0, "t1": 12.0,
               "slot": 0, "key": 0, "lane_n": 1, "lane_source": "FRED", "axis": True}
        pins = [{"type": "marker", "label": f"{d[5:7]}월 {d[8:]}일 인하", "sub": "3.75~4%", "date": d, "lane": "policy_rate",
                 "t0": 1.0 + k * gap_sec, "t1": 11.0} for k, d in enumerate(dates)]
        rng = lane_range([ser], "policy_rate", cst)
        pins_on_series([ser, *pins], cst, {"policy_rate": rng})
        isl = {"type": "island", "kind": "chart", "box": "left_tall", "t0": 0.0, "t1": 12.0}
        chart = {"stage": cst, "cams": cams, "events": [ser, *pins]}
        return pins, PinScene(cst, [ser, *pins], {"policy_rate": rng}, {}, island_view_at([isl, ser, *pins], chart))

    def test_rows_clear_all_obstacles(self) -> None:
        from engine.pin_labels import assign_pin_rows, pin_label_check  # noqa: PLC0415

        pins, scene = self._scene(["2025-10-29", "2025-12-10"])
        dropped = assign_pin_rows(scene)
        self.assertEqual(dropped, [])
        self.assertTrue(all(p["pin_row"] in (1, 2, -1, -2) for p in pins))
        self.assertNotEqual(pins[0]["pin_row"], pins[1]["pin_row"])   # 가까운 두 핀은 다른 단
        self.assertEqual(pin_label_check(scene), [])

    def test_crowded_pins_drop_label_or_hard(self) -> None:
        from engine.pin_labels import assign_pin_rows, pin_label_check  # noqa: PLC0415

        pins, scene = self._scene(["2025-11-01", "2025-11-03", "2025-11-05", "2025-11-07", "2025-11-09"], gap_sec=0.1)
        dropped = assign_pin_rows(scene)
        self.assertTrue(dropped)   # 자리 넷이 다 막히면 점만
        self.assertTrue(all(p["pin_row"] is None for p in pins if p["label"] in dropped))
        rows = [{"a": "x", "b": "계열 FEDFUNDS", "t0": 1.0, "t1": 2.0}]
        P = NS(R=NS(cache={"pin_labels": {"collisions": rows}}))
        self.assertTrue(checks.check_island_pin_collision(P)[0].startswith("[island-pin-collision]"))
        self.assertIn("island_pin_collision", checks.HARD)
        self.assertEqual([r for r in pin_label_check(scene) if r["a"] not in dropped and not r["b"].startswith("핀")], [])


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
                                                                     {"id": "inflation", "label": "물가", "kind": "line", "unit": "%"}]}
        isl = TimelineStage(config=cfg)   # 상한은 레인 둘 이상일 때만(D-0274 — 하나면 액자 세로 전체)
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


class EndLabelVsTickTest(unittest.TestCase):
    """v7.4.0 — 감독 지적(preview_v8_zoom): 금리 레인 끝값 라벨 "3.63%" 가 축 눈금 라벨 "3.5%" 와 겹쳤다. 끝값 라벨은 세로로 비킨다."""

    def test_end_label_moves_off_tick_label(self) -> None:
        import cairo  # noqa: PLC0415

        from engine.layers.series import _hits, axis_label_boxes, clear_axis_labels  # noqa: PLC0415
        from engine.projection import View  # noqa: PLC0415

        st = _stage("2025-01-01")
        v = View(st, _P(st).cams[0])
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        ticks = axis_label_boxes(ctx, v, st, "policy_rate", (3.0, 5.0), "%")
        S = TIMELINE.series  # noqa: N806
        t = ticks[1]   # 3.5% 눈금 라벨 자리에 끝값 라벨을 겹쳐 놓는다
        x0, lw, by = t[0] - 4, 34.0, t[3]
        nb = clear_axis_labels(ctx, v, st, "policy_rate", (3.0, 5.0), "%", x0, lw, by)
        box = (x0, nb - S.value_size, x0 + lw, nb)
        # 비킬 자리가 없으면(눈금 간격이 좁다) 그 눈금 라벨을 생략한다 — 그린 눈금 라벨과는 어느 쪽이든 안 겹친다
        drawn = axis_label_boxes(ctx, v, st, "policy_rate", (3.0, 5.0), "%", [box])
        self.assertFalse(any(_hits(box, b) for b in drawn))
        self.assertLess(len(drawn), len(ticks)) if nb == by else self.assertEqual(len(drawn), len(ticks))


class PinsOnSeriesTest(unittest.TestCase):
    """v7.4.0 D-0274 §1①(UF-142) — 사건 핀은 값 레인 위의 점: 월드 y = 그 날짜 계열 값. 계열 없는 레인의 핀은 오류."""

    def test_pin_y_is_series_value(self) -> None:
        from data.series import load_series  # noqa: PLC0415
        from engine.layers.series import value_y  # noqa: PLC0415
        from engine.project import pins_on_series  # noqa: PLC0415

        st = _stage("2025-01-01")
        rng = lane_range(SER, "policy_rate", st)
        ser = {**SER[0], "style": "step"}
        mk = {"type": "marker", "date": "2025-10-29", "lane": "policy_rate", "label": "10월 29일 인하"}
        pins_on_series([ser, mk], st, {"policy_rate": rng})
        want = [v for d, v in load_series("FEDFUNDS").values if d <= date(2025, 10, 29)][-1]
        self.assertEqual(mk["pin_value"], want)
        self.assertAlmostEqual(mk["world"][1], value_y(st, "policy_rate", rng, want))
        self.assertAlmostEqual(mk["world"][0], st.x_of("2025-10-29"))

    def test_pin_on_lane_without_series_is_error(self) -> None:
        from engine.project import ProjectError, pins_on_series  # noqa: PLC0415

        st = _stage("2025-01-01")
        with self.assertRaisesRegex(ProjectError, "계열이 없다"):
            pins_on_series([{"type": "marker", "date": "2025-10-29", "lane": "policy_rate", "label": "x"}], st, {})


class PlotHeightTest(unittest.TestCase):
    """v7.4.0 D-0274 §1①(UF-142) — 값 레인 세로 합 ≥ 액자 안쪽 높이 × plot_min_ratio. 레인 하나면 lane_h 상한 없이 틀 세로 전체."""

    def _P(self, lanes: list[dict]) -> NS:  # noqa: N802
        st = TimelineStage(config={"start": "2025-01-01", "end": "2026-12-31", "lanes": lanes})
        st.fit_frame(tuple(TIMELINE.frame.box), ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        return NS(R=NS(stage=st, cache={}), cams=None, events=SER)

    def test_single_lane_fills_frame(self) -> None:
        P = self._P([{"id": "policy_rate", "label": "금리", "kind": "step", "unit": "%"}])  # noqa: N806
        plot, inner = checks.plot_height(P)
        self.assertGreater(plot, TIMELINE.lane_h)   # 상한 96 을 넘어 틀 세로 전체
        self.assertEqual(checks.check_plot_height(P), [])

    def test_stacked_lanes_fail(self) -> None:
        lanes = [{"id": f"l{i}", "label": f"레인{i}", "kind": "line", "unit": "%"} for i in range(4)]
        P = self._P(lanes)  # noqa: N806
        P.events = [{**SER[0], "lane": "l0"}]
        with mock.patch.object(P.R.stage, "y_px_per_unit", 30.0):   # 레인 넷 × 30 = 120 < 270 × 0.7
            self.assertTrue(checks.check_plot_height(P))


class AxisLabelColumnTest(unittest.TestCase):
    """v7.4.0 — 감독 지시(R-0273 관찰): 금리 선이 오른쪽 축 눈금 라벨 "3.5%" 를 가로질렀다. 축 값 라벨 열은 예약 열 — 선이 들어가지 않는다."""

    def test_line_end_left_of_label_column(self) -> None:
        import cairo  # noqa: PLC0415

        from engine.layers.series import axis_label_boxes, draw_series, plot_right  # noqa: PLC0415
        from engine.projection import View  # noqa: PLC0415
        from engine.style import C  # noqa: PLC0415

        st = _stage("2025-01-01")
        P = _P(st, center="2026-06-20", w=150.0)   # noqa: N806 — 자료 끝(2026-08 달의 끝)이 라벨 열 안에 오는 자리
        v = View(st, P.cams[0])
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(v.ox + v.vw) + 1, int(v.oy + v.vh) + 1)
        ctx = cairo.Context(surf)
        rng = P.R.cache["series_range"]["policy_rate"]
        pr = plot_right(ctx, v, st, "policy_rate", rng, "%")
        self.assertLess(pr, min(b[0] for b in axis_label_boxes(ctx, v, st, "policy_rate", rng, "%")))
        e = {"type": "series", "lane": "policy_rate", "series_id": "FEDFUNDS", "style": "step", "col": "amber", "grow": False,
             "axis": False, "slot": 1, "t0": 0.0, "t1": 9.0, "lane_n": 1}
        draw_series(ctx, P.R, v, 4.0, e)
        surf.flush()
        a = np.ndarray((surf.get_height(), surf.get_stride() // 4, 4), np.uint8, surf.get_data())[:, :surf.get_width()]
        rgb = np.array([round(c * 255) for c in C["amber"]])
        hit = np.abs(a[..., 2::-1][..., :3].astype(int) - rgb).max(axis=2) < 40
        hit &= a[..., 3] > 200
        xs = np.nonzero(hit.any(axis=0))[0]
        self.assertGreater(len(xs), 0)
        self.assertLess(xs.max(), pr + 1)   # 선 끝 x < 라벨 열 x


if __name__ == "__main__":
    unittest.main()

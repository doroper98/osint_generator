"""시간축 무대 TimelineStage (v4.3.0, docs/handoff/20 §2.3·§6, back_and_forth D-0084 작업 3·9, D-0085 A).

프로토콜 준수·to_world 왕복·압축 연속·LOD·압축 물결 표시·비등방 View(세로 척도 고정)·앵커 키 검사.
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from pathlib import Path

import cairo
import numpy as np
import yaml

from engine.direction import Direction, DirectionError, build, shot_stages
from engine.projection import View
from engine.stage import Stage, StageError, StageSet, attach_world, make_stage
from engine.stage_timeline import TimelineError, TimelineStage
from engine.style import C, H_OUT, TIMELINE, W_OUT
from engine.timebase import Timebase
from tests.test_direction_schema import _plan

REPO = Path(__file__).resolve().parent.parent
LANES = [{"id": "policy_rate", "label": "기준금리", "kind": "step", "unit": "%"},
         {"id": "inflation", "label": "물가상승률", "kind": "line", "unit": "%"},
         {"id": "events", "label": "사건", "kind": "pins"}]
CFG = {"start": "2019-01-01", "end": "2026-10-01", "lanes": LANES,
       "compress": [{"from": "2019-06-01", "to": "2021-01-01", "factor": 0.25}]}


def stage(cfg: dict | None = None) -> TimelineStage:
    return make_stage("timeline", config=cfg or CFG)  # type: ignore[return-value]


class ProtocolTest(unittest.TestCase):
    def test_is_stage(self) -> None:
        s = stage()
        self.assertIsInstance(s, Stage)
        self.assertEqual(s.anchor_keys, ("date", "lane"))
        self.assertEqual(s.bounds[:2], (0.0, 0.0))
        self.assertEqual(s.bounds[3], 3.0)

    def test_config_required(self) -> None:
        with self.assertRaises(TimelineError):
            make_stage("timeline")

    def test_bad_config_rejected(self) -> None:
        for bad in ({**CFG, "end": "2018-01-01"},
                    {**CFG, "compress": [{"from": "2018-01-01", "to": "2019-06-01", "factor": 0.5}]},
                    {**CFG, "compress": [{"from": "2020-01-01", "to": "2020-06-01", "factor": 1.5}]},
                    {**CFG, "lanes": LANES + [LANES[0]]}):
            with self.assertRaises(ValueError):
                stage(bad)


class WorldTest(unittest.TestCase):
    def test_round_trip_days(self) -> None:
        s = stage()
        d = date(2019, 1, 1)
        while d < date(2026, 10, 1):
            x, y = s.to_world(date=d.isoformat(), lane="inflation")
            self.assertEqual(s.from_world(x, y), {"date": d.isoformat(), "lane": "inflation"})
            d += timedelta(days=37)

    def test_compress_continuous_monotonic(self) -> None:
        s = stage()
        xs = [s.x_of(date(2019, 1, 1) + timedelta(days=k)) for k in range(0, 2800)]
        self.assertTrue(all(b > a for a, b in zip(xs, xs[1:])))
        steps = {round(b - a, 6) for a, b in zip(xs, xs[1:])}
        self.assertEqual(steps, {1.0, 0.25})   # 압축 안 하루 = factor 일, 밖 = 1일(경계에서 끊김 없음)
        self.assertAlmostEqual(s.x_of("2021-01-01") - s.x_of("2019-06-01"), (date(2021, 1, 1) - date(2019, 6, 1)).days * 0.25)

    def test_lane_is_id_string(self) -> None:
        s = stage()
        self.assertEqual(s.to_world(date="2022-01-01", lane="policy_rate")[1], 2.5)
        self.assertEqual(s.to_world(date="2022-01-01")[1], 1.5)   # lane 없음 = 세로 가운데(카메라)
        with self.assertRaises(TimelineError):
            s.to_world(date="2022-01-01", lane=1)   # type: ignore[arg-type]
        with self.assertRaises(TimelineError):
            s.to_world(date="2022-01-01", lane="nope")
        with self.assertRaises(TimelineError):
            s.to_world(lon=1.0, lat=2.0)

    def test_mercator_rejects_timeline_anchor(self) -> None:
        with self.assertRaises(StageError):
            make_stage("mercator").to_world(date="2022-01-01", lane="events")


class ViewTest(unittest.TestCase):
    def test_vertical_scale_fixed(self) -> None:
        """D-0085 A — 세로 배율 = lane_h, w 는 시간 폭만. 레인 3개(288px)는 레인 영역 가운데."""
        s = stage()
        for w in (2000.0, 400.0, 30.0):
            v = View(s, np.array([1200.0, 1.5, w]))
            self.assertEqual((v.sy, v.s), (TIMELINE.lane_h, W_OUT / w))
            top = v.to_screen(0, 3.0)[1]
            bot = v.to_screen(0, 0.0)[1]
            self.assertAlmostEqual(bot - top, 3 * TIMELINE.lane_h)
            self.assertAlmostEqual(top - TIMELINE.area_top, TIMELINE.area_bottom - bot)

    def test_w_clamped_to_range(self) -> None:
        s = stage()
        v = View(s, np.array([0.0, 1.5, 1e6]))
        self.assertEqual((v.x0, v.w), (0.0, s.bounds[2]))

    def test_tall_lanes_follow_camera_y(self) -> None:
        lanes = [{"id": f"l{i}", "label": f"L{i}", "kind": "line"} for i in range(6)]
        s = stage({"start": "2020-01-01", "end": "2021-01-01", "lanes": lanes})
        a = View(s, np.array([100.0, 6.0, 100.0])).y1
        b = View(s, np.array([100.0, 0.0, 100.0])).y1
        self.assertGreater(a, b)
        for y1 in (a, b):   # 레인 영역을 벗어나 빈 곳을 보이지 않는다
            v = View(s, np.array([100.0, 6.0 if y1 == a else 0.0, 100.0]))
            self.assertLessEqual(v.to_screen(0, 6.0)[1], TIMELINE.area_top + 1e-9)
            self.assertGreaterEqual(v.to_screen(0, 0.0)[1], TIMELINE.area_bottom - 1e-9)


class LodTest(unittest.TestCase):
    def test_tick_unit_by_w(self) -> None:
        s = stage()
        L = TIMELINE.lod  # noqa: N806
        self.assertEqual(s.tick_unit(L.quarter_below_w + 1), "year")
        self.assertEqual(s.tick_unit(L.quarter_below_w - 1), "quarter")
        self.assertEqual(s.tick_unit(L.month_below_w - 1), "month")
        self.assertEqual(s.tick_unit(L.day_below_w - 1), "day")

    def test_labels_change_with_zoom(self) -> None:
        s = stage()
        wide = View(s, np.array([1800.0, 1.5, 2600.0]))
        near = View(s, np.array([s.x_of("2022-03-16"), 1.5, 30.0]))
        self.assertTrue(all(k == "year" for _, k in s.ticks(wide)))
        self.assertEqual(s.tick_unit(near.w), "day")
        self.assertTrue(any(k == "minor" for _, k in s.ticks(near)))
        self.assertEqual(s.tick_label(date(2022, 3, 15), "day"), "3.15")
        self.assertEqual(s.tick_label(date(2022, 1, 1), "day"), "2022")


class CompressMarkTest(unittest.TestCase):
    def _render(self, s: TimelineStage, v: View) -> np.ndarray:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
        s.render_base(cairo.Context(surf), v)
        s.draw_labels(cairo.Context(surf), v, [], 1.0)
        surf.flush()
        return np.ndarray((H_OUT, W_OUT, 4), np.uint8, surf.get_data())[:, :, 2::-1].astype(int)

    def test_wave_drawn_where_compressed(self) -> None:
        """압축 메타 ↔ 화면 표시(20 §5.3): 압축 구간이 화면에 걸리면 경계에 물결(amber) 이 그려진다."""
        s = stage()
        v = View(s, np.array([s.x_of("2020-06-01"), 1.5, 1200.0]))
        self.assertEqual(len(s.compress_on_screen(v)), 1)
        img = self._render(s, v)
        amber = np.array(C[TIMELINE.wave.color]) * 255
        xa = int(v.to_screen(s.x_of("2019-06-01"), 0)[0])
        near = img[:, max(0, xa - 5): xa + 6]
        self.assertTrue((np.abs(near - amber).sum(axis=2) < 90).any(), "압축 경계에 물결 없음")

    def test_no_wave_without_compress(self) -> None:
        s = stage({**CFG, "compress": []})
        v = View(s, np.array([s.x_of("2020-06-01"), 1.5, 1200.0]))
        self.assertEqual(s.compress_on_screen(v), [])


class DirectionTimelineTest(unittest.TestCase):
    def _doc(self) -> Direction:
        ex = yaml.safe_load((REPO / "tests" / "fixtures" / "preview" / "stage_timeline.yaml").read_text(encoding="utf-8"))
        return Direction.model_validate(ex["direction"])

    def test_preview_example_builds(self) -> None:
        doc = self._doc()
        self.assertEqual(doc.main_stage(), "timeline")
        cfg = doc.stage_settings("timeline")
        self.assertEqual([ln["id"] for ln in cfg["lanes"]], ["policy_rate", "inflation", "events"])   # 장르 프로필 기본 레인
        ss = StageSet(configs=doc.stage_configs())
        keys, events, _ = build(doc, Timebase(_plan()), ss.get("timeline"))
        self.assertEqual(keys[1].w, 60)
        st = ss.get("timeline")
        self.assertEqual((keys[1].x, keys[1].y), st.to_world(date="2022-03-16", lane="events"))
        shots = shot_stages(doc, Timebase(_plan()), ss.get)
        self.assertEqual([s.stage for s in shots], ["timeline", "timeline"])
        from engine.registry import validate_events  # noqa: PLC0415

        ev = validate_events(events)
        attach_world(ev, st)
        self.assertEqual(ev[0]["world"], st.to_world(date="2022-03-16", lane="events"))

    def test_camera_anchor_must_match_stage(self) -> None:
        raw = self._doc().model_dump(exclude_none=True)
        raw["shots"][1]["camera"] = {"lon": 1.0, "lat": 2.0, "w": 60}
        with self.assertRaisesRegex(ValueError, "앵커"):
            Direction.model_validate(raw)

    def test_map_marker_on_timeline_is_error(self) -> None:
        doc = self._doc()
        st = StageSet(configs=doc.stage_configs()).get("timeline")
        from engine.registry import validate_events  # noqa: PLC0415

        ev = validate_events([{"type": "marker", "t0": 0, "t1": 1, "lon": 56.3, "lat": 26.5, "label": "호르무즈"}])
        with self.assertRaises(ValueError):
            attach_world(ev, st)

    def test_stage_config_for_unused_stage_is_error(self) -> None:
        raw = self._doc().model_dump(exclude_none=True, by_alias=True)
        raw["stage_config"]["mercator"] = {"x": 1}
        with self.assertRaises(ValueError):
            Direction.model_validate(raw)


if __name__ == "__main__":
    unittest.main()


class BacktrackTest(unittest.TestCase):
    """20 §6 — 시간축 카메라는 왼쪽 → 오른쪽이 기본. 되돌아가면 shots 경고, reason 이 있으면 통과."""

    def test_backtrack_warning_and_reason(self) -> None:
        from engine.shots import ShotStage, timeline_backtrack  # noqa: PLC0415

        a = ShotStage(t=0, mode="cut", stage="timeline", x=500, y=1.5, w=300)
        b = ShotStage(t=10, mode="move", stage="timeline", x=200, y=1.5, w=300)
        self.assertEqual(len(timeline_backtrack([a, b])), 1)
        self.assertEqual(timeline_backtrack([a, ShotStage(**{**b.__dict__, "reason": "끝 물러나기"})]), [])
        self.assertEqual(timeline_backtrack([a, ShotStage(**{**b.__dict__, "x": 800})]), [])
        self.assertEqual(timeline_backtrack([ShotStage(**{**a.__dict__, "stage": "mercator"}), ShotStage(**{**b.__dict__, "stage": "mercator"})]), [])

    def test_grow_front_reaches_end_when_view_reaches_end(self) -> None:
        from types import SimpleNamespace  # noqa: PLC0415

        from engine.project import prepare_series  # noqa: PLC0415
        from engine.registry import validate_events  # noqa: PLC0415
        from engine.style import FPS  # noqa: PLC0415

        s = stage()
        ev = validate_events([{"type": "series", "t0": 0, "t1": 5, "lane": "policy_rate", "series_id": "FEDFUNDS", "style": "step"}])
        n = int(5 * FPS) + 1
        R = SimpleNamespace(stage=s, cache={})  # noqa: N806
        prepare_series(R, ev, np.tile(np.array([s.bounds[2] / 2, 1.5, s.bounds[2]]), (n, 1)), n)
        self.assertAlmostEqual(R.cache["series_front"][0][-1], s.bounds[2], places=6)   # 전체 화면 = 전부 드러남
        prepare_series(R, ev, np.tile(np.array([500.0, 1.5, 400.0]), (n, 1)), n)
        self.assertAlmostEqual(R.cache["series_front"][0][-1], 300 + 400 * TIMELINE.series.playhead, places=6)

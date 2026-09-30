"""G12 아일랜드(v5.1.0, back_and_forth D-0123 §1·D-0126 Q1~Q4 A).

- Q1: backdrop 주 무대의 `stage: timeline` 숏 = 차트 아일랜드 뷰포트 카메라(무대 전환 아님).
- Q2: 차트 아일랜드 레인 세로 척도 = min(lane_h, 레인 영역 ÷ 레인 수) — 넘침 0.
- Q3: 제자리 상자 교차·자막 구역 교차·동시 수 초과 = [island-overlap] hard.
- Q4: backdrop 무대 위 패널 = 아일랜드 상자(덮개 대신). 다른 무대 패널 무변경.
- 시간축 앵커 이벤트는 차트 아일랜드 구간 안에서만(밖이면 오류 — 조용히 안 보이는 것 금지, P6).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

import cairo
import yaml

from engine import checks
from engine.direction import Direction, is_island_shot
from engine.island import draw_frame, island_box, island_overlap
from engine.project import check_islands, island_chart_events
from engine.projection import View
from engine.shots import ShotStage, stage_continuity
from engine.stage import StageSet
from engine.style import ISLAND, TIMELINE
from rules import load_rules
from tests.anti_inertia._ast_util import REPO

PREVIEW = REPO / "tests" / "fixtures" / "preview"
SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from


def _tl_stage():  # noqa: ANN202
    raw = yaml.safe_load((PREVIEW / "stage_timeline.yaml").read_text(encoding="utf-8"))["direction"]
    cfg = {**raw["stage_config"]["timeline"], "lanes": [{"id": f"l{i}", "label": f"L{i}", "kind": "line"} for i in range(4)]}
    return StageSet(configs={"timeline": cfg}).get("timeline")


class CameraTest(unittest.TestCase):
    def test_timeline_shot_is_island_camera_not_switch(self) -> None:
        raw = yaml.safe_load((PREVIEW / "stage_backdrop.yaml").read_text(encoding="utf-8"))["direction"]
        raw = {**raw, "stage_config": {"timeline": {"start": "2019-01-01", "end": "2026-12-31"}},
               "shots": raw["shots"] + [{"at": 0, "mode": "cut", "dur": 0, "stage": "timeline", "camera": {"date": "2026-01-01", "w": 400}}]}
        doc = Direction.model_validate(raw)
        self.assertEqual([is_island_shot(doc, s, doc.main_stage()) for s in doc.shots], [False, True])
        ss = [ShotStage(t=0, mode="cut", stage="backdrop", x=0, y=0, w=854),
              ShotStage(t=0, mode="cut", stage="timeline", x=1, y=1, w=400, island=True)]
        self.assertEqual(stage_continuity(ss), [])   # 아일랜드 카메라는 무대 전환이 아니다

    def test_viewport_width_scales_days(self) -> None:
        st = _tl_stage()
        v = View(st, (1000.0, 2.0, 400.0), viewport=(540.0, 298.0))
        self.assertAlmostEqual(v.s, 540.0 / 400.0)
        self.assertEqual((v.vw, v.vh), (540.0, 298.0))


class LaneFitTest(unittest.TestCase):
    def test_lane_auto_fit_no_overflow(self) -> None:
        st = _tl_stage()
        h = ISLAND.boxes["center"][3]
        st.fit_island(h, ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
        area = h - ISLAND.chart.pad_top - ISLAND.chart.pad_bottom
        self.assertAlmostEqual(st.y_px_per_unit, min(TIMELINE.lane_h, area / 4))
        self.assertLessEqual(st.n * st.y_px_per_unit, area + 1e-9)
        v = View(st, (1000.0, 2.0, 400.0), viewport=(ISLAND.boxes["center"][2], h))
        top, _ = st.lane_screen(v, 0)
        _, bot = st.lane_screen(v, st.n - 1)
        self.assertGreaterEqual(top, ISLAND.chart.pad_top - 1e-6)
        self.assertLessEqual(bot, h - ISLAND.chart.pad_bottom + 1e-6)
        self.assertTrue(st.island)


def _isl(t0: float, t1: float, box: str = "center") -> dict:
    return {"type": "island", "kind": "chart", "box": box, "t0": t0, "t1": t1}


class OverlapTest(unittest.TestCase):
    def test_intersection_hard(self) -> None:
        b = [("a", 0, 10, (0.0, 0.0, 100.0, 100.0)), ("b", 5, 12, (50.0, 50.0, 100.0, 100.0)), ("c", 20, 30, (50.0, 50.0, 10.0, 10.0))]
        out = island_overlap(b)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[island-overlap] a ↔ b"))
        self.assertIn("island_overlap", checks.HARD)

    def test_subtitle_zone_and_concurrency(self) -> None:
        self.assertEqual(len(island_overlap([("low", 0, 5, (0.0, SUB_Y - 10, 50.0, 20.0))])), 1)
        n = ISLAND.max_concurrent + 1
        many = [(f"i{k}", 0, 5, (k * 100.0, 0.0, 90.0, 90.0)) for k in range(n)]
        self.assertTrue(any("동시 아일랜드" in s for s in island_overlap(many)))

    def test_rule_boxes_clear_subtitle(self) -> None:
        for name, (x, y, w, h) in ISLAND.boxes.items():
            self.assertLessEqual(y + h, SUB_Y, name)
        self.assertEqual(island_box({"box": "left"}), tuple(ISLAND.boxes["left"]))


class WiringTest(unittest.TestCase):
    def test_timeline_events_only_inside_island(self) -> None:
        ser = {"type": "series", "t0": 1.0, "t1": 50.0}
        pin = {"type": "marker", "t0": 2.0, "t1": 3.0, "date": "2026-09-16", "lane": "events"}
        ev = [_isl(0.0, 40.0), ser, pin]
        island_chart_events(ev)
        self.assertTrue(ser["in_island"] and pin["in_island"])
        errs = check_islands(ev, "backdrop", object())
        self.assertEqual(len(errs), 1)
        self.assertIn("차트 아일랜드 구간 밖", errs[0])
        self.assertTrue(check_islands([_isl(0, 5)], "mercator", None))   # island 는 backdrop 무대에만
        self.assertTrue(check_islands([_isl(0, 5), _isl(4, 9)], "backdrop", object()))   # 차트 아일랜드 겹침

    def test_panel_on_backdrop_uses_island_box(self) -> None:
        from engine.panels.base import make_panel_renderer  # noqa: PLC0415

        drawn: list[str] = []
        fn = make_panel_renderer(lambda ctx, R, t, e, a: drawn.append("body"))  # noqa: N803
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
        e = {"t0": 0.0, "t1": 10.0}
        with mock.patch("engine.island.draw_frame", side_effect=lambda *a: drawn.append("frame")), \
             mock.patch("engine.panels.base.draw_panel_cover", side_effect=lambda *a: drawn.append("cover")):
            fn(ctx, NS(stage=NS(name="backdrop")), 5.0, e)
            fn(ctx, NS(stage=NS(name="mercator")), 5.0, e)
        self.assertEqual(drawn, ["frame", "body", "cover", "body"])   # 지도 무대 패널 무변경(Q4 A)

    def test_frame_draws(self) -> None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
        draw_frame(cairo.Context(surf), tuple(ISLAND.boxes["center"]), 1.0)
        surf.flush()
        x, y = int(ISLAND.boxes["center"][0] + 40), int(ISLAND.boxes["center"][1] + 40)
        self.assertGreater(surf.get_data()[(y * 854 + x) * 4 + 3], 0)


if __name__ == "__main__":
    unittest.main()

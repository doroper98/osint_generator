"""G7 패널 장면 인물 뱃지 자리 (v4.8.0, back_and_forth D-0104 D2(c) — dmz_mine M7: 지도 뱃지가 패널에 가렸다)."""

from __future__ import annotations

import unittest

import numpy as np

from engine.placement import PlacementError, resolve_places
from engine.projection import View
from engine.stage import MercatorStage, ym
from rules import load_rules

PL = load_rules().placement
TIERS = {"W": {"lon0": 20.0, "lon1": 150.0, "lat0": -10.0, "lat1": 60.0, "levels": []}}


def view(_t: float) -> View:
    return View(MercatorStage(tiers=TIERS), np.array([56.0, ym(26.0), 14.0]))


def panel(t0: float, t1: float) -> dict:
    return {"type": "panel", "kind": "statement", "t0": t0, "t1": t1}


def badge(t0: float, t1: float, place: str = "map_upper_left") -> dict:
    return {"type": "badge", "kind": "person", "pid": "p", "flag": "kr", "t0": t0, "t1": t1, "label": "인물", "place": place}


class PanelBadgeTest(unittest.TestCase):
    def test_rules_slot(self) -> None:
        self.assertEqual(PL.stage_slots["panel"], {"badge": "panel_badge"})
        self.assertGreaterEqual(len(PL.slots["panel_badge"].screen), 2)

    def test_badge_starting_in_panel_goes_over_panel(self) -> None:
        ev = [panel(0, 10), badge(2, 8)]
        rec = resolve_places(ev, view)
        b = ev[1]
        self.assertTrue(b["over_panel"])
        self.assertEqual(b["screen"], list(PL.slots["panel_badge"].screen[0]))
        self.assertIn("lon", b)                           # 앵커는 남는다(모델 검증)
        self.assertEqual(rec["badge:인물"], "stage:panel_badge")

    def test_badge_outside_panel_unchanged(self) -> None:
        ev = [panel(0, 10), badge(11, 15)]
        resolve_places(ev, view)
        self.assertNotIn("over_panel", ev[1])

    def test_two_concurrent_take_two_points_third_errors(self) -> None:
        ev = [panel(0, 10), badge(1, 8), badge(2, 8)]
        resolve_places(ev, view)
        self.assertNotEqual(ev[1]["screen"], ev[2]["screen"])
        n = len(PL.slots["panel_badge"].screen)
        ev = [panel(0, 10)] + [badge(1 + i * 0.1, 8) for i in range(n + 1)]
        with self.assertRaises(PlacementError):
            resolve_places(ev, view)

    def test_over_panel_badge_drawn_after_panels(self) -> None:
        import inspect

        from engine import render
        src = inspect.getsource(render.render_frame)
        # v4.9.0 D-0108 — 패널 위 뱃지는 레이어 선택(LayerSet.over_panel: 전편 badges.draw_over_panel)으로 그린다
        self.assertLess(src.index('e["type"] == "panel"'), src.index("L.over_panel("))

    def test_over_panel_badge_screen_and_pool(self) -> None:
        from engine.layers.badges import assign_person_sizes, badge_R, screen_xy
        ev = [panel(0, 10), badge(2, 8)]
        resolve_places(ev, view)
        b = ev[1]
        b["R"] = None
        m = {"type": "badge", "kind": "person", "pid": "q", "flag": "us", "R": None, "t0": 0, "t1": 10, "label": "지도"}
        assign_person_sizes([b, m])
        self.assertEqual(badge_R(b, 5), load_rules().layout_480p.badge.R_person_solo)   # 패널 위 풀은 따로 센다
        self.assertEqual(screen_xy(b, view(0)), tuple(b["screen"]))


if __name__ == "__main__":
    unittest.main()

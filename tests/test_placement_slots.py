"""engine/placement — 배치 슬롯(17 §2 `place:`) → 좌표 (v3.1.0, back_and_forth D-0047 작업 5·9)."""

from __future__ import annotations

import unittest

import numpy as np

from engine.placement import PlacementError, resolve_places
from engine.projection import View, ym
from rules import load_rules

PL = load_rules().placement
TIERS = {"W": {"lon0": 20.0, "lon1": 150.0, "lat0": -10.0, "lat1": 60.0, "levels": []}}


def view(_t: float) -> View:
    return View(np.array([56.0, ym(26.0), 14.0]), TIERS, {})


class SlotTest(unittest.TestCase):
    def test_box_slot(self) -> None:
        ev = [{"type": "photo", "t0": 1, "t1": 5, "mid": "rok_iraq", "place": "panel_gap"}]
        rec = resolve_places(ev, view)
        self.assertEqual((ev[0]["x"], ev[0]["y"], ev[0]["w"]), PL.slots["panel_gap"].box)
        self.assertNotIn("place", ev[0])
        self.assertEqual(rec["rok_iraq"], "slot:panel_gap")

    def test_point_slot_inverse_projects(self) -> None:
        ev = [{"type": "badge", "t0": 3, "t1": 8, "label": "서울", "place": "map_upper_right"}]
        resolve_places(ev, view)
        x, y = view(3).xy(ev[0]["lon"], ev[0]["lat"])
        self.assertAlmostEqual(x, PL.slots["map_upper_right"].point[0], places=6)
        self.assertAlmostEqual(y, PL.slots["map_upper_right"].point[1], places=6)

    def test_card_slot_default_y(self) -> None:
        ev = [{"type": "card", "t0": 1, "t1": 2, "place": "card_right"}]
        resolve_places(ev, view)
        self.assertNotIn("y", ev[0])   # null = 렌더러 기본

    def test_wrong_kind_and_unknown_slot(self) -> None:
        with self.assertRaises(PlacementError):
            resolve_places([{"type": "badge", "t0": 0, "t1": 1, "place": "panel_gap"}], view)
        with self.assertRaises(PlacementError):
            resolve_places([{"type": "photo", "t0": 0, "t1": 1, "mid": "x", "place": "nowhere"}], view)

    def test_auto_media_is_v3_slots(self) -> None:
        self.assertEqual(PL.slots[PL.auto_media["clip"]["map"]].box, (40, 150, 300))
        self.assertEqual(PL.slots[PL.auto_media["photo"]["map"]].box, (560, 196, 262))


if __name__ == "__main__":
    unittest.main()

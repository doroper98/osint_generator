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


REPO_HZ = __import__("pathlib").Path(__file__).resolve().parent.parent / "projects" / "hormuz_korea"


@unittest.skipUnless((REPO_HZ / "plan.json").exists(), "hormuz_korea plan.json(로컬 생성물) 없음")
class CheckDirectionPlaceTest(unittest.TestCase):
    """연출 워커의 저장 전 점검은 렌더와 같은 경로 — place 로 둔 뱃지는 좌표 없이도 통과해야 한다(v3.1.0 hormuz_ai 실측 버그)."""

    def test_badge_place_passes(self) -> None:
        from engine.direction import load_direction_doc  # noqa: PLC0415
        from workers.direction_io import check_direction  # noqa: PLC0415

        doc = load_direction_doc(REPO_HZ / "direction.yaml")
        badge = next(e for e in doc.events if e.get("type") == "badge")
        placed = {k: v for k, v in badge.items() if k not in ("lon", "lat", "at_place")} | {"place": "map_upper_right"}
        doc = doc.model_copy(update={"events": [*doc.events, placed]})
        check_direction(doc, REPO_HZ)

    def test_bad_slot_is_value_error(self) -> None:
        from engine.direction import load_direction_doc  # noqa: PLC0415
        from workers.direction_io import check_direction  # noqa: PLC0415

        doc = load_direction_doc(REPO_HZ / "direction.yaml")
        badge = next(e for e in doc.events if e.get("type") == "badge")
        bad = {k: v for k, v in badge.items() if k not in ("lon", "lat", "at_place")} | {"place": "nowhere"}
        with self.assertRaises(ValueError):
            check_direction(doc.model_copy(update={"events": [*doc.events, bad]}), REPO_HZ)

"""engine/framing.frame_points — 자동 프레이밍(v3.3.0, 05 §7-1, D-0056 작업 2)."""

from __future__ import annotations

import math
import unittest

from engine.framing import badge_point, default_reserve, frame_points, marker_point, place, plain_point
from rules import load_rules

FR = load_rules().camera.framing
GULF = [marker_point(56.3, 26.6, "hormuz"), marker_point(54.4, 24.5, "abu_dhabi"), badge_point(51.4, 35.7, 30, "tehran")]


class FramePointsTest(unittest.TestCase):
    def test_all_points_inside_and_minimal(self) -> None:
        r = frame_points(GULF)
        self.assertTrue(r.ok, r.reason)
        ok, _, _ = place(GULF, r.lon, r.lat, r.w)
        self.assertTrue(ok)
        smaller = r.w * 0.97
        if smaller >= FR.w_min:   # 더 작은 w 부터 찾게 해도 그보다 작은 답은 없다 = 최소
            self.assertGreaterEqual(frame_points(GULF, w_min=smaller).w, smaller)
            self.assertFalse(place(GULF, r.lon, r.lat, smaller)[0] and frame_points(GULF, w_min=smaller).w > smaller + 1e-6)

    def test_single_point_gets_min_w(self) -> None:
        self.assertAlmostEqual(frame_points([plain_point(127.0, 37.5, "seoul")]).w, FR.w_min, places=3)

    def test_badge_needs_more_room_than_marker(self) -> None:
        a = frame_points([marker_point(126.9, 37.5), marker_point(129.0, 35.1)])
        b = frame_points([badge_point(126.9, 37.5, 34), badge_point(129.0, 35.1, 34)])
        self.assertGreater(b.w, a.w)

    def test_card_reserve_avoided(self) -> None:
        pts = [marker_point(56.3, 26.6, "hormuz"), marker_point(60.0, 27.0, "east")]
        free = frame_points(pts)
        card = frame_points(pts, reserve=default_reserve(card=True))
        self.assertTrue(card.ok)
        cz = default_reserve(card=True)[1]
        for b in card.boxes.values():
            self.assertFalse(b[0] < cz[2] and cz[0] < b[2] and b[1] < cz[3] and cz[1] < b[3])
        self.assertGreaterEqual(card.w, free.w - 1e-9)

    def test_resolution_independent(self) -> None:
        a = frame_points(GULF, width=854, height=480)
        b = frame_points(GULF, width=1280, height=720)
        self.assertEqual(a.ok, b.ok)
        self.assertAlmostEqual(a.w, b.w, places=6)
        self.assertLess(abs(a.lon - b.lon) + abs(a.lat - b.lat), 0.05)

    def test_bounds_clamp_detects_edge(self) -> None:
        """티어 경계로 카메라가 밀리면 장소가 가장자리에 붙는다 — 클램프한 뒤 검사해 잡아낸다(05 §2.1)."""
        pts = [marker_point(20.5, 20.0, "edge"), marker_point(22.0, 20.0)]
        free = frame_points(pts)
        clamped = frame_points(pts, bounds=(20.0, -10.0, 150.0, 60.0))
        self.assertTrue(free.ok)
        self.assertTrue(clamped.w >= free.w - 1e-9)

    def test_empty_is_error(self) -> None:
        with self.assertRaises(ValueError):
            frame_points([])

    def test_log_spacing_rule_values(self) -> None:
        self.assertTrue(math.isclose(FR.w_min, 2.5) and FR.w_max >= 88)


if __name__ == "__main__":
    unittest.main()

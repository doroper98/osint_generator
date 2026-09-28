"""카드 RESERVED 회피 (D-0032 작업 4·6, D-0033·D36)."""

from __future__ import annotations

import unittest

from engine.reserved import RES, Zone, avoid_badge, presence, push_vector

CARD = (560.0, 70.0, 830.0, 180.0)


class ReservedTest(unittest.TestCase):
    def test_no_overlap_no_move(self) -> None:
        self.assertEqual(avoid_badge((100, 100, 150, 150), [Zone(CARD, 1.0, "card:x")])[:3], (0.0, 0.0, 1.0))

    def test_push_minimal_and_clear(self) -> None:
        b = (780.0, 150.0, 830.0, 200.0)   # 카드 아래쪽에 살짝 걸침
        dx, dy, ka, info = avoid_badge(b, [Zone(CARD, 1.0, "card:x")])
        self.assertEqual(info["strategy"], "push")
        self.assertEqual(info["direction"], "down")   # 아래가 가장 짧다
        self.assertAlmostEqual(dy, CARD[3] + RES.push_gap_px - b[1])
        moved = (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
        self.assertGreaterEqual(moved[1], CARD[3] + RES.push_gap_px)   # 겹침 0
        self.assertEqual(ka, 1.0)

    def test_push_scales_with_card_presence(self) -> None:
        b = (780.0, 150.0, 830.0, 200.0)
        full = avoid_badge(b, [Zone(CARD, 1.0, "c")])[1]
        half = avoid_badge(b, [Zone(CARD, 0.5, "c")])[1]
        self.assertAlmostEqual(half, full * 0.5)

    def test_too_far_hides(self) -> None:
        big = (0.0, 0.0, 854.0, 470.0)   # 화면 거의 전체 — 어느 방향으로도 max_push 안에 못 나감
        dx, dy, ka, info = avoid_badge((400, 200, 450, 250), [Zone(big, 0.8, "card:big")])
        self.assertEqual((dx, dy), (0.0, 0.0))
        self.assertAlmostEqual(ka, 0.2)
        self.assertEqual(info["strategy"], "hide")

    def test_handover_between_cards_is_continuous(self) -> None:
        """한 카드가 빠지는 동안 다른 카드가 떠 있으면 이동이 끊기지 않는다(hormuz review 168.2초)."""
        b = (780.0, 90.0, 830.0, 140.0)
        tall = (560.0, 68.0, 830.0, 196.0)
        ys = [avoid_badge(b, [Zone(tall, a, "article"), Zone(CARD, 1.0, "card")])[1] for a in (1.0, 0.75, 0.5, 0.25, 0.01)]
        steps = [abs(p - q) for p, q in zip(ys, ys[1:])]
        self.assertLess(max(steps), 0.3 * (ys[0] - ys[-1]) + 1e-9)

    def test_presence_leads_in_and_follows_card_out(self) -> None:
        e = {"t0": 10.0, "t1": 20.0}
        self.assertEqual(presence(9.0, e, 0.45), 0.0)
        self.assertGreater(presence(10.0 - RES.lead_sec / 2, e, 0.45), 0.0)   # 카드보다 먼저 비킨다
        self.assertEqual(presence(15.0, e, 0.45), 1.0)
        self.assertEqual(presence(20.0, e, 0.45), 0.0)                          # 카드가 사라지면 영역도 없다

    def test_multiple_zones_cleared(self) -> None:
        z2 = (560.0, 185.0, 830.0, 260.0)
        pv = push_vector((780.0, 150.0, 830.0, 200.0), [Zone(CARD, 1, "a"), Zone(z2, 1, "b")])
        self.assertIsNotNone(pv)
        self.assertIn(pv[2], ("left", "down", "left-down"))


if __name__ == "__main__":
    unittest.main()

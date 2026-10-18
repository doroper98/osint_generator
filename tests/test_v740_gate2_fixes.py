"""v7.4.0 back_and_forth D-0240(게이트 ② 조건부 승인) — 인셋 안전 영역([inset-clipped] hard)·프레스 사진 자료사진 줄([press-credit-missing] hard)·
홀로 뜬 국기 뱃지([badge-orphan] warning)."""

from __future__ import annotations

import unittest

from engine.checks import HARD, WARN, badge_orphans
from engine.layers.article import press_photo_credit_text
from engine.layers.flight import F, inset_box, inset_fits, inset_safe


class InsetSafeTest(unittest.TestCase):
    def test_fallback_side_inside_safe(self) -> None:
        top = inset_safe()[1]
        e = {"inset": {"mid": "x", "side": "up"}}
        b = inset_box(e, 400.0, top + 10)   # 위로 그리면 날짜 배지 줄 위로 잘린다 → 다음 자리
        self.assertTrue(inset_fits(b))
        self.assertGreaterEqual(b[1], top)

    def test_no_fit_reports(self) -> None:
        old = list(F.inset.side_order)
        try:
            F.inset.side_order.clear()
            b = inset_box({"inset": {"mid": "x", "side": "up"}}, 400.0, inset_safe()[1] + 10)
            self.assertFalse(inset_fits(b))   # 대체 자리 없음 → [inset-clipped] 가 잡는다
        finally:
            F.inset.side_order.extend(old)
        self.assertIn("inset_clipped", HARD)


class PressCreditTest(unittest.TestCase):
    def test_official_photo_line(self) -> None:
        s = press_photo_credit_text({"press": "diesel_road_2026_trump_1006"})
        self.assertTrue(s.startswith("자료사진 · 2026. 10. 06"))
        self.assertIn("Public domain", s)
        self.assertIsNone(press_photo_credit_text({}))   # 블러 폴백은 줄 없음
        self.assertIn("press_credit", HARD)


class BadgeOrphanTest(unittest.TestCase):
    def _flag(self, **kw) -> dict:  # noqa: ANN003
        return {"type": "badge", "kind": "flag", "flag": "ru", "label": "러시아", "world": (135.0, 46.0), "t0": 10.0, "t1": 14.0, **kw}

    def test_alone_warns(self) -> None:
        self.assertEqual(len(badge_orphans([self._flag()])), 1)
        self.assertIn("badge_orphan", WARN)

    def test_with_card_or_marker_ok(self) -> None:
        card = {"type": "card", "t0": 10.5, "t1": 14.0}
        self.assertEqual(badge_orphans([self._flag(), card]), [])
        marker = {"type": "marker", "world": (136.0, 47.0), "t0": 9.0, "t1": 15.0}
        self.assertEqual(badge_orphans([self._flag(), marker]), [])


if __name__ == "__main__":
    unittest.main()

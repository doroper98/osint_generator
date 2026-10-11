"""v5.21.3 — 타이틀 카드 제목 폭 맞춤. 맞는 제목은 title_size 그대로(종전 바이트), 넘치는 제목만 줄이고, 최소 크기 밑이면 오류."""

from __future__ import annotations

import unittest

import cairo

from engine.fullcards import TitleOverflowError, title_fit_size
from engine.style import TITLE_CARD, W_OUT
from engine.typography import tw


class TitleFitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def test_fitting_title_unchanged(self) -> None:
        self.assertEqual(title_fit_size(self.ctx, "호르무즈와 한국"), TITLE_CARD.title_size)

    def test_long_title_shrinks_to_room(self) -> None:
        t = "걸프의 새 방패 — 파키스탄군은 왜 사우디에 있나"
        s = title_fit_size(self.ctx, t)
        self.assertLess(s, TITLE_CARD.title_size)
        self.assertGreaterEqual(s, TITLE_CARD.title_min_size)
        self.assertLessEqual(tw(self.ctx, t, s, "disp"), W_OUT * TITLE_CARD.max_w_ratio + 0.5)

    def test_too_long_title_is_error(self) -> None:
        with self.assertRaises(TitleOverflowError):
            title_fit_size(self.ctx, "아주 긴 제목 " * 12)


if __name__ == "__main__":
    unittest.main()

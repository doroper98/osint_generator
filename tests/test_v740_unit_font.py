"""v7.4.0 back_and_forth D-0229 §2.4(UF-111 "십자가 같은 t") — display 숫자 뒤 라틴 단위는 rules fonts.unit_font 로 그린다."""

from __future__ import annotations

import unittest
from unittest import mock

import cairo

from engine import typography as ty
from rules import load_rules


class SplitTest(unittest.TestCase):
    def test_rule(self) -> None:
        self.assertEqual(load_rules().fonts.unit_font, "sans")

    def test_split(self) -> None:
        self.assertEqual(ty.unit_split("750만 t", "disp"), ("750만", " t", "sansbb"))
        self.assertEqual(ty.unit_split("약 590만 t", "dispm"), ("약 590만", " t", "sansb"))
        self.assertEqual(ty.unit_split("3.4 mb/d", "disp")[1], " mb/d")
        self.assertEqual(ty.unit_split("120kb/d", "disp")[:2], ("120", "kb/d"))

    def test_no_split(self) -> None:
        for s in ("45%", "3 / 7", "Hormuz", "1,159개", "2026"):
            self.assertIsNone(ty.unit_split(s, "disp"), s)
        self.assertIsNone(ty.unit_split("750만 t", "sansm"))   # display 글꼴만

    def test_unit_face(self) -> None:
        self.assertEqual(ty.unit_face("t"), "sansbb")
        self.assertEqual(ty.unit_face("척"), "disp")


class RenderTest(unittest.TestCase):
    def _fonts(self, s: str) -> list[str]:
        used: list[str] = []
        real = ty.font

        def rec(ctx: cairo.Context, name: str, size: float) -> None:
            used.append(name)
            real(ctx, name, size)

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 80))
        with mock.patch.object(ty, "font", rec):
            ty.text(ctx, s, 10, 50, 30, "disp", (1, 1, 1), 1.0, 0, "l")
        return used

    def test_unit_glyph_drawn_with_sans(self) -> None:
        self.assertEqual(set(self._fonts("750만 t")), {"disp", "sansbb"})   # 측정(adv)·그리기 호출 모두
        self.assertEqual(set(self._fonts("750")), {"disp"})

    def test_width_consistent(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 80))
        w = ty.text(ctx, "750만 t", 10, 50, 30, "disp", (1, 1, 1), 1.0, 0, "r")
        self.assertAlmostEqual(w, ty.tw(ctx, "750만", 30, "disp") + ty.tw(ctx, " t", 30, "sansbb"))

    def test_disp_latin_log(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 80))
        ty.DISP_LATIN = []
        try:
            ty.text(ctx, "750만 t", 10, 50, 30, "disp")
            ty.text(ctx, "Ton", 10, 50, 30, "disp")
            log = list(ty.DISP_LATIN)
        finally:
            ty.DISP_LATIN = None
        self.assertEqual(log, ["Ton"])


if __name__ == "__main__":
    unittest.main()

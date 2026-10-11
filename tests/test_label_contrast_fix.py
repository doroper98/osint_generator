"""v5.21.2 back_and_forth D-0186 §2-1 — 지명 국소 대비 보정.

검사와 보정이 같은 식(engine.contrast) · 4.5 미만 글자만 다시 그림 · 통과 글자는 바이트 그대로 · 보정 전 측정 항목은 검사 기록에서 빠짐 ·
알파가 검사 문턱 미만이면 손대지 않음 · 기록(stage.label_contrast_fixed).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import cairo
import numpy as np

from engine import typography as ty
from engine.contrast import surface_text_ratio, text_box_ratio
from engine.layers import labels as LB
from rules import load_rules

LIGHT = load_rules().geo.themes.light.map
QA = load_rules().qa_checks


def _surface(gray: float) -> tuple[cairo.ImageSurface, cairo.Context]:
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, 200, 60)
    c = cairo.Context(s)
    c.set_source_rgb(gray, gray, gray)
    c.paint()
    return s, c


def _draw(c: cairo.Context, stage: NS, a: float = 0.82) -> None:
    w = ty.tw(c, "무스카트", 10.5, "sansm")
    ty.text(c, "무스카트", 20, 30, 10.5, "sansm", LIGHT.city_label, a, 2.6, "l", halo_rgb=tuple(LIGHT.halo), contrast="required")
    LB._fix_contrast(c, stage, "무스카트", 20, 30, w, 10.5, "sansm", LIGHT, a, tuple(LIGHT.halo))


class LabelContrastFixTest(unittest.TestCase):
    def setUp(self) -> None:
        ty.CONTRAST_LOG = []

    def tearDown(self) -> None:
        ty.CONTRAST_LOG = None

    def test_rules_present_both_themes(self) -> None:
        g = load_rules().geo.themes
        self.assertIsNotNone(g.light.map.label_contrast_fix)
        self.assertIsNotNone(g.dark.map.label_contrast_fix)

    def test_low_contrast_label_redrawn_and_recorded(self) -> None:
        s, c = _surface(0.38)   # 어두운 바탕 위 light 글자색(진한 잉크) — 대비 부족
        st = NS()
        w = ty.tw(c, "무스카트", 10.5, "sansm")
        ty.text(c, "무스카트", 20, 30, 10.5, "sansm", LIGHT.city_label, 0.82, 2.6, "l", halo_rgb=tuple(LIGHT.halo), contrast="required")
        before = surface_text_ratio(c, ty.CONTRAST_LOG[-1][1], LIGHT.city_label)
        self.assertLess(before, QA.map_contrast_text)
        LB._fix_contrast(c, st, "무스카트", 20, 30, w, 10.5, "sansm", LIGHT, 0.82, tuple(LIGHT.halo))
        self.assertEqual(len(ty.CONTRAST_LOG), 1)   # 보정 전 항목은 빠지고 다시 그린 글자 하나만
        after = surface_text_ratio(c, ty.CONTRAST_LOG[-1][1], LIGHT.city_label)
        self.assertGreater(after, before)
        self.assertEqual(st.label_contrast_fixed, {"무스카트": before})

    def test_passing_label_untouched_bytes(self) -> None:
        s1, c1 = _surface(0.93)
        s2, c2 = _surface(0.93)
        ty.text(c1, "무스카트", 20, 30, 10.5, "sansm", LIGHT.city_label, 0.82, 2.6, "l", halo_rgb=tuple(LIGHT.halo), contrast="required")
        st = NS()
        _draw(c2, st)
        s1.flush(), s2.flush()
        self.assertEqual(bytes(s1.get_data()), bytes(s2.get_data()))
        self.assertFalse(hasattr(st, "label_contrast_fixed"))

    def test_low_alpha_not_touched(self) -> None:
        s, c = _surface(0.38)
        st = NS()
        _draw(c, st, a=QA.map_contrast_min_alpha - 0.05)
        self.assertFalse(hasattr(st, "label_contrast_fixed"))

    def test_check_and_fix_share_formula(self) -> None:
        s, c = _surface(0.5)
        ty.text(c, "무스카트", 20, 30, 10.5, "sansm", LIGHT.city_label, 0.82, 2.6, "l", halo_rgb=tuple(LIGHT.halo), contrast="required")
        box = ty.CONTRAST_LOG[-1][1]
        s.flush()
        buf = np.frombuffer(bytes(s.get_data()), np.uint8).reshape(60, s.get_stride() // 4, 4)[:, :200, :3][..., ::-1]
        from engine.contrast import rel_lum

        whole = text_box_ratio(rel_lum(buf.astype(np.float64) / 255.0), box, LIGHT.city_label)["ratio"]
        self.assertEqual(whole, surface_text_ratio(c, box, LIGHT.city_label))


if __name__ == "__main__":
    unittest.main()

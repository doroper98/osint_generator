"""프리미티브 statement_diff (v4.2.0, docs/handoff/20 §4.2·§10, back_and_forth D-0081 작업 5·9).

데이터 검증 실패 = 오류(P6), 단어 단위 차이, 색 의미 없는 장르 = 오류, 판독 최소 크기, 예약 영역 = 그린 상자.
"""

from __future__ import annotations

import copy
import unittest

import cairo

from engine import typography
from engine.checks import check_glyph_size
from engine.primitives import PrimitiveError, module, primitive_box, style_for
from engine.primitives.statement_diff import diff_tokens
from engine.registry import RegistryError, validate_events
from engine.style import PRIMITIVES, QUOTE_MAX_CHARS
from genres.load import load_genre
from rules import load_rules

FX = module("statement_diff").PREVIEW_FIXTURE


def ev(**over: object) -> dict:
    d = copy.deepcopy(FX)
    d.update(over)
    return d


class StatementDiffDataTest(unittest.TestCase):
    def test_fixture_passes(self) -> None:
        self.assertEqual(validate_events([FX])[0]["id"], "statement_diff")

    def test_invalid_data_is_error(self) -> None:
        bad = {
            "empty source": ev(source=" "),
            "bad date": ev(date="9월 17일"),
            "no change": ev(after=FX["before"]),
            "too long": ev(after="가 " * QUOTE_MAX_CHARS),
            "unknown field": ev(color="red"),
            "missing label": {k: v for k, v in FX.items() if k != "after_label"},
        }
        for why, e in bad.items():
            with self.subTest(why=why), self.assertRaises(RegistryError):
                validate_events([e])

    def test_diff_words(self) -> None:
        left, right = diff_tokens("금리를 동결 한다", "금리를 인하 한다")
        self.assertEqual(left, [("금리를", "same"), ("동결", "removed"), ("한다", "same")])
        self.assertEqual(right, [("금리를", "same"), ("인하", "added"), ("한다", "same")])


class StatementDiffStyleTest(unittest.TestCase):
    def test_genre_without_colors_is_error(self) -> None:
        with self.assertRaisesRegex(PrimitiveError, "added"):
            style_for("statement_diff", load_genre("geopolitics").color_semantics)

    def test_semantic_colors(self) -> None:
        st = style_for("statement_diff", {"added": "green", "removed": "#ff5566", "hike": "rgba(255,122,89,0.5)"})
        self.assertEqual(set(st.colors), {"added", "removed"})   # 요소가 쓰는 키만
        self.assertEqual(st.color("removed")[-1], 1.0)

    def test_fade_in_rule_range(self) -> None:
        self.assertTrue(0.4 <= PRIMITIVES["statement_diff"].fade_sec <= 0.6)   # type: ignore[attr-defined]  # 20 §4.2

    def test_draw_box_and_glyphs(self) -> None:
        e = validate_events([FX])[0]
        st = style_for("statement_diff", {"added": "green", "removed": "ru"})
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
        typography.GLYPH_LOG = []
        try:
            box = module("statement_diff").draw(ctx, None, (e["t0"] + e["t1"]) / 2, e, st)
        finally:
            drawn, typography.GLYPH_LOG = typography.GLYPH_LOG, None
        self.assertEqual(box, primitive_box(e))   # 예약 영역 = 실제 그린 상자
        self.assertTrue(drawn)
        self.assertEqual(check_glyph_size([("sd", s, r, x) for s, r, x in drawn]), [])
        self.assertGreaterEqual(min(s for s, _, _ in drawn), load_rules().layout_480p.min_font_px)
        texts = " ".join(x for _, _, x in drawn)
        self.assertIn(FX["source"], texts)   # 출처·날짜 줄(불변 층)
        self.assertIn(FX["date"], texts)


if __name__ == "__main__":
    unittest.main()

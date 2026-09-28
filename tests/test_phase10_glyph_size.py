"""최소 글자 glyph_size (v3.6.0, back_and_forth D-0066 작업 5 · D-0069 A).

임계 = rules `layout_480p.min_font_px`(9.5, 09 §2 "최소 글자"), 설계 px 판정(해상도 무관), hard.
예외는 역할 레지스트리 `qa_checks.glyph_size_exempt`(end_card·media_meta)뿐 — 역할 없이 그린 글자는 예외가 아니다(기본 엄격).
"""

from __future__ import annotations

import ast
import unittest

import cairo

from engine import checks, typography
from rules import load_rules
from tests.anti_inertia._ast_util import REPO, iter_py

R = load_rules()


class GlyphSizeRuleTest(unittest.TestCase):
    def test_threshold_is_min_font_px(self) -> None:
        self.assertEqual(R.layout_480p.min_font_px, 9.5)
        self.assertFalse(hasattr(R.qa_checks, "glyph_size_min_px"))   # 값은 한 곳(D-0069 요건 1)
        self.assertEqual(R.qa_checks.glyph_size_exempt, ["end_card", "media_meta"])

    def test_body_94_hard(self) -> None:
        out = checks.check_glyph_size([("t=1.00", 9.4, None, "본문 글자")])
        self.assertEqual(len(out), 1)
        self.assertIn("[glyph-size]", out[0])
        self.assertIn("9.4", out[0])

    def test_meta_78_exempt(self) -> None:
        self.assertEqual(checks.check_glyph_size([("t=1.00", 7.8, "media_meta", "U.S. Navy · Public domain")]), [])
        self.assertEqual(checks.check_glyph_size([("END", 7.8, "end_card", "2026. 09. 26 기준")]), [])

    def test_roleless_78_hard(self) -> None:
        self.assertEqual(len(checks.check_glyph_size([("t=1.00", 7.8, None, "U.S. Navy")])), 1)

    def test_at_threshold_passes_and_dedup(self) -> None:
        self.assertEqual(checks.check_glyph_size([("a", 9.5, None, "강원도")]), [])
        self.assertEqual(len(checks.check_glyph_size([("a", 9.0, None, "x"), ("b", 9.0, None, "x")])), 1)

    def test_in_hard(self) -> None:
        self.assertIn("glyph_size", checks.HARD)


class RecorderTest(unittest.TestCase):
    def test_text_records_role(self) -> None:
        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 32, 32))
        typography.GLYPH_LOG = []
        try:
            typography.text(c, "2026. 09 기준", 0, 10, 7.8, "monom", role="end_card")   # 모노 + 한글 런 분할 → 한 번만 기록
            typography.text(c, "", 0, 10, 7.8)                                        # 빈 글자 = 기록 없음
            typography.text(c, "x", 0, 10, 7.8, a=0.0)                                # 보이지 않는 글자 = 기록 없음
        finally:
            log, typography.GLYPH_LOG = typography.GLYPH_LOG, None
        self.assertEqual(log, [(7.8, "end_card", "2026. 09 기준")])

    def test_off_by_default(self) -> None:
        self.assertIsNone(typography.GLYPH_LOG)


class RoleRegistryTest(unittest.TestCase):
    def test_roles_in_code_are_registered(self) -> None:
        """엔진이 text(role=…) 로 쓰는 역할 이름은 전부 규칙 레지스트리에 있다(P10 — 조용한 예외 금지)."""
        used: set[str] = set()
        for p in iter_py("engine"):
            for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "text":
                    used |= {k.value.value for k in n.keywords if k.arg == "role" and isinstance(k.value, ast.Constant)}
        self.assertTrue(used)
        self.assertLessEqual(used, set(R.qa_checks.glyph_size_exempt), used)
        self.assertTrue((REPO / "engine" / "fullcards.py").exists())


if __name__ == "__main__":
    unittest.main()

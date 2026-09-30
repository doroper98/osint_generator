"""G12 §C 기사 프레스 규약 v2(v5.1.0, back_and_forth D-0121 §C·D-0126 Q5·Q6 A, 사용자 결정 D107).

- theme dark·light(덮개·글자 색), 연출이 이벤트 theme 로 고른다.
- 프레스 사진 = 레지스트리 photo·rights_clear 만(아니면 RightsError). 없으면 블러 무대 폴백(지금 표면을 블러 — 사진을 지어내지 않는다).
- 헤드라인 = 원문(headline_original, 인용 부호) — 없으면 번역 헤드라인 + source 줄 "헤드라인 번역". 인용 상한·줄 수 초과 = 오류.
- 세리프 글꼴이 없으면 FontMissingError. 콘티 판 = [프레스: id] + 같은 글자. 옛 오른쪽·가운데 카드 경로 없음(P2).
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import unittest
from types import SimpleNamespace as NS
from unittest import mock

import cairo

from engine.credits import RightsError
from engine.layers import article as A_
from engine.layers.article import ArticleOverflowError, article_layout, article_phase, validate_press
from engine.style import ARTICLE, QUOTE_MAX_CHARS, W_OUT
from engine.typography import FontMissingError
from rules import load_rules

SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from


def _ctx(w: int = 1, h: int = 1) -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, w, h))


def _txt(original: str | None, headline: str = "연준, 금리 동결", sub: str = "요지") -> dict:
    return dict(pub="CNN", date="2026-07-29", headline=headline, sub=sub, original=original)


class LayoutTest(unittest.TestCase):
    def test_original_headline_quoted_left_center(self) -> None:
        with mock.patch.object(A_, "article_text", return_value=_txt("Fed holds rates steady")):
            L = article_layout(_ctx(), {"mid": "m"})  # noqa: N806
        self.assertEqual(L.headline, ["“Fed holds rates steady”"])
        self.assertEqual(L.sub, ["연준, 금리 동결"])   # 부제 = 한국어 번역 헤드라인
        self.assertEqual(L.source, "— CNN, 2026.7.29")
        self.assertFalse(L.translated)
        self.assertAlmostEqual(L.x, W_OUT * ARTICLE.x_left_ratio)
        self.assertAlmostEqual((L.box[1] + L.box[3]) / 2, SUB_Y / 2)   # 자막 구역 위 공간의 세로 가운데
        self.assertEqual(L.rule[1] - L.rule[0], L.hl_base[-1] - L.box[1] + ARTICLE.headline.size * A_.DESCENT)

    def test_translated_fallback_marked(self) -> None:
        with mock.patch.object(A_, "article_text", return_value=_txt(None, sub="파병 계획 재조정")):
            L = article_layout(_ctx(), {"mid": "m"})  # noqa: N806
        self.assertEqual(L.headline, ["연준, 금리 동결"])   # 부호 없음(원문 아님)
        self.assertEqual(L.sub, ["파병 계획 재조정"])
        self.assertTrue(L.source.endswith(ARTICLE.source.translated_note))
        self.assertTrue(L.translated)

    def test_quote_cap_and_line_overflow(self) -> None:
        with mock.patch.object(A_, "article_text", return_value=_txt("x" * (QUOTE_MAX_CHARS + 1))):
            with self.assertRaises(ArticleOverflowError):
                article_layout(_ctx(), {"mid": "m"})
        long = "very long headline words keep going " * 8
        with mock.patch.object(A_, "article_text", return_value=_txt(long[:QUOTE_MAX_CHARS])):
            with self.assertRaises(ArticleOverflowError):
                article_layout(_ctx(), {"mid": "m"})

    def test_serif_font_required(self) -> None:
        from engine import typography  # noqa: PLC0415

        typography.require_family.cache_clear()
        try:
            with mock.patch.object(A_, "article_text", return_value=_txt("Fed holds")), \
                 mock.patch.object(typography, "family_found", return_value=False):
                with self.assertRaises(FontMissingError):
                    article_layout(_ctx(), {"mid": "m"})
        finally:
            typography.require_family.cache_clear()


class ThemeTest(unittest.TestCase):
    def _overlay_px(self, theme: str) -> tuple[int, int, int]:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, 854, 480)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0.5, 0.5, 0.5)
        ctx.paint()
        with mock.patch.object(A_, "article_text", return_value=_txt("Fed holds")):
            A_.draw_article_text(ctx, {"mid": "m", "theme": theme}, 1.0)
        surf.flush()
        d = surf.get_data()
        i = (5 * 854 + 5) * 4
        return d[i + 2], d[i + 1], d[i]

    def test_dark_and_light(self) -> None:
        dark, light = self._overlay_px("dark"), self._overlay_px("light")
        self.assertLess(max(dark), 40)      # 검정 덮개 0.82
        self.assertGreater(min(light), 200)  # 흰 덮개 0.82
        self.assertEqual(ARTICLE.theme_default, "dark")

    def test_phase_press_lead(self) -> None:
        e = {"t0": 10.0, "t1": 20.0}
        pa, ta = article_phase(10.0 + ARTICLE.press_lead_sec * 0.9, e)
        self.assertGreater(pa, 0.9)
        self.assertEqual(ta, 0.0)   # 프레스 사진 단독 구간
        self.assertGreater(article_phase(15.0, e)[1], 0.99)


class PressTest(unittest.TestCase):
    def test_rights_gate(self) -> None:
        reg = {"ok": NS(kind="photo", rights_status="rights_clear", file="a.jpg"), "art": NS(kind="article", rights_status="rights_clear", file=None),
               "tbd": NS(kind="photo", rights_status="pending_review", file="b.jpg")}
        self.assertIsNone(validate_press({"mid": "m"}, reg))
        self.assertIs(validate_press({"mid": "m", "press": "ok"}, reg), reg["ok"])
        for bad in ("art", "tbd", "nope"):
            with self.assertRaises(RightsError, msg=bad):
                validate_press({"mid": "m", "press": bad}, reg)

    def test_blur_fallback_uses_current_stage(self) -> None:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, 854, 480)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, 427, 480)
        ctx.fill()
        A_.draw_press(ctx, NS(out=NS(k=1), cache={}), {"mid": "m"}, 1.0)
        surf.flush()
        d = surf.get_data()
        edge = d[(240 * 854 + 427) * 4]
        self.assertTrue(0 < edge < 255)   # 경계가 번졌다(블러) — 새 그림을 만들지 않고 지금 무대를 흐린다


class AnimaticAndLegacyTest(unittest.TestCase):
    def test_animatic_press_label(self) -> None:
        from engine.layers import animatic  # noqa: PLC0415

        self.assertEqual(animatic.label("press", "fed_hq"), "[프레스: fed_hq]")

    def test_old_card_path_deleted(self) -> None:
        from engine.layers import media  # noqa: PLC0415

        for name in ("article_geom", "article_alpha", "draw_article"):
            self.assertFalse(hasattr(media, name), name)
        self.assertNotIn("center", load_rules().placement.slots)   # 옛 가운데 기사 슬롯
        for k in ("w", "paper", "center_dim", "slide_sec"):
            self.assertNotIn(k, type(ARTICLE).model_fields)

    def test_no_literals(self) -> None:
        bad = []
        for fn in (A_.article_layout, A_.draw_article_text, A_.draw_press, A_.article_phase):
            tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
            bad += [f"{fn.__name__}: {n.value!r}" for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
                    and n.value not in (0, 1, 2, 3, 4, -1, 0.01)]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 C0.0 2b(D917·UF-905·UF-907·UF-908) — 인물·발언·기사(engine/skin_people.py, rules skin.quote·person_card·person_pill·article).

- 규칙: 엄격 모델(모르는 키·줄 수와 기준선 수 불일치·min_h > max_h = 오류), 그림자 겹 sheet.
- 발언(skin): 덮개 없음(카드·글자에서 먼 화소 = 발언 없는 화면), 카드 안 흰색·직각 모서리, 글자 잉크 짙고 테두리 없음, 글자 둘레 흰 번짐,
  quote_box ⊇ 카드 ∪ 글자 덩어리, 넘침 = QuoteError(자름 없음). 맞선 발언 = 알약 ∪ 글자.
- 기사(skin): 종이 카드 흰색, 뒤 종이가 앞 종이 오른쪽 밖에 보인다, 제호 아래 잉크 선, 화면 전체 덮개 없음, article_box = 카드 상자, 넘침 = ArticleOverflowError.
- 비 skin: draw_quote·draw_article 이 skin_people 를 부르지 않는다(바이트 동일은 감독 identity 스크립트가 HEAD 와 대조).
- 시연 프로젝트 projects/studio_showcase_people: 문장·이벤트가 기록된 영상(휴전안 cold_1·2, 경유의 길 act5_21·22) 그대로.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cairo
import numpy as np
import yaml
from PIL import Image
from pydantic import ValidationError

from engine import skin, skin_people
from engine.layers import article as article_mod
from engine.layers.article import ArticleOverflowError, article_box, article_layout, draw_article
from engine.quote import QuoteError, draw_quote, quote_box, quote_lines
from engine.style import H_OUT, SKIN, W_OUT, apply_palette
from rules import load_rules
from schemas.rules_models import SkinArticle, SkinQuote, SkinRules
from tests.anti_inertia._ast_util import REPO

BG = 0.92
PORTRAIT = REPO / "assets" / "library" / "people" / "zelensky_mono_v01.png"
QUOTE = dict(type="quote", t0=0.0, t1=6.0, pid="zelensky", flag="ua", speaker="볼로디미르 젤렌스키", role="우크라이나 대통령",
             text="처음 듣는 소식", src="NBC News", date="2026.10.11", pos="center")
ARTICLE_EV = dict(type="article", t0=0.0, t1=10.0, mid="iran_ceasefire_2026_art_0005")


def _on() -> None:
    skin.apply("studio")
    apply_palette(SKIN.palette)


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


def _R() -> SimpleNamespace:  # noqa: N802
    """초상 = 저장소 공용 라이브러리 파일(assets/library/people) — 프로젝트 자산 폴더 없이 같은 그림."""
    img = {"portrait:zelensky": Image.open(PORTRAIT).convert("RGBA")}
    return SimpleNamespace(cache={}, out=SimpleNamespace(k=1.0), tb=None, assets=SimpleNamespace(load_image=lambda k: None, img=img))


def _canvas() -> tuple[cairo.ImageSurface, cairo.Context]:
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    c = cairo.Context(s)
    c.set_source_rgb(BG, BG, BG)
    c.paint()
    return s, c


def _lum(s: cairo.ImageSurface) -> np.ndarray:
    s.flush()
    a = np.ndarray((H_OUT, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :W_OUT, 2::-1].astype(np.float64) / 255.0
    return a @ np.array([0.2126, 0.7152, 0.0722])


def _render(draw) -> np.ndarray:  # noqa: ANN001
    s, c = _canvas()
    draw(c)
    return _lum(s)


class RulesTest(unittest.TestCase):
    def test_strict_models(self) -> None:
        raw = load_rules().skin.model_dump()
        SkinRules.model_validate(raw)
        self.assertTrue(SKIN.shadow.sheet)
        for key in ("quote", "person_card", "person_pill", "article"):
            with self.assertRaises(ValidationError, msg=key):
                SkinRules.model_validate({**raw, key: {**raw[key], "nope": 1}})
        q = raw["quote"]
        with self.assertRaises(ValidationError):
            SkinQuote.model_validate({**q, "tiers": [[56, [232]], [44, [214]]]})   # 2단계인데 기준선 1개
        a = raw["article"]
        with self.assertRaises(ValidationError):
            SkinArticle.model_validate({**a, "min_h": a["max_h"] + 1})
        with self.assertRaises(ValidationError):
            SkinRules.model_validate({**raw, "person_card": {**raw["person_card"], "level": "floating"}})


class QuoteSkinTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()
        self.c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def tearDown(self) -> None:
        _off()

    def test_card_and_bare_text(self) -> None:
        L = skin_people.quote_layout(self.c, QUOTE)  # noqa: N806
        on = _render(lambda c: draw_quote(c, _R(), 3.0, QUOTE))
        off = _render(lambda c: None)
        # 덮개 없음 — 카드·글자에서 먼 화소는 그대로
        for x, y in ((W_OUT - 6, H_OUT - 6), (6, 6), (W_OUT - 30, 380), (380, 440)):
            self.assertAlmostEqual(on[y, x], off[y, x], places=6, msg=(x, y))
        x, y, w, h = L.card
        self.assertGreater(on[int(y + h - 12), int(x + w / 2)], 0.96)   # 카드 안(직함 아래) 흰색
        self.assertGreater(on[int(y), int(x)], 0.95)                     # 왼쪽 위 모서리 화소도 카드 면(직각, UF-908)
        x0, y0, x1, y1 = (int(v) for v in L.text_rect)
        glyph = on[int(L.bases[0] - L.size * 0.6):int(L.bases[0]), int(L.x):x1]
        self.assertLess(glyph.min(), 0.2)                                 # 잉크 글자는 짙다
        # 흰 번짐 — 첫 줄 바로 위 띠가 바탕보다 밝다(테두리가 아니라 번짐)
        cols = slice(int(L.x), x1)
        ink_top = int(np.argmax((on[:, cols] < 0.5).any(axis=1) & (np.arange(H_OUT) > L.bases[0] - L.size * 1.2)))
        band = on[ink_top - 3, cols]
        self.assertGreater(band.max(), off[ink_top - 3, int(L.x)] + 0.02)
        # 테두리 없음 — 같은 줄을 종전 테두리(halo 3)로 그린 것보다 어두운 화소가 훨씬 적다
        from engine.typography import text  # noqa: PLC0415

        out = _render(lambda c: text(c, L.lines[0], L.x, L.bases[0], L.size, SKIN.quote.font, skin.INK, 1.0, 3.0, halo_rgb=(0, 0, 0)))
        region = (slice(y0, y1), slice(x0, x1))
        self.assertLess((on[region] < 0.5).sum(), 0.8 * (out[region] < 0.5).sum())

    def test_no_scrim_and_box(self) -> None:
        L = skin_people.quote_layout(self.c, QUOTE)  # noqa: N806
        b = quote_box(self.c, QUOTE)
        cx, cy, cw, ch = L.card
        self.assertLessEqual(b[0], cx)
        self.assertLessEqual(b[1], cy)
        self.assertGreaterEqual(b[2], L.text_rect[2])
        self.assertGreaterEqual(b[3], cy + ch)
        self.assertEqual(quote_lines(self.c, QUOTE), ["처음 듣는 소식"])

    def test_pair_and_flag_only(self) -> None:
        for pos in ("upper", "lower"):
            L = skin_people.quote_layout(self.c, dict(QUOTE, pos=pos))  # noqa: N806
            self.assertIsNone(L.card)
            self.assertGreater(L.x, L.pill[0] + L.pill[2])
            b = quote_box(self.c, dict(QUOTE, pos=pos))
            self.assertLessEqual(b[0], L.pill[0])
            self.assertLessEqual(b[1], L.pill[1])
        L = skin_people.quote_layout(self.c, dict(QUOTE, pid=None))  # noqa: N806
        self.assertIsNone(L.card)
        self.assertEqual(L.x, SKIN.quote.text_x_flag)

    def test_overflow(self) -> None:
        with self.assertRaises(QuoteError):
            quote_lines(self.c, dict(QUOTE, text="아주 긴 발언 " * 20))
        with self.assertRaises(QuoteError):
            quote_lines(self.c, dict(QUOTE, speaker="아주아주아주 긴 이름의 인물 볼로디미르 젤렌스키"))
        with self.assertRaises(QuoteError):
            quote_lines(self.c, dict(QUOTE, pos="upper", text="아주 긴 발언 " * 20))


class ArticleSkinTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()
        self.c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def tearDown(self) -> None:
        _off()

    def test_paper_card(self) -> None:
        L = skin_people.skin_article_layout(self.c, ARTICLE_EV)  # noqa: N806
        x, y, w, h = L.box
        self.assertEqual((x, w), (SKIN.article.x, SKIN.article.w))
        self.assertTrue(SKIN.article.min_h <= h <= SKIN.article.max_h)
        self.assertEqual(article_box(self.c, ARTICLE_EV), (x, y, x + w, y + h))   # 프레스 사진 없음 = 카드 상자
        self.assertEqual(article_layout(self.c, ARTICLE_EV).box, (x, y, x + w, y + h))
        on = _render(lambda c: draw_article(c, _R(), 5.0, ARTICLE_EV))
        off = _render(lambda c: None)
        for px, py in ((2, 2), (W_OUT - 3, 2), (2, H_OUT - 3), (W_OUT - 3, H_OUT - 3)):   # 화면 전체 덮개 없음
            self.assertAlmostEqual(on[py, px], off[py, px], places=6)
        self.assertGreater(on[int(y + h - 10), int(x + w / 2)], 0.96)   # 종이 흰색
        row = on[int(y + h / 2)]
        bx = int(x + w + SKIN.article.back.dx)   # 뒤 종이 오른쪽 끝 — 안쪽(종이)이 바깥(그림자만)보다 밝은 단차
        self.assertGreater(row[bx - 2], row[bx + 2] + 0.03)
        rule_y = int(y + SKIN.article.rule.dy)
        self.assertLess(on[rule_y - 1:rule_y + 3, int(x + w / 2)].min(), 0.4)   # 제호 아래 잉크 선(1.2 px — 화소 경계에 걸쳐도)

    def test_overflow(self) -> None:
        long = dict(pub="The National", date="2026-10-31", headline="긴 제목 " * 40, sub="부제", original=None)
        with mock.patch.object(skin_people, "article_text", return_value=long), self.assertRaises(ArticleOverflowError):
            skin_people.skin_article_layout(self.c, ARTICLE_EV)
        two_sub = dict(long, headline="짧은 제목", sub="부제 " * 60)
        with mock.patch.object(skin_people, "article_text", return_value=two_sub), self.assertRaises(ArticleOverflowError):
            skin_people.skin_article_layout(self.c, ARTICLE_EV)


class NonSkinTest(unittest.TestCase):
    def test_old_path_untouched(self) -> None:
        _off()
        boom = mock.Mock(side_effect=AssertionError("skin_people 를 불렀다"))
        R = SimpleNamespace(cache={"badge_placeholder": lambda *a: None}, out=SimpleNamespace(k=1.0), tb=None)  # noqa: N806
        with mock.patch.object(skin_people, "draw_quote", boom), mock.patch.object(skin_people, "draw_article", boom), \
                mock.patch.object(skin_people, "quote_layout", boom), mock.patch.object(skin_people, "skin_article_layout", boom):
            s, c = _canvas()
            draw_quote(c, R, 3.0, QUOTE)
            draw_article(c, R, 5.0, ARTICLE_EV)
            quote_box(c, QUOTE)
            article_box(c, ARTICLE_EV)
        self.assertEqual(article_mod.article_layout(c, ARTICLE_EV).x, W_OUT * article_mod.ARTICLE.x_left_ratio)


class ShowcaseTest(unittest.TestCase):
    def test_recorded_content_only(self) -> None:
        P = REPO / "projects"  # noqa: N806
        src = {}
        for name, scene in (("iran_ceasefire_2026", "cold"), ("diesel_road_2026", "act5")):
            sc = yaml.safe_load((P / name / "script.yaml").read_text(encoding="utf-8"))
            for s_ in sc["scenes"]:
                if s_["id"] == scene:
                    src[name] = s_["sentences"]
        mine = yaml.safe_load((P / "studio_showcase_people" / "script.yaml").read_text(encoding="utf-8"))
        got = [s_ for sc in mine["scenes"] for s_ in sc["sentences"]]
        want = src["iran_ceasefire_2026"][1:3] + src["diesel_road_2026"][21:23]
        self.assertEqual([(s_["text"], s_["date"], s_["sources"]) for s_ in got], [(s_["text"], s_["date"], s_["sources"]) for s_ in want])
        d = yaml.safe_load((P / "studio_showcase_people" / "direction.yaml").read_text(encoding="utf-8"))
        self.assertEqual(d["stage"], "studio")
        old_q = next(e for e in yaml.safe_load((P / "diesel_road_2026" / "direction.yaml").read_text(encoding="utf-8"))["events"]
                     if e["type"] == "quote" and e["start"].get("sid") == "act5_22")
        q = next(e for e in d["events"] if e["type"] == "quote")
        keys = ("pid", "flag", "speaker", "role", "text", "src", "date", "pos")
        self.assertEqual({k: q[k] for k in keys}, {k: str(old_q[k]) if k == "date" else old_q[k] for k in keys})
        self.assertIn(q["text"], got[3]["text"])
        art = next(e for e in d["events"] if e["type"] == "article")
        self.assertEqual(art["mid"], "iran_ceasefire_2026_art_0005")


if __name__ == "__main__":
    unittest.main()

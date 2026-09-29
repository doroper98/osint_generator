"""G7 기사 카드 조판 확대 (v4.8.0, back_and_forth D-0101 §2, 사용자 결정 D89)."""

from __future__ import annotations

import ast
import inspect
import textwrap
import unittest
from unittest import mock

import cairo

from engine.layers import media
from engine.layers.media import ArticleOverflowError, article_geom
from engine.placement import resolve_places
from engine.style import CARD, W_OUT
from rules import load_rules

A = load_rules().layout_480p.article_card
SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from


def ctx() -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def fake(headline: str, sub: str = "부제") -> dict:
    return dict(pub="매체", date="2026. 09. 16", headline=headline, hl=None, sub=sub, note="메모")


class ArticleCardTest(unittest.TestCase):
    def test_rules_values(self) -> None:
        self.assertEqual((A.w, A.y, A.pad, A.pub_size, A.date_size, A.headline_size, A.headline_gap, A.sub_size, A.sub_gap, A.meta_size),
                         (440, 60, 20, 15, 10, 18, 26, 12, 17, 9))
        self.assertEqual((A.headline_max_lines, A.sub_max_lines), (3, 3))

    def test_geometry_from_rules(self) -> None:
        with mock.patch.object(media, "article_text", return_value=fake("짧은 헤드라인")):
            x, y, w, h, hl, sub = article_geom(ctx(), {"mid": "m"})
        self.assertEqual((x, y, w), (W_OUT - A.w - CARD.x_right_margin, A.y, A.w))
        self.assertEqual(h, A.body_top + A.headline_gap + A.sub_lead + A.foot_h)
        self.assertEqual((len(hl), len(sub)), (1, 1))

    def test_center_align(self) -> None:
        with mock.patch.object(media, "article_text", return_value=fake("짧은 헤드라인")):
            x, y, w, h, _, _ = article_geom(ctx(), {"mid": "m", "align": "center"})
        self.assertEqual(x, (W_OUT - A.w) / 2)
        self.assertEqual(y, (SUB_Y - h) / 2)

    def test_overflow_errors(self) -> None:
        long = "아주 긴 헤드라인 문장이 계속 이어진다 " * 12
        with mock.patch.object(media, "article_text", return_value=fake(long)):
            with self.assertRaises(ArticleOverflowError):
                article_geom(ctx(), {"mid": "m"})
        with mock.patch.object(media, "article_text", return_value=fake("짧다", sub=long)):
            with self.assertRaises(ArticleOverflowError):
                article_geom(ctx(), {"mid": "m"})

    def test_center_slot(self) -> None:
        ev = [{"type": "article", "t0": 1, "t1": 5, "mid": "fox_0916", "place": "center"}]
        rec = resolve_places(ev, lambda t: None)
        self.assertEqual(ev[0]["align"], "center")
        self.assertEqual(rec["article:0"], "slot:center")

    def test_no_literals_in_article_functions(self) -> None:
        """draw_article·article_geom 수치 = rules article_card(0·1·2 만 허용)."""
        bad = []
        for fn in (media.article_geom, media.draw_article, media.article_alpha):
            tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
            bad += [f"{fn.__name__}: {n.value!r}" for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
                    and n.value not in (0, 1, 2, 3, -1, 0.01)]   # 0.01 = 전 레이어 공통 보임 문턱
        self.assertEqual(bad, [])

    def test_fed_policy_articles_center(self) -> None:
        import yaml

        from pathlib import Path
        d = yaml.safe_load((Path(__file__).resolve().parents[1] / "projects/fed_policy_2026/direction.yaml").read_text(encoding="utf-8"))
        arts = [e for e in d["events"] if e["type"] == "article"]
        self.assertEqual(len(arts), 2)
        self.assertTrue(all(e.get("place") == "center" for e in arts))


if __name__ == "__main__":
    unittest.main()

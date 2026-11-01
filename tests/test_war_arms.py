"""v7.4.0 전쟁사 D-0605 ①③ — 병종 글리프 레지스트리·부호 모양·입체·대열 격자(병력 비례 아님)·3D 장면 조각."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cairo
import numpy as np

from engine.glyphs.arms import GLYPHS, GlyphError, draw_glyph
from rules import load_rules


class ArmsRegistryTest(unittest.TestCase):
    def test_rule_glyphs_registered_and_ancient_complete(self) -> None:
        ws = load_rules().war_history.symbol_sets
        used = {g for s in ws.by_era().values() for g in s.glyphs.values()}
        self.assertLessEqual(used, set(GLYPHS))                                     # 규칙 → 레지스트리(P10)
        self.assertEqual(set(ws.ancient.glyphs), set(ws.ancient.units))             # 고대 병종은 전부 글리프
        self.assertEqual(set(ws.ancient.units), {"heavy_inf", "light_inf", "heavy_cav", "light_cav", "skirmisher", "elephant"})

    def test_gallery_covers_all_glyphs(self) -> None:
        from tools.element_gallery import arms_sheet

        with tempfile.TemporaryDirectory() as d:
            rep = arms_sheet(Path(d) / "arms.png")
            self.assertEqual(rep["glyphs"], list(GLYPHS))
            self.assertTrue((Path(d) / "arms.png").is_file())

    def test_unknown_glyph_is_error(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 20, 20))
        with self.assertRaises(GlyphError):
            draw_glyph(ctx, "archer_x", 10, 10, 15, (1, 1, 1), 1, (0, 0, 0), 1)

    def test_glyphs_draw_ink(self) -> None:
        for n in GLYPHS:
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 40, 40)
            draw_glyph(cairo.Context(surf), n, 20, 20, 30, (1, 1, 1), 1, (0, 0, 0), 1)
            a = np.frombuffer(surf.get_data(), np.uint8).reshape(40, 40, 4)[..., 3]
            self.assertGreater((a > 0).mean(), 0.08, n)


class ShapeTest(unittest.TestCase):
    def test_shape_and_glyph_lookup(self) -> None:
        ws = load_rules().war_history.symbol_sets
        self.assertEqual(ws.shape_of("heavy_cav"), "wedge")
        self.assertEqual(ws.shape_of("skirmisher"), "dots")
        self.assertEqual(ws.shape_of("app6_inf"), "app6")
        self.assertIsNone(ws.glyph_of("regiment_block"))
        with self.assertRaises(KeyError):
            ws.shape_of("infantry_block")   # v1 부호 이름은 지웠다(P2)

    def test_shapes_must_cover_units(self) -> None:
        from schemas.rules_models import WarSymbolSet

        with self.assertRaises(ValueError):
            WarSymbolSet(units=["a", "b"], shapes={"a": "block"}, faction_tokens=2)
        with self.assertRaises(ValueError):
            WarSymbolSet(units=["a"], shapes={"a": "block"}, glyphs={"z": "heavy_inf"}, faction_tokens=2)


class RankPostsTest(unittest.TestCase):
    def test_fixed_spacing_not_strength(self) -> None:
        """대열 기둥 = 고정 간격 — 같은 면적이면 같은 수(병력 입력이 없다), 윤곽 밖 점 없음, 결정적."""
        from sketch.war.terrain3d import rank_posts

        sq = [[0, 0], [700, 0], [700, 700], [0, 700]]
        a = rank_posts(sq, 70, 1000)
        self.assertEqual(a, rank_posts(sq, 70, 1000))
        self.assertTrue(all(0 < x < 700 and 0 < z < 700 for x, z in a))
        self.assertEqual(len(rank_posts(sq, 70, 5)), 5)
        tri = [[0, 0], [700, 0], [350, 700]]
        self.assertLess(len(rank_posts(tri, 70, 1000)), len(a))

    def test_shape_poly_matches_2d(self) -> None:
        from sketch.war.terrain3d import shape_poly

        rect = [[0, 0], [100, 0], [100, 50], [0, 50]]
        self.assertEqual(len(shape_poly("wedge", rect)), 4)
        self.assertEqual(shape_poly("wedge", rect)[3], [50.0, 50.0])
        self.assertEqual(len(shape_poly("triangle", rect)), 3)
        self.assertEqual(shape_poly("block", rect), [[float(a), float(b)] for a, b in rect])


class C2ExcludeTest(unittest.TestCase):
    """D-0610 ③ — 이름 없는 부대 블록끼리 맞닿음은 SK-C2 에서 빼고 제외 프레임을 센다. 이름 있는 라벨과의 겹침은 그대로 센다."""

    def test_unnamed_pairs_excluded(self) -> None:
        from sketch.common.checks import UNNAMED_UNIT, CheckReport, check_label_overlap
        from sketch.common.draw import SK

        self.assertTrue(SK.checks.c2_exclude_unnamed_units)
        a, b = (0, 0, 10, 10, UNNAMED_UNIT), (5, 5, 15, 15, UNNAMED_UNIT)
        lab = (5, 5, 15, 15, "")
        ex: list = []
        rep = CheckReport()
        self.assertEqual(check_label_overlap(rep, [(0.0, [a, b]), (0.1, [a, lab])], SK.checks, ex), 1)
        self.assertEqual(ex, [0.0])


if __name__ == "__main__":
    unittest.main()

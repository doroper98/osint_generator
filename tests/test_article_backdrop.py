"""v5.21.12 D-0193 — 사진 없는 기사 카드 무대 밝기 상한(지도 테마 무관) + 영상 안 기사 카드 theme 하나(article_backdrop hard)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from PIL import Image

from engine.checks import HARD, check_article_backdrop
from engine.layers.article import ARTICLE, fallback_gain

F = ARTICLE.press_fallback


def _flat(v: int) -> Image.Image:
    return Image.new("RGB", (64, 36), (v, v, v))


class TestGain(unittest.TestCase):
    def test_dark_map_keeps_dim(self) -> None:
        """어두운 지도(골든 0.066·0.070 수준) — 종전 배율 1 − dim 그대로(골든 무변경)."""
        self.assertAlmostEqual(fallback_gain(_flat(35)), 1 - F.dim)

    def test_light_map_capped(self) -> None:
        """밝은 지도(블러 뒤 0.8 수준) — 결과 평균 밝기 = max_luma."""
        g = fallback_gain(_flat(210))
        self.assertLess(g, 1 - F.dim)
        self.assertAlmostEqual(210 / 255 * g, F.max_luma, places=4)

    def test_rule(self) -> None:
        self.assertLessEqual(0.0704, F.max_luma)   # dark 골든 실측 최댓값 이상


class TestCheck(unittest.TestCase):
    def test_one_theme_per_video(self) -> None:
        self.assertIn("article_backdrop", HARD)
        same = [{"type": "article", "mid": "a", "theme": "dark"}, {"type": "article", "mid": "b"}]
        mixed = same + [{"type": "article", "mid": "c", "theme": "light"}]
        self.assertEqual(check_article_backdrop(SimpleNamespace(events=same)), [] if ARTICLE.theme_default == "dark" else ["x"])
        out = check_article_backdrop(SimpleNamespace(events=mixed))
        self.assertEqual(len(out), 1)
        self.assertIn("2종", out[0])


if __name__ == "__main__":
    unittest.main()

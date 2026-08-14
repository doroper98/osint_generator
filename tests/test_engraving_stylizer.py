"""판화 스타일라이저(workers/engraving_stylizer.py) 단위 테스트.

원칙: 실존 인물 사진은 테스트에 넣지 않는다. 모든 입력은 합성 이미지다.
"""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from workers.engraving_stylizer import (
    INK_COLOR,
    EngravingResult,
    build_tone_map,
    stylize_engraving,
    stylize_stipple,
)


def make_gradient(width: int = 240, height: int = 160) -> Image.Image:
    """좌(흰색)→우(검정) 수평 그라디언트. 배경 제거가 끼어들지 않게 단조롭게."""
    ramp = np.linspace(255.0, 0.0, width, dtype=np.float32)
    grid = np.repeat(ramp[np.newaxis, :], height, axis=0)
    return Image.fromarray(grid.astype(np.uint8), mode="L").convert("RGB")


def make_flat(width: int = 120, height: int = 90, value: int = 128) -> Image.Image:
    grid = np.full((height, width), value, dtype=np.uint8)
    return Image.fromarray(grid, mode="L").convert("RGB")


class ToneMapTest(unittest.TestCase):
    def test_darkness_follows_luminance(self) -> None:
        tone = build_tone_map(make_gradient(), remove_background=False)
        left = float(tone.darkness[:, :40].mean())
        right = float(tone.darkness[:, -40:].mean())
        self.assertLess(left, 0.15)
        self.assertGreater(right, 0.6)
        self.assertGreaterEqual(float(tone.darkness.min()), 0.0)
        self.assertLessEqual(float(tone.darkness.max()), 1.0)


class StippleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = make_gradient()
        self.tone = build_tone_map(self.image, remove_background=False)

    def test_dot_density_increases_with_darkness(self) -> None:
        result = stylize_stipple(self.image, seed=3, tone=self.tone)
        self.assertGreater(len(result.dots), 100)

        width = result.width
        bright = [d for d in result.dots if d.x < width * 0.25]
        dark = [d for d in result.dots if d.x > width * 0.75]
        self.assertGreater(len(dark), len(bright) * 3)

    def test_dot_radius_increases_with_darkness(self) -> None:
        result = stylize_stipple(self.image, seed=3, tone=self.tone)
        width = result.width
        bright = [d.r for d in result.dots if d.x < width * 0.25]
        dark = [d.r for d in result.dots if d.x > width * 0.75]
        self.assertTrue(bright and dark)
        self.assertGreater(sum(dark) / len(dark), sum(bright) / len(bright))

    def test_seed_determinism(self) -> None:
        first = stylize_stipple(self.image, seed=11, tone=self.tone).to_svg()
        second = stylize_stipple(self.image, seed=11, tone=self.tone).to_svg()
        other = stylize_stipple(self.image, seed=12, tone=self.tone).to_svg()
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_threshold_suppresses_highlights(self) -> None:
        white = Image.fromarray(
            np.full((80, 80), 255, dtype=np.uint8), mode="L"
        ).convert("RGB")
        tone = build_tone_map(white, remove_background=False)
        result = stylize_stipple(white, seed=5, tone=tone)
        self.assertEqual(len(result.dots), 0)


class EngravingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = make_gradient()
        self.tone = build_tone_map(self.image, remove_background=False)

    def test_stroke_width_increases_with_darkness(self) -> None:
        result = stylize_engraving(self.image, seed=3, tone=self.tone)
        self.assertGreater(len(result.strokes), 20)

        width = result.width
        bright: list[float] = []
        dark: list[float] = []
        for stroke in result.strokes:
            for (x0, _y0), (x1, _y1) in zip(stroke.points, stroke.points[1:]):
                mid_x = (x0 + x1) / 2.0
                if mid_x < width * 0.25:
                    bright.append(stroke.width)
                elif mid_x > width * 0.75:
                    dark.append(stroke.width)
        self.assertTrue(bright and dark)
        self.assertGreater(sum(dark) / len(dark), sum(bright) / len(bright) * 1.5)

    def test_dark_side_carries_more_ink(self) -> None:
        result = stylize_engraving(self.image, seed=3, tone=self.tone)
        width = result.width
        bright_ink = 0.0
        dark_ink = 0.0
        # 획은 그림 전체를 가로지르므로 획 단위가 아니라 **선분 단위**로
        # 잉크량(길이 x 두께)을 좌/우 밴드에 나눠 담는다.
        for stroke in result.strokes:
            for (x0, y0), (x1, y1) in zip(stroke.points, stroke.points[1:]):
                ink = float(np.hypot(x1 - x0, y1 - y0)) * stroke.width
                mid_x = (x0 + x1) / 2.0
                if mid_x < width * 0.25:
                    bright_ink += ink
                elif mid_x > width * 0.75:
                    dark_ink += ink
        self.assertGreater(dark_ink, bright_ink * 2)

    def test_cross_hatch_adds_strokes(self) -> None:
        with_cross = stylize_engraving(self.image, seed=3, tone=self.tone)
        without_cross = stylize_engraving(
            self.image, seed=3, tone=self.tone, cross_hatch=False
        )
        self.assertGreater(len(with_cross.strokes), len(without_cross.strokes))

    def test_seed_determinism(self) -> None:
        first = stylize_engraving(self.image, seed=21, tone=self.tone).to_svg()
        second = stylize_engraving(self.image, seed=21, tone=self.tone).to_svg()
        other = stylize_engraving(self.image, seed=22, tone=self.tone).to_svg()
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)


class SvgContractTest(unittest.TestCase):
    def _results(self) -> list[EngravingResult]:
        image = make_gradient(200, 130)
        tone = build_tone_map(image, remove_background=False)
        return [
            stylize_stipple(image, seed=1, tone=tone),
            stylize_engraving(image, seed=1, tone=tone),
        ]

    def test_svg_is_valid_xml_with_source_viewbox(self) -> None:
        for result in self._results():
            with self.subTest(style=result.style):
                root = ET.fromstring(result.to_svg())
                self.assertTrue(root.tag.endswith("svg"))
                self.assertEqual(
                    root.get("viewBox"), f"0 0 {result.width} {result.height}"
                )
                self.assertEqual(root.get("width"), str(result.width))
                self.assertEqual(root.get("height"), str(result.height))
                self.assertEqual((result.width, result.height), (200, 130))

    def test_svg_has_no_background_fill_and_single_ink(self) -> None:
        for result in self._results():
            with self.subTest(style=result.style):
                svg = result.to_svg()
                self.assertNotIn("<rect", svg)
                colors = {
                    token
                    for token in ("#" + part.split('"')[0] for part in svg.split("#")[1:])
                }
                self.assertEqual(colors, {INK_COLOR})

    def test_geometry_lives_in_pixel_coordinates(self) -> None:
        for result in self._results():
            with self.subTest(style=result.style):
                for dot in result.dots:
                    self.assertTrue(-1.0 <= dot.x <= result.width + 1.0)
                    self.assertTrue(-1.0 <= dot.y <= result.height + 1.0)
                for stroke in result.strokes:
                    for x, y in stroke.points:
                        self.assertTrue(-8.0 <= x <= result.width + 8.0)
                        self.assertTrue(-8.0 <= y <= result.height + 8.0)


class PngPreviewTest(unittest.TestCase):
    def test_png_matches_geometry_aspect_and_reacts_to_tone(self) -> None:
        import tempfile
        from pathlib import Path

        image = make_gradient(200, 130)
        tone = build_tone_map(image, remove_background=False)
        result = stylize_stipple(image, seed=9, tone=tone)
        with tempfile.TemporaryDirectory() as tmp:
            path = result.to_png(Path(tmp) / "preview.png", out_width=400)
            with Image.open(path) as png:
                self.assertEqual(png.size, (400, 260))
                gray = np.asarray(png.convert("L"), dtype=np.float32)
        # 어두운 쪽(오른쪽)이 실제로 잉크가 더 많아야 한다.
        self.assertLess(float(gray[:, -80:].mean()), float(gray[:, :80].mean()))


class BackgroundMaskTest(unittest.TestCase):
    def test_flat_border_is_suppressed(self) -> None:
        canvas = np.full((160, 160, 3), 230, dtype=np.uint8)
        canvas[40:120, 40:120] = 40  # 가운데 어두운 사각형 = 피사체
        image = Image.fromarray(canvas, mode="RGB")
        tone = build_tone_map(image, remove_background=True)
        self.assertLess(float(tone.foreground[:10, :10].mean()), 0.2)
        self.assertGreater(float(tone.foreground[70:90, 70:90].mean()), 0.8)

    def test_disabled_background_removal_keeps_everything(self) -> None:
        tone = build_tone_map(make_flat(), remove_background=False)
        self.assertAlmostEqual(float(tone.foreground.mean()), 1.0, places=5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

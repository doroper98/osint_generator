"""인쇄 스크리닝 스타일라이저(workers/engraving_stylizer.py) 단위 테스트.

원칙: 실존 인물 사진은 테스트에 넣지 않는다. 모든 입력은 합성 이미지다.
"""

from __future__ import annotations

import math
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from workers.engraving_stylizer import (
    INK_COLOR,
    ScreenResult,
    build_print_tone,
    compose_mono_shadow,
    make_crumpled_paper,
    stylize_halftone,
    stylize_linescreen,
    stylize_mono,
)


def make_gradient(width: int = 240, height: int = 160) -> Image.Image:
    """좌(흰색)→우(검정) 수평 그라디언트. 배경 제거가 끼어들지 않게 단조롭게."""
    ramp = np.linspace(255.0, 0.0, width, dtype=np.float32)
    grid = np.repeat(ramp[np.newaxis, :], height, axis=0)
    return Image.fromarray(grid.astype(np.uint8), mode="L").convert("RGB")


def make_flat(width: int = 120, height: int = 90, value: int = 128) -> Image.Image:
    grid = np.full((height, width), value, dtype=np.uint8)
    return Image.fromarray(grid, mode="L").convert("RGB")


def make_subject(size: int = 160) -> Image.Image:
    """밝은 배경 + 가운데 어두운 사각형(피사체). 배경 제거·섀도 합성 검증용."""
    canvas = np.full((size, size, 3), 230, dtype=np.uint8)
    canvas[40:120, 40:120] = 40
    return Image.fromarray(canvas, mode="RGB")


class PrintToneTest(unittest.TestCase):
    def test_ink_follows_darkness(self) -> None:
        tone = build_print_tone(make_gradient(), remove_background=False)
        left = float(tone.ink[:, :40].mean())
        right = float(tone.ink[:, -40:].mean())
        self.assertLess(left, 0.05)
        self.assertGreater(right, 0.8)
        self.assertGreaterEqual(float(tone.ink.min()), 0.0)
        self.assertLessEqual(float(tone.ink.max()), 1.0)

    def test_highlights_are_exactly_zero_ink(self) -> None:
        """상위 명도(하이라이트)는 잉크 0 — 종이가 깨끗이 비어야 한다."""
        tone = build_print_tone(
            make_gradient(), remove_background=False, highlight_percentile=80.0
        )
        clean = float((tone.ink <= 0.0).mean())
        self.assertGreater(clean, 0.12)
        # 가장 밝은 세로 띠는 전부 잉크 0.
        self.assertEqual(float(tone.ink[:, :10].max()), 0.0)

    def test_value_is_complement_of_ink(self) -> None:
        tone = build_print_tone(make_gradient(), remove_background=False)
        self.assertTrue(np.allclose(tone.value, 1.0 - tone.ink, atol=1e-6))

    def test_midtone_gamma_darkens_without_dirtying_highlights(self) -> None:
        plain = build_print_tone(
            make_gradient(), remove_background=False, midtone_gamma=1.0
        )
        pushed = build_print_tone(
            make_gradient(), remove_background=False, midtone_gamma=2.2
        )
        self.assertGreater(float(pushed.ink.mean()), float(plain.ink.mean()))
        self.assertEqual(float(pushed.ink[:, :10].max()), 0.0)

    def test_background_flood_fill_suppresses_border(self) -> None:
        tone = build_print_tone(make_subject(), remove_background=True)
        self.assertLess(float(tone.foreground[:10, :10].mean()), 0.2)
        self.assertGreater(float(tone.foreground[70:90, 70:90].mean()), 0.8)
        self.assertEqual(float(tone.ink[:10, :10].max()), 0.0)

    def test_disabled_background_removal_keeps_everything(self) -> None:
        tone = build_print_tone(make_flat(), remove_background=False)
        self.assertAlmostEqual(float(tone.foreground.mean()), 1.0, places=5)


class MonoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = make_gradient()
        self.tone = build_print_tone(self.image, remove_background=False)

    def test_duotone_raster_size_and_mode(self) -> None:
        result = stylize_mono(self.image, seed=1, tone=self.tone)
        self.assertEqual(result.style, "mono")
        self.assertEqual(result.image.mode, "RGBA")
        self.assertEqual(result.image.size, (self.tone.width, self.tone.height))

    def test_dark_side_is_darker_than_bright_side(self) -> None:
        result = stylize_mono(self.image, seed=1, tone=self.tone)
        gray = np.asarray(result.image.convert("L"), dtype=np.float32)
        self.assertGreater(float(gray[:, :30].mean()), 240.0)
        self.assertLess(float(gray[:, -30:].mean()), 60.0)

    def test_background_becomes_transparent(self) -> None:
        result = stylize_mono(make_subject(), seed=1)
        alpha = np.asarray(result.image.split()[3], dtype=np.float32)
        self.assertLess(float(alpha[:10, :10].mean()), 40.0)
        self.assertGreater(float(alpha[70:90, 70:90].mean()), 220.0)

    def test_seed_determinism_bytewise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = stylize_mono(self.image, seed=11, tone=self.tone).to_png(
                Path(tmp) / "a.png"
            )
            second = stylize_mono(self.image, seed=11, tone=self.tone).to_png(
                Path(tmp) / "b.png"
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_png_resize_keeps_aspect(self) -> None:
        result = stylize_mono(self.image, seed=1, tone=self.tone)
        with tempfile.TemporaryDirectory() as tmp:
            path = result.to_png(Path(tmp) / "m.png", out_width=480, background="white")
            with Image.open(path) as png:
                self.assertEqual(png.size, (480, 320))


class ComposeMonoShadowTest(unittest.TestCase):
    ACCENT = "#B03A2E"
    PAPER = "#E8DFC9"

    def test_shadow_follows_silhouette_not_a_rectangle(self) -> None:
        composed = compose_mono_shadow(
            make_subject(), accent=self.ACCENT, offset=(12, 12), paper=self.PAPER
        )
        pixels = np.asarray(composed.convert("RGB"), dtype=np.int16)
        # 피사체 사각형(40..120)이 (12,12) 밀린 자리 = 섀도만 보이는 띠.
        shadow = pixels[124, 60]
        self.assertLess(abs(int(shadow[0]) - 0xB0), 12)
        self.assertLess(abs(int(shadow[1]) - 0x3A), 12)
        # 실루엣 밖(원본에도 섀도에도 안 닿는 구석)은 종이색 그대로.
        paper = pixels[5, 5]
        self.assertLess(abs(int(paper[0]) - 0xE8), 6)
        self.assertLess(abs(int(paper[2]) - 0xC9), 6)
        # 섀도가 밀려 나간 반대쪽(왼쪽 위)은 종이색이어야 한다 = 사각 그림자 아님.
        self.assertLess(abs(int(pixels[35, 35][0]) - 0xE8), 8)

    def test_subject_stays_monochrome_on_top(self) -> None:
        composed = compose_mono_shadow(
            make_subject(), accent=self.ACCENT, offset=(12, 12), paper=self.PAPER
        )
        pixels = np.asarray(composed.convert("RGB"), dtype=np.int16)
        center = pixels[80, 80]
        self.assertLess(int(center.max()) - int(center.min()), 12)

    def test_transparent_paper_keeps_alpha(self) -> None:
        composed = compose_mono_shadow(
            make_subject(), accent=self.ACCENT, offset=(12, 12), paper=None
        )
        self.assertEqual(composed.mode, "RGBA")
        alpha = np.asarray(composed.split()[3], dtype=np.float32)
        self.assertLess(float(alpha[5, 5]), 20.0)
        self.assertGreater(float(alpha[80, 80]), 220.0)

    def test_pad_grows_canvas(self) -> None:
        composed = compose_mono_shadow(
            make_subject(160), accent=self.ACCENT, pad=(20, 10, 30, 0)
        )
        self.assertEqual(composed.size, (160 + 20 + 30, 160 + 10))

    def test_determinism(self) -> None:
        first = compose_mono_shadow(make_subject(), accent=self.ACCENT)
        second = compose_mono_shadow(make_subject(), accent=self.ACCENT)
        self.assertEqual(first.tobytes(), second.tobytes())


class ShadowGrammarTest(unittest.TestCase):
    """v0.45.3 섀도 문법 확장 — shadow_mode × shadow_fill."""

    ACCENT = "#B03A2E"
    PAPER = "#E8DFC9"
    RADIUS = 14

    def _compose(self, **kwargs: object) -> Image.Image:
        params: dict[str, object] = {
            "accent": self.ACCENT,
            "paper": self.PAPER,
            "offset": (12, 12),
            "outline_px": self.RADIUS,
            "seed": 5,
        }
        params.update(kwargs)
        return compose_mono_shadow(make_subject(), **params)  # type: ignore[arg-type]

    @staticmethod
    def _split(composed: Image.Image) -> tuple[np.ndarray, np.ndarray]:
        """(액센트 섀도 마스크, 인물 잉크 마스크). 종이·경계 혼합 픽셀은 어디에도 없다."""
        rgb = np.asarray(composed.convert("RGB"), dtype=np.int16)
        accent = np.abs(rgb - np.array([0xB0, 0x3A, 0x2E], dtype=np.int16)).sum(2) < 40
        paper = np.abs(rgb - np.array([0xE8, 0xDF, 0xC9], dtype=np.int16)).sum(2) < 40
        gray = np.abs(rgb[..., 0] - rgb[..., 1]) + np.abs(rgb[..., 1] - rgb[..., 2])
        ink = (~accent) & (~paper) & (gray < 24)
        return accent, ink

    def test_outline_mode_dilates_the_silhouette(self) -> None:
        accent, ink = self._split(self._compose(shadow_mode="outline"))
        # outline 섀도는 실루엣을 덮으므로 총 섀도 = 보이는 링 + 인물 면적.
        self.assertGreater(int(accent.sum()) + int(ink.sum()), int(ink.sum()) * 1.4)
        self.assertGreater(int(accent.sum()), 0)

        ink_ys, ink_xs = np.nonzero(ink)
        sh_ys, sh_xs = np.nonzero(accent | ink)
        for grown, base, sign in (
            (int(sh_xs.min()), int(ink_xs.min()), -1),
            (int(sh_ys.min()), int(ink_ys.min()), -1),
            (int(sh_xs.max()), int(ink_xs.max()), +1),
            (int(sh_ys.max()), int(ink_ys.max()), +1),
        ):
            self.assertAlmostEqual(grown, base + sign * self.RADIUS, delta=3)

    def test_outline_shadow_stays_inside_the_dilation_reach(self) -> None:
        """섀도는 실루엣에서 outline_px 안쪽에만 존재한다(사각 피사체 = 볼록)."""
        accent, ink = self._split(self._compose(shadow_mode="outline"))
        ink_ys, ink_xs = np.nonzero(ink)
        x0, x1 = int(ink_xs.min()), int(ink_xs.max())
        y0, y1 = int(ink_ys.min()), int(ink_ys.max())

        ys, xs = np.nonzero(accent)
        near_x = np.clip(xs, x0, x1)
        near_y = np.clip(ys, y0, y1)
        distance = np.hypot(xs - near_x, ys - near_y)
        self.assertLessEqual(float(distance.max()), self.RADIUS + 2.0)

    def test_outline_ignores_the_offset_vector(self) -> None:
        """두 모드는 상호 배타 — outline 에서 offset 은 결과를 바꾸지 않는다."""
        first = self._compose(shadow_mode="outline", offset=(0, 0))
        second = self._compose(shadow_mode="outline", offset=(40, -25))
        self.assertEqual(first.tobytes(), second.tobytes())

    def test_pattern_fills_are_deterministic(self) -> None:
        for fill in ("hatch", "dots"):
            with self.subTest(fill=fill):
                first = self._compose(shadow_mode="outline", shadow_fill=fill, seed=5)
                second = self._compose(shadow_mode="outline", shadow_fill=fill, seed=5)
                other = self._compose(shadow_mode="outline", shadow_fill=fill, seed=6)
                self.assertEqual(first.tobytes(), second.tobytes())
                self.assertNotEqual(first.tobytes(), other.tobytes())

    def test_pattern_never_leaks_outside_the_shadow(self) -> None:
        """패턴은 섀도 영역에서 정확히 클리핑된다 — 밖에는 한 픽셀도 없다."""
        for mode in ("offset", "outline"):
            solid_accent, solid_ink = self._split(
                self._compose(shadow_mode=mode, shadow_fill="solid")
            )
            region = solid_accent | solid_ink
            for fill in ("hatch", "dots"):
                with self.subTest(mode=mode, fill=fill):
                    accent, _ = self._split(
                        self._compose(shadow_mode=mode, shadow_fill=fill)
                    )
                    self.assertEqual(int((accent & ~region).sum()), 0)
                    # 선·점 사이로 종이가 비쳐야 한다 = 먹면보다 잉크가 적다.
                    self.assertLess(int(accent.sum()), int(solid_accent.sum()) * 0.8)
                    self.assertGreater(int(accent.sum()), 0)

    def test_unknown_grammar_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._compose(shadow_mode="glow")
        with self.assertRaises(ValueError):
            self._compose(shadow_fill="scribble")

    def test_image_paper_is_used_as_background(self) -> None:
        texture = make_crumpled_paper(240, 240, seed=2)
        composed = compose_mono_shadow(
            make_subject(), accent=self.ACCENT, paper=texture, offset=(12, 12)
        )
        self.assertEqual(composed.size, (160, 160))
        sheet = np.asarray(texture.resize((160, 160), Image.LANCZOS), dtype=np.int16)
        pixels = np.asarray(composed.convert("RGB"), dtype=np.int16)
        # 인물·섀도가 닿지 않는 왼쪽 위 구석은 종이 텍스처 그대로여야 한다.
        self.assertLess(int(np.abs(pixels[:20, :20] - sheet[:20, :20]).max()), 3)


class CrumpledPaperTest(unittest.TestCase):
    def test_seed_determinism(self) -> None:
        first = make_crumpled_paper(180, 240, seed=4)
        second = make_crumpled_paper(180, 240, seed=4)
        other = make_crumpled_paper(180, 240, seed=5)
        self.assertEqual(first.size, (180, 240))
        self.assertEqual(first.mode, "RGB")
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertNotEqual(first.tobytes(), other.tobytes())

    def test_brightness_stays_close_to_the_base_tone(self) -> None:
        """종이는 질감이지 주인공이 아니다 — 명도 변동이 ±amplitude 언저리."""
        paper = make_crumpled_paper(320, 320, seed=9, base="#DDD3BD", amplitude=0.06)
        gray = np.asarray(paper.convert("L"), dtype=np.float32)
        mean = float(gray.mean())
        self.assertGreater(mean, 180.0)
        self.assertLess(mean, 225.0)
        low, high = np.percentile(gray, (1.0, 99.0))
        self.assertLess(float(high - low) / mean, 0.16)
        # 완전 단색이 아니어야 질감이다.
        self.assertGreater(float(gray.std()), 1.0)


class HalftoneTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = make_gradient()
        self.tone = build_print_tone(self.image, remove_background=False)

    def test_dots_sit_on_a_regular_lattice(self) -> None:
        result = stylize_halftone(self.image, seed=3, tone=self.tone, cell=5.0)
        self.assertGreater(len(result.dots), 500)
        # 45° 격자 → 회전 좌표가 셀 간격의 정수배(+위상)에 딱 떨어져야 한다.
        ux, uy = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
        residual = [
            abs(((dot.x * ux + dot.y * uy) / 5.0) % 1.0 - 0.5)
            for dot in result.dots[:200]
        ]
        self.assertLess(float(np.std(residual)), 1e-3)

    def test_radius_increases_with_darkness(self) -> None:
        result = stylize_halftone(self.image, seed=3, tone=self.tone)
        width = result.width
        bright = [d.r for d in result.dots if d.x < width * 0.35]
        dark = [d.r for d in result.dots if d.x > width * 0.75]
        self.assertTrue(bright and dark)
        self.assertGreater(sum(dark) / len(dark), sum(bright) / len(bright) * 1.5)

    def test_highlights_carry_no_ink(self) -> None:
        result = stylize_halftone(self.image, seed=3, tone=self.tone)
        self.assertEqual([d for d in result.dots if d.x < result.width * 0.1], [])

        white = Image.fromarray(
            np.full((80, 80), 255, dtype=np.uint8), mode="L"
        ).convert("RGB")
        tone = build_print_tone(white, remove_background=False)
        self.assertEqual(len(stylize_halftone(white, seed=5, tone=tone).dots), 0)

    def test_seed_determinism(self) -> None:
        first = stylize_halftone(self.image, seed=11, tone=self.tone).to_svg()
        second = stylize_halftone(self.image, seed=11, tone=self.tone).to_svg()
        other = stylize_halftone(self.image, seed=12, tone=self.tone).to_svg()
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)


class LinescreenTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = make_gradient()
        self.tone = build_print_tone(self.image, remove_background=False)

    def test_strokes_are_straight_lines_at_the_screen_angle(self) -> None:
        result = stylize_linescreen(self.image, seed=3, tone=self.tone, angle=45.0)
        self.assertGreater(len(result.strokes), 50)
        for stroke in result.strokes:
            self.assertEqual(len(stroke.points), 2)
            (x0, y0), (x1, y1) = stroke.points
            length = math.hypot(x1 - x0, y1 - y0)
            self.assertGreater(length, 0.0)
            # 45° → dx 와 dy 가 같아야 한다(물결·warp 금지).
            self.assertLess(abs((x1 - x0) - (y1 - y0)), 1e-6 * max(1.0, length))

    def test_width_increases_with_darkness(self) -> None:
        result = stylize_linescreen(self.image, seed=3, tone=self.tone)
        width = result.width
        bright: list[float] = []
        dark: list[float] = []
        for stroke in result.strokes:
            mid_x = (stroke.points[0][0] + stroke.points[1][0]) / 2.0
            if mid_x < width * 0.35:
                bright.append(stroke.width)
            elif mid_x > width * 0.75:
                dark.append(stroke.width)
        self.assertTrue(bright and dark)
        self.assertGreater(sum(dark) / len(dark), sum(bright) / len(bright) * 1.5)

    def test_dark_side_carries_more_ink(self) -> None:
        result = stylize_linescreen(self.image, seed=3, tone=self.tone)
        width = result.width
        bright_ink = 0.0
        dark_ink = 0.0
        for stroke in result.strokes:
            (x0, y0), (x1, y1) = stroke.points
            ink = math.hypot(x1 - x0, y1 - y0) * stroke.width
            mid_x = (x0 + x1) / 2.0
            if mid_x < width * 0.35:
                bright_ink += ink
            elif mid_x > width * 0.75:
                dark_ink += ink
        self.assertGreater(dark_ink, bright_ink * 2)

    def test_highlights_carry_no_ink(self) -> None:
        white = Image.fromarray(
            np.full((80, 80), 255, dtype=np.uint8), mode="L"
        ).convert("RGB")
        tone = build_print_tone(white, remove_background=False)
        self.assertEqual(len(stylize_linescreen(white, seed=5, tone=tone).strokes), 0)

    def test_seed_determinism(self) -> None:
        first = stylize_linescreen(self.image, seed=21, tone=self.tone).to_svg()
        second = stylize_linescreen(self.image, seed=21, tone=self.tone).to_svg()
        other = stylize_linescreen(self.image, seed=22, tone=self.tone).to_svg()
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)


class SvgContractTest(unittest.TestCase):
    def _results(self) -> list[ScreenResult]:
        image = make_gradient(200, 130)
        tone = build_print_tone(image, remove_background=False)
        return [
            stylize_halftone(image, seed=1, tone=tone),
            stylize_linescreen(image, seed=1, tone=tone),
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
                    self.assertTrue(-8.0 <= dot.x <= result.width + 8.0)
                    self.assertTrue(-8.0 <= dot.y <= result.height + 8.0)
                for stroke in result.strokes:
                    for x, y in stroke.points:
                        self.assertTrue(-8.0 <= x <= result.width + 8.0)
                        self.assertTrue(-8.0 <= y <= result.height + 8.0)


class PngPreviewTest(unittest.TestCase):
    def test_png_matches_geometry_aspect_and_reacts_to_tone(self) -> None:
        image = make_gradient(200, 130)
        tone = build_print_tone(image, remove_background=False)
        for result in (
            stylize_halftone(image, seed=9, tone=tone),
            stylize_linescreen(image, seed=9, tone=tone),
        ):
            with self.subTest(style=result.style):
                with tempfile.TemporaryDirectory() as tmp:
                    path = result.to_png(Path(tmp) / "preview.png", out_width=400)
                    with Image.open(path) as png:
                        self.assertEqual(png.size, (400, 260))
                        gray = np.asarray(png.convert("L"), dtype=np.float32)
                # 어두운 쪽(오른쪽)이 실제로 잉크가 더 많아야 한다.
                self.assertLess(float(gray[:, -80:].mean()), float(gray[:, :80].mean()))
                # 밝은 쪽(왼쪽 끝)은 종이 그대로 — 잉크가 거의 없어야 한다.
                self.assertGreater(float(gray[:, :20].mean()), 250.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

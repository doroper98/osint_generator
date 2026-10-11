"""Q3 지도 테마 두 개 정식(v5.18.0, back_and_forth D-0161·D-0170 §3·D-0171, 사용자 결정 D154).

장르 기본값(지정학 = light)·direction 선택 사유 필수·[map-theme-override] warning·시리즈 레지스트리([series-theme-mismatch] hard, 중복 소속 = 로드 오류)·
장르 프로필 테마 없음 = 오류(조용한 dark 폴백 금지)·의미색 테마 보정(색상 불변·어둡게, 지도 무대만)·해안선↔국경 분리(공유 변만 국경, 한 번만)·
대비 측정(합성본)·콘티 막지도 같은 테마·카드·자막·HUD·엔딩은 테마 무관(지도 색 함수를 쓰지 않는다).
"""

from __future__ import annotations

import colorsys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cairo
import numpy as np
import yaml

from engine import style
from engine.direction import load_direction_doc, map_theme_override_warning, series_theme_error
from engine.stage import FlatMercatorStage, StageError, split_lines, to_uv
from rules import load_rules
from schemas.series_models import SeriesRegistry

REPO = Path(__file__).resolve().parent.parent
HORMUZ_DIR = REPO / "projects" / "hormuz_korea" / "direction.yaml"


def _doc(stage_config: dict | None):  # noqa: ANN202 — Direction
    """골든 연출에서 stage_config 블록만 바꾼 연출(파일 → 검증 경로 그대로). YAML 1.1 `off` 키가 있어 텍스트로 바꾼다."""
    text = HORMUZ_DIR.read_text(encoding="utf-8")
    head, rest = text.split("stage_config:", 1)
    rest = rest[rest.index("\nplaces:") + 1:]
    block = yaml.safe_dump({"stage_config": stage_config}, allow_unicode=True) if stage_config is not None else ""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "direction.yaml"
        p.write_text(head + block + rest, encoding="utf-8")
        return load_direction_doc(p)


class ThemeChoiceTest(unittest.TestCase):
    def test_genre_default_is_light_without_warning(self) -> None:
        mt = _doc(None).map_theme("any_project")
        self.assertEqual((mt["effective"], mt["source"], mt["declared"], mt["genre_default"]), ("light", "genre", False, "light"))
        self.assertEqual(map_theme_override_warning(mt), [])

    def test_declared_theme_needs_reason(self) -> None:
        with self.assertRaises(Exception):
            _doc({"mercator": {"theme": "dark"}})
        with self.assertRaises(Exception):
            _doc({"mercator": {"theme_reason": "사유만"}})

    def test_override_warning_only_when_different_from_genre(self) -> None:
        mt = load_direction_doc(HORMUZ_DIR).map_theme("hormuz_korea")
        self.assertEqual((mt["effective"], mt["source"]), ("dark", "direction"))
        self.assertEqual(len(map_theme_override_warning(mt)), 1)
        same = _doc({"mercator": {"theme": "light", "theme_reason": "장르와 같음"}}).map_theme("x")
        self.assertEqual(map_theme_override_warning(same), [])

    def test_genre_profile_without_theme_is_error(self) -> None:
        doc = _doc(None)
        prof = doc.genre_profile().model_copy(deep=True)
        prof.stage.mercator = None
        with mock.patch.object(type(doc), "genre_profile", return_value=prof), self.assertRaises(StageError):
            doc.map_theme("x")


class SeriesTest(unittest.TestCase):
    def _reg(self, theme: str) -> SeriesRegistry:
        return SeriesRegistry.model_validate({"schema_version": 1, "series": {
            "gulf": {"title": "걸프", "map_theme": theme, "decided_by": "D-0171", "projects": ["p1"]}}})

    def test_series_mismatch_is_hard_error(self) -> None:
        mt = {"effective": "dark", "source": "direction", "declared": True, "reason": "r", "series": "gulf", "genre_default": "light"}
        self.assertIn("[series-theme-mismatch]", series_theme_error(mt, self._reg("light")))
        self.assertIsNone(series_theme_error(mt, self._reg("dark")))
        self.assertEqual(map_theme_override_warning(mt), [])   # 시리즈 테마가 사유 — override warning 없음

    def test_project_in_two_series_is_load_error(self) -> None:
        with self.assertRaises(Exception):
            SeriesRegistry.model_validate({"schema_version": 1, "series": {
                "a": {"title": "A", "map_theme": "light", "decided_by": "D-0171", "projects": ["p1"]},
                "b": {"title": "B", "map_theme": "dark", "decided_by": "D-0171", "projects": ["p1"]}}})

    def test_registry_file_loads_and_starts_empty(self) -> None:
        from rules import load_series_registry  # noqa: PLC0415

        self.assertEqual(load_series_registry().series, {})


class SemanticColorTest(unittest.TestCase):
    def test_light_keeps_hue_and_is_darker(self) -> None:
        c = load_rules().colors
        for k, h in c.themes["light"].items():
            if k == "white":
                continue
            base = style.hexc(getattr(c, style.TEXT_BASE.get(k, k)))   # gold_text = gold 색상(v5.20.1)
            hb, lb, _ = colorsys.rgb_to_hls(*base)
            ht, lt, _ = colorsys.rgb_to_hls(*style.hexc(h))
            self.assertAlmostEqual(hb, ht, delta=0.01, msg=k)
            self.assertLess(lt, lb, k)

    def test_map_c_only_on_themed_map_stage(self) -> None:
        light = mock.Mock(theme_name="light")
        dark = mock.Mock(theme_name="dark")
        self.assertEqual(style.map_c(light, "gold"), style.C_THEME["light"]["gold"])
        self.assertEqual(style.map_c(dark, "gold"), style.C["gold"])
        self.assertEqual(style.map_c(object(), "gold"), style.C["gold"])   # 지도 무대가 아님(아일랜드 등)

    def test_cards_subtitles_hud_endcard_do_not_use_map_colors(self) -> None:
        for rel in ("engine/fullcards.py", "engine/cards.py", "engine/subtitles.py", "engine/hud.py", "engine/island.py"):
            src = (REPO / rel).read_text(encoding="utf-8")
            for name in ("map_c(", "map_halo(", "C_THEME"):
                self.assertNotIn(name, src, f"{rel} 가 지도 테마 색을 쓴다 — 카드·자막·HUD·엔딩은 테마 무관(D-0161 §3)")


class CoastBorderTest(unittest.TestCase):
    def test_shared_edge_is_border_once_rest_is_coast(self) -> None:
        a = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], np.float64)
        b = np.array([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]], np.float64)
        out = split_lines({"A": to_uv([a]), "B": to_uv([b])})
        self.assertEqual(len(out["border"]), 1)
        np.testing.assert_allclose(sorted(map(tuple, out["border"][0][0])), sorted(map(tuple, to_uv([a])[0][0][1:3])))
        coast_edges = sum(len(seg) - 1 for seg, _, _ in out["coast"])
        self.assertEqual(coast_edges, 6)   # 4 + 4 변 − 공유 변 2


class ContrastMeasureTest(unittest.TestCase):
    def _snap(self, bg: float, fg: float) -> tuple[bytes, int, int]:
        w, h = 60, 30
        img = np.full((h, w, 4), int(bg * 255), np.uint8)
        img[12:18, 10:50, :3] = int(fg * 255)
        return img.tobytes(), w, h

    def test_dark_on_light_passes_gray_on_gray_fails(self) -> None:
        from engine.checks import QA, measure_contrast  # noqa: PLC0415

        box = (8, 8, 52, 22)
        good = measure_contrast(self._snap(0.95, 0.05), [("required", box, (0.05, 0.05, 0.05), 1.0, "a")])[0]
        bad = measure_contrast(self._snap(0.6, 0.45), [("required", box, (0.45, 0.45, 0.45), 1.0, "b")])[0]
        self.assertGreater(good["ratio"], QA.map_contrast_text)
        self.assertLess(bad["ratio"], QA.map_contrast_text)
        faded = measure_contrast(self._snap(0.95, 0.05), [("required", box, (0.05, 0.05, 0.05), 0.3, "c")])
        self.assertEqual(faded, [])   # 페이드 중(알파 < min) 은 재지 않는다


class FlatMapThemeTest(unittest.TestCase):
    def test_animatic_flat_map_uses_same_theme(self) -> None:
        from engine.layers.animatic import draw_flat_map  # noqa: PLC0415
        from engine.projection import View  # noqa: PLC0415

        FM = load_rules().animatic.flat_map  # noqa: N806
        tier = {"lon0": 40.0, "lat0": 5.0, "lon1": 80.0, "lat1": 40.0}
        seen = {}
        for theme in ("dark", "light"):
            st = FlatMercatorStage(tier, {}, None, {"theme": theme})
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, 32, 18)
            draw_flat_map(cairo.Context(surf), st, View(st, (60.0, 20.0, 30.0)))
            px = np.frombuffer(surf.get_data(), np.uint8).reshape(18, surf.get_stride() // 4, 4)[5, 5, 2::-1] / 255
            seen[theme] = px
        np.testing.assert_allclose(seen["dark"], FM.sea[:3], atol=0.01)
        np.testing.assert_allclose(seen["light"], FM.themes["light"]["sea"][:3], atol=0.01)


class LightUserAD173Test(unittest.TestCase):
    """v5.20.1 사용자 결정 D173(D-0178) — light 도형 = A(휘도 0.11) 그대로, 글자 토큰만 4.5 최소 보정, 글로우 = 공통."""

    A = {"ru": "#be0013", "us": "#005abc", "gold": "#7c5612", "teal": "#1a6673", "green": "#2f6a2a", "muted": "#555e6e",
         "amber": "#885000", "water": "#005eae"}

    def test_shape_tokens_are_a_and_glow_common(self) -> None:
        light = load_rules().colors.themes["light"]
        self.assertEqual({k: light[k] for k in self.A}, self.A)
        self.assertIsNone(load_rules().geo.themes.light.map.border_glow)   # 키 삭제 = 공통 글로우

    def test_text_tokens_keep_hue_and_dark_unchanged(self) -> None:
        light = load_rules().colors.themes["light"]
        for k, base in (("gold_text", "gold"), ("white", None)):
            if base:
                h0, _, _ = colorsys.rgb_to_hls(*style.hexc(self.A[base]))
                h1, _, _ = colorsys.rgb_to_hls(*style.hexc(light[k]))
                self.assertAlmostEqual(h0, h1, delta=0.02, msg=k)
        dark = mock.Mock(theme_name="dark")
        self.assertEqual(style.map_c(dark, "gold_text"), style.C["gold"])   # dark 바이트 그대로


class CleanupV5191Test(unittest.TestCase):
    """v5.19.1(D-0173 §2 메모 → Fable 지시) — 조용한 경로 두 개를 막았다."""

    def test_view_without_stage_is_error(self) -> None:
        from types import SimpleNamespace as NS  # noqa: PLC0415

        from engine.layers.markers import draw_marker  # noqa: PLC0415

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 100)
        e = {"type": "marker", "t0": 0.0, "t1": 9.0, "world": (0.0, 0.0), "label": "도하"}
        with self.assertRaisesRegex(AttributeError, "stage"):   # 무대 없는 view 가 공통색으로 조용히 넘어가지 않는다(P6)
            draw_marker(cairo.Context(surf), NS(zones=[], reserved=[]), NS(to_screen=lambda *w: (50.0, 50.0), vw=200, vh=100), 5.0, e)

    def test_portrait_fit_errors_only_swallow_asset_error(self) -> None:
        from types import SimpleNamespace as NS  # noqa: PLC0415

        from engine import project  # noqa: PLC0415
        from engine.assets import AssetError  # noqa: PLC0415
        from engine.layers import badges  # noqa: PLC0415

        with mock.patch.object(project, "BADGE", create=True), mock.patch("engine.style.BADGE.head_popout", False):
            with mock.patch.object(badges, "portrait_fit", side_effect=AssetError("자산 없음")):
                self.assertEqual(project.portrait_fit_errors(NS(cache={}), "x"), [])   # 파일 없음 = 자산 점검이 보고
            with mock.patch.object(badges, "portrait_fit", side_effect=ValueError("다른 오류")), self.assertRaises(ValueError):
                project.portrait_fit_errors(NS(cache={}), "y")


if __name__ == "__main__":
    unittest.main()

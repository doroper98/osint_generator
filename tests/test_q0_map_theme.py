"""지도 테마 틀(v5.13.0 back_and_forth D-0153 Q0-2, 가이드 23 §13·§15).

- dark 테마 값 = v3 합격 값(reference_code prep3.py) — 지형 래스터는 v3 식과 바이트 동일(합성 고도로 확인).
- light 테마: 바다 회색 g → (g−21, g−5, g+8)(육지 제외), 해저 별도 hillshade.
- 테마 자산 경로(assets/theme_<이름>/), stage_config.mercator.theme 검사, 자산·무대 테마 불일치 오류, 지도 색 리터럴 없음.
"""

from __future__ import annotations

import ast
import math
import pickle
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image, ImageFilter
from pydantic import ValidationError
from shapely.geometry import box

import geo.prep_tiers as pt
from engine.assets import AssetError, Assets
from engine.stage import MercatorStage, StageError, mercator_theme
from engine.typography import HALO_RGB
from geo.prep import assets_dir
from rules import load_rules
from schemas.rules_models import GeoThemes
from tests.anti_inertia._ast_util import REPO

PREP3 = REPO / "docs" / "handoff" / "reference_code" / "v3_hormuz_korea" / "prep3.py"
TIER = pt.TierSpec("T", 24, 5, 50.0, 20.0, 58.0, 28.0)


def _fake_mosaic(_tiles: Path, T: pt.TierSpec) -> tuple[np.ndarray, int, int]:  # noqa: N803
    """합성 고도 — 서쪽 육지 산(최고 3000 m), 동쪽 해저 골(최저 −5000 m). 타일 범위 크기 그대로."""
    xr, yr = pt.tile_range(T)
    h, w = len(yr) * pt.TILE, len(xr) * pt.TILE
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    M = 3000 * np.exp(-((xx - w * 0.3) ** 2 + (yy - h * 0.5) ** 2) / (0.02 * w * h)) \
        - 5000 * np.exp(-((xx - w * 0.75) ** 2 + (yy - h * 0.4) ** 2) / (0.03 * w * h)) + 50 * np.sin(xx / 7) * np.cos(yy / 5)
    return M.astype(np.float32), xr.start, yr.start


def _build(theme: str | None, d: Path) -> np.ndarray:
    G = {"XX": box(50.0, 20.0, 54.0, 28.0)}  # noqa: N806 — 서쪽 절반 육지
    with mock.patch.object(pt, "mosaic", _fake_mosaic):
        pt.build_tier(TIER, G, d, d, 1.0, theme=None if theme is None else pt.terrain_theme(theme))
    return np.asarray(Image.open(d / "base_T_24.png").convert("RGB"), np.int16)


def _v3_reference(d: Path) -> np.ndarray:
    """prep3.py build_tier 의 색 계산(19a §H) — 상수는 v3 그대로 적는다(테마 규칙을 거치지 않는 대조 기준)."""
    T = TIER  # noqa: N806
    M, x0, y0 = _fake_mosaic(d, T)  # noqa: N806
    S, ppd = 256 * 2 ** T.z, T.ppd  # noqa: N806
    W, H = int(round((T.lon1 - T.lon0) * ppd)), int(round((pt.ym(T.lat1) - pt.ym(T.lat0)) * ppd))  # noqa: N806
    ext = ((T.lon0 + 180) / 360 * S - x0 * 256, (1 - pt.ym(T.lat1) / 180) / 2 * S - y0 * 256,
           (T.lon1 + 180) / 360 * S - x0 * 256, (1 - pt.ym(T.lat0) / 180) / 2 * S - y0 * 256)
    E = np.asarray(Image.fromarray(M, "F").transform((W, H), Image.EXTENT, ext, Image.BICUBIC), np.float32)  # noqa: N806
    lat_rows = np.degrees(2 * np.arctan(np.exp(np.radians(pt.ym(T.lat1) - (np.arange(H) + 0.5) / ppd))) - np.pi / 2)
    mpp = (111320 * np.cos(np.radians(lat_rows)) / ppd)[:, None]
    mimg, _ = pt.rasterize_land({"XX": box(50.0, 20.0, 54.0, 28.0)}, T, W, H)
    land = np.asarray(mimg.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    gy, gx = np.gradient(np.maximum(E, 0) * 2.8)
    gx /= mpp
    gy /= mpp
    az, alt = math.radians(315), math.radians(42)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    hs = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    h = pt.hexc
    lc = pt.lerp_col([(0, h("#2b313a")), (400, h("#30353c")), (1500, h("#3b3a3a")), (4000, h("#4b4640"))], np.clip(E, 0, 4000))
    lc = lc * np.clip((0.58 + 0.95 * (hs - np.sin(alt)))[..., None], 0.5, 1.5)
    sc = pt.lerp_col([(0, h("#1c4a66")), (60, h("#18415c")), (400, h("#11304a")), (2000, h("#0c2236")), (6000, h("#081626"))],
                     np.clip(-E, 0, 6000))
    glow = np.asarray(mimg.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255
    sc = sc + np.array(h("#3a9cb8"), np.float32) * glow * 0.2
    out = sc * (1 - land[..., None]) + lc * land[..., None]
    return np.clip(out, 0, 255).astype(np.uint8).astype(np.int16)


class DarkIsV3Test(unittest.TestCase):
    def test_dark_values_equal_v3_reference_code(self) -> None:
        """rules geo.themes.dark.terrain = prep3.py 리터럴(팔레트·과장·광원·음영·광채)."""
        src = PREP3.read_text(encoding="utf-8")
        t = load_rules().geo.themes.dark.terrain
        stops = re.findall(r"lerp_col\(\[(.*?)\], np\.clip", src)
        parse = [[(float(v), c) for v, c in re.findall(r"\((\d+), hexc\('(#[0-9a-f]{6})'\)\)", s)] for s in stops]
        self.assertEqual([[(v, c) for v, c in t.land_stops], [(v, c) for v, c in t.sea_stops]], parse)
        self.assertIn(f"ex = {t.exaggeration[0]} if ppd < 64 else {t.exaggeration[1]}", src)
        self.assertIn(f"math.radians({t.sun[0]:g}), math.radians({t.sun[1]:g})", src)
        s = t.land_shade
        self.assertIn(f"({s.base} + {s.gain} * (hs - np.sin(alt)))[..., None], {s.lo}, {s.hi})", src)
        g = t.coast_glow
        self.assertIn(f"GaussianBlur({g.blur_px[0]:g} if ppd < 64 else {g.blur_px[1]:g})", src)
        self.assertIn(f"hexc('{g.rgb}'), np.float32) * glow * {g.strength}", src)
        self.assertIsNone(t.sea_shade)
        self.assertIsNone(t.sea_tint)

    def test_dark_raster_bytes_equal_v3_formula(self) -> None:
        """기본(dark) 테마 래스터 = v3 식 그대로(바이트 동일) — 골든 지형 무변경의 근거."""
        with tempfile.TemporaryDirectory() as d:
            got = _build(None, Path(d))
            ref = _v3_reference(Path(d))
            self.assertEqual(got.shape, ref.shape)
            self.assertTrue(np.array_equal(got, ref))


class LightTerrainTest(unittest.TestCase):
    def test_sea_tint_and_land_untouched(self) -> None:
        """light: 바다 = 회색 g → (g−21, g−5, g+8)(§15), 육지는 회색 톤 그대로(변환 없음), dark 와 다른 래스터."""
        th = pt.terrain_theme("light")
        self.assertEqual(tuple(th.sea_tint), (-21, -5, 8))
        with tempfile.TemporaryDirectory() as d:
            img = _build("light", Path(d))
        h, w, _ = img.shape
        sea = img[:, int(w * 0.75):].reshape(-1, 3)       # 해안에서 먼 바다(광채 없음, 육지 블렌드 0)
        land = img[:, : int(w * 0.4)].reshape(-1, 3)
        dg, db = sea[:, 1] - sea[:, 0], sea[:, 2] - sea[:, 0]
        self.assertLessEqual(np.abs(dg - 16).max(), 1)
        self.assertLessEqual(np.abs(db - 29).max(), 1)
        self.assertLessEqual((land[:, 2] - land[:, 0]).max(), 1)          # 육지에 바다 변환(B +29) 없음 — 회색·따뜻한 회색 그대로
        self.assertGreater(land.mean(), 200)                               # 밝은 육지
        self.assertGreater(sea[:, 0].std(), 1.0)                           # 해저 hillshade 가 결을 만든다

    def test_theme_extra_key_rejected(self) -> None:
        raw = load_rules().geo.themes.model_dump()
        raw["light"]["terrain"]["glow"] = 1
        with self.assertRaises(ValidationError):
            GeoThemes.model_validate(raw)
        raw = load_rules().geo.themes.model_dump()
        raw["default"] = "sepia"
        with self.assertRaises(ValidationError):
            GeoThemes.model_validate(raw)


class ThemePathAndStageTest(unittest.TestCase):
    def test_assets_dir_per_theme(self) -> None:
        p = Path("/x")
        self.assertEqual(assets_dir(p, None), p / "assets")
        self.assertEqual(assets_dir(p, None, "dark"), p / "assets")
        self.assertEqual(assets_dir(p, None, "light"), p / "assets" / "theme_light")
        self.assertEqual(assets_dir(p, "720p", "light"), p / "assets" / "theme_light" / "res_720p")
        with self.assertRaises(ValueError):
            assets_dir(p, None, "sepia")

    def test_stage_config_theme(self) -> None:
        self.assertEqual(mercator_theme(None), "dark")
        self.assertEqual(mercator_theme({"theme": "light", "border_glow": False}), "light")
        with self.assertRaises(StageError):
            mercator_theme({"theme": "sepia"})
        with self.assertRaises(StageError):
            mercator_theme({"palette": "light"})
        R = load_rules().geo.themes  # noqa: N806
        self.assertEqual(MercatorStage().theme, R.dark.map)
        self.assertEqual(MercatorStage(config={"theme": "light"}).theme, R.light.map)

    def test_assets_theme_dir_and_mismatch(self) -> None:
        """light 자산이 없으면 오류(dark 로 대신 그리지 않음, P6), 있으면 theme_light 에서 읽고 무대와 테마가 다르면 오류."""
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "assets"
            tl = a / "theme_light"
            tl.mkdir(parents=True)
            tier = dict(lon0=0.0, lon1=1.0, lat0=0.0, lat1=1.0, ppd=6, tiles="", z=1, levels=[6])
            pickle.dump({"W": tier}, open(a / "tiers.pkl", "wb"))
            Image.new("RGB", (6, 6), (1, 2, 3)).save(a / "base_W_6.png")
            pickle.dump({"places": []}, open(a / "geo.pkl", "wb"))
            with self.assertRaises(AssetError) as cm:
                Assets(Path(d), None, theme="light")  # type: ignore[arg-type]
            self.assertIn("--theme light", str(cm.exception))
            pickle.dump({"W": tier}, open(tl / "tiers.pkl", "wb"))
            Image.new("RGB", (6, 6), (200, 201, 202)).save(tl / "base_W_6.png")
            A = Assets(Path(d), None, theme="light")  # type: ignore[arg-type]  # noqa: N806
            self.assertEqual(A.base[("W", 6)].getpixel((0, 0)), (200, 201, 202))
            dark = Assets(Path(d), None)  # type: ignore[arg-type]
            self.assertEqual(dark.base[("W", 6)].getpixel((0, 0)), (1, 2, 3))
            with self.assertRaises(StageError):
                MercatorStage.__init__(object.__new__(MercatorStage), dark, config={"theme": "light"})


class NoMapColorLiteralTest(unittest.TestCase):
    def test_map_layers_take_colors_from_theme(self) -> None:
        """draw_borders·draw_labels 의 set_source_rgba 에 숫자 리터럴 색이 없다 — 색은 stage.theme(rules) 에서만."""
        for rel, fn in (("engine/layers/borders.py", "draw_borders"), ("engine/layers/labels.py", "draw_labels")):
            tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
            f = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn)
            for c in ast.walk(f):
                if isinstance(c, ast.Call) and getattr(c.func, "attr", "") in ("set_source_rgba", "set_source_rgb"):
                    lits = [a for a in c.args[:3] if isinstance(a, ast.Constant)]
                    self.assertEqual(lits, [], f"{rel}:{c.lineno} 색 리터럴")

    def test_default_halo_equals_dark_theme(self) -> None:
        self.assertEqual(tuple(HALO_RGB), tuple(load_rules().geo.themes.dark.map.halo))


if __name__ == "__main__":
    unittest.main()

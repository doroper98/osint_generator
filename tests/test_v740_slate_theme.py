"""v7.4.0 UF-900·D903 R1 — 지도 테마 `slate`(레퍼런스 벤치마크 docs/handoff/reports/benchmark_wartech_2026-11-17.md §2.2·§4.2).

- rules 에 slate 가 있고 GeoThemes.names() 에 든다. 없는 이름은 오류(조용히 dark 로 가지 않는다, P6).
- 지도 키 집합 = dark 와 같다(국경 발광 border_glow 만 더한다).
- 바다 = 단색(모든 수심 정지점 같은 색, 해저 음영·색 변환·해안 광채 없음), 평지 = ramp 색 그대로(land_shade.base 1.0).
- 국경 발광은 정지(run_layers [] — 흐르는 빛 없음): 시각이 달라도 같은 그림.
- 지형 굽기(합성 고도, 네트워크 없음): 바다 화소가 전부 #1a1e27, 평지는 첫 정지점 색.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cairo
import numpy as np
from PIL import Image
from shapely.geometry import box

import geo.prep_tiers as pt
from engine.layers.borders import draw_border_glow
from engine.projection import View
from engine.stage import MercatorStage, StageError, mercator_theme, to_uv, ym
from geo.prep import assets_dir
from rules import load_rules
from schemas.rules_models import GeoThemes

TIER = pt.TierSpec("T", 24, 5, 50.0, 20.0, 58.0, 28.0)
TIERS = {"W": {"lon0": 40.0, "lat0": 15.0, "lon1": 70.0, "lat1": 40.0}}


def _keys(m: object, pre: str = "") -> set[str]:
    out: set[str] = set()
    for k in type(m).model_fields:
        v = getattr(m, k)
        if v is None:
            continue
        out.add(pre + k)
        if hasattr(type(v), "model_fields"):
            out |= _keys(v, pre + k + ".")
    return out


def _flat_mosaic(_tiles: Path, T: pt.TierSpec) -> tuple[np.ndarray, int, int]:  # noqa: N803
    """합성 고도 — 서쪽 육지는 0 m 평지(바다 쪽은 −10~−5000 m 기울기). 평지 색·바다 단색 확인용."""
    xr, yr = pt.tile_range(T)
    h, w = len(yr) * pt.TILE, len(xr) * pt.TILE
    _, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    M = np.where(xx < w * 0.5, 0.0, -10.0 - 5000.0 * (xx - w * 0.5) / (w * 0.5))
    return M.astype(np.float32), xr.start, yr.start


class SlateRulesTest(unittest.TestCase):
    def test_registered(self) -> None:
        th = load_rules().geo.themes
        self.assertIn("slate", GeoThemes.names())
        self.assertIs(th.get("slate"), th.slate)
        self.assertEqual(th.default, "dark")   # 기본 테마는 그대로(장르 기본값 변경은 R4)

    def test_map_keys_equal_dark_plus_glow(self) -> None:
        """채운 지도 키 = dark 와 같다. 다른 것은 국경 발광(border_glow)과, dark 가 무대 LOD 알파(null)로 두는 선 알파뿐."""
        th = load_rules().geo.themes
        dk, sk = _keys(th.dark.map), _keys(th.slate.map)
        self.assertEqual(sk - dk - {"border.alpha", "admin.alpha"}, {k for k in sk if k.startswith("border_glow")})
        self.assertEqual(dk - sk, set())
        self.assertIn("border_glow", sk)

    def test_flat_sea_no_glow(self) -> None:
        t = load_rules().geo.themes.slate.terrain
        self.assertEqual({c.lower() for _, c in t.sea_stops}, {"#1a1e27"})
        self.assertIsNone(t.sea_shade)
        self.assertIsNone(t.sea_tint)
        self.assertEqual(t.coast_glow.strength, 0.0)
        self.assertEqual(t.land_shade.base, 1.0)   # 평지(hs = sin 고도) = ramp 색 그대로

    def test_static_white_border(self) -> None:
        m = load_rules().geo.themes.slate.map
        self.assertEqual(tuple(m.border.rgb), (1.0, 1.0, 1.0))
        self.assertIsNone(m.coast)   # 해안선 = 국경과 같은 선(dark 와 같음)
        self.assertEqual(m.admin.dash, [])
        self.assertTrue(m.border_glow.enabled)
        self.assertEqual(m.border_glow.run_layers, [])   # 흐르는 빛 없음
        self.assertTrue(m.border_glow.halo)


class SlateStageTest(unittest.TestCase):
    def test_mercator_theme(self) -> None:
        self.assertEqual(mercator_theme({"theme": "slate", "theme_reason": "r"}), "slate")
        with self.assertRaises(StageError):
            mercator_theme({"theme": "slate_blue"})
        st = MercatorStage(config={"theme": "slate"})
        self.assertEqual(st.theme, load_rules().geo.themes.slate.map)
        self.assertTrue(st.border_glow)

    def test_assets_dir(self) -> None:
        p = Path("/x")
        self.assertEqual(assets_dir(p, "1080p", "slate"), p / "assets" / "theme_slate" / "res_1080p")

    def test_glow_is_static(self) -> None:
        """slate 발광은 시각과 무관(정지 halo 만). dark 는 흐르는 빛이라 시각마다 다르다(대조)."""
        def frame(theme: str, t: float) -> bytes:
            st = MercatorStage(tiers=TIERS, config={"theme": theme})
            ring = np.array([[50.0, 22.0], [60.0, 22.0], [60.0, 32.0], [50.0, 32.0]], np.float64)
            st.bord = {lod: {"XX": to_uv([ring])} for lod in ("coarse", "fine")}
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
            draw_border_glow(cairo.Context(surf), st, View(st, np.array([55.0, ym(27.0), 20.0])), t)
            surf.flush()
            return bytes(surf.get_data())

        self.assertEqual(frame("slate", 0.0), frame("slate", 3.7))
        self.assertNotEqual(frame("slate", 0.0), bytes(854 * 480 * 4))
        self.assertNotEqual(frame("dark", 0.0), frame("dark", 3.7))


class SlateTerrainBakeTest(unittest.TestCase):
    def test_bake_flat_sea_and_plain_land(self) -> None:
        th = pt.terrain_theme("slate")
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(pt, "mosaic", _flat_mosaic):
                pt.build_tier(TIER, {"XX": box(50.0, 20.0, 53.0, 28.0)}, Path(d), Path(d), 1.0, theme=th)
            img = np.asarray(Image.open(Path(d) / "base_T_24.png").convert("RGB"), np.int16)
        h, w, _ = img.shape
        sea = img[:, int(w * 0.6):].reshape(-1, 3)
        land = img[2:-2, 2:int(w * 0.3)].reshape(-1, 3)
        # 단색 바다(수심·광채 무관). 같은 색 두 정지점 사이 보간의 부동소수(29.99… → uint8 29) 때문에 ±1 까지 허용
        self.assertLessEqual(np.abs(sea - pt.hexc("#1a1e27")).max(), 1)
        self.assertEqual(tuple(np.median(sea, 0).astype(int)), tuple(pt.hexc("#1a1e27")))
        self.assertLessEqual(np.abs(land - pt.hexc(th.land_stops[0][1])).max(), 1)   # 평지 = 첫 정지점 색


if __name__ == "__main__":
    unittest.main()

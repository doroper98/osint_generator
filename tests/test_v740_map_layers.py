"""v7.4.0 back_and_forth D-0229 §2.1(UF-106) — 지도 도로·강 레이어, 수도 상시 표기.

(a) geo.pkl(build_geo)에 roads·rivers 키(coarse/fine × 등급), (b) 근접 폭(w=8)에서 도로 색 화소 > 0, 넓은 폭(w=60)에서 0,
(c) 두 테마의 map 토큰 키 집합 동일(roads·rivers 포함), (d) 옛 geo.pkl(roads·rivers 없음)은 오류(조용히 빼고 그리지 않는다, P6).
골든 25컷 무변화는 tests/anti_inertia 골든 e2e 가 본다.
"""

from __future__ import annotations

import types
import unittest
from pathlib import Path

import cairo
import numpy as np

from engine.layers.rivers import draw_rivers
from engine.layers.roads import draw_roads
from engine.projection import View
from engine.stage import MercatorStage, StageError, to_uv, ym
from geo.prep_geometry import ROAD_CLASSES, RIVER_CLASSES, build_geo
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
NE = REPO / "data" / "geo" / "ne"
TIERS = {"W": {"lon0": 20.0, "lat0": 30.0, "lon1": 80.0, "lat1": 70.0}}


def _stage(theme: str = "dark") -> MercatorStage:
    st = MercatorStage(tiers=TIERS, config={"theme": theme})
    line = [np.array([[37.0, 55.0], [40.0, 54.6]], np.float32)]   # 모스크바 → 랴잔 근처(M5 모양) 합성 선
    st.roads = {lod: {c: to_uv(line) for c in ROAD_CLASSES} for lod in ("coarse", "fine")}
    st.rivers = {lod: {c: to_uv(line) for c in RIVER_CLASSES} for lod in ("coarse", "fine")}
    return st


def _ink(theme: str, w: float, fn) -> int:  # noqa: ANN001
    st = _stage(theme)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    view = View(st, np.array([38.5, ym(54.8), w]))
    fn(cairo.Context(surf), st, view)
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(480, -1, 4)
    return int((a[..., 3] > 0).sum())


class GeoPklTest(unittest.TestCase):
    def test_build_geo_has_roads_rivers(self) -> None:
        if not (NE / "ne_10m_roads.geojson").exists():
            self.fail("Natural Earth 도로 파일 없음 — `python -m geo.prep <프로젝트>` 가 data/geo/ne 에 받는다")
        geo, _ = build_geo(NE, (36.0, 53.0, 42.0, 57.0), set())
        for key, classes in (("roads", ROAD_CLASSES), ("rivers", RIVER_CLASSES)):
            self.assertEqual(set(geo[key]) - {"scalerank"}, {"coarse", "fine"})
            for lod in ("coarse", "fine"):
                self.assertEqual(set(geo[key][lod]), set(classes))
        self.assertGreater(sum(len(v) for v in geo["roads"]["fine"].values()), 0)   # 모스크바·랴잔 권역 도로
        self.assertGreater(sum(len(v) for v in geo["rivers"]["fine"].values()), 0)   # 오카·볼가 수계

    def test_old_geo_pkl_is_error(self) -> None:
        A = types.SimpleNamespace(geo=dict(coarse={}, fine={}, admin1={}, meta={}, places=[]), theme=None, tiers=TIERS,  # noqa: N806
                                  labels=types.SimpleNamespace(seas=[]))
        with self.assertRaises(StageError):
            MercatorStage(A)


class LodRenderTest(unittest.TestCase):
    def test_roads_near_on_far_off(self) -> None:
        for th in ("dark", "light"):
            self.assertGreater(_ink(th, 8.0, draw_roads), 0, th)
            self.assertEqual(_ink(th, 60.0, draw_roads), 0, th)

    def test_rivers_minor_near_major_mid(self) -> None:
        self.assertGreater(_ink("dark", 8.0, draw_rivers), 0)
        self.assertGreater(_ink("dark", 30.0, draw_rivers), 0)    # 큰 강은 40° 아래부터
        self.assertEqual(_ink("dark", 60.0, draw_rivers), 0)


class ThemeTokenParityTest(unittest.TestCase):
    def test_same_key_sets(self) -> None:
        th = load_rules().geo.themes

        def keys(m: object, pre: str = "") -> set[str]:
            out: set[str] = set()
            for k in type(m).model_fields:
                v = getattr(m, k)
                if v is None:
                    continue
                out.add(pre + k)
                if hasattr(type(v), "model_fields"):
                    out |= keys(v, pre + k + ".")
            return out

        dk, lk = keys(th.dark.map), keys(th.light.map)
        for k in ("roads.motorway", "roads.trunk", "roads.primary", "rivers.rgb"):
            self.assertIn(k, dk)
        self.assertEqual({k for k in dk if k.startswith(("roads", "rivers"))}, {k for k in lk if k.startswith(("roads", "rivers"))})


class CapitalAlwaysTest(unittest.TestCase):
    def test_rule_on(self) -> None:
        self.assertTrue(load_rules().labels.capital_always)

    def test_only_national_capitals(self) -> None:
        """1급 행정 중심(NE Admin-1 capital — 담맘·푸자이라 등)은 상시 표기 대상이 아니다(cap0 = 나라 수도만)."""
        from geo.prep_geometry import load_places  # noqa: PLC0415
        from shapely.geometry import box  # noqa: PLC0415

        if not (NE / "ne_10m_populated_places.geojson").exists():
            self.fail("Natural Earth 도시 파일 없음 — `python -m geo.prep <프로젝트>` 가 받는다")
        pl = {p["ko"]: p for p in load_places(NE, box(44, 20, 62, 32))}
        self.assertTrue(pl["도하"]["cap0"])
        self.assertFalse(pl["담맘"]["cap0"])
        self.assertTrue(pl["담맘"]["cap"])   # 기존 cap(rank+2 가산)은 그대로


if __name__ == "__main__":
    unittest.main()

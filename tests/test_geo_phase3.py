"""Phase 3 지오 테스트 (v2.2.0, D-0015 §1-7).

재귀 평탄화(프랑스 회귀), 타일 범위(19a §H 값), 커버리지 검출, 박스 클램프, 크림 재분류 on/off,
geo/ 의 legacy_v3 비의존. 네트워크·지형 타일 없이 도는 픽스처만 쓴다.
"""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from shapely.geometry import GeometryCollection, MultiPolygon, Point, box, shape

from geo.prep import GeoConf, classify_miss
from rules import load_rules
from geo.prep_geometry import build_geo, parse_bbox, polys, rings
from geo.prep_tiers import MERC_LAT_MAX, TierSpec, lonlat_to_tile, rasterize_land, tile_range

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures" / "geo"


class FlattenTest(unittest.TestCase):
    def test_nested_multipolygon_in_collection(self) -> None:
        mp = MultiPolygon([box(0, 0, 1, 1), box(2, 0, 3, 1)])
        gc = GeometryCollection([Point(5, 5), GeometryCollection([mp]), box(4, 4, 5, 5)])
        self.assertEqual(len(polys(gc)), 3)  # v2 1단계 펼침은 여기서 MultiPolygon 을 통째로 잃었다
        self.assertEqual(polys(None), [])
        self.assertEqual(len(rings(gc, 0.001)), 3)

    def test_france_regression(self) -> None:
        """유럽 bbox 에서 프랑스 대표점이 육지로 칠해진다(04 §3.3)."""
        fc = json.loads((FIX / "fr_europe.geojson").read_text(encoding="utf-8"))
        g = shape(fc["features"][0]["geometry"])
        G = {"FR": GeometryCollection([g])}  # noqa: N806 — 교집합 결과가 컬렉션으로 감싸인 경우
        T = TierSpec.parse("EU:24:5:-12,35,20,60")  # noqa: N806
        W = int(round((T.lon1 - T.lon0) * T.ppd))  # noqa: N806
        from geo.prep_tiers import ym

        H = int(round((ym(T.lat1) - ym(T.lat0)) * T.ppd))  # noqa: N806
        mimg, miss = rasterize_land(G, T, W, H)
        self.assertEqual(miss, [])
        rp = g.representative_point()
        x, y = (rp.x - T.lon0) * T.ppd, (ym(T.lat1) - ym(rp.y)) * T.ppd
        self.assertGreaterEqual(mimg.getpixel((int(x), int(y))), 128)


class TileRangeTest(unittest.TestCase):
    def test_v3_tiers(self) -> None:
        """19a §H 티어의 타일 수 = Phase 1 에 받은 장수(W 77, G 42, K 16)."""
        for s, n in (("W:24:5:28,-12,140,48", 77), ("G:96:7:46,20.5,62,32.5", 42), ("K:96:7:122.5,32.3,131.8,39.8", 16)):
            xr, yr = tile_range(TierSpec.parse(s))
            self.assertEqual(len(xr) * len(yr), n, s)
        xr, yr = tile_range(TierSpec.parse("W:24:5:28,-12,140,48"))
        self.assertEqual((xr.start, xr.stop - 1, yr.start, yr.stop - 1), (18, 28, 11, 17))

    def test_box_clamp(self) -> None:
        T = TierSpec.parse("X:8:3:-180.0000001,-89,180.0000001,89.5")  # noqa: N806
        self.assertEqual((T.lon0, T.lon1), (-180.0, 180.0))
        self.assertEqual((T.lat0, T.lat1), (-MERC_LAT_MAX, MERC_LAT_MAX))
        self.assertEqual(lonlat_to_tile(180.0, 0.0, 3), (7, 4))
        self.assertEqual(lonlat_to_tile(0.0, 90.0, 3)[1], 0)
        xr, yr = tile_range(T)
        self.assertEqual((len(xr), len(yr)), (8, 8))
        with self.assertRaises(ValueError):
            TierSpec.parse("X:8:3:10,10,10,20")
        with self.assertRaises(ValueError):
            parse_bbox("1,2,3")


class CoverageTest(unittest.TestCase):
    def test_tiny_island_is_reported(self) -> None:
        """v3 W 티어에서 몰디브(산호섬 176조각)는 land-miss 로 드러나고 스리랑카는 육지다(Phase 1 실측과 같음)."""
        from geo.prep_tiers import ym

        fc = json.loads((FIX / "mv_lk.geojson").read_text(encoding="utf-8"))
        G = {f["properties"]["ISO_A2_EH"]: shape(f["geometry"]) for f in fc["features"]}  # noqa: N806
        T = TierSpec.parse("W:24:5:28,-12,140,48")  # noqa: N806
        W = int(round((T.lon1 - T.lon0) * T.ppd))  # noqa: N806
        H = int(round((ym(T.lat1) - ym(T.lat0)) * T.ppd))  # noqa: N806
        _, miss = rasterize_land(G, T, W, H)
        self.assertEqual(miss, ["MV"])
        cls = classify_miss(miss, G, T.ppd)  # 임계는 rules geo.land_miss_allow_px2 (D29)
        self.assertEqual((cls["small"], cls["drops"]), (["MV"], []))
        self.assertLess(cls["px2"]["MV"], load_rules().geo.land_miss_allow_px2)
        big = classify_miss(["LK"], G, T.ppd)  # 스리랑카 크기가 누락되면 허용되지 않는다
        self.assertEqual(big["drops"], ["LK"])


class CrimeaTest(unittest.TestCase):
    def test_off_and_on(self) -> None:
        bb = (25, 40, 45, 55)
        geo_off, G_off = build_geo(FIX / "ne_crimea", bb, set())  # noqa: N806
        self.assertTrue(G_off["RU"].contains(Point(34.5, 45.2)))
        self.assertFalse(G_off["UA"].contains(Point(34.5, 45.2)))
        geo_on, G_on = build_geo(FIX / "ne_crimea", bb, set(), crimea_to_ua=True)  # noqa: N806
        self.assertTrue(G_on["UA"].contains(Point(34.5, 45.2)))
        self.assertFalse(G_on["RU"].intersects(Point(34.5, 45.2)))
        self.assertTrue(G_on["RU"].contains(Point(38, 45)))  # 크림 밖 러시아는 그대로
        self.assertEqual(set(geo_on["coarse"]), {"UA", "RU"})


class ConfTest(unittest.TestCase):
    def test_geo_yaml_contract(self) -> None:
        import yaml

        for proj in ("hormuz_korea", "taiwan_strait"):
            conf = GeoConf.model_validate(yaml.safe_load((REPO / "projects" / proj / "geo.yaml").read_text(encoding="utf-8")))
            self.assertIn("W", [t.name for t in conf.tiers], proj)
        with self.assertRaises(Exception):
            GeoConf.model_validate({"bbox": [0, 0, 1, 1], "tiers": [], "extra": 1})


class NoLegacyTest(unittest.TestCase):
    def test_geo_does_not_import_legacy(self) -> None:
        for p in (REPO / "geo").glob("*.py"):
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    mods = [node.module or ""]
                for m in mods:
                    self.assertFalse(m.startswith("legacy_v3"), f"{p.name}: import {m}")


if __name__ == "__main__":
    unittest.main()

"""국가 지오메트리 키 충돌 — 같은 ISO 키 피처는 합집합, 커버리지는 면적 비율 (v4.1.0, back_and_forth D-0078, PIPELINE-AP-011).

증상: `load_countries` 가 `G[ISO_A2_EH] = …` 로 덮어써 카자흐스탄(KZ)이 뒤에 나오는 바이코누르 조각만 남고 바다로 그려졌다.
대표점 한 점 커버리지 검사는 그 조각 위에서 찍어 통과했다. 픽스처 = Natural Earth 10m 에서 KZ·바이코누르·UZ 만 뽑은 단순화본.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shapely.geometry import Point, box
from shapely.ops import unary_union

from geo.prep import CACHE, classify_miss
from geo.prep_geometry import country_parts, coverage_reference, load_countries
from geo.prep_tiers import TierSpec, fill_ratios, rasterize_land, ym
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures" / "geo" / "ne_kz"
RATCLIFFE_BB = box(-95, 5, 75, 72)                       # projects/ratcliffe2026/geo.yaml bbox
TIER = TierSpec.parse("W:24:5:-88,12,70,66")              # 랫클리프 W 티어


def _raster(G: dict, ref: dict | None = None, ratios: dict | None = None) -> tuple:  # noqa: N803
    W = int(round((TIER.lon1 - TIER.lon0) * TIER.ppd))  # noqa: N806
    H = int(round((ym(TIER.lat1) - ym(TIER.lat0)) * TIER.ppd))  # noqa: N806
    return rasterize_land(G, TIER, W, H, None, ref, ratios)


def _overwritten(bb: object) -> dict:
    """v4.0.0 까지의 덮어쓰기(뒤 피처가 이긴다) 재현."""
    return {k: v[-1][1].intersection(bb) for k, v in country_parts(FIX, bb).items()}


class UnionTest(unittest.TestCase):
    def test_same_key_features_are_unioned(self) -> None:
        parts = country_parts(FIX, RATCLIFFE_BB)
        self.assertEqual([p["ADMIN"] for p, _ in parts["KZ"]], ["Kazakhstan", "Baykonur Cosmodrome"])
        G, META = load_countries(FIX, RATCLIFFE_BB)  # noqa: N806
        want = unary_union([g.intersection(RATCLIFFE_BB) for _, g in parts["KZ"]])   # 단순화 픽스처는 바이코누르 구멍이 메워져 겹친다
        self.assertAlmostEqual(G["KZ"].area, want.area, places=6)
        self.assertTrue(all(G["KZ"].buffer(1e-9).contains(g.intersection(RATCLIFFE_BB)) for _, g in parts["KZ"]))
        self.assertTrue(G["KZ"].contains(Point(70.0, 50.0)))      # 카자흐스탄 중부(아스타나 남서) — 옛 방식은 바다
        self.assertEqual(META["KZ"]["name"], "Kazakhstan")          # META 는 면적이 큰 피처

    def test_kz_area_in_ratcliffe_bbox(self) -> None:
        G, _ = load_countries(FIX, RATCLIFFE_BB)  # noqa: N806
        self.assertGreaterEqual(G["KZ"].area, 240)
        self.assertLess(_overwritten(RATCLIFFE_BB)["KZ"].area, 1)  # 옛 방식 = 바이코누르 0.75 deg²

    def test_single_feature_key_unchanged(self) -> None:
        """피처 하나인 키는 v3 계산(g ∩ 권역) 그대로 — 다른 나라 지오메트리·골든 무변경."""
        G, _ = load_countries(FIX, RATCLIFFE_BB)  # noqa: N806
        (_, g), = country_parts(FIX, RATCLIFFE_BB)["UZ"]
        self.assertTrue(G["UZ"].equals_exact(g.intersection(RATCLIFFE_BB), 0))


class AreaCoverageTest(unittest.TestCase):
    def test_area_check_catches_overwrite(self) -> None:
        """대표점 검사만으로는 통과하던 덮어쓰기를 면적 비율 검사가 잡는다."""
        old = _overwritten(RATCLIFFE_BB)
        _, miss_point = _raster(old)
        self.assertNotIn("KZ", miss_point)                          # 옛 검사의 구멍(D-0078)
        ref = coverage_reference(FIX, RATCLIFFE_BB)
        ratios: dict = {}
        _, miss = _raster(old, ref, ratios)
        self.assertIn("KZ", miss)
        self.assertLess(ratios["KZ"], load_rules().geo.land_fill_min_ratio)
        cls = classify_miss(miss, old, TIER.ppd, ref)
        self.assertIn("KZ", cls["drops"])                           # 잃은 면적(원본 기준)으로 재서 drop

    def test_fixed_geometry_passes(self) -> None:
        G, _ = load_countries(FIX, RATCLIFFE_BB)  # noqa: N806
        ratios: dict = {}
        _, miss = _raster(G, coverage_reference(FIX, RATCLIFFE_BB), ratios)
        self.assertNotIn("KZ", miss)
        self.assertGreater(ratios["KZ"], 0.99)

    def test_fill_ratios_skip_tiny(self) -> None:
        G, _ = load_countries(FIX, RATCLIFFE_BB)  # noqa: N806
        mimg, _ = _raster(G)
        tiny = {"XX": box(10.0, 50.0, 10.01, 50.01)}
        self.assertEqual(fill_ratios(mimg, tiny, TIER, 0.02), {})   # 16px² 미만은 대표점·small 규칙 몫

    def test_rule_value_in_rules(self) -> None:
        self.assertTrue(0 < load_rules().geo.land_fill_min_ratio <= 1)


@unittest.skipUnless((CACHE / "ne" / "ne_10m_admin_0_countries.geojson").exists(),
                     "Natural Earth 실데이터 없음(`python tools/fetch_data.py ne`) — 픽스처 테스트가 같은 규칙을 본다")
class RealDataTest(unittest.TestCase):
    def test_every_colliding_key_is_union(self) -> None:
        """실데이터에서 피처가 2개 이상인 키(KZ·FR·BR·AU 등)는 전부 합집합으로 조립된다(세계 bbox)."""
        ne = CACHE / "ne"
        bb = box(-180, -85, 180, 85)
        parts = country_parts(ne, bb)
        multi = {k for k, v in parts.items() if len(v) > 1}
        self.assertTrue({"KZ", "FR"} <= multi, sorted(multi))
        G, _ = load_countries(ne, bb)  # noqa: N806
        for k in multi:
            self.assertAlmostEqual(G[k].area, sum(g.intersection(bb).area for _, g in parts[k]), delta=1e-6, msg=k)


if __name__ == "__main__":
    unittest.main()

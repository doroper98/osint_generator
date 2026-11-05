"""[basemap-upscale] — 지도 확대 때 지형 원천 늘림(v7.4.0 back_and_forth D-0630 §2, 사용자 의견 UF-261 "지도가 확대될때 해상도가 크게 낮아지네").

- 판정 함수 basemap_upscale_runs: 늘림 배율 > max_ratio 가 max_sec 넘게 이어질 때만 실패(줌 이동 중 잠깐은 허용).
- MercatorStage.tier_plan·upscale_ratio: 그리기와 검사가 같은 함수. 실효 원천 ppd = 고른 레벨과 타일 줌 고유 해상도(256·2^z/360) 중 작은 값.
- 콘티 판 v2 칸나이 실측: 3도 폭 6.8배·1.75도 12배(W 40ppd) — 실패. 기본(v3) 블렌딩은 그대로(골든 불변), blend: relative 는 아래 층 대비 비율로 이음.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine.checks import QA, basemap_upscale_runs
from engine.stage import MercatorStage

W = {"lon0": -10.0, "lon1": 30.0, "lat0": 28.0, "lat1": 49.0, "ppd": 40, "z": 6, "levels": [40, 20, 10]}
I = {"lon0": -1.6, "lon1": 23.5, "lat0": 36.1, "lat1": 46.6, "ppd": 120, "z": 8, "levels": [120, 60, 30], "blend": "relative"}
A = {"lon0": 11.6, "lon1": 19.7, "lat0": 39.6, "lat1": 43.2, "ppd": 360, "z": 10, "levels": [360, 180, 90], "blend": "relative"}
G = {"lon0": 15.5, "lon1": 16.7, "lat0": 40.9, "lat1": 41.75, "ppd": 1200, "z": 11, "levels": [1200, 600, 300]}


def _stage(tiers: dict) -> MercatorStage:
    return MercatorStage(tiers=tiers)


def _view(st: MercatorStage, lon: float, lat: float, w: float):  # noqa: ANN202
    from engine.projection import View  # noqa: PLC0415

    return View(st, (lon, st.to_world(lon=lon, lat=lat)[1], w))


class RunsTest(unittest.TestCase):
    def test_short_zoom_pass_allowed_long_fails(self) -> None:
        c = QA.basemap_upscale
        short = [(i * c.step_sec, 6.0, "W") for i in range(int(c.max_sec / c.step_sec))]
        self.assertEqual(basemap_upscale_runs(short), [])
        long = [(i * c.step_sec, 6.8, "W") for i in range(20)]
        self.assertEqual(len(basemap_upscale_runs(long)), 1)
        self.assertEqual(basemap_upscale_runs([(0.0, 1.2, "K"), (0.25, 1.4, "K")]), [])


class StageRatioTest(unittest.TestCase):
    def test_v2_cannae_views_fail_with_w_only(self) -> None:
        st = _stage({"W": W, "G": G})
        for w, want in ((3.1, 6.8), (1.75, 12.2)):
            r, tier = st.upscale_ratio(_view(st, 16.0, 41.3, w))
            self.assertEqual(tier, "W")
            self.assertAlmostEqual(r, want, delta=0.2)
            self.assertGreater(r, QA.basemap_upscale.max_ratio)

    def test_mid_tier_fixes_and_native_zoom_caps(self) -> None:
        st = _stage({"W": W, "A": A})
        r, tier = st.upscale_ratio(_view(st, 15.6, 41.4, 3.1))
        self.assertEqual(tier, "A")
        self.assertLessEqual(r, QA.basemap_upscale.max_ratio)
        low_z = dict(A, z=7)   # 레벨 360 이어도 z7 타일 고유 해상도 91 px/도 — 늘림
        st2 = _stage({"W": W, "A": low_z})
        self.assertGreater(st2.upscale_ratio(_view(st2, 15.6, 41.4, 3.1))[0], QA.basemap_upscale.max_ratio)

    def test_relative_blend_is_gradual(self) -> None:
        """겹친 티어 사슬(W 40 → I 120 → A 360): 아래 층이 모자라기 전(비율 0.8)에 안에 들고 1.2 까지 천천히 섞인다."""
        st = _stage({"W": W, "I": I, "A": A})
        alphas = [dict((n, a) for n, a, _ in st.tier_plan(_view(st, 15.6, 41.4, w))).get("A", 0.0) for w in (8.0, 7.4, 6.8, 6.2, 5.6, 5.0)]
        self.assertEqual(alphas, sorted(alphas))   # 확대할수록 커진다
        self.assertTrue(any(0.05 < a < 0.95 for a in alphas))   # 한 프레임에 0 → 1 로 튀지 않는다

    def test_v3_blend_unchanged(self) -> None:
        """기본 티어는 옛 규칙 smooth((설계 ppd − 26)/18) 그대로(골든 불변)."""
        from engine.stage import MERCATOR_LOD  # noqa: PLC0415
        from engine.style import W_OUT  # noqa: PLC0415
        from engine.timebase import smooth  # noqa: PLC0415

        st = _stage({"W": W, "G": G})
        v = _view(st, 16.1, 41.3, 0.6)
        tb = MERCATOR_LOD["tier_blend_ppd"]
        self.assertAlmostEqual(dict((n, a) for n, a, _ in st.tier_plan(v))["G"], smooth((W_OUT / 0.6 - tb["from"]) / tb["span"]))
        self.assertEqual(NS(x=1).x, 1)


if __name__ == "__main__":
    unittest.main()

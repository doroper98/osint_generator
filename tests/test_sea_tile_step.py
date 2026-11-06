"""v7.4.0 D-0634 §2(RENDER-AP-040) — [sea-tile-step] 바다 타일 계단 장치와 바다 수심 원천 줌(geo.sea_bathymetry_max_z).

칸나이 v1 아드리아해(9~36·306~318초): AWS terrarium z9 이상은 해안을 낀 타일의 바다가 0 m(수심 없음), 옆 먼바다 타일은 수심 있음 →
바다 색이 타일 단위로 계단. 실제 프레임 판정(프리뷰 14·31초, final 12·309·312초 실패 / 콘티 판 v2 23.3초 통과)은 R 에 기록.
"""

from __future__ import annotations

import unittest

import numpy as np

from engine import checks as C
from geo.prep_tiers import TierSpec, sea_spec
from rules import load_rules

SEA_DEEP = (20, 60, 110)
SEA_SHALLOW = (60, 120, 170)
LAND = (200, 170, 120)


def _img(w: int = 200, h: int = 120, col: tuple = SEA_DEEP) -> np.ndarray:
    a = np.zeros((h, w, 3), np.float32)
    a[...] = col
    return a


class SeaTileStepPure(unittest.TestCase):
    def test_step_on_grid_line_fails(self) -> None:
        a = _img()
        a[:, 100:] = SEA_SHALLOW        # 격자선 x=100 오른쪽 타일만 0 m 바다(옅은 색)
        hits = C.sea_tile_steps(a, [100.0], [])
        self.assertTrue(hits)
        self.assertEqual(hits[0][0], "x")
        self.assertGreater(hits[0][4], load_rules().qa_checks.sea_tile_step.max_step)

    def test_smooth_sea_gradient_passes(self) -> None:
        a = _img()
        ramp = np.linspace(0, 30, a.shape[1], dtype=np.float32)[None, :, None]
        a = a + ramp * np.array([1, 1, 1], np.float32)   # 화면 폭 전체에 걸친 수심 기울기 — 4 px 띠 사이 차는 1 미만
        self.assertEqual(C.sea_tile_steps(a, [100.0], []), [])

    def test_coastline_on_grid_line_passes(self) -> None:
        a = _img()
        a[:, :100] = LAND               # 육지·바다 경계가 격자선과 겹쳐도 양쪽 다 바다가 아니면 세지 않는다
        self.assertEqual(C.sea_tile_steps(a, [100.0], []), [])

    def test_short_run_passes(self) -> None:
        a = _img()
        cfg = load_rules().qa_checks.sea_tile_step
        n = cfg.min_run_px - 2 * cfg.sea_erode_px - 4
        a[:, :] = LAND
        a[40:40 + n + 2 * cfg.sea_erode_px, :] = SEA_DEEP
        a[40:40 + n + 2 * cfg.sea_erode_px, 100:] = SEA_SHALLOW
        self.assertEqual(C.sea_tile_steps(a, [100.0], []), [])

    def test_horizontal_grid_line(self) -> None:
        a = _img()
        a[60:, :] = SEA_SHALLOW
        hits = C.sea_tile_steps(a, [], [60.0])
        self.assertTrue(hits and hits[0][0] == "y")


class SeaBathymetrySource(unittest.TestCase):
    def test_high_zoom_tier_uses_low_zoom_sea(self) -> None:
        mz = load_rules().geo.sea_bathymetry_max_z
        self.assertEqual(mz, 8)
        s = sea_spec(TierSpec("A", 360, 10, 11.5, 39.5, 19.8, 43.3))
        self.assertIsNotNone(s)
        self.assertEqual((s.z, s.lon0, s.lat1), (8, 11.5, 43.3))
        self.assertIsNone(sea_spec(TierSpec("I", 120, 8, -1.7, 36.0, 23.6, 46.7)))   # 골든 hormuz 티어(z5~7)·z8 은 그대로

    def test_check_registered_hard(self) -> None:
        self.assertIn("sea_tile_step", C.HARD)
        self.assertIsNotNone(load_rules().qa_checks.sea_tile_step)


if __name__ == "__main__":
    unittest.main()

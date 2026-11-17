"""지도는 멈춰 있지 않는다 — 느린 연속 흐름과 [map-still] (v7.4.0 사용자 의견 UF-920, D936).

사용자 원문(2026-11-17): "지도가 멈춰있으면 안된다고 했잖아. 계속 천천히 움직여야해. 지루함이 없어야 한다는거지."
이동 숏 사이의 지도는 3 % 푸시인이 9초 만에 잦아들면 그대로 멈췄다. [static-camera](UF-120)는 20초 창에 새 요소가 하나라도 있으면 통과했다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from engine.camera import ambient, ambient_spec, speed, still_runs
from engine.style import FPS, W_OUT
from rules import load_rules

SPEC = load_rules().camera.ambient


def _px(track: np.ndarray) -> np.ndarray:
    sp = speed(track, (), FPS)
    return sp["pan"] * W_OUT + sp["zoom"] * W_OUT / 2


class AmbientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.still = np.tile(np.array([117.0, 18.0, 62.0]), (FPS * 120, 1))   # 2분 동안 키가 하나뿐인 지도

    def test_rule_covers_the_map_theme_of_new_videos(self) -> None:
        self.assertIn("porcelain", SPEC.themes)
        self.assertIsNotNone(ambient_spec(SimpleNamespace(theme_name="porcelain")))
        self.assertIsNone(ambient_spec(SimpleNamespace(theme_name="dark")), "옛 테마(회귀 기준 재현)는 화소 그대로")
        self.assertIsNone(ambient_spec(SimpleNamespace()), "지도가 아닌 무대")

    def test_plain_track_is_still_and_ambient_never_is(self) -> None:
        self.assertEqual(float(_px(self.still).max()), 0.0)
        px = _px(ambient(self.still, FPS, SPEC))
        self.assertGreater(float(px.min()), SPEC.min_speed_px_s, "멈춘 순간이 있다")
        self.assertEqual(still_runs(px, FPS, SPEC.min_speed_px_s, SPEC.still_max_sec), [])

    def test_slow_and_bounded(self) -> None:
        out = ambient(self.still, FPS, SPEC)
        self.assertLess(float(_px(out).max()), 12.0, "천천히 — 설계 px/초")
        self.assertLessEqual(float(np.abs(out[:, 0] - 117.0).max()), 62.0 * SPEC.pan_ratio * (1 + SPEC.zoom_ratio) + 1e-9)
        self.assertLessEqual(float(np.abs(out[:, 2] / 62.0 - 1).max()), SPEC.zoom_ratio + 1e-9)

    def test_function_of_time_only(self) -> None:
        a = ambient(self.still, FPS, SPEC)
        b = ambient(self.still, FPS, SPEC)
        self.assertTrue(np.array_equal(a, b), "같은 시각 = 같은 화면(무작위 없음)")
        moved = self.still.copy()
        moved[:, 0] += 10.0
        self.assertTrue(np.allclose(ambient(moved, FPS, SPEC)[:, 0] - 10.0, a[:, 0]), "키가 달라도 흐름은 같은 시각 함수")


class StillRunsTest(unittest.TestCase):
    def test_long_still_is_reported_short_is_not(self) -> None:
        px = [5.0] * 24 + [0.0] * 60 + [5.0] * 24 + [0.0] * 12 + [5.0] * 24
        self.assertEqual(still_runs(px, 24, 1.5, 1.0), [(24, 84)])

    def test_covered_frames_are_not_counted(self) -> None:
        px = [0.0] * 96
        self.assertEqual(still_runs(px, 24, 1.5, 1.0, [True] * 96), [])
        self.assertEqual(still_runs(px, 24, 1.5, 1.0), [(0, 96)])


if __name__ == "__main__":
    unittest.main()

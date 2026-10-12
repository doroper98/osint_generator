"""v5.21.9 D-0191 §1-1 — 카메라 이동 중간 꺾임(사용자 의견 UF-02).

조각 3차 이징은 이동 한가운데서 가속도가 뒤집혀 3차 차분(저크)이 튄다. 규칙 shot_grammar.move_ease = quintic,
본 엔진 검사 camera_continuity(hard)·스케치 SK-C1 이 같은 측정 함수와 같은 임계(rules sketch.checks)를 쓴다.
"""

from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

import numpy as np

import engine.camera as C
from engine.timebase import ease_io, ease_quintic
from rules import load_rules
from sketch.common.checks import CheckReport, check_camera

FPS = 24
TH = load_rules().sketch.checks


def _track(ease, dur: float = 2.6, n: int = 24 * 8) -> np.ndarray:
    """2초에 시작해 dur 동안 3배 줌인 + 이동하는 카메라 키 둘."""
    keys = [C.cam(0.0, 50.0, 25.0, 30.0, 0, "cut"), C.cam(2.0, 46.0, 24.0, 10.0, dur)]
    old = C._EASE
    try:
        C._EASE = ease
        return C.build_camera(keys, n, FPS)
    finally:
        C._EASE = old


class TestEase(unittest.TestCase):
    def test_rule_is_quintic(self) -> None:
        self.assertEqual(load_rules().shot_grammar.move_ease, "quintic")
        self.assertIs(C._EASE, ease_quintic)

    def test_quintic_endpoints_and_flat_ends(self) -> None:
        self.assertEqual(ease_quintic(0.0), 0.0)
        self.assertEqual(ease_quintic(1.0), 1.0)
        self.assertAlmostEqual(ease_quintic(0.5), 0.5)
        h = 1e-4   # 끝에서 속도·가속도 0
        self.assertLess(ease_quintic(h) / h, 1e-6)
        self.assertLess((1 - ease_quintic(1 - h)) / h, 1e-6)

    def test_cubic_acceleration_flips_mid_move(self) -> None:
        """조각 3차의 2차 도함수는 한가운데서 +12 → −12(불연속), 5차는 연속(0 을 지난다)."""
        def acc(f, x: float, h: float = 1e-4) -> float:
            return (f(x + h) - 2 * f(x) + f(x - h)) / h ** 2
        self.assertAlmostEqual(acc(ease_io, 0.5 - 1e-3), 12, delta=0.1)
        self.assertAlmostEqual(acc(ease_io, 0.5 + 1e-3), -12, delta=0.1)
        self.assertLess(abs(acc(ease_quintic, 0.5 - 1e-3) - acc(ease_quintic, 0.5 + 1e-3)), 0.1)


class TestContinuity(unittest.TestCase):
    def test_cubic_fails_quintic_passes_jerk(self) -> None:
        d3 = {}
        for name, f in (("cubic", ease_io), ("quintic", ease_quintic)):
            m = C.continuity(_track(f))
            d3[name] = max(m[k].max() for k in m if k.startswith("d3"))
        self.assertGreater(d3["cubic"], TH.max_d3_per_frame)
        self.assertLess(d3["quintic"], TH.max_d3_per_frame)

    def test_cut_frames_excluded(self) -> None:
        keys = [C.cam(0.0, 50.0, 25.0, 30.0, 0, "cut"), C.cam(3.0, 20.0, 10.0, 5.0, 0, "cut")]
        tr = C.build_camera(keys, FPS * 6, FPS)
        cut = math.ceil(3.0 * FPS)
        raw = C.continuity(tr)
        self.assertGreater(raw["d1 ln w"].max(), TH.max_dlogw_per_frame)
        m = C.continuity(tr, [cut])
        for k, v in m.items():
            self.assertLess(v.max(), 1e-3, k)

    def test_engine_check_reports(self) -> None:
        from engine.checks import HARD, check_camera_continuity
        self.assertIn("camera_continuity", HARD)
        keys = [C.cam(0.0, 50.0, 25.0, 30.0, 0, "cut"), C.cam(2.0, 46.0, 24.0, 10.0, 2.6)]
        R = SimpleNamespace(stage=SimpleNamespace(bounds=(-1e9, -1e9, 1e9, 1e9), name="mercator"))   # noqa: N806 — 경계 없는 합성 무대(v7.1.0 화면 궤적 측정)
        good = SimpleNamespace(cams=_track(ease_quintic), keys=keys, R=R)
        bad = SimpleNamespace(cams=_track(ease_io), keys=keys, R=R)
        self.assertEqual(check_camera_continuity(good), [])
        out = check_camera_continuity(bad)
        self.assertTrue(out and all(s.startswith("[camera-continuity]") for s in out))
        self.assertTrue(any("꺾임" in s for s in out))
        self.assertEqual(check_camera_continuity(SimpleNamespace(cams=None, keys=[])), [])

    def test_sketch_sk_c1_same_measure(self) -> None:
        """스케치 SK-C1 도 3차를 본다(교훈을 한 트랙에만 배선하지 않는다)."""
        rep = CheckReport()
        worst = check_camera(rep, _track(ease_io), FPS, TH, SimpleNamespace(bounds=(-1e9, -1e9, 1e9, 1e9), name="mercator"))
        self.assertIn("d3 ln w", worst)
        self.assertTrue(any("꺾임" in f.message for f in rep.hard))
        rep2 = CheckReport()
        check_camera(rep2, _track(ease_quintic), FPS, TH, SimpleNamespace(bounds=(-1e9, -1e9, 1e9, 1e9), name="mercator"))
        self.assertEqual(rep2.hard, [])

    def test_sketch_camera_uses_rule(self) -> None:
        import sketch.common.camera as SC
        self.assertIs(SC._EASE, ease_quintic)


if __name__ == "__main__":
    unittest.main()

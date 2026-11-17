"""자라는 경로 선·항로 위 배가 프레임마다 끊김 없이 전진한다 (v7.4.0 사용자 의견 UF-921, D936).

사용자 원문(2026-11-17): "어떤 국가에서다른 국가로 넘어가는 것을 그리는 점선? 같은것의 프레임레이트가 왤케 떨어지는거지? 부드럽게 선이 나오게 해.
예전에 선박이 중동에서 한국으로 오는 걸 표현하는 양식도 굉장히 프레임 레이트가 유난히 그 선만 떨어지게 표현하더니 이번에도 그러네?"
원인: 선 머리를 곡선 표본점 단위(`S_[:int(len × prog)]`)로만 잘랐다 — 꼭짓점 4개 경로는 37개 표본이라 7초 동안 37번만 전진했다(초당 약 5번).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import numpy as np

from engine.layers.routes import DECLARED_SAMPLES, along, catmull, grown, head_dir, head_pos

FRAMES = 168   # 7초 × 24fps — nvidia-chips-china-2026 의 베이징 → 쿠알라룸푸르 경로


def _heads(S_: np.ndarray) -> np.ndarray:  # noqa: N803
    return np.array([grown(S_, k / FRAMES)[-1] for k in range(FRAMES + 1)])


class GrowthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.curve = catmull([(396.0, 60.0), (350.0, 150.0), (320.0, 230.0), (304.0, 263.0)], DECLARED_SAMPLES)

    def test_head_moves_every_frame(self) -> None:
        h = _heads(self.curve)
        step = np.hypot(*np.diff(h, axis=0).T)
        self.assertGreater(float(step.min()), 0.0, "멈춘 프레임이 있다(머리가 표본점에서 기다린다)")
        self.assertEqual(len({(round(x, 3), round(y, 3)) for x, y in h}), FRAMES + 1, "프레임마다 다른 머리 위치")

    def test_no_jumps(self) -> None:
        step = np.hypot(*np.diff(_heads(self.curve), axis=0).T)
        self.assertLessEqual(float(step.max()), 3.0 * float(np.median(step)), "한 프레임에 여러 프레임 몫을 건너뛴다")

    def test_old_cut_was_quantized(self) -> None:
        """옛 식의 머리 위치는 표본점 수만큼만 있었다 — 같은 경로에서 새 식과 견준다(회귀 방지의 근거)."""
        old = {tuple(self.curve[max(2, int(len(self.curve) * k / FRAMES)) - 1]) for k in range(FRAMES + 1)}
        self.assertLessEqual(len(old), len(self.curve))
        self.assertLess(len(old), (FRAMES + 1) // 3)

    def test_ends_and_whole_curve(self) -> None:
        self.assertTrue(np.allclose(grown(self.curve, 0.0)[-1], self.curve[0]))
        self.assertIs(grown(self.curve, 1.0), self.curve)
        self.assertEqual(head_pos(len(self.curve), 0.5), (len(self.curve) - 1) / 2)
        g = grown(self.curve, 0.5)
        self.assertTrue(np.allclose(g[:-1], self.curve[:len(g) - 1]), "지나온 표본점은 곡선 그대로")

    def test_head_direction_follows_the_segment(self) -> None:
        a0 = head_dir(self.curve, 0.3001)
        a1 = head_dir(self.curve, 0.3002)
        self.assertAlmostEqual(a0, a1, places=6, msg="짧은 끝 조각으로 재면 각도가 떨린다 — 표본 구간 방향을 쓴다")


class TankerLoopTest(unittest.TestCase):
    def test_ship_moves_between_samples(self) -> None:
        curve = catmull([(100.0, 300.0), (300.0, 260.0), (520.0, 180.0)], 12)
        pos = np.array([along(curve, k / 600)[:2] for k in range(600)])
        step = np.hypot(*np.diff(pos, axis=0).T)
        self.assertGreater(float(step.min()), 0.0, "배가 표본점에서 표본점으로 건너뛴다")
        self.assertLessEqual(float(step.max()), 3.0 * float(np.median(step)))


class NoSampleCutTest(unittest.TestCase):
    """본 엔진과 스케치 트랙 어디에도 '표본점 단위로 자르는 자람'이 남아 있지 않다(C12 §3 — 한 트랙에만 건 장치는 미보호)."""

    CUT = re.compile(r"\[\s*:\s*(max\(\d+,\s*)?int\([^\]]*(prog|grow)")

    def test_no_integer_cut_growth_in_any_track(self) -> None:
        root = Path(__file__).resolve().parents[1]
        bad = []
        for d in ("engine", "sketch"):
            for f in sorted((root / d).rglob("*.py")):
                for no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    code = line.split("#", 1)[0]
                    if self.CUT.search(code) and '"""' not in line:
                        bad.append(f"{f.relative_to(root)}:{no}")
        self.assertEqual(bad, [], "자라는 선은 engine.layers.routes.grown 으로 자른다(머리 보간)")

    def test_sketch_lines_use_the_shared_helper(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel in ("sketch/campaign/fronts.py", "sketch/missile/launch.py", "sketch/missile/eez.py", "sketch/missile/profile.py",
                    "sketch/missile/globe_scene.py"):
            self.assertIn("grown(", (root / rel).read_text(encoding="utf-8"), rel)

    def test_grown_works_on_3d_points(self) -> None:
        A = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 5.0], [20.0, 0.0, 0.0]])  # noqa: N806
        g = grown(A, 0.25)
        self.assertEqual(g.shape[1], 3)
        np.testing.assert_allclose(g[-1], [5.0, 0.0, 2.5])


if __name__ == "__main__":
    unittest.main()

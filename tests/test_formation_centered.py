"""[formation-centered] — 전술 화면 진형은 가운데(v7.4.0 back_and_forth D-0625, 사용자 의견 UF-255
"군대의 진형(칸나이 전투 같은)은 중앙에 위치하게 해야 되는데 칸나이 전투 마지막 쯤에는 왼쪽 상단에 위치하더라고").

판정 함수(engine.checks.formation_fault·formation_runs)는 본편 terrain3d 구간과 스케치 전쟁사 2D 전술 축척·3D 컷이 같이 쓴다(C12 ③).
상자 값은 칸나이 실측(설계 좌표 854×480, 부대 라벨 상자 합집합):
- 콘티 판 v1 222초(궤도 끝) = 가운데 → 통과
- 콘티 판 v1 232~256초(encirclement_9 카메라 16.12·41.325 w 0.11) = 위로 밀림 → 실패
- D-0619 ② 연출(카드 숏에서 진형을 왼쪽으로 비킴, 145~170초) → 실패
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.checks import QA, formation_fault, formation_runs
from engine.style import FPS

V1_222 = (285.0, 132.0, 676.0, 384.0)
# v1 232~256초: 현재 프레임(16.14) 상자를 v1 카메라 경도 16.12 로 옮긴 값 — 내려다보기 90°라 화면 x 는 경도에 선형(Δx = 0.02/0.11 × 854 = 155 px)
V1_240 = (30.0 + 155.0, 11.0, 384.0 + 155.0, 244.0)
LEFT_SHIFT_150 = (13.0, 159.0, 398.0, 319.0)


class FormationFaultTest(unittest.TestCase):
    def test_v1_end_fails_and_222_passes(self) -> None:
        self.assertIsNone(formation_fault([V1_222]))
        why = formation_fault([V1_240])
        self.assertIsNotNone(why)
        self.assertIn("세로", why)   # 위로 밀림(dy ≈ −0.24)

    def test_left_shift_fails(self) -> None:
        self.assertIn("가로", formation_fault([LEFT_SHIFT_150]))

    def test_safe_area(self) -> None:
        self.assertIn("안전 영역", formation_fault([(300.0, 200.0, 560.0, 425.0)]))   # 자막 자리(y ≥ 410)로 내려감
        self.assertIn("안전 영역", formation_fault([(300.0, 5.0, 560.0, 300.0)]))     # 위 띠
        self.assertIsNone(formation_fault([]))

    def test_union_of_boxes(self) -> None:
        self.assertIsNone(formation_fault([(285.0, 132.0, 480.0, 250.0), (470.0, 260.0, 676.0, 384.0)]))


class FormationRunsTest(unittest.TestCase):
    def test_short_blip_ignored_long_run_reported(self) -> None:
        step = QA.formation_centered.step_sec
        n_short = int(QA.formation_centered.max_sec / step)   # max_sec 이하 길이
        s = [(i * step, [V1_222]) for i in range(10)]
        s += [((10 + i) * step, [V1_240]) for i in range(n_short)]
        s += [((10 + n_short + i) * step, [V1_222]) for i in range(10)]
        self.assertEqual(formation_runs(s), [])
        long = [(i * step, [V1_240]) for i in range(n_short + 2)]
        runs = formation_runs(long)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0][0], 0.0)


class SketchHooksTest(unittest.TestCase):
    def test_sketch_2d_samples_tactical_full_only(self) -> None:
        from sketch.war.checks import formation_samples  # noqa: PLC0415

        lim = QA.formation_centered.sketch_tactical_max_w_deg
        units = [(0.0, lim * 10, [V1_240, V1_240]),           # 작전 지도 축척 — 대상 아님
                 (1.0, lim / 2, [V1_222]),                     # 부대가 아직 나타나는 중
                 (2.0, lim / 2, [V1_222, V1_222]),
                 (3.0, lim / 2, [V1_240, V1_240])]
        self.assertEqual([t for t, _ in formation_samples(units)], [2.0, 3.0])

    def test_sketch_3d_labels(self) -> None:
        from sketch.war.terrain3d import formation_faults  # noqa: PLC0415

        width = 1280
        k = width / 854

        def rec(x: float, y: float) -> dict:
            return {"k": "unit", "name": "보병", "x": x * k, "y": y * k, "behind": False}

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "labels.json"
            p.write_text(json.dumps({"schema_version": 1, "frames": [[rec(330, 200), rec(520, 300)], [rec(60, 60), rec(200, 120)]]}),
                         encoding="utf-8")
            bad = formation_faults(p, width)
        self.assertEqual([i for i, _ in bad], [1])


class EngineSamplerTest(unittest.TestCase):
    def test_no_segments_no_samples(self) -> None:
        from types import SimpleNamespace  # noqa: PLC0415

        from engine.checks import terrain3d_formation_samples  # noqa: PLC0415

        P = SimpleNamespace(R=SimpleNamespace(cache={}))  # noqa: N806
        self.assertEqual(terrain3d_formation_samples(P), [])
        self.assertGreater(FPS, 0)


if __name__ == "__main__":
    unittest.main()

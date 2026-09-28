"""무대 연속성 검사 `checks:stage_continuity` (v4.1.0, back_and_forth D-0076 작업 5·D-0077, docs/handoff/20 §2.2·§12, GOAL G3-17).

합성 숏 목록으로 네 규칙(max_secondary·switch_without_dip·teleport·max_switches)을 하나씩 일으키고, 주+보조 1회 왕복(전부 dip)은 통과.
가짜 무대 이름은 순수 함수 입력일 뿐이다 — 라이브 규칙 파일·레지스트리에 넣지 않는다(D-0077).
"""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from engine.shots import ShotStage, stage_continuity
from engine.stage import ym
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "docs" / "handoff" / "reports" / "phaseG1"


def S(t: float, mode: str, stage: str = "mercator", lon: float = 56.0, lat: float = 26.0, w: float = 14.0) -> ShotStage:  # noqa: N802
    return ShotStage(t=t, mode=mode, stage=stage, x=lon, y=ym(lat), w=w)


def keys(shots: list[ShotStage]) -> list[str]:
    return [k for k, _ in stage_continuity(shots)]


class StageContinuityRulesTest(unittest.TestCase):
    def test_pass_main_secondary_round_trip_all_dip(self) -> None:
        shots = [S(0, "cut"), S(10, "move", lon=58.0), S(30, "dip", stage="timeline", lon=2020.0, lat=0.0),
                 S(45, "move", stage="timeline", lon=2021.0, lat=0.0), S(60, "dip", lon=56.0)]
        self.assertEqual(stage_continuity(shots), [])

    def test_fail_two_secondary_stages(self) -> None:
        shots = [S(0, "cut"), S(20, "dip", stage="timeline"), S(40, "dip", stage="chart_wall")]
        self.assertIn("max_secondary", keys(shots))

    def test_fail_switch_without_dip(self) -> None:
        shots = [S(0, "cut"), S(20, "move", stage="timeline")]
        self.assertEqual(keys(shots), ["switch_without_dip"])

    def test_fail_teleport_far_cut_same_stage(self) -> None:
        """호르무즈(56E) → 서울(127E) 을 암전 없이 cut — shot_grammar.auto_transition 이 dip 을 요구하는 거리."""
        shots = [S(0, "cut"), S(20, "cut", lon=127.0, lat=37.5, w=8.0)]
        self.assertEqual(keys(shots), ["teleport"])

    def test_near_cut_and_far_dip_are_allowed(self) -> None:
        self.assertEqual(keys([S(0, "cut"), S(20, "cut", lon=56.5, w=14.0)]), [])            # 가까운 cut
        self.assertEqual(keys([S(0, "cut"), S(20, "dip", lon=127.0, lat=37.5, w=8.0)]), [])  # 먼 이동은 dip
        self.assertEqual(keys([S(0, "cut"), S(20, "move", lon=127.0, lat=37.5, w=8.0)]), [])  # move 는 보간(연속)

    def test_fail_three_switches(self) -> None:
        """주 → 보조 → 주 → 보조: 전환 3회 > max_switches(장면마다 새 캔버스)."""
        shots = [S(0, "cut"), S(20, "dip", stage="timeline"), S(40, "dip"), S(60, "dip", stage="timeline")]
        self.assertEqual(keys(shots), ["max_switches"])

    def test_first_shot_cut_is_not_teleport(self) -> None:
        self.assertEqual(keys([S(0, "cut", lon=127.0)]), [])

    def test_rule_values_from_rules(self) -> None:
        st = load_rules().stage
        self.assertEqual((st.max_secondary, st.continuity.max_switches), (1, 2))

    def test_no_rule_literals_in_code(self) -> None:
        """판정 함수에 규칙 수치 리터럴 0(0 은 시각 비교 t > 0 뿐) — 임계는 rules stage·shot_grammar."""
        src = (REPO / "engine" / "shots.py").read_text(encoding="utf-8")
        fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "stage_continuity")
        nums = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool)]
        self.assertTrue(set(nums) <= {0, 1, 2}, nums)   # 0 = t>0, 1·2 = 인덱스·f-string 자릿수


class StageContinuityProjectsTest(unittest.TestCase):
    """실증 영상 hard 0 — `reports/phaseG1/stage_continuity_{hormuz,ratcliffe}.json`(작업 9)이 있으면 그 값으로."""

    def test_real_projects_hard_zero(self) -> None:
        for name in ("hormuz", "ratcliffe"):
            p = REPORTS / f"stage_continuity_{name}.json"
            if not p.exists():
                self.skipTest(f"{p.name} 없음 — 작업 9 산출물")
            d = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(d["hard"], 0, name)
            self.assertEqual(d["violations"], [], name)


if __name__ == "__main__":
    unittest.main()

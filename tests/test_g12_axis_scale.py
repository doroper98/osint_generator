"""G12 §A(v5.1.0, back_and_forth D-0121 §A, 사용자 피드백 D105) — 시간축 축 스케일 고정.

- w 변화 = 시간축 숏의 연속 두 숏 w 가 다름(첫 숏 설정 제외, 지도 무대 제외).
- `[timeline-rescale]` hard: 장면 안 변화 · 영상당 > max · 비율 < min.
- 연출·수정 프롬프트에 규칙 값이 들어간다({{RULES.stage_timeline.axis_scale}}). 코드는 w 를 고치지 않는다(P8).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine import checks
from engine.shots import ShotStage, timeline_rescale, timeline_w_changes
from rules import load_rules
from workers.prompt_loader import load_prompt

AX = load_rules().stage_timeline.axis_scale
SENT = [NS(sid="a_0", scene="a", t0=0.0), NS(sid="b_0", scene="b", t0=20.0), NS(sid="c_0", scene="c", t0=40.0),
        NS(sid="d_0", scene="d", t0=60.0), NS(sid="e_0", scene="e", t0=80.0)]


def _shot(t: float, w: float, stage: str = "timeline") -> ShotStage:
    return ShotStage(t=t, mode="move", stage=stage, x=t, y=1.5, w=w)


class AxisScaleTest(unittest.TestCase):
    def test_rule_values(self) -> None:
        self.assertEqual((AX.w_changes_per_video_max, AX.w_change_ratio_min, AX.scene_fixed), (3, 1.5, True))

    def test_change_inside_scene_is_hard(self) -> None:
        ch = timeline_w_changes([_shot(0, 400), _shot(5, 120)], SENT)
        self.assertEqual(len(ch), 1)
        out = timeline_rescale(ch)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[timeline-rescale] t=5.00 w 400→120 (장면 a 안"))

    def test_pan_only_and_first_shot_are_not_changes(self) -> None:
        self.assertEqual(timeline_w_changes([_shot(0, 400), _shot(5, 400), _shot(30, 400)], SENT), [])

    def test_count_over_max(self) -> None:
        ws = [(0, 60), (19, 400), (39, 120), (59, 400), (79, 60)]   # 장면 경계(선행 1.5초 안) 변화 4회
        out = timeline_rescale(timeline_w_changes([_shot(t, w) for t, w in ws], SENT))
        self.assertEqual(len(out), 1)
        self.assertIn(f"영상 4번째 > {AX.w_changes_per_video_max}", out[0])

    def test_ratio_below_min(self) -> None:
        out = timeline_rescale(timeline_w_changes([_shot(0, 200), _shot(19, 260)], SENT))
        self.assertEqual(len(out), 1)
        self.assertIn("비율 1.3 < 1.5", out[0])
        self.assertEqual(timeline_rescale(timeline_w_changes([_shot(0, 200), _shot(19, 400)], SENT)), [])

    def test_map_stage_excluded(self) -> None:
        self.assertEqual(timeline_w_changes([_shot(0, 90, "mercator"), _shot(5, 12, "mercator"), _shot(9, 3, "mercator")], SENT), [])

    def test_check_hard_and_reads_cache(self) -> None:
        self.assertIn("timeline_rescale", checks.HARD)
        P = NS(R=NS(cache={"timeline": {"w_changes": timeline_w_changes([_shot(0, 400), _shot(5, 120)], SENT)}}))  # noqa: N806
        self.assertEqual(len(checks.check_timeline_rescale(P)), 1)
        self.assertEqual(checks.check_timeline_rescale(NS(R=NS(cache={}))), [])

    def test_prompts_carry_rule_values(self) -> None:
        for name in ("director", "revise_direction"):
            txt = load_prompt(name, load_rules())
            self.assertIn(f"영상 전체 {AX.w_changes_per_video_max}회 이하", txt, name)
            self.assertIn(f"{AX.w_change_ratio_min:g}배 이상", txt, name)
            self.assertNotIn("{{RULES.stage_timeline.axis_scale}}", txt)
        self.assertTrue(any("축 스케일" in g for g in load_rules().direction_grammar))


if __name__ == "__main__":
    unittest.main()

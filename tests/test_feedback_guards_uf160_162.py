"""사용자 의견 UF-160~162 장치(v7.4.0, back_and_forth D-0289 — 중국 수출통제 콘티 판 v2 검토).

UF-160 원문: "1:30~1:50 즘 까지 거의 아무것도 안뜨고 자막과 나레이션만 나오는 구간이 있어. 사진 하나정도 더 추가 하는게 좋을거 같아."
UF-161 원문: "이미지의 경로 개략, 좌표 비공개 라는 문구는 빼."
UF-162 원문: "마지막 쯤에 시진핑과 트럼프 뱃지가 나오는데 너무 빨리 사라져."
- [element-gap] hard: 화면 요소 없이 지도·자막만 이어지는 구간 > qa_checks.element_gap.max_sec
- [label-banned-terms] hard: 지도 라벨에 qa_checks.label_banned_terms.terms
- [badge-hold] hard: 뱃지 노출 < qa_checks.badge_hold.min_hold_sec(사진·영상으로 곧바로 넘기면 예외)
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from engine import checks
from rules import load_rules

Q = load_rules().qa_checks


def _P(events: list[dict], total: float = 60.0, name: str = "showcase_geo",  # noqa: N802
       fullcard: tuple[float, float] | None = None) -> NS:
    tb = NS(in_fullcard=lambda t: fullcard is not None and fullcard[0] <= t <= fullcard[1])
    return NS(root=Path("/x") / name, events=events, plan=NS(total=total), R=NS(tb=tb))


class ElementGapTest(unittest.TestCase):
    def test_v2_gap_fails(self) -> None:
        """콘티 판 v2 act1_8~10 재현: 사진 끝 → 21.7초 지도만 → 다음 사진 = hard."""
        ev = [{"type": "photo", "t0": 0.0, "t1": 10.0}, {"type": "photo", "t0": 31.7, "t1": 60.0}]
        out = checks.check_element_gap(_P(ev))
        self.assertEqual(len(out), 1)
        self.assertIn("[element-gap]", out[0])
        self.assertIn("element_gap", checks.HARD)

    def test_marker_appearance_counts_only_briefly(self) -> None:
        """떠 있기만 한 마커는 요소가 아니다 — 나타난 뒤 appear_hold_sec 만 센다."""
        ev = [{"type": "marker", "t0": 0.0, "t1": 60.0}]
        runs = checks.element_gaps(_P(ev))
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0][0], Q.element_gap.appear_hold_sec, delta=0.11)
        # 새 마커가 중간에 나타나면 공백이 끊긴다
        ev2 = ev + [{"type": "route", "t0": 15.0, "t1": 60.0}, {"type": "country", "t0": 30.0, "t1": 60.0},
                    {"type": "marker", "t0": 45.0, "t1": 60.0}]
        self.assertEqual(checks.check_element_gap(_P(ev2)), [])

    def test_fullcard_breaks_gap_and_exempt(self) -> None:
        ev = [{"type": "photo", "t0": 0.0, "t1": 5.0}]
        self.assertEqual(checks.check_element_gap(_P(ev, total=30.0, fullcard=(14.0, 30.0))), [])
        self.assertEqual(sorted(Q.element_gap.exempt_projects), ["hormuz_korea"])
        self.assertEqual(checks.check_element_gap(_P(ev, name="hormuz_korea")), [])

    def test_rules_key(self) -> None:
        self.assertEqual(Q.element_gap.max_sec, 18)   # v2 21.7초 실패 · 전달본 16.2초 통과 — 바꾸면 결정 기록과 함께


class LabelBannedTermsTest(unittest.TestCase):
    def test_v2_labels_fail(self) -> None:
        ev = [{"type": "marker", "t0": 1.0, "t1": 5.0, "label": "경기도", "sub": "전력구 공사 · 좌표 비공개"},
              {"type": "route", "t0": 1.0, "t1": 5.0, "label": "굴착기 2대 · 경로 개략"}]
        out = checks.check_label_banned_terms(_P(ev))
        self.assertEqual(len(out), 2)
        self.assertIn("label_banned_terms", checks.HARD)

    def test_clean_labels_and_other_types_pass(self) -> None:
        ev = [{"type": "marker", "t0": 1.0, "t1": 5.0, "label": "경기도", "sub": "전력구 공사"},
              {"type": "route", "t0": 1.0, "t1": 5.0, "label": "굴착기 2대"},
              {"type": "photo", "t0": 1.0, "t1": 5.0, "caption": "개략도"}]   # 사진 설명은 지도 라벨이 아니다
        self.assertEqual(checks.check_label_banned_terms(_P(ev)), [])

    def test_rules_key(self) -> None:
        self.assertEqual(Q.label_banned_terms.terms, ["개략", "비공개"])


class BadgeHoldTest(unittest.TestCase):
    def test_v2_short_badge_fails(self) -> None:
        """콘티 판 v2 act4_6 재현: 문장 끝 +0.3초에 사라진 3.3초 뱃지 = hard."""
        ev = [{"type": "badge", "t0": 358.7, "t1": 362.0, "label": "트럼프"}]
        out = checks.check_badge_hold(_P(ev, total=400.0))
        self.assertEqual(len(out), 1)
        self.assertIn("badge_hold", checks.HARD)

    def test_long_or_handoff_passes(self) -> None:
        ev = [{"type": "badge", "t0": 358.7, "t1": 367.4, "label": "트럼프"},       # 다음 문장 끝까지(8.7초)
              {"type": "badge", "t0": 172.9, "t1": 177.6, "label": "시진핑"},       # 4.7초 → 같은 장면 사진으로 넘김
              {"type": "photo", "t0": 177.6, "t1": 180.2}]
        self.assertEqual(checks.check_badge_hold(_P(ev, total=400.0)), [])

    def test_rules_key(self) -> None:
        self.assertEqual(Q.badge_hold.min_hold_sec, 6)


class PromptLinesTest(unittest.TestCase):
    def test_director_and_revise_have_guard_lines(self) -> None:
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        rules = load_rules()
        for name in ("director", "revise_direction"):
            s = load_prompt(name, rules)
            self.assertIn(f"{Q.element_gap.max_sec:g}초 이하", s)
            self.assertIn("·".join(Q.label_banned_terms.terms), s)
            self.assertIn(f"{Q.badge_hold.min_hold_sec:g}초 이상", s)
            self.assertNotIn("{max_sec}", s)
            self.assertNotIn("{min_hold_sec}", s)


if __name__ == "__main__":
    unittest.main()

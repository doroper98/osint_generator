"""NB21 — 시각 검수 JSON `fix.event_ref` 누락(재요청 반복)을 프롬프트 문구로 막는다 (v4.0.0, back_and_forth D-0072 작업 11, LLM-AP-008).

15 P4·P11: 프롬프트가 말하는 필수 필드 = 스키마의 필수 필드(파리티). 검수 판정을 프롬프트에 자동 편입하지 않고, 사람이 승인한 문구 개정만 한다.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from pydantic import ValidationError

from engine.qa import QAFix, QAIssue, QAVerdict, resolve_refs

REPO = Path(__file__).resolve().parent.parent
PROMPT = (REPO / "prompts" / "visual_qa.md").read_text(encoding="utf-8")


def fix_rule_lines() -> str:
    return "\n".join(line for line in PROMPT.splitlines() if "fix" in line and "필수" in line)


class FixParityTest(unittest.TestCase):
    def test_prompt_names_every_required_fix_field(self) -> None:
        required = QAFix.model_json_schema().get("required", [])
        self.assertEqual(sorted(required), ["event_ref", "suggest"])
        rule = fix_rule_lines()
        for f in required:
            self.assertIn(f"`{f}`", rule, f"프롬프트 필수 규칙에 {f} 없음")

    def test_fix_without_event_ref_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            QAIssue.model_validate({"frame": "p_0184.20", "severity": "hard", "category": "occlusion",
                                    "evidence": "뱃지 이름표가 카드 뒤에 가려진다", "fix": {"suggest": "위치를 옮긴다"}})
        with self.assertRaises(ValidationError):
            QAIssue.model_validate({"frame": "p_0184.20", "severity": "hard", "category": "occlusion",
                                    "evidence": "뱃지 이름표가 카드 뒤에 가려진다", "fix": {}})

    def test_omitted_fix_is_valid(self) -> None:
        QAIssue.model_validate({"frame": "p_0184.20", "severity": "soft", "category": "density",
                                "evidence": "도입 컷에 라벨이 세 개뿐이라 휑하다"})

    def test_frame_name_as_event_ref_resolves(self) -> None:
        """프롬프트의 대안(컷 이름을 event_ref 로) 은 코드가 실제로 해석한다(resolve_refs 컷 → 활성 이벤트)."""
        frames = {"frames": [{"file": "p_0184.20.png", "events": [{"type": "badge", "label": "부산에서 출항"}]}]}
        self.assertIn(("badge", "부산에서 출항"), resolve_refs({"p_0184.20"}, frames=frames))

    def test_prompt_example_validates(self) -> None:
        m = re.search(r"```json\n(.*?)\n```", PROMPT, re.S)
        assert m
        v = QAVerdict.model_validate(json.loads(m.group(1)))
        self.assertTrue(all(i.fix is None or i.fix.event_ref for i in v.issues))


if __name__ == "__main__":
    unittest.main()

"""LLM-AP-018 (v5.21.1) — 연출 필드 표가 badge flag·quote text 의 검증기 제약을 보인다(LLM-AP-011 과 같은 클래스).

gulf_pact_2026 AI 연출가가 person 뱃지 flag 누락·인용문 따옴표로 두 번 거부됐다 — 필드 표에 타입만 있었다.
"""

from __future__ import annotations

import unittest

from workers.direction_io import event_fields_table


class FieldNotesTest(unittest.TestCase):
    def test_badge_and_quote_constraints_in_table(self) -> None:
        rows = {ln.split(":", 1)[0]: ln for ln in event_fields_table().splitlines() if ln.startswith("- ")}
        self.assertIn("flag: Optional[str] (kind person·flag 이면 필수", rows["- badge"])
        self.assertIn("pid: Optional[str] (kind person 이면 필수)", rows["- badge"])
        self.assertIn("img: Optional[str] (kind emblem 이면 필수)", rows["- badge"])
        self.assertIn("text*: str (따옴표", rows["- quote"])


if __name__ == "__main__":
    unittest.main()

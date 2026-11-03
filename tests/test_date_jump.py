"""[date-jump] — 날짜 표지가 근거 없는 날짜로 튀지 않는다(v7.4.0 back_and_forth D-0619 ⑤·D-0622).

칸나이 콘티 판 v1 의 deployment_9("이 영상의 카르타고 표지는 그 기호를 본뜬 재현입니다")가 원고 머리 날짜(제작일 2026.11.01)를
가져가 기원전 216년 진형 위에 오늘 날짜가 떴다. 고치는 방법은 D-0622 (가): 그 문장이 같은 타니트 기호를 말하므로 비석 연대(-300~-201)를 쓴다.
원칙: 날짜 맞추기는 그 문장이 카드와 같은 대상을 말할 때만 한다. 다른 대상 문장의 날짜를 바꿔 [media-sentence-span] 을 통과시키면 UF-173 우회다 —
그때는 카드를 줄이거나 옮긴다(D-0622 보충, 최종 감독 D337).
"""

from __future__ import annotations

import unittest

from engine.checks import date_jump_hits

CANNAE = [("deployment_7", "-216"), ("deployment_8", "-300~-201"), ("deployment_9", "2026.11.01"), ("deployment_10", "-216"),
          ("ending_2", "-216"), ("ending_3", "1856"), ("ending_4", "1856"), ("ending_5", "1885"), ("ending_6", "-216")]
CARDS = {"deployment_8": ["-300~-201"], "deployment_9": ["-300~-201"], "ending_3": ["1856"], "ending_4": ["1856"], "ending_5": ["1885"]}


class DateJumpTest(unittest.TestCase):
    def test_v1_production_date_fails(self) -> None:
        hits = date_jump_hits(CANNAE, CARDS)
        self.assertEqual(len(hits), 1)
        self.assertIn("deployment_9", hits[0])
        self.assertIn("2026.11.01", hits[0])

    def test_same_object_date_passes(self) -> None:
        fixed = [(s, "-300~-201" if s == "deployment_9" else d) for s, d in CANNAE]   # D-0622 (가)
        self.assertEqual(date_jump_hits(fixed, CARDS), [])

    def test_card_dated_badges_pass(self) -> None:
        """작품·기록 카드 연대와 맞는 표지(1856·1885)는 이웃과 달라도 통과."""
        self.assertFalse([h for h in date_jump_hits(CANNAE, CARDS) if "ending" in h])

    def test_later_record_date_within_video_span_passes(self) -> None:
        """그 순간 카드가 없어도 영상이 다루는 날짜 범위 안(예: 1667 — 다른 문장·카드 연대 범위 안)이면 통과."""
        s = [("a", "-216"), ("b", "1667"), ("c", "-216"), ("d", "1773")]
        self.assertEqual(date_jump_hits(s, {"d": ["1773"]}), [])

    def test_ends_and_missing_dates_skipped(self) -> None:
        self.assertEqual(date_jump_hits([("a", "2026.11.01"), ("b", "-216"), ("c", None)], {}), [])


if __name__ == "__main__":
    unittest.main()

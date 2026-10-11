"""v5.21.13 D-0194 — 인용(quote) 문구 ⊂ 그 구간 문장 화면 원고(사용자 의견: 내레이션과 따옴표 불일치)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine.checks import HARD, check_quote_in_script
from engine.events import QuoteEvent
from rules import load_rules


def _s(sid: str, t0: float, t1: float, text: str) -> SimpleNamespace:
    return SimpleNamespace(sid=sid, t0=t0, t1=t1, text=text)


PLAN = SimpleNamespace(sentences=[
    _s("a_0", 0.0, 5.0, "10월 7일, 앞서 본 군 대변인의 CNN 인터뷰로 주둔 사실이 공식 확인됐습니다."),
    _s("a_1", 5.5, 10.0, "사우디 주도 연합군은 이를 '전면적 전쟁범죄'라고 규정했습니다."),
])


def _q(t0: float, t1: float, text: str) -> dict:
    return {"type": "quote", "t0": t0, "t1": t1, "text": text, "speaker": "s"}


class TestQuoteInScript(unittest.TestCase):
    def test_registered(self) -> None:
        self.assertIn("quote_in_script", HARD)

    def test_gulf_troop6_case_fails(self) -> None:
        """gulf troop_numbers_6 — 원고가 말하지 않는 '여러 역량으로'."""
        out = check_quote_in_script(SimpleNamespace(plan=PLAN, events=[_q(0.3, 5.6, "여러 역량으로")]))
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[quote-in-script] 인용 's'"))

    def test_in_script_passes_with_punct_and_space(self) -> None:
        ev = [_q(5.8, 10.6, "전면적 전쟁범죄"), _q(5.8, 10.6, "전면적  전쟁 범죄!")]
        self.assertEqual(check_quote_in_script(SimpleNamespace(plan=PLAN, events=ev)), [])

    def test_other_sentence_does_not_count(self) -> None:
        """다른 문장(구간 밖)에 있는 문구는 인정하지 않는다."""
        out = check_quote_in_script(SimpleNamespace(plan=PLAN, events=[_q(0.3, 4.0, "전면적 전쟁범죄")]))
        self.assertEqual(len(out), 1)

    def test_field_description_and_grammar(self) -> None:
        """LLM-AP-018 교훈 — 필드 표 description 과 연출 문법 한 줄."""
        self.assertIn("quote_in_script", QuoteEvent.model_fields["text"].description)
        self.assertEqual(sum("[quote-in-script]" in g for g in load_rules().direction_grammar), 1)


if __name__ == "__main__":
    unittest.main()

"""G6.5(v4.7.0, back_and_forth D-0104) — dmz_mine 브랜치 병합 뒤 반영한 결정(D2(a) 연출 문법 등)."""

from __future__ import annotations

import unittest

from rules import load_rules


class DirectionGrammarTest(unittest.TestCase):
    def test_director_prompts_carry_direction_grammar(self) -> None:
        """D2(a) — 발언 주체 인물 문장 → 초상 뱃지 또는 기사 카드(규칙 SSOT, 연출·수정 프롬프트 둘 다)."""
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        R = load_rules()  # noqa: N806
        self.assertTrue(any("발언 주체" in g for g in R.direction_grammar))
        for name in ("director", "revise_direction"):
            text = load_prompt(name, R)
            self.assertNotIn("{{RULES.direction_grammar}}", text)
            for g in R.direction_grammar:
                self.assertIn(g, text, name)


if __name__ == "__main__":
    unittest.main()

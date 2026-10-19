"""v7.4.0 back_and_forth D-0246(사용자 의견 UF-127 "조사로서 -가 가 붙었는데 경유까, 제트유까 하고 발음 함. 재발 방지 해") —
발음 사전 "유가"(油價 → 유까)가 '…유 + 조사 가' 를 바꾸지 못하게: 규칙 tts_rules.tensification_traps 생성 예외 + short_key_boundary."""

from __future__ import annotations

import unittest
from unittest import mock

from rules import load_rules
from script import lint as L


class TensificationTrapTest(unittest.TestCase):
    def test_two_sentences_kept(self) -> None:
        self.assertEqual(L.pronounce_tts("한국 항구에서 실린 경유가 들어간 셈입니다."), "한국 항구에서 실린 경유가 들어간 셈입니다.")
        self.assertEqual(L.pronounce_tts("경유와 휘발유, 제트유가 수출된 기록은 없다고"), "경유와 휘발유, 제트유가 수출된 기록은 없다고")

    def test_other_yu_nouns_kept_and_oil_price_still_tense(self) -> None:
        for t in ("이유가 있다", "자유가 있다", "브렌트유가 올랐다", "비축유가 늘었다"):
            self.assertEqual(L.pronounce_tts(t), t)
        self.assertEqual(L.pronounce_tts("유가 급등"), "유까 급등")            # 油價 낱말은 그대로 경음
        self.assertEqual(L.pronounce_tts("국제 유가가 올랐다"), "국제 유까가 올랐다")
        self.assertEqual(L.pronounce_tts("중동산 원유가 줄었다"), "중동산 워뉴가 줄었다")   # 명사 자체 사전 읽기는 살린다

    def test_entries_come_from_rules(self) -> None:
        tt = load_rules().tts_rules.tensification_traps
        ent = L.tensification_entries()
        self.assertEqual(len(ent), len(tt.suffix_nouns) * len(tt.particles))
        R = load_rules()  # noqa: N806
        more = tt.model_copy(update={"suffix_nouns": [*tt.suffix_nouns, "식용유"]})
        fake = R.model_copy(update={"tts_rules": R.tts_rules.model_copy(update={"tensification_traps": more})})
        with mock.patch.object(L, "load_rules", return_value=fake):
            self.assertIn("식용유가", L.tensification_entries())   # 규칙에 명사를 더하면 항목이 는다(손 등재 없음)

    def test_short_key_boundary(self) -> None:
        mp = {"유가": "유까", "달러": "딸러"}
        self.assertEqual(L.apply_dict("경유가 들어간", mp), "경유가 들어간")   # 예외 목록 없이도 경계 규칙이 막는다
        self.assertEqual(L.apply_dict("유가 급등", mp), "유까 급등")
        self.assertEqual(L.apply_dict("육십달러", mp), "육십딸러")               # 수사 음절 뒤 허용
        self.assertEqual(L.apply_dict("60달러", mp), "60딸러")


if __name__ == "__main__":
    unittest.main()

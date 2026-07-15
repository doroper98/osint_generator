"""자막/음성 카피 안전 규칙 테스트 (C0.2 · docs/08_AUDIO_AND_TTS_SPEC.md §4).

"한두 건만 들려도 AI 티가 나는" 클래스의 회귀 잠금:
- 중간 절단(…) 자막/말하다 마는 음성 (TTS-AP-066)
- 이중 경어·ㄴ다 오활용 (TTS-AP-067)
- 콤마 숫자 파탄·숫자-단위 연음 (TTS-AP-064·065 — test_tts_pronounce 와 상보)

순수 함수 — 디스크/네트워크 불필요.
실행: python -m unittest tests.test_cue_copy
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hyperframes" / "scripts"))

from bundle_to_video import clip_cue, lint_cues, settle_ellipsis, to_polite, tts_of


class TestSettleEllipsis(unittest.TestCase):
    def test_no_ellipsis_passthrough(self) -> None:
        self.assertEqual(settle_ellipsis("온전한 문장입니다."), "온전한 문장입니다.")

    def test_rewinds_to_last_sentence(self) -> None:
        self.assertEqual(
            settle_ellipsis("첫 문장입니다. 둘째 문장은 잘렸 …"), "첫 문장입니다.")

    def test_all_truncated_becomes_empty(self) -> None:
        # 완결 문장이 없으면 빈 문자열 — 억지 문장보다 생략 (C0.2)
        self.assertEqual(settle_ellipsis("SK하이닉스는 이번 거래로 …"), "")
        self.assertEqual(settle_ellipsis("SK하이닉스는 이번 거래로 ..."), "")


class TestClipCue(unittest.TestCase):
    def test_never_mid_cut_no_ellipsis(self) -> None:
        long = "첫 문장은 여기서 끝납니다. 두 번째 문장은 조금 더 이어집니다. 세 번째는 예산 밖입니다."
        out = clip_cue(long, 40)
        self.assertNotIn("…", out)
        self.assertTrue(out.endswith("."))

    def test_single_long_sentence_kept_whole(self) -> None:
        # 첫 문장부터 예산 초과 → 길어도 통째 (긴 온전함 > 짧은 절단)
        s = "이 문장은 하나뿐인데 아주 길어서 예산 사십 자를 훌쩍 넘어가지만 자르면 안 되는 문장입니다."
        self.assertEqual(clip_cue(s, 40), s)

    def test_fits_untouched(self) -> None:
        self.assertEqual(clip_cue("짧은 문장입니다.", 100), "짧은 문장입니다.")


class TestToPolite(unittest.TestCase):
    def test_already_polite_untouched(self) -> None:
        # TTS-AP-067: "팔았습니다" → "팔았습니습니다" 재적용 금지
        self.assertEqual(to_polite("현금을 투입합니다."), "현금을 투입합니다.")
        self.assertEqual(to_polite("168달러에 팔았습니다."), "168달러에 팔았습니다.")

    def test_nda_conjugation(self) -> None:
        # TTS-AP-067: 받침 ㄴ+다 — 둔다→둡니다 (둔습니다 아님)
        self.assertEqual(to_polite("무게를 둔다."), "무게를 둡니다.")
        self.assertEqual(to_polite("믿음이 간다."), "믿음이 갑니다.")

    def test_neunda_general(self) -> None:
        self.assertEqual(to_polite("시장이 먹는다."), "시장이 먹습니다.")
        self.assertEqual(to_polite("공장을 짓는다."), "공장을 짓습니다.")

    def test_specific_rules_kept(self) -> None:
        self.assertEqual(to_polite("가능성을 낮게 본다."), "가능성을 낮게 봅니다.")
        self.assertEqual(to_polite("우세하다."), "우세합니다.")


class TestTtsOfTruncation(unittest.TestCase):
    def test_truncated_only_is_silent(self) -> None:
        # TTS-AP-066: 말하다 마는 음성보다 침묵
        self.assertEqual(tts_of("SK하이닉스는 이번 거래로 …"), "")

    def test_truncated_tail_rewound(self) -> None:
        self.assertEqual(tts_of("완결 문장입니다. 그리고 절단 …"), "완결 문장입니다.")


class TestLintCues(unittest.TestCase):
    def test_flags_all_slop_classes(self) -> None:
        bad = [
            {"t": 0, "text": "SK하이닉스는 이번 거래로 …", "tts": "SK하이닉스는 이번 거래로"},
            {"t": 1, "text": "숫자 자막.", "tts": "일,삼백구십오,영 원입니다."},
            {"t": 2, "text": "경어.", "tts": "무게를 둔습니다."},
            {"t": 3, "text": "이중.", "tts": "팔았습니습니다."},
        ]
        joined = "\n".join(lint_cues(bad))
        for token in ("절단(자막)", "미완(음성)", "콤마잔재(음성)", "ㄴ다오활용(음성)", "이중경어(음성)"):
            self.assertIn(token, joined)

    def test_clean_cues_pass(self) -> None:
        clean = [
            {"t": 0, "text": "온전한 자막 문장입니다.", "tts": "백육십팔딸러에 팔았습니다."},
            {"t": 1, "text": "신발을 신습니다.", "tts": "신발을 신습니다."},  # 정상 ㄴ받침 활용 예외
        ]
        self.assertEqual(lint_cues(clean), [])


if __name__ == "__main__":
    unittest.main()

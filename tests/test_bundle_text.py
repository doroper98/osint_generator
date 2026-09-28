"""bundle/ 이관 회귀 테스트 (v2.0.0).

`bundle_to_video.py`(archive/hyperframes-briefing) 에서 본문 무변경으로 옮긴 순수 함수의 출력을
고정한다 (docs/handoff/19 §5.3). 알려진 버그 2건(개월 수사·'-ㄴ다' 경어체)은 올바른 기대값으로 쓰고
strict xfail 로 두었다가 v2.3.0 에서 고쳐 마커를 뗐다(TTS-AP-064, D18).
"""

from __future__ import annotations

import unittest

from bundle.charts import build_versus, norm_network, split_unit
from bundle.text import (
    em_segments_line,
    josa,
    native_count,
    sentence_grounded,
    build_corpus,
    to_polite,
    tts_of,
)


class TtsOfFrozenTest(unittest.TestCase):
    def test_months_count_sino(self) -> None:
        self.assertEqual(tts_of("18개월"), "십팔 개월")

    def test_decimal_policy_d6(self) -> None:
        # 저장소 정책 유지 (DECISIONS D6, TTS-AP-059): 쩜, 무공백
        self.assertEqual(tts_of("13.1%"), "십삼쩜일 퍼센트")

    def test_month_irregular(self) -> None:
        self.assertEqual(tts_of("6월 17일"), "유월 십칠일")

    def test_slash_date(self) -> None:
        self.assertEqual(tts_of("7/13 발표"), "칠월 십삼일 발표")

    def test_native_unit(self) -> None:
        self.assertEqual(tts_of("5가지 이유"), "다섯 가지 이유")


class TextHelpersTest(unittest.TestCase):
    def test_to_polite(self) -> None:
        self.assertEqual(to_polite("크다"), "큽니다.")

    def test_josa_and_native(self) -> None:
        self.assertEqual(josa("한국", "은", "는"), "은")
        self.assertEqual(native_count(7), "일곱")

    def test_em_segments(self) -> None:
        self.assertEqual(
            em_segments_line("호르무즈 해협을 닫았다", ["해협"]),
            [["호르무즈 ", 0], ["해협", 1], ["을 닫았다", 0]],
        )

    def test_grounded(self) -> None:
        corpus = build_corpus({"x": "유가 83.9달러"})
        self.assertTrue(sentence_grounded("유가는 83.9달러", corpus))
        self.assertFalse(sentence_grounded("유가는 90달러", corpus))


class ChartsTest(unittest.TestCase):
    def test_split_unit(self) -> None:
        self.assertEqual(split_unit("수출액 (단위: 억 달러)"), ("수출액", "억 달러"))

    def test_network_flag_from_moved_dir(self) -> None:
        out = norm_network({"data": {"nodes": [{"id": "kr", "label": "한국"}, {"id": "us", "label": "미국"}],
                                     "links": [{"source": "kr", "target": "us"}]}})
        assert out is not None
        self.assertEqual(out["nodes"][0]["img"], "assets/flags/kr.svg")

    def test_versus_polite(self) -> None:
        v = build_versus({"resolution": "다수설", "side_a": "한국은행은 금리를 낮춘다", "side_b": "b"}, {})
        self.assertEqual(v["cards"][0]["line"], "금리를 낮춥니다.")


if __name__ == "__main__":
    unittest.main()

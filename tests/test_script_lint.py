"""원고 린트 (v2.3.0, back_and_forth D-0021 작업 7, 03 §2).

- 사용자 지정 금지 문구 12개(03 §2 원문 목록을 문장으로 채운 샘플) 전부 slop 오류
- v3 원고 45문장(projects/hormuz_korea/script.yaml) 오류 0
- 발음 텍스트 기호 6종 전부 tts-symbol 오류
- 출처 누락·자막 줄 수 초과는 경고(오류 아님)
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from script.lint import lint, subtitle_lines
from script.schema import Script

REPO = Path(__file__).resolve().parent.parent

# 03 §2 사용자 원문 12개 — ㅁㅁ 자리를 채운 문장
BANNED_SAMPLES: tuple[str, ...] = (
    "세 가지 화살이 한곳으로 모인다.",
    "미국의 발표가 시장을 한번에 흔들었다.",
    "세겹의 문제가 눌려있는 지점입니다.",
    "앞으로 이 결정이 한국 해운의 방향을 정한다.",
    "결국 이야기는 같은자리로 돌아온다.",
    "숫자로 읽으면 이렇다.",
    "그래서 이 카테고리 승부는 이제 화면이 아니라 공정에서 난다.",
    "한국 부품 장비 회사에 이 발표가 진짜 뉴스인 이유도 거기 있다.",
    "저 수준의 공정을 누가 대량으로 받아 주느냐가 다음 계약서에 그대로 적힌다.",
    "한국이 서 있는 자리는 좁습니다.",
    "지도만 보면 봉쇄로 읽힌다.",
    "정부가 말하는것, 그리고 말하지 않는것.",
)

TTS_SYMBOL_SAMPLES: tuple[str, ...] = (
    "원유의 61퍼센트가 지났습니다.",   # 숫자
    "원유의 육십일%가 지났습니다.",     # %
    "하루 이천만~이천이백만 배럴입니다.",  # ~
    "한국/일본이 수입합니다.",          # /
    "시각 열한:삼십에 발표했습니다.",    # :
    "호르무즈 → 인도양으로 나갑니다.",   # →
)


def _script(texts: list[str], tts: list[str | None] | None = None, sources: bool = True) -> Script:
    sents = []
    for i, t in enumerate(texts):
        d: dict = {"date": "2026.09.18", "text": t}
        if tts and tts[i] is not None:
            d["tts"] = tts[i]
        if sources:
            d["sources"] = ["테스트 출처"]
        sents.append(d)
    return Script.model_validate({"title": "t", "subtitle": "s", "date": "2026.09.18",
                                  "scenes": [{"id": "x", "sentences": sents}]})


class ScriptLintTest(unittest.TestCase):
    def test_banned_samples_all_detected(self) -> None:
        self.assertEqual(len(BANNED_SAMPLES), 12)
        for t in BANNED_SAMPLES:
            rep = lint(_script([t]))
            kinds = [i.kind for i in rep.errors]
            self.assertIn("slop", kinds, f"검출 안 됨: {t}")

    def test_v3_script_passes(self) -> None:
        raw = yaml.safe_load((REPO / "projects/hormuz_korea/script.yaml").read_text(encoding="utf-8"))
        script = Script.model_validate(raw)
        self.assertEqual(sum(len(sc.sentences) for sc in script.scenes), 45)
        rep = lint(script)
        self.assertEqual([i.line() for i in rep.errors], [])

    def test_tts_symbols_detected(self) -> None:
        for say in TTS_SYMBOL_SAMPLES:
            rep = lint(_script(["자막 문장입니다."], [say]))
            self.assertEqual([i.kind for i in rep.errors], ["tts-symbol"], say)

    def test_subtitle_digits_allowed_when_tts_clean(self) -> None:
        rep = lint(_script(["9월 18일, 기자회견을 열었습니다."], ["구월 십팔일, 기자회견을 열었습니다."]))
        self.assertEqual(rep.errors, [])

    def test_source_missing_is_warning(self) -> None:
        rep = lint(_script(["대통령실이 밝혔습니다."], sources=False))
        self.assertEqual(rep.errors, [])
        self.assertEqual([i.kind for i in rep.warnings], ["source-missing"])
        self.assertEqual(rep.warnings[0].sid, "x_0")

    def test_subtitle_over_two_lines_is_warning(self) -> None:
        long = " ".join(["호르무즈 해협을 지나는 유조선의 항로와 보험료가"] * 6)
        self.assertGreater(subtitle_lines(long), 2)
        rep = lint(_script([long]))
        self.assertEqual(rep.errors, [])
        self.assertIn("subtitle-lines", [i.kind for i in rep.warnings])
        self.assertEqual(subtitle_lines("짧은 자막입니다."), 1)


if __name__ == "__main__":
    unittest.main()

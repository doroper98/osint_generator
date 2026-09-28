"""나레이션 TTS-위험 표기 린터 테스트 (v0.16.0 → v3.0.0 script.lint.tts_risks, 패턴은 rules tts_risk).

순수 함수라 디스크/네트워크 불필요. 깨끗한 한국어는 통과, 위험 표기는 카테고리별로 탐지.

실행: python -m unittest tests.test_tts_lint
"""

from __future__ import annotations

import unittest

from script.lint import tts_risks


class _Issue:
    def __init__(self, kind: str, snippet: str, hint: str) -> None:
        self.category, self.snippet, self.hint = kind, snippet, hint


def lint_narration(text: str) -> list[_Issue]:
    """v3.0.0 — 옛 orchestrator.tts_lint.lint_narration 을 script.lint.tts_risks 로 병합(D-0040 작업 8). 같은 기대값."""
    return [_Issue(*t) for t in tts_risks(text)]


class TestLintNarration(unittest.TestCase):
    def test_clean_korean_passes(self) -> None:
        # 맨 숫자/소수/연월일 한국어는 정상 — 플래그 안 됨.
        clean = "2024년 4월 3일, 미국 지질조사소는 규모 7.4 지진을 확인했습니다. 약 18킬로미터 지점입니다."
        self.assertEqual(lint_narration(clean), [])

    def test_roman_acronyms_flagged(self) -> None:
        cats = {i.category for i in lint_narration("USGS와 CWA가 확인했고 OSINT 분석입니다.")}
        self.assertIn("roman_letters", cats)

    def test_time_colon_flagged(self) -> None:
        self.assertIn("time_colon", {i.category for i in lint_narration("09:30에 발표했습니다.")})

    def test_date_separator_flagged(self) -> None:
        self.assertIn("date_sep", {i.category for i in lint_narration("2026.05.19 기준입니다.")})
        self.assertIn("date_sep", {i.category for i in lint_narration("2026-05-19 기준.")})

    def test_arrow_and_range_flagged(self) -> None:
        self.assertIn("arrow", {i.category for i in lint_narration("14일 → 4일로 단축.")})
        self.assertIn("range_tilde", {i.category for i in lint_narration("3~5일 걸립니다.")})

    def test_slash_flagged(self) -> None:
        self.assertIn("slash", {i.category for i in lint_narration("설계/해석 단계입니다.")})

    def test_thousands_comma_flagged(self) -> None:
        self.assertIn("thousands_comma", {i.category for i in lint_narration("3,000원 입니다.")})

    def test_unit_attached_flagged(self) -> None:
        cats = {i.category for i in lint_narration("100kWh 규모입니다.")}
        self.assertIn("unit_attached", cats)

    def test_version_flagged(self) -> None:
        self.assertIn("version", {i.category for i in lint_narration("버전은 v1.2.3 입니다.")})

    def test_url_flagged(self) -> None:
        self.assertIn("url_email", {i.category for i in lint_narration("https://example.com 참고.")})

    def test_symbols_flagged(self) -> None:
        self.assertIn("symbols", {i.category for i in lint_narration("※ 참고: 중요합니다.")})



if __name__ == "__main__":
    unittest.main()

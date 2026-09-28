"""나레이션 TTS-위험 표기 린터 (v0.16.0).

사람이라면 그렇게 안 읽는 표기(약어/시각콜론/날짜점/화살표/슬래시/숫자+단위/버전/URL/
기호 등)가 narration 에 들어가면 TTS 가 기계적으로 읽어 "AI 티"가 난다
(docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md). 본 모듈은 그런 패턴을 **결정론적으로 탐지**해
생성 단계의 재발을 막는 자동 가드다 (순수 함수, I/O 없음).

원칙
----
- 검사 대상은 **narration**(TTS 가 읽는 본문)뿐. on_screen_caption(화면 자막)은 영문/기호
  허용 — 검사하지 않는다.
- 한국어 숫자(2024, 7.4, 18 같은 맨 숫자/소수)는 정상이므로 플래그하지 않는다. 위험한
  '문맥'(콜론 시각, 점/하이픈 날짜, 천단위 콤마, 붙은 단위, 범위, 버전)만 잡는다.
- 거짓 양성을 줄이기 위해 고신뢰 패턴만. 운율/감정 등 비표기 항목은 사람 검수 영역.
"""

from __future__ import annotations

import re
from typing import NamedTuple



class LintIssue(NamedTuple):
    category: str
    snippet: str
    hint: str


# (category, 정규식, 교정 힌트). 순서는 보고 우선순위.
_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("url_email", re.compile(r"https?://\S+|[\w.+-]+@[\w.-]+\.\w+"),
     "URL/이메일은 음성에서 읽지 말 것 — 자막/화면으로. narration 에서 제거."),
    ("file_path", re.compile(r"[A-Za-z]:\\\S+|/\w+/\S+|\b\w+\.(?:json|exe|xlsx|csv|png|mp4|txt|py|js|wav|mp3)\b"),
     "파일명/경로/확장자는 의미로 풀어서 ('해당 실행 파일' 등). narration 에서 제거."),
    ("version", re.compile(r"\bv(?:er)?\.?\s*\d+(?:\.\d+)+", re.IGNORECASE),
     "버전 표기는 '버전 일 점 이' 처럼 한국어로."),
    # 한글은 유니코드 \w 라 숫자 뒤 \b 가 한글 앞에서 깨진다 → 숫자 룩어라운드 사용.
    ("time_colon", re.compile(r"(?<!\d)\d{1,2}:\d{2}(?!\d)"),
     "시각 콜론(09:30)은 '아홉 시 삼십 분'처럼. 비율(1:1)은 '일대일'."),
    ("date_sep", re.compile(r"\b\d{4}\s*[.\-]\s*\d{1,2}\s*[.\-]\s*\d{1,2}\b"),
     "날짜 점/하이픈(2026.05.19)은 '이천이십육년 오월 십구일'로."),
    ("arrow", re.compile(r"→|⟶|=>|->"),
     "화살표는 '~에서 ~로'로 풀어서."),
    ("range_tilde", re.compile(r"\d\s*~\s*\d|\d\s*∼\s*\d"),
     "물결 범위(3~5)는 '삼에서 오까지'로."),
    ("thousands_comma", re.compile(r"(?<!\d)\d{1,3}(?:,\d{3})+(?!\d)"),
     "천단위 콤마(3,000)는 '삼천'처럼 한국어 수로."),
    ("unit_attached", re.compile(
        r"\d\s?(?:kg|km|cm|mm|kWh|MWh|Wh|mAh|Ah|Hz|kHz|GHz|ms|kbps|Mbps|ppm|°C|℃|°F)(?![A-Za-z])",
        re.IGNORECASE),
     "숫자+영문/기호 단위는 단위를 한국어로 ('18킬로미터', '백 킬로와트시')."),
    ("slash", re.compile(r"(?<=\S)/(?=\S)"),
     "슬래시는 '와/또는/부터'로 풀거나 생략 (날짜·비율 포함)."),
    ("symbols", re.compile(r"[※▲▼△▽◆◇■□●○•◦#@±℃→←↑↓]"),
     "기호(※▲•#@ 등)는 풀어 읽거나 생략 ('참고로', '첫 번째' 등)."),
    # 로마자: narration 은 순수 한국어여야 한다. 약어/영단어는 한국어 명칭·음차로.
    # (단위/버전/URL 등 위 패턴이 먼저 잡은 것과 중복될 수 있으나, 일반 영문은 이게 잡는다.)
    ("roman_letters", re.compile(r"[A-Za-z]{1,}"),
     "narration 에 로마자 금지 — 한국어 명칭/음차로 (예: USGS→'미국 지질조사소'). 영문은 caption 에만."),
]

# roman_letters 가 unit/version/url/file 과 중복 보고되는 것을 줄이기 위해, 그 매치 범위가
# 더 구체적인 카테고리에 이미 포함되면 생략한다.
_SPECIFIC_BEFORE_ROMAN = {"url_email", "file_path", "version", "unit_attached"}


def lint_narration(text: str) -> list[LintIssue]:
    """narration 문자열에서 TTS-위험 표기를 탐지해 LintIssue 목록 반환 (순수)."""
    if not text:
        return []
    issues: list[LintIssue] = []
    seen: set[tuple[str, str]] = set()
    covered_spans: list[tuple[int, int]] = []  # 구체 패턴이 덮은 구간 (roman 중복 억제용)

    for category, pattern, hint in _PATTERNS:
        for m in pattern.finditer(text):
            snippet = m.group(0)
            if category == "roman_letters":
                # 이미 구체 카테고리가 덮은 구간이면 생략.
                s, e = m.span()
                if any(cs <= s and e <= ce for cs, ce in covered_spans):
                    continue
            key = (category, snippet)
            if key in seen:
                continue
            seen.add(key)
            issues.append(LintIssue(category=category, snippet=snippet[:60], hint=hint))
            if category in _SPECIFIC_BEFORE_ROMAN:
                covered_spans.append(m.span())
    return issues


__all__ = ["LintIssue", "lint_narration"]

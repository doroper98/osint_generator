"""원고 린트 (v2.1.0, plan3 `BANNED, lint()`, 03 §2).

패턴은 `rules/video_rules.yaml`에서 읽는다(15 P3). 위반 종류:
- slop: AI 상투 문구(banned_phrases.patterns)
- tts-symbol: 발음 텍스트 안의 숫자·기호(tts_rules.forbidden_chars_regex, TTS-AP-021~025·058)
- emphasis-missing: 강조어가 자막에 없음
"""

from __future__ import annotations

import re

from rules import load_rules
from script.schema import Script


def lint(script: Script) -> list[tuple[str, ...]]:
    r = load_rules()
    banned = [re.compile(p) for p in r.banned_phrases.patterns]
    forbidden = re.compile(r.tts_rules.forbidden_chars_regex)
    bad: list[tuple[str, ...]] = []
    for sc in script.scenes:
        for s in sc.sentences:
            for p in banned:
                if p.search(s.text):
                    bad.append(("slop", p.pattern, s.text))
            say = s.tts or s.text
            if forbidden.search(say):
                bad.append(("tts-symbol", say))
            for e in s.emphasis:
                if e not in s.text:
                    bad.append(("emphasis-missing", e, s.text))
    return bad

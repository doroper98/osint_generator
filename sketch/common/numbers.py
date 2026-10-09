"""단위 붙은 숫자 찾기 — SK-H1 자유 문구 검사의 공통 틀(D-0145 §6). 단위 표 = rules sketch.numbers.units(check: true 인 것)."""

from __future__ import annotations

import re

from rules import load_rules

NU = load_rules().sketch.numbers


def unit_pattern() -> re.Pattern[str]:
    """단위 붙은 숫자(규칙 단위 표의 접두·접미 그대로)."""
    alts = []
    for u in NU.units.values():
        if not u.check:
            continue
        if u.suffix:
            alts.append(r"(?P<n%d>\d[\d,]*(?:\.\d+)?)\s*" % len(alts) + re.escape(u.suffix))
        if u.prefix:
            alts.append(re.escape(u.prefix.strip()) + r"\s*(?P<n%d>\d[\d,]*(?:\.\d+)?)" % len(alts))
    return re.compile("|".join(alts))


UNIT_NUM = unit_pattern()


def unit_of(token: str) -> str:
    """찾은 토큰의 단위 이름."""
    for name, u in NU.units.items():
        if not u.check:
            continue
        if (u.suffix and token.strip().endswith(u.suffix)) or (u.prefix and token.strip().startswith(u.prefix.strip())):
            return name
    raise KeyError(token)


def unit_numbers(s: str) -> list[tuple[str, str, float]]:
    """문자열 안 (토큰, 단위, 값) 목록."""
    out = []
    for m in UNIT_NUM.finditer(s):
        val = next(g for g in m.groups() if g is not None)
        out.append((m.group(0).strip(), unit_of(m.group(0)), float(val.replace(",", ""))))
    return out

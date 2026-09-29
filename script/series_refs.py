"""원고 문장의 데이터 레코드 참조 `series:<series_id>` — 수치 대조 린트 (v4.3.0, back_and_forth D-0088, docs/handoff/20 §5.1·§9-4).

`sources: ["series:FEDFUNDS"]` 는 claim 이 아니라 데이터 레코드(data/series/<id>)를 가리킨다. 검증 라벨 계산에서 빠진다
(근거 = 엔딩 카드 auto: series 절 + 화면 시리즈의 출처·기준 시점 줄). 대조는 **자막 텍스트**로 한다(발음 텍스트는 숫자 금지, 03 §4).

오류 `series-value-mismatch`(D-0088):
1. `N%` — 문장 date 달의 레코드 값을 자막이 쓴 소수 자리로 반올림(half-up)해 비교.
2. `N%p` — 문장 date 달 값 − 직전 관측 달 값(missing 건너뜀). 자막에 날짜(YYYY년 M월)가 둘이면 그 두 달의 차.
3. 문장 date 달이 레코드 missing 인데 `N%`·`N%p` 를 말함(D-0086 보정 2). 수치 없는 문장은 통과.
4. 참조가 둘 이상인데 수치가 있음 → 어느 레코드인지 구분 불가(문장을 나눠 쓴다).
날짜가 달 단위가 아니거나 레코드 구간 밖이면 "대조 불가" 오류 — 계산식을 린트가 추정하지 않는다.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

PREFIX = "series:"
PCT = re.compile(r"(-?\d+(?:\.\d+)?)\s*(%p|%)")
YM = re.compile(r"(\d{4})년\s*(\d{1,2})월")


def is_series_ref(s: str) -> bool:
    return s.startswith(PREFIX)


def series_id(ref: str) -> str:
    return ref[len(PREFIX):]


def _month(d: str) -> Optional[date]:
    parts = d.split(".")
    if len(parts) < 2:
        return None
    return date(int(parts[0]), int(parts[1]), 1)


def _round(v: float, like: str) -> Decimal:
    places = len(like.split(".")[1]) if "." in like else 0
    return Decimal(repr(v)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def check_series_sentence(text: str, sent_date: str, refs: list[str]) -> list[str]:
    """문장 하나 → 오류 설명 목록(빈 목록 = 통과). refs = series: 참조(레코드 존재는 호출하는 쪽이 먼저 확인)."""
    from data.series import load_series  # noqa: PLC0415

    nums = PCT.findall(text)
    if not nums or not refs:
        return []
    if len(refs) > 1:
        return [f"series 참조 {refs} 가 둘 이상인데 수치 {[''.join(n) for n in nums]} 가 있다 — 어느 레코드 값인지 구분할 수 없다(문장을 나눠 쓴다)"]
    rec = load_series(series_id(refs[0]))
    by = dict(rec.values)
    miss = set(rec.missing_dates())
    m = _month(sent_date)
    if m is None:
        return [f"문장 date {sent_date!r} 가 달 단위가 아니라 {rec.series_id} 값과 대조할 수 없다"]
    if m in miss:
        return [f"{m:%Y-%m} 은 {rec.series_id} 의 빈 달(missing: {next(x.note for x in rec.missing if x.date == m)}) — 값을 말하지 않는다"]
    out: list[str] = []
    for num, unit in nums:
        if unit == "%":
            if m not in by:
                out.append(f"{m:%Y-%m} 은 {rec.series_id} 구간({rec.start:%Y-%m}~{rec.end:%Y-%m}) 밖 — 대조 불가")
                continue
            want = _round(by[m], num)
            if want != Decimal(num):
                out.append(f"자막 {num}% ≠ {rec.series_id} {m:%Y-%m} 값 {by[m]}(→ {want}%)")
            continue
        yms = [date(int(y), int(mo), 1) for y, mo in YM.findall(text)]
        if len(yms) >= 2:
            a, b = yms[0], yms[1]
        else:
            prev = [d for d in (d for d, _ in rec.values) if d < m]
            if not prev:
                out.append(f"{m:%Y-%m} 직전 관측 달이 없다 — {num}%p 대조 불가")
                continue
            a, b = prev[-1], m
        if a not in by or b not in by:
            out.append(f"{num}%p: {a:%Y-%m}·{b:%Y-%m} 중 {rec.series_id} 값이 없는 달 — 대조 불가")
            continue
        want = _round(by[b] - by[a], num)
        if want != Decimal(num):
            out.append(f"자막 {num}%p ≠ {rec.series_id} {b:%Y-%m} − {a:%Y-%m} = {by[b] - by[a]:.4g}(→ {want}%p)")
    return out


__all__ = ["PREFIX", "check_series_sentence", "is_series_ref", "series_id"]

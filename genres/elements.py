"""연출이 쓴 요소 종류 — 장르 프로필 대조용 (v4.2.0, back_and_forth D-0081 작업 3, checks genre_elements).

요소 이름 = 레지스트리 이름(장르 프로필 `primitives.reuse`·`new` 와 같은 이름공간):
- `panel` 이벤트 → 패널 kind(예: versus). 운반 타입 `panel` 자체는 세지 않는다.
- `primitive` 이벤트 → 프리미티브 id(예: statement_diff). 운반 타입 `primitive` 자체는 세지 않는다.
- `badge` 이벤트 → `badge` 와 뱃지 kind(person·flag·emblem) 둘 다.
- 그 밖 → 이벤트 type.
입력은 direction.yaml 의 events(연출이 쓴 것)다. 숏의 dip(카메라 전환)이 만든 암전 이벤트는 넣지 않는다.
"""

from __future__ import annotations

from collections import Counter

CARRIERS: dict[str, str] = {"panel": "kind", "primitive": "id"}   # 운반 타입 → 요소 이름 필드


def _field(e: dict, key: str) -> object:
    data = e.get("data")
    return e.get(key, data.get(key) if isinstance(data, dict) else None)


def event_elements(e: dict) -> list[str]:
    typ = str(e.get("type"))
    if typ in CARRIERS:
        return [str(_field(e, CARRIERS[typ]))]
    if typ == "badge":
        return ["badge", str(_field(e, "kind"))]
    return [typ]


def used_elements(events: list[dict]) -> dict[str, int]:
    """요소 이름 → 쓰인 이벤트 수(이름순)."""
    c: Counter[str] = Counter(x for e in events for x in event_elements(e))
    return dict(sorted(c.items()))


def outside(used: dict[str, int], allowed: set[str]) -> dict[str, int]:
    """프로필 밖 요소(이름 → 수)."""
    return {k: v for k, v in used.items() if k not in allowed}


__all__ = ["CARRIERS", "event_elements", "outside", "used_elements"]

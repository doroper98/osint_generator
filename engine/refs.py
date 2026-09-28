"""이벤트 안의 자산 참조 찾기 (v2.5.0) — 뱃지 이벤트든 패널 노드든 같은 규칙으로 찾는다.

휘장은 `badge` 이벤트만이 아니라 관계 패널 노드(D-0032) 안에도 올 수 있다. 권리·자산 점검·provenance 가
이벤트 타입으로 거르면 패널 안 휘장이 점검을 조용히 빠져나간다(15 P6). 그래서 중첩 dict 를 모두 본다.
"""

from __future__ import annotations

from typing import Iterator


def walk_dicts(o: object) -> Iterator[dict]:
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk_dicts(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from walk_dicts(v)


def emblem_ids(e: dict) -> list[str]:
    """이벤트(중첩 포함)가 참조하는 휘장 id — `kind: emblem` + `img`."""
    return [d["img"] for d in walk_dicts(e) if d.get("kind") == "emblem" and isinstance(d.get("img"), str)]

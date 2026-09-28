"""번들 노드·마커 → 엔티티 레지스트리 조인 (v3.5.0, docs/handoff/12 §2·§4·§7, back_and_forth D-0063 작업 1).

- 1차: **id 매칭**. stakeholder_map `nodes[].id`·`map.markers[].id` 가 `assets/entities.yaml`(+ 인물 라이브러리 자동 등재)
  의 엔티티 id 와 같으면 조인한다.
- 없으면 `unmatched[]` 에 기록한다. **추측으로 엔티티를 만들지 않는다**. 라벨이 레지스트리 별칭과 정확히 같으면
  `alias_candidate` 로 적어 두기만 한다(사람이 확인해 entities.yaml 에 id 로 등재).
- 문장 언급 탐지(`mentions`, 12 §4 별칭)는 **폴백**이다. 결과는 초안 주석에 unmatched 와 함께 남는다 — 연출 입력의
  뱃지 후보일 뿐, 번들이 문장별 `entity_refs` 를 주면(12 §6) 그것이 우선이다.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from engine.entities import EntityRegistry
from schemas.models import ReportBundle

STAKEHOLDER = "stakeholder_map"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BundleEntity(_Strict):
    """번들 쪽 엔티티 하나(노드 또는 마커)와 조인 결과."""

    id: str
    label: str
    origin: Literal["node", "marker"]
    chart_id: Optional[str] = None           # 노드가 나온 stakeholder_map
    kind: Optional[str] = None               # 번들 표기 그대로(person·military·chokepoint …)
    flag: Optional[str] = None               # ISO2 소문자(번들 대문자 정규화)
    logo: Optional[str] = None               # 기관 도메인(번들 표기)
    role: str = ""
    entity_id: Optional[str] = None          # 조인된 레지스트리 id. None = unmatched
    alias_candidate: Optional[str] = None    # 라벨이 레지스트리 별칭과 같은 엔티티 id(조인 아님, 확인 필요)


class Unmatched(_Strict):
    id: str
    label: str
    origin: Literal["node", "marker"]
    reason: str
    alias_candidate: Optional[str] = None


class Mention(_Strict):
    """문장 안 언급(폴백) — 별칭이 처음 나타난 글자 위치 비율(0~1)."""

    id: str
    alias: str
    at: float = Field(ge=0, le=1)


class EntityJoin(_Strict):
    entities: list[BundleEntity] = Field(default_factory=list)
    unmatched: list[Unmatched] = Field(default_factory=list)

    def by_id(self) -> dict[str, BundleEntity]:
        return {e.id: e for e in self.entities}


def _flag(v: object) -> Optional[str]:
    return str(v).lower() if isinstance(v, str) and len(v) == 2 and v.isalpha() else None


def _nodes(b: ReportBundle) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for c in b.charts:
        if c.type == STAKEHOLDER and isinstance(c.data, dict):
            out += [(c.chart_id, n) for n in c.data.get("nodes", []) if isinstance(n, dict) and n.get("id")]
    return out


def join_entities(b: ReportBundle, reg: EntityRegistry) -> EntityJoin:
    """stakeholder 노드·지도 마커 → 레지스트리 조인. 결정적(같은 입력 = 같은 출력)."""
    ents: list[BundleEntity] = []
    unm: list[Unmatched] = []
    seen: set[tuple[str, str]] = set()

    def add(e: BundleEntity) -> None:
        if (e.origin, e.id) in seen:
            return
        seen.add((e.origin, e.id))
        if e.id in reg.entities:
            e.entity_id = e.id
        else:
            e.alias_candidate = reg.alias.get(e.label)
            unm.append(Unmatched(id=e.id, label=e.label, origin=e.origin, alias_candidate=e.alias_candidate,
                                 reason="레지스트리에 같은 id 없음" + (" — 라벨이 별칭과 같음(확인 후 등재)" if e.alias_candidate else "")))
        ents.append(e)

    for cid, n in _nodes(b):
        add(BundleEntity(id=str(n["id"]), label=str(n.get("label") or n["id"]), origin="node", chart_id=cid,
                         kind=n.get("kind"), flag=_flag(n.get("flag")), logo=n.get("logo"), role=str(n.get("role") or "")))
    for m in (b.map.markers if b.map else []):
        add(BundleEntity(id=m.id, label=m.name or m.id, origin="marker", kind=getattr(m, "kind", None)))
    return EntityJoin(entities=ents, unmatched=unm)


def aliases(e: BundleEntity, reg: EntityRegistry) -> list[str]:
    """언급 탐지 별칭(12 §4): 라벨, 인물이면 라벨 마지막 어절(성), 조인됐으면 레지스트리 이름들. 긴 것 먼저."""
    out = {e.label}
    if e.kind == "person" and " " in e.label:
        out.add(e.label.split()[-1])
    if e.entity_id:
        out.update(reg.get(e.entity_id).names)
    return sorted((a for a in out if a), key=lambda a: (-len(a), a))


def mentions(text: str, join: EntityJoin, reg: EntityRegistry) -> list[Mention]:
    """문장 안 엔티티 언급(폴백). 엔티티마다 별칭이 처음 나타난 위치. 위치 순 정렬."""
    out: list[Mention] = []
    n = max(len(text), 1)
    for e in join.entities:
        hits = [(text.find(a), a) for a in aliases(e, reg) if a in text]
        if hits:
            i, a = min(hits)
            out.append(Mention(id=e.id, alias=a, at=round(i / n, 4)))
    return sorted(out, key=lambda m: (m.at, m.id))


__all__ = ["BundleEntity", "EntityJoin", "Mention", "Unmatched", "aliases", "join_entities", "mentions"]

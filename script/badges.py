"""이름 → 뱃지 자동 제안 (v2.4.0, back_and_forth D-0029 작업 6, 07 §6, 12 §4 mention 탐지).

원고 문장에서 엔티티 별칭을 찾아 그 문장 시각에 놓을 뱃지를 **제안만** 한다. 연출 확정은 LLM+사용자(15 P8) —
이 함수는 이벤트를 만들지 않는다. provenance `assets.badges.suggested/used` 로 제안과 실제 사용을 나란히 남긴다.

한국어는 띄어쓰기 경계가 약하다. 별칭 앞은 비한글(시작·공백·문장부호)이어야 하고, 뒤는 비한글이거나 조사여야 한다
("인도양"·"인도네시아"에서 "인도"를 잡지 않는다). 긴 별칭부터 겹치지 않게 고른다("대한민국" 안의 "한국" 제외).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from engine.entities import EntityRegistry, load_entities
from script.schema import Plan

PARTICLE_HEADS = set("은는이가을를의에과와도로으만께서부까처보라란랑며엔")


class BadgeSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sid: str
    entity: str
    alias: str
    kind: Literal["person", "flag", "emblem"]
    at: float                      # 제안 시각(문장 안 글자 비율로 근사). 확정 시각은 연출이 정한다
    pid: Optional[str] = None
    flag: Optional[str] = None
    img: Optional[str] = None


def _hangul(ch: str) -> bool:
    return "가" <= ch <= "힣"


def find_mentions(text: str, reg: EntityRegistry) -> list[tuple[int, str, str]]:
    """(위치, 별칭, 엔티티 id). 긴 별칭 우선, 겹침 없음."""
    taken = [False] * len(text)
    out: list[tuple[int, str, str]] = []
    for alias in sorted(reg.alias, key=len, reverse=True):
        start = 0
        while (i := text.find(alias, start)) >= 0:
            start = i + 1
            j = i + len(alias)
            before_ok = i == 0 or not _hangul(text[i - 1])
            after_ok = j == len(text) or not _hangul(text[j]) or text[j] in PARTICLE_HEADS
            if not (before_ok and after_ok) or any(taken[i:j]):
                continue
            taken[i:j] = [True] * (j - i)
            out.append((i, alias, reg.alias[alias]))
    return sorted(out)


def _badge_fields(reg: EntityRegistry, eid: str) -> dict:
    e = reg.get(eid)
    if e.kind == "person":
        return dict(kind="person", pid=e.portrait or e.library, flag=e.flag)
    if e.kind == "org" and e.emblem is not None:
        return dict(kind="emblem", img=e.emblem, flag=e.flag)
    return dict(kind="flag", flag=e.flag)


def suggest_badges(plan: Plan, reg: EntityRegistry | None = None) -> list[BadgeSuggestion]:
    reg = reg or load_entities()
    out: list[BadgeSuggestion] = []
    for s in plan.sentences:
        for i, alias, eid in find_mentions(s.text, reg):
            at = s.t0 + (s.t1 - s.t0) * i / max(1, len(s.text))
            out.append(BadgeSuggestion(sid=s.sid, entity=eid, alias=alias, at=round(at, 3), **_badge_fields(reg, eid)))
    return out


def badge_entity(e: dict, reg: EntityRegistry) -> str:
    """뱃지 이벤트 → 엔티티 id (provenance 용)."""
    if e["kind"] == "person":
        for eid, ent in reg.of_kind("person").items():
            if e["pid"] in (ent.portrait, ent.library):
                return eid
    if e["kind"] == "emblem":
        return reg.emblem_owner(e["img"]).id
    for eid, ent in reg.of_kind("country").items():
        if ent.flag == e.get("flag"):
            return eid
    return f"?{e.get('pid') or e.get('img') or e.get('flag')}"


def badge_usage(plan: Plan, events: list[dict], reg: EntityRegistry | None = None) -> dict:
    """provenance `badges`: 제안된 엔티티, 실제 뱃지로 쓰인 엔티티, 둘의 교집합."""
    reg = reg or load_entities()
    sug = suggest_badges(plan, reg)
    suggested = sorted({b.entity for b in sug})
    used = sorted({badge_entity(e, reg) for e in events if e["type"] == "badge"})
    return {"suggested": suggested, "used": used, "suggested_and_used": sorted(set(suggested) & set(used)),
            "suggestions": len(sug)}

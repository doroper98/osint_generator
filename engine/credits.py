"""엔딩 크레딧 데이터와 권리 대조 (v2.4.0, render3 `credit_sections, credits`, 07 §7, back_and_forth D-0029 작업 7).

크레딧 문구는 프로젝트 `credits.yaml` 에 있다. 각 항목은 `rights:` 로 권리 레지스트리 항목을 가리킨다
(`people.<pid>`, `emblems.<id>`, `media.<mid>`, `flags.<id>`, `music.<id>`, `fonts.<id>`, `map.<id>`, `narration.<id>`).
절(section)에 `auto: <절 이름>` 을 쓰면 그 절의 레지스트리 항목 중 이번 렌더가 쓰는 것을 자동으로 나열한다.

렌더 전 검사(`check_credits`, C9·15 P6): 이번 렌더가 쓰는 자산(`required_refs`)은 전부
① 권리 레지스트리에 있고 ② 권리 상태가 확인됐고(rights_clear) ③ 표기 위치가 정해져 있어야 한다.
표기 위치는 규칙 `credits:` 절(D-0030, D35): `card_kinds` = 엔딩 카드 항목이 가리켜야 함,
`description_only_kinds` = 설명문 자동 크레딧 블록(`description_credits`)에 나열. 두 목록 밖 종류 = 오류.
하나라도 어기면 `RightsError`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from rules import load_rules
from schemas.rules_models import CreditRules

RightsSection = Literal["people", "emblems", "media", "flags", "music", "fonts", "map", "narration"]
# 렌더가 항상 쓰는 묶음 자산 — 레지스트리 절의 항목 전부가 크레딧 대상이다
ALWAYS_USED: tuple[RightsSection, ...] = ("music", "fonts", "map", "narration")


class RightsError(RuntimeError):
    pass


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreditItem(_Strict):
    main: str
    license: Optional[str] = None
    license_ref: Optional[str] = None  # rights_registry.people 의 pid — 라이선스 문구를 레지스트리에서 읽는다
    license_suffix: str = ""
    rights: list[str] = Field(default_factory=list)   # v2.4.0 — 이 행이 표기하는 권리 레지스트리 항목

    @model_validator(mode="after")
    def _one_source(self) -> "CreditItem":
        if self.license is not None and self.license_ref is not None:
            raise ValueError(f"license 와 license_ref 는 함께 쓸 수 없다: {self.main!r}")
        return self

    def refs(self) -> list[str]:
        return [*self.rights, *([f"people.{self.license_ref}"] if self.license_ref else [])]


class CreditSection(_Strict):
    title: str
    column: Literal[0, 1]
    items: list[CreditItem] = Field(default_factory=list)
    auto: Optional[RightsSection] = None   # v2.4.0 — 레지스트리 절 자동 나열

    @model_validator(mode="after")
    def _items_or_auto(self) -> "CreditSection":
        if bool(self.items) == (self.auto is not None):
            raise ValueError(f"크레딧 절 {self.title!r}: items 와 auto 중 정확히 하나")
        return self


class Credits(_Strict):
    schema_version: int = 1
    sections: list[CreditSection] = Field(min_length=1)


def load_credits(path: Path) -> Credits:
    return Credits.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def registry_view(rights: dict, media: dict) -> dict[str, dict]:
    """권리 레지스트리 + 미디어 레지스트리를 `절.키 → 항목` 하나로."""
    out: dict[str, dict] = {}
    for sec, entries in rights.items():
        for k, v in (entries or {}).items():
            out[f"{sec}.{k}"] = v
    for k, v in media.items():
        out[f"media.{k}"] = v
    return out


def _auto_items(sec: RightsSection, view: dict[str, dict], used: Optional[set[str]]) -> list[tuple[str, str]]:
    items = []
    for ref, v in view.items():
        if not ref.startswith(sec + ".") or (used is not None and ref not in used):
            continue
        name = v.get("name") or v.get("title") or ref.split(".", 1)[1]
        who = v.get("author") or v.get("artist") or ""
        items.append((name, " · ".join(x for x in (who, v["license"]) if x)))
    return items


def credit_sections(cr: Credits, rights: dict, media: Optional[dict] = None,
                    used: Optional[set[str]] = None) -> list[tuple[str, list[tuple[str, str]]]]:
    view = registry_view(rights, media or {})
    out = []
    for sec in cr.sections:
        if sec.auto is not None:
            out.append((sec.title, _auto_items(sec.auto, view, used)))
            continue
        items = []
        for it in sec.items:
            if it.license_ref is not None:
                people = rights.get("people", {})
                if it.license_ref not in people:
                    raise RightsError(f"권리 레지스트리에 인물 없음: {it.license_ref}")
                lic = people[it.license_ref]["license"] + it.license_suffix
            else:
                lic = (it.license or "") + it.license_suffix
            items.append((it.main, lic))
        out.append((sec.title, items))
    return out


def credit_lines(cr: Credits, rights: dict, media: Optional[dict] = None, used: Optional[set[str]] = None) -> list[str]:
    return [f"{sec}: {' / '.join(m + (' — ' + l if l else '') for m, l in items)}"
            for sec, items in credit_sections(cr, rights, media, used)]


def required_refs(events: list[dict], rights: dict, emblem_flag: Callable[[str], Optional[str]],
                  image_keys: set[str]) -> set[str]:
    """이번 렌더가 쓰는 자산의 권리 참조. 이벤트(인물·휘장·미디어) + 불러온 이미지(국기) + 항상 쓰는 묶음 자산."""
    need: set[str] = set()

    def walk(o: object):  # noqa: ANN202
        if isinstance(o, dict):
            yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                yield from walk(v)

    for e in events:
        for d in walk(e):
            if d.get("pid") is not None:
                need.add(f"people.{d['pid']}")
        if e["type"] == "badge" and e.get("kind") == "emblem" and emblem_flag(e["img"]) is None:
            need.add(f"emblems.{e['img']}")
        if e["type"] in ("photo", "clip", "cutout") and e.get("mid"):
            need.add(f"media.{e['mid']}")
    if any(k.startswith(("flag11:", "flag43:")) for k in image_keys):
        need |= {f"flags.{k}" for k in rights.get("flags", {})} or {"flags.?"}
    for sec in ALWAYS_USED:
        need |= {f"{sec}.{k}" for k in rights.get(sec, {})} or {f"{sec}.?"}
    return need


def description_credits(rights: dict, required: set[str], rules: Optional[CreditRules] = None) -> list[str]:
    """설명문 자동 크레딧 블록 — description_only_kinds 자산의 이름·라이선스·출처 URL (D-0030 §3)."""
    rules = rules or load_rules().credits
    view = registry_view(rights, {})
    lines: list[str] = []
    for kind in rules.description_only_kinds:
        for r in sorted(x for x in required if x.startswith(kind + ".") and x in view):
            v = view[r]
            lines.append(" · ".join(x for x in (v.get("name") or r, v.get("author", ""), v["license"], v.get("url", "")) if x))
    return lines


def credit_summary(required: set[str], rules: Optional[CreditRules] = None) -> dict[str, dict[str, int]]:
    """provenance `credits`: 표기 위치별 종류 → 개수."""
    rules = rules or load_rules().credits
    out: dict[str, dict[str, int]] = {"card": {}, "description_only": {}}
    for r in required:
        kind = r.split(".", 1)[0]
        where = "card" if kind in rules.card_kinds else "description_only" if kind in rules.description_only_kinds else None
        if where:
            out[where][kind] = out[where].get(kind, 0) + 1
    return {k: dict(sorted(v.items())) for k, v in out.items()}


def check_credits(cr: Credits, rights: dict, media: dict, required: set[str], rules: Optional[CreditRules] = None,
                  description: Optional[list[str]] = None) -> None:
    """누락·미확인·미표기 자산이 있으면 RightsError(C9, 15 P6). 통과하면 None."""
    rules = rules or load_rules().credits
    view = registry_view(rights, media)
    errs: list[str] = []
    for kind in sorted({r.split(".", 1)[0] for r in view} - set(rules.card_kinds) - set(rules.description_only_kinds)):
        errs.append(f"권리 종류 {kind} 의 표기 위치가 규칙(credits.card_kinds/description_only_kinds)에 없다")
    covered: set[str] = set()
    for sec in cr.sections:
        if sec.auto is not None:
            covered |= {r for r in required if r.startswith(sec.auto + ".")}
        for it in sec.items:
            for r in it.refs():
                if r not in view:
                    errs.append(f"크레딧 {it.main!r} 이 가리키는 권리 항목 없음: {r}")
                covered.add(r)
    desc = description if description is not None else description_credits(rights, required, rules)
    for r in sorted(required):
        kind = r.split(".", 1)[0]
        if r.endswith(".?"):
            errs.append(f"권리 레지스트리 {r[:-2]} 절이 비었다 — 렌더가 쓰는 자산의 권리 기록 없음")
            continue
        if r not in view:
            errs.append(f"권리 레지스트리에 없음: {r}")
            continue
        status = view[r].get("rights_status", "rights_clear")
        if status != "rights_clear":
            errs.append(f"권리 미확인 자산({status}): {r} — <미검증> 라벨 외 사용 금지(C9)")
        if kind in rules.card_kinds and r not in covered:
            errs.append(f"엔딩 크레딧 누락: {r}")
        name = view[r].get("name") or r
        if kind in rules.description_only_kinds and not any(line.startswith(name) for line in desc):
            errs.append(f"설명문 크레딧 누락: {r}")
    if errs:
        raise RightsError("크레딧·권리 점검 실패:\n" + "\n".join(errs))

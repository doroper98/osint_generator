"""엔티티 레지스트리 로더 (v2.4.0, back_and_forth D-0029 작업 2, 07 §6, 13).

`assets/entities.yaml` + 저장소 인물 라이브러리(`assets/library/library_manifest.json`) 조인.
- 라이브러리 인물은 자동 등재(id = person_id, 이름 = name_ko·name_en·aliases, 초상 = 첫 변형).
- yaml 의 같은 id 항목은 보강(국기·직함·강조색·별칭 추가). yaml 전용 인물은 프로젝트 초상 id 를 쓴다.
- 별칭이 두 엔티티에 겹치면 오류. 등재 없는 이름·id 를 연출이 참조하면 `RegistryError`(15 P10).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from engine.registry import RegistryError
from schemas.emblem_models import EmblemRegistry
from schemas.entity_models import EntitiesFile, Entity

REPO = Path(__file__).resolve().parent.parent
ENTITIES_PATH = REPO / "assets" / "entities.yaml"
LIBRARY_PATH = REPO / "assets" / "library" / "library_manifest.json"
EMBLEM_REGISTRY_PATH = REPO / "assets" / "emblems" / "registry.json"


@dataclass
class EntityRegistry:
    entities: dict[str, Entity]
    alias: dict[str, str] = field(default_factory=dict)   # 별칭 → id

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            raise RegistryError(f"엔티티 레지스트리에 없음: {eid} (assets/entities.yaml)")
        return self.entities[eid]

    def lookup(self, name: str) -> Entity:
        if name not in self.alias:
            raise RegistryError(f"엔티티 별칭 없음: {name!r} (assets/entities.yaml)")
        return self.entities[self.alias[name]]

    def of_kind(self, kind: str) -> dict[str, Entity]:
        return {k: e for k, e in self.entities.items() if e.kind == kind}

    @property
    def flags(self) -> set[str]:
        return {e.flag for e in self.entities.values() if e.kind == "country" and e.flag}

    def emblem_owner(self, emblem_id: str) -> Entity:
        for e in self.entities.values():
            if e.kind == "org" and e.emblem == emblem_id:
                return e
        raise RegistryError(f"휘장 {emblem_id} 를 가진 기관 엔티티 없음 (assets/entities.yaml)")


def _library_entities(manifest: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in manifest.get("people", []):
        pid = p["person_id"]
        names = [n for n in (p.get("name_ko"), p.get("name_en"), *p.get("aliases", [])) if n]
        out[pid] = dict(kind="person", names=names, library=pid, role_default=p.get("role", ""),
                        rights=f"library.{pid}")
    return out


def build_registry(data: EntitiesFile, manifest: dict) -> EntityRegistry:
    merged = _library_entities(manifest)
    lib_ids = set(merged)
    for eid, ein in data.entities.items():
        d = ein.model_dump(exclude_none=True)
        if ein.library is not None and ein.library not in lib_ids:
            raise RegistryError(f"{eid}: 라이브러리에 없는 person_id {ein.library}")
        base = merged.get(ein.library or eid, {}) if ein.kind == "person" else {}
        names = [*base.get("names", []), *[n for n in d.pop("names", []) if n not in base.get("names", [])]]
        merged[eid] = {**base, **{k: v for k, v in d.items() if v != ""}, "names": names}
        if "role_default" not in d or not d["role_default"]:
            merged[eid]["role_default"] = base.get("role_default", "")
    entities = {eid: Entity.model_validate({"id": eid, **d}) for eid, d in merged.items()}
    alias: dict[str, str] = {}
    for eid, e in entities.items():
        for n in e.names:
            if n in alias and alias[n] != eid:
                raise RegistryError(f"별칭 {n!r} 이 두 엔티티에 겹친다: {alias[n]}, {eid}")
            alias[n] = eid
    return EntityRegistry(entities, alias)


def load_entities(path: Path = ENTITIES_PATH, library: Path = LIBRARY_PATH) -> EntityRegistry:
    data = EntitiesFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    manifest = json.loads(library.read_text(encoding="utf-8")) if library.exists() else {"people": []}
    return build_registry(data, manifest)


def load_emblem_registry(path: Path = EMBLEM_REGISTRY_PATH) -> EmblemRegistry:
    """휘장 레지스트리(D-0029 작업 3). 파일이 없으면 빈 레지스트리 — 휘장 뱃지를 쓰면 렌더 전 오류가 된다."""
    if not path.exists():
        return EmblemRegistry(emblems={})
    return EmblemRegistry.model_validate_json(path.read_text(encoding="utf-8"))


def check_event_refs(events: list[dict], reg: EntityRegistry) -> list[str]:
    """연출이 참조한 인물 id·국기·휘장이 레지스트리에 있는지. 문제 목록(빈 목록 = 통과)."""
    errs: list[str] = []

    def walk(o: object):  # noqa: ANN202
        if isinstance(o, dict):
            yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                yield from walk(v)

    persons = reg.of_kind("person")
    portrait_ids = {e.portrait or e.library for e in persons.values()}
    for e in events:
        where = f"{e['type']} t0={e['t0']:.2f}"
        for d in walk(e):
            if d.get("pid") is not None and d["pid"] not in portrait_ids:
                errs.append(f"인물 {d['pid']} 미등재 ({where})")
            if isinstance(d.get("flag"), str) and d["flag"] not in reg.flags:
                errs.append(f"국기 {d['flag']} 미등재 국가 ({where})")
        if e["type"] == "badge" and e.get("kind") == "emblem":
            try:
                reg.emblem_owner(e["img"])
            except RegistryError as ex:
                errs.append(f"{ex} ({where})")
    return errs

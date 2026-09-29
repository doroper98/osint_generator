"""엔티티·휘장 레지스트리 데이터 계약 (v2.4.0, back_and_forth D-0029 작업 2·3, 07 §5·§6, 13).

- `assets/entities.yaml`: 인물·기관·국가 사전. 이름 별칭 → 엔티티 id. 인물은 저장소 라이브러리
  (`assets/library/library_manifest.json`)와 **조인**한다 — 라이브러리 인물은 자동 등재, yaml 은 보강만.
- 휘장 레지스트리 계약은 `schemas/emblem_models.py`.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.events import Accent

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EntityIn(_Strict):
    """`entities.yaml` 한 항목(사람이 쓰는 형식). 라이브러리 인물은 `library` 로 조인한다."""

    kind: Literal["person", "org", "country"]
    names: list[str] = Field(default_factory=list)
    flag: Optional[str] = Field(default=None, pattern=r"^[a-z]{2}$")
    portrait: Optional[str] = None      # 프로젝트 portraits/ id(= 뱃지 pid). 라이브러리 인물은 조인으로 채운다
    library: Optional[str] = None       # library_manifest person_id
    emblem: Optional[str] = None        # emblems/registry.json 키(org 전용)
    role_default: str = ""
    accent: Optional[Accent] = None
    note: Optional[str] = None          # v4.8.0 D-0109 — 사람용 메모(표기·연혁). 렌더에 쓰지 않는다
    rights: Optional[str] = None        # 권리 레지스트리 참조 "people.<pid>" · "emblems.<id>" · "library.<pid>" · "flags.<set>"


class Entity(EntityIn):
    """조인·검증이 끝난 엔티티."""

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    names: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _kind_fields(self) -> "Entity":
        if self.kind == "country" and self.flag is None:
            raise ValueError(f"국가 엔티티 {self.id}: flag 필요")
        if self.kind == "person" and self.portrait is None and self.library is None:
            raise ValueError(f"인물 엔티티 {self.id}: portrait 또는 library 필요")
        if self.kind == "org" and self.flag is None:
            raise ValueError(f"기관 엔티티 {self.id}: 대체 국기(flag) 필요 — 휘장 제한 시 국기로 대체(D5)")
        if self.kind != "org" and self.emblem is not None:
            raise ValueError(f"{self.id}: emblem 은 기관(org)만")
        if self.rights is None:
            raise ValueError(f"엔티티 {self.id}: rights 참조 필요(C9)")
        return self


class EntitiesFile(_Strict):
    schema_version: int = 1
    entities: dict[str, EntityIn]

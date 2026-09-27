"""엔딩 크레딧 데이터 (v2.1.0, render3 `credit_sections, credits`, 07 §7).

크레딧 문구는 프로젝트 `credits.yaml`에 있다. 인물 사진 라이선스는 권리 레지스트리(`rights_registry.json`)에서
`license_ref`로 읽는다 — 레지스트리에 없으면 오류(C9, 15 P6). 전 자산 자동 생성은 Phase 5.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreditItem(_Strict):
    main: str
    license: Optional[str] = None
    license_ref: Optional[str] = None  # rights_registry.people 의 pid
    license_suffix: str = ""

    @model_validator(mode="after")
    def _one_source(self) -> "CreditItem":
        if self.license is not None and self.license_ref is not None:
            raise ValueError(f"license 와 license_ref 는 함께 쓸 수 없다: {self.main!r}")
        return self


class CreditSection(_Strict):
    title: str
    column: Literal[0, 1]
    items: list[CreditItem] = Field(min_length=1)


class Credits(_Strict):
    schema_version: int = 1
    sections: list[CreditSection] = Field(min_length=1)


def load_credits(path: Path) -> Credits:
    return Credits.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def credit_sections(cr: Credits, rights: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    out = []
    for sec in cr.sections:
        items = []
        for it in sec.items:
            if it.license_ref is not None:
                people = rights.get("people", {})
                if it.license_ref not in people:
                    raise KeyError(f"권리 레지스트리에 인물 없음: {it.license_ref}")
                lic = people[it.license_ref]["license"] + it.license_suffix
            else:
                lic = (it.license or "") + it.license_suffix
            items.append((it.main, lic))
        out.append((sec.title, items))
    return out


def credit_lines(cr: Credits, rights: dict) -> list[str]:
    return [f"{sec}: {' / '.join(m + (' — ' + l if l else '') for m, l in items)}"
            for sec, items in credit_sections(cr, rights)]

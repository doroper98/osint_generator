"""장르 프로필 `genres/<genre>.yaml` — Pydantic 계약 (v4.2.0, docs/handoff/20 §1.2·§3, back_and_forth D-0081 작업 1).

장르 층(20 §1.2)을 선언하는 파일이다. 불변 층(20 §1.1)은 여기서 바꿀 수 없다 — 이 모델에는 그 자리가 없다.

이름 규칙(15 P10 — 미등록 이름 = 로드 오류):
- `stage.primary`·`secondary` ∈ `rules registries.stages`(구현됨). `status: proposed` 만 `registries.stages_planned` 도 허용.
- `primitives.reuse` ∈ registries 의 등록 요소(event_types ∪ panel_kinds ∪ badge_kinds ∪ primitives).
- `primitives.new` ∈ `registries.primitives`.
- `qa_extra` ∈ 결정적 검사 id(`engine.checks.HARD ∪ WARN`). `status: proposed` 만 `rules qa_checks.planned` 도 허용.
- `color_semantics` 값 = `#rrggbb`, `rgba(r,g,b,a)`(r·g·b 0~255, a 0~1), 또는 색 토큰 이름(`registries.accents`).
- `status: approved` 는 사용자 승인 뒤에만(20 §3). approved 가 planned 를 참조하면 오류.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

GenreStatus = Literal["proposed", "approved"]
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
RGBA_RE = re.compile(r"^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9]*\.?[0-9]+)\s*\)$")
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimelineLane(_Strict):
    """시간축 무대의 레인(20 §3 stage.timeline.lanes). 무대 구현은 G3 — 여기서는 모양만 고정한다."""

    id: str
    label: str
    kind: Literal["step", "line", "pins"]
    unit: Optional[str] = None


class TimelineSettings(_Strict):
    lanes: list[TimelineLane] = Field(min_length=1)


class GenreStage(_Strict):
    """주 무대 1 + 보조 무대(20 §2.2-1) + 무대별 설정(그 무대 이름을 키로)."""

    primary: str
    secondary: list[str] = Field(default_factory=list)
    mercator: Optional[dict[str, Any]] = None
    timeline: Optional[TimelineSettings] = None
    chart_wall: Optional[dict[str, Any]] = None
    flow: Optional[dict[str, Any]] = None
    structure: Optional[dict[str, Any]] = None
    document: Optional[dict[str, Any]] = None

    def names(self) -> list[str]:
        return [self.primary, *self.secondary]

    def settings(self) -> dict[str, object]:
        return {k: v for k in ("mercator", "timeline", "chart_wall", "flow", "structure", "document") if (v := getattr(self, k)) is not None}

    @model_validator(mode="after")
    def _shape(self) -> "GenreStage":
        if len(set(self.names())) != len(self.names()):
            raise ValueError(f"stage: 무대 이름 중복 {self.names()}")
        stray = sorted(set(self.settings()) - set(self.names()))
        if stray:
            raise ValueError(f"stage: 주·보조 무대가 아닌 무대의 설정 {stray}")
        return self


class GenrePrimitives(_Strict):
    reuse: list[str] = Field(min_length=1)
    new: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _shape(self) -> "GenrePrimitives":
        for k in ("reuse", "new"):
            v = getattr(self, k)
            if len(set(v)) != len(v):
                raise ValueError(f"primitives.{k} 중복")
        both = sorted(set(self.reuse) & set(self.new))
        if both:
            raise ValueError(f"primitives: reuse 와 new 에 같은 이름 {both}")
        return self


class GenreDataSources(_Strict):
    required_fields: list[str] = Field(min_length=1)


class GenreNarration(_Strict):
    define_terms_once: bool = False
    avoid: list[str] = Field(default_factory=list)


class GenreMedia(_Strict):
    preferred: list[str] = Field(min_length=1)


class GenreProfile(_Strict):
    """장르 프로필 최상위 모델(20 §3)."""

    schema_version: Literal[1] = 1
    genre: str
    status: GenreStatus
    stage: GenreStage
    color_semantics: dict[str, str] = Field(min_length=1)
    primitives: GenrePrimitives
    badges: dict[str, Literal["from_library", "rights_check"]] = Field(default_factory=dict)
    data_sources: Optional[GenreDataSources] = None
    narration: Optional[GenreNarration] = None
    media: Optional[GenreMedia] = None
    qa_extra: list[str] = Field(default_factory=list)

    @field_validator("genre")
    @classmethod
    def _name(cls, v: str) -> str:
        if not NAME_RE.match(v):
            raise ValueError(f"genre 이름은 영문 소문자 snake_case: {v!r}")
        return v

    def elements(self) -> set[str]:
        """이 장르에서 연출이 쓸 수 있는 요소 이름(reuse ∪ new) — checks genre_elements 의 허용 집합."""
        return set(self.primitives.reuse) | set(self.primitives.new)

    @model_validator(mode="after")
    def _registries(self) -> "GenreProfile":
        from rules import load_rules  # noqa: PLC0415

        rules = load_rules()
        reg = rules.registries
        proposed = self.status == "proposed"
        errs: list[str] = []
        stages_ok = set(reg.stages) | (set(reg.stages_planned) if proposed else set())
        for s in self.stage.names():
            if s not in stages_ok:
                why = "구현 전(stages_planned) — approved 는 등록 무대만" if s in reg.stages_planned else "레지스트리에 없음"
                errs.append(f"stage {s!r}: {why}")
        if len(self.stage.secondary) > rules.stage.max_secondary:
            errs.append(f"stage.secondary {len(self.stage.secondary)}개 > rules stage.max_secondary {rules.stage.max_secondary}")
        registered = registered_elements()
        errs += [f"primitives.reuse {x!r}: 등록 요소가 아님(registries event_types·panel_kinds·badge_kinds·primitives)"
                 for x in self.primitives.reuse if x not in registered]
        errs += [f"primitives.new {x!r}: registries.primitives 에 없음" for x in self.primitives.new if x not in reg.primitives]
        checks_ok = check_ids() | (set(rules.qa_checks.planned) if proposed else set())
        for q in self.qa_extra:
            if q not in checks_ok:
                why = "G3 예정(qa_checks.planned) — approved 는 구현된 검사만" if q in rules.qa_checks.planned else "결정적 검사 id 가 아님"
                errs.append(f"qa_extra {q!r}: {why}")
        for k, v in self.color_semantics.items():
            if not (HEX_RE.match(v) or _rgba_ok(v) or v in reg.accents):
                errs.append(f"color_semantics.{k} {v!r}: #rrggbb · rgba(r,g,b,a) · 색 토큰({reg.accents}) 중 하나가 아님")
        if errs:
            raise ValueError(f"장르 프로필 {self.genre!r}({self.status}) 점검 실패: " + "; ".join(errs))
        return self


def _rgba_ok(v: str) -> bool:
    m = RGBA_RE.match(v)
    return bool(m) and all(int(m.group(i)) <= 255 for i in (1, 2, 3)) and float(m.group(4)) <= 1


def registered_elements() -> set[str]:
    """등록 요소 이름 전부(연출이 쓸 수 있는 이벤트·패널·뱃지·프리미티브 종류)."""
    from rules import load_rules  # noqa: PLC0415

    reg = load_rules().registries
    return set(reg.event_types) | set(reg.panel_kinds) | set(reg.badge_kinds) | set(reg.primitives)


def check_ids() -> set[str]:
    """결정적 검사 id(engine.checks HARD ∪ WARN) — qa_extra 가 참조할 수 있는 이름."""
    from engine.checks import HARD, WARN  # noqa: PLC0415

    return set(HARD) | set(WARN)


__all__ = ["GenreProfile", "GenreStage", "GenreStatus", "TimelineLane", "check_ids", "registered_elements"]

"""원고(script.yaml)와 타임라인(plan.json) 계약 (v2.1.0, docs/handoff/02 §2.1·§2.2).

- `Script`: 사람(또는 원고 LLM)이 쓰는 입력. 장면 수·길이는 고정하지 않는다(G4-13, rules script_schema.scene_count=free).
- `Plan`: plan 단계 출력. 문장별 음성 길이로 t0/t1 을 계산한 결과.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DATE_RE = re.compile(r"^\d{4}(\.\d{2}(\.\d{2})?)?$")  # rules script_schema.date_formats


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MediaCue(_Strict):
    """문장의 미디어 비트(14 §10.3-1, v2.5.5 optional). 자산을 정했으면 asset_id(미디어 레지스트리 mid),
    아직이면 query(수집 검색어). at 은 등장 단어(자막 텍스트 안), dur 는 표시 초."""

    kind: Literal["photo", "clip", "cutout", "article"]
    asset_id: Optional[str] = None
    query: Optional[str] = None
    at: Optional[str] = None
    dur: Optional[float] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _one_ref(self) -> "MediaCue":
        if (self.asset_id is None) == (self.query is None):
            raise ValueError("media 는 asset_id 와 query 중 정확히 하나")
        return self


class Sentence(_Strict):
    date: str
    text: str
    tts: Optional[str] = None
    emphasis: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    media: Optional[MediaCue] = None   # v2.5.5 optional(C3 호환) — 14 §10.3-1

    @field_validator("date")
    @classmethod
    def _date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError(f"날짜 형식 YYYY / YYYY.MM / YYYY.MM.DD 만 허용: {v!r}")
        return v

    @model_validator(mode="after")
    def _emphasis_substring(self) -> "Sentence":
        for e in self.emphasis:
            if e not in self.text:
                raise ValueError(f"강조어가 자막 텍스트에 없다: {e!r} ⊄ {self.text!r}")
        if self.media and self.media.at and self.media.at not in self.text:
            raise ValueError(f"media.at 단어가 자막 텍스트에 없다: {self.media.at!r}")
        return self


class Scene(_Strict):
    id: str
    sentences: list[Sentence] = Field(min_length=1)
    # v3.4.0 D-0060 작업 4(10 §7-2) — 장면 음악 강도 힌트(0~1, 선택). 연출가(LLM)가 sound.intensity 를 만들 때 읽는 입력일 뿐,
    # 코드는 direction 에 자동 주입하지 않는다(P8).
    music_intensity: Optional[float] = Field(default=None, ge=0, le=1)


class Script(_Strict):
    schema_version: int = 1
    title: str
    subtitle: str
    date: str
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_scene_ids(self) -> "Script":
        ids = [s.id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError(f"장면 id 중복: {ids}")
        return self


class PlanAlignment(_Strict):
    """v5.16.0 optional(D-0164 §5-4) — 이 문장 정렬의 출처·문장 점수·정렬 시간(provenance 로 전달). edge 는 출처만."""
    source: str
    score_mean: Optional[float] = None
    elapsed_ms: Optional[int] = None


class PlanSentence(_Strict):
    sid: str
    scene: str
    date: str
    text: str
    tts: str
    segments: list[tuple[str, int]]
    mp3: str
    npy: str
    dur: float
    t0: float
    t1: float
    trim_offset: Optional[float] = None  # v2.3.0 optional(C3 호환) — 원본 mp3 앞에서 잘라낸 초. 정렬 시각 보정용
    chunks: Optional[list[str]] = None   # v5.11.0 optional(D-0152) — Supertonic 이 문장을 나눈 조각(사이 무음 tts.supertonic.silence_sec)
    alignment: Optional[PlanAlignment] = None   # v5.16.0 optional(D-0164 §5-4) — 정렬 출처·점수·시간


class Card(_Strict):
    kind: Literal["title", "end"]
    t0: float
    t1: float


class Plan(_Strict):
    sentences: list[PlanSentence]
    cards: list[Card]
    scene_start: dict[str, float]
    total: float
    voice: str
    title: str
    subtitle: str
    date: str
    tts_resynthesized: list[str] = Field(default_factory=list)  # v2.3.0 optional — 정렬이 없어 다시 합성한 문장 id(D34)
    lint_waived: Optional[list[dict[str, str]]] = None  # v5.17.0 optional(D-0168) — 면제로 통과한 린트 [{kind, sid, decided_by}]


class Fact(_Strict):
    """사실 한 건(17 §5.1). contested 면 양측(sides) 필수 — 논쟁 사실은 양측을 같은 무게로."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    date: Optional[str] = None
    place: Optional[str] = None
    actors: list[str] = Field(default_factory=list)
    numbers: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(min_length=1)          # 출처 없는 사실 금지
    confidence: Literal["low", "medium", "high"]
    contested: bool = False
    sides: Optional[list[str]] = None

    @model_validator(mode="after")
    def _sides(self) -> "Fact":
        if self.contested and (not self.sides or len(self.sides) < 2):
            raise ValueError(f"{self.id}: contested 사실은 sides 2개 이상(양측)")
        return self


class Facts(_Strict):
    """사실 목록(17 §5.1) — ResearchWorker 출력 `facts.json`(v3.2.0 D-0051 작업 7). source_ids = claims.json claim_id."""

    schema_version: int = 1
    facts: list[Fact] = Field(min_length=1)


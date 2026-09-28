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

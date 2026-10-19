"""원고(script.yaml)와 타임라인(plan.json) 계약 (v2.1.0, docs/handoff/02 §2.1·§2.2).

- `Script`: 사람(또는 원고 LLM)이 쓰는 입력. 장면 수·길이는 고정하지 않는다(G4-13, rules script_schema.scene_count=free).
- `Plan`: plan 단계 출력. 문장별 음성 길이로 t0/t1 을 계산한 결과.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DATE_RE = re.compile(r"^\d{4}(\.\d{2}(\.\d{2})?)?$")  # rules script_schema.date_formats


from script.tts.prosody import FinalFallRecord  # noqa: E402 — v5.20.0 plan row prosody 기록 모델

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
    # v7.4.0 D-0229 §2.2·§2.9(UF-104·105·115) optional — 문장의 구조 역할. intro = 막 도입(막전), outro = 막 정리(막후),
    # bridge = 시점(시간·무대) 전환 고지 문장(앞에 rules transition.bridge_pause_sec 호흡). 린트 [transition-bridge]·[act-frame].
    # background = 회고·배경 문장(장면 날짜와 멀어도 [transition-in-scene] 경고 없음, D-0230 §2)
    role: Optional[Literal["intro", "outro", "bridge", "background"]] = None

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
    # v7.4.0 D-0229 §2.2(UF-105) optional — 이야기 무대(지리·전장 이름, 예 "러시아"·"걸프"). 앞 장면과 다르면 무대 전환 = 린트 [transition-bridge]
    stage: Optional[str] = None
    # v7.4.0 D-0229 §2.9(UF-104·115) optional — 장면 종류. act(기본) 만 [act-frame](도입·정리 문장 수)을 본다. cold = 콜드 오픈, ending = 마무리
    kind: Literal["cold", "act", "ending"] = "act"


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
    """v5.16.0 optional(D-0164 §5-4) — 이 문장 정렬의 출처·문장 점수·정렬 시간(provenance 로 전달)."""
    source: str
    score_mean: Optional[float] = None
    elapsed_ms: Optional[int] = None
    realigned_from: Optional[str] = None   # v6.0.1 optional(D-0214) — 옛 음성 보관본을 MMS 로 다시 정렬했을 때 옛 출처(음성은 그대로)


class PlanProsody(_Strict):
    """v5.20.0 optional(D-0175) — 이 문장 음성에 적용한 운율 보정 기록(provenance features.prosody 로 집계)."""
    final_fall: FinalFallRecord


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
    prosody: Optional[PlanProsody] = None       # v5.20.0 optional(D-0175) — 문장 끝 억양 보정 기록
    role: Optional[Literal["intro", "outro", "bridge", "background"]] = None   # v7.4.0 optional(D-0229 §2.2) — 원고 Sentence.role 그대로


class Card(_Strict):
    kind: Literal["title", "end"]
    t0: float
    t1: float


class PlanTransition(_Strict):
    """v7.4.0 D-0229 §2.2(UF-105) — 시점 전환 한 곳. bridge 문장 앞에 넣은 호흡(음악만) 구간."""

    sid: str                  # bridge 문장
    pause_t0: float           # 호흡 시작(앞 문장 끝 + 문장 간격)
    pause_sec: float          # rules transition.bridge_pause_sec
    kind: list[Literal["stage", "date_jump"]] = Field(default_factory=list)   # 린트가 본 전환 종류(없으면 원고가 명시한 bridge)


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
    transitions: list[PlanTransition] = Field(default_factory=list)   # v7.4.0 optional(D-0229 §2.2) — provenance transitions[]


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


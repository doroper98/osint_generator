"""새 엔진 데이터 계약 모음 (v2.1.0, D-0010 §1-8, 02 §2).

정의 위치는 각 패키지다 — 원고·타임라인은 `script/schema.py`, 카메라 키는 `engine/camera.py`,
이벤트는 `engine/events.py`. 여기서는 그것들을 한곳에서 import 할 수 있게 다시 내보내고,
자산 계약(Tier·RightsRegistry·MediaRegistry)과 CLI 출력(StageResult, 16 §4)을 정의한다.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from engine.camera import CamKey
from engine.events import (ArticleEvent, BadgeEvent, BarrierEvent, BoomEvent, CardEvent, ClipEvent, CountryEvent,
                           CutoutEvent, DipEvent, MarkerEvent, PanelPrecedent, PanelRefusal, PanelStatement,
                           PanelTimeline, PanelVersus, PhotoEvent, RouteEvent, ShipsEvent, TankerLoopEvent)
from script.schema import Card, Plan, PlanSentence, Scene, Script, Sentence

__all__ = [
    "ArticleEvent", "BadgeEvent", "BarrierEvent", "BoomEvent", "CamKey", "Card", "CardEvent", "ClipEvent",
    "CountryEvent", "CutoutEvent", "DipEvent", "MarkerEvent", "MediaEntry", "MediaRegistry", "PanelPrecedent",
    "PanelRefusal", "PanelStatement", "PanelTimeline", "PanelVersus", "PhotoEvent", "Plan", "PlanSentence",
    "RightsRegistry", "RouteEvent", "Scene", "Script", "Sentence", "ShipsEvent", "StageResult", "TankerLoopEvent",
    "Tier",
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Tier(_Strict):
    """지형 티어 (02 §2.5 tiers.pkl 한 항목)."""

    lon0: float
    lon1: float
    lat0: float
    lat1: float
    ppd: int
    tiles: str
    z: int
    levels: list[int] = Field(min_length=1)


class PersonRights(_Strict):
    src: str
    license: str = Field(min_length=1)
    artist: str
    url: str
    title: Optional[str] = None


class EmblemRights(_Strict):
    license: str = Field(min_length=1)
    url: str
    title: str
    restrictions: str = ""


class RightsRegistry(_Strict):
    """권리 레지스트리 (02 §2.5, C9). 뱃지가 쓰는 인물·휘장은 전부 여기에 있어야 한다."""

    people: dict[str, PersonRights] = Field(default_factory=dict)
    emblems: dict[str, EmblemRights] = Field(default_factory=dict)


class MediaEntry(_Strict):
    kind: Literal["photo", "video", "cutout", "article"]  # 레지스트리 어휘(video = clip 이벤트)
    title: str
    license: str = Field(min_length=1)
    author: str
    date: str
    url: str
    caption: str
    file_note: str
    duration: Optional[float] = None


class MediaRegistry(RootModel[dict[str, MediaEntry]]):
    """미디어 레지스트리 (14 §6). 키 = 이벤트의 `mid`."""


class StageResult(_Strict):
    """엔진 CLI 표준 출력 (16 §4). drops 가 있으면 ok=False(15 P6)."""

    ok: bool
    stage: str
    artifacts: dict[str, str] = Field(default_factory=dict)
    provenance: Optional[dict] = None
    drops: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)  # v2.3.0 optional — ok 를 막지 않는 알림(원고 린트 경고 등)

    @model_validator(mode="after")
    def _drops_fail(self) -> "StageResult":
        if self.ok and (self.drops or self.errors):
            raise ValueError("drops 또는 errors 가 있으면 ok 일 수 없다")
        return self

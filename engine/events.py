"""연출 이벤트 계약 — 타입별 Pydantic 모델 (v2.1.0, 02 §2.4, 15 P10).

`direction.py`가 만든 이벤트(dict)는 렌더 전에 전부 여기서 검증된다. 모르는 필드·빠진 필드·
레지스트리에 없는 색 이름은 렌더 시작 전 오류다(`extra="forbid"`, 15 P6).
패널 문구는 이벤트 필드(D25), 패널 좌표·크기·타이밍·색은 `engine/panels/*.py`.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from engine.style import C
from rules import load_rules

_ACCENTS = frozenset(load_rules().registries.accents)


def _accent(v: str) -> str:
    if v not in _ACCENTS:
        raise ValueError(f"레지스트리에 없는 accent: {v!r} (rules registries.accents)")
    return v


def _color(v: str) -> str:
    if v not in C:
        raise ValueError(f"스타일 색 이름 아님: {v!r} (engine/style.py C)")
    return v


Accent = Annotated[str, AfterValidator(_accent)]
ColorName = Annotated[str, AfterValidator(_color)]
LonLat = tuple[float, float]


class _Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    t0: float
    t1: float

    @model_validator(mode="after")
    def _order(self) -> "_Event":
        if self.t1 < self.t0:
            raise ValueError(f"{self.type}: t1({self.t1}) < t0({self.t0})")
        return self


# ------------------------------------------------------------------ 지도 레이어
class MarkerEvent(_Event):
    type: Literal["marker"]
    lon: float
    lat: float
    label: str
    sub: str = ""
    side: Literal["right", "left", "top", "bottom"] = "right"
    hl: bool = False
    icon: Literal["dot", "boom"] = "dot"


class RouteEvent(_Event):
    type: Literal["route"]
    pts: list[LonLat] = Field(min_length=2)
    grow: float
    col: ColorName
    ship: bool = False
    dashed: bool = False
    glow_only: bool = False
    label: str = ""


class TankerLoopEvent(_Event):
    type: Literal["tanker_loop"]
    pts: list[LonLat] = Field(min_length=2)


class BarrierEvent(_Event):
    type: Literal["barrier"]
    p0: LonLat
    p1: LonLat
    label: str


class ShipsEvent(_Event):
    type: Literal["ships"]
    box: tuple[float, float, float, float]  # lon0, lon1, lat0, lat1
    n: int = Field(gt=0)
    seed: int


class BoomEvent(_Event):
    type: Literal["boom"]
    lon: float
    lat: float


class CountryEvent(_Event):
    type: Literal["country"]
    codes: list[str] = Field(min_length=1)
    col: ColorName
    a: float = Field(ge=0, le=1)


class BadgeEvent(_Event):
    type: Literal["badge"]
    lon: float
    lat: float
    kind: Literal["person", "flag", "emblem"]
    pid: Optional[str] = None
    flag: Optional[str] = None
    img: Optional[str] = None
    R: float = 30
    label: str = ""
    role: Optional[str] = None
    accent: Accent = "gold"
    side: Optional[Literal["right"]] = None

    @model_validator(mode="after")
    def _kind_fields(self) -> "BadgeEvent":
        need = {"person": ("pid", "flag"), "flag": ("flag",), "emblem": ("img",)}[self.kind]
        missing = [f for f in need if getattr(self, f) is None]
        if missing:
            raise ValueError(f"badge kind={self.kind} 에 필요한 필드 없음: {missing}")
        return self


class CutoutEvent(_Event):
    type: Literal["cutout"]
    img: str
    lon: float
    lat: float
    w: float
    label: str
    sub: str
    mid: str


# ------------------------------------------------------------------ 화면 레이어
class DipEvent(_Event):
    type: Literal["dip"]
    under: bool = False


class CardEvent(_Event):
    type: Literal["card"]
    tag: str
    lines: list[str] = Field(default_factory=list)
    bigs: list[tuple[str, str]] = Field(default_factory=list)
    accent: Accent
    src: Optional[str] = None
    quote: bool = False
    y: Optional[float] = None


class PhotoEvent(_Event):
    type: Literal["photo"]
    img: str
    x: float
    y: float
    w: float
    caption: str
    credit: str = Field(min_length=1)
    mid: str


class ClipEvent(_Event):
    type: Literal["clip"]
    clip: str
    x: float
    y: float
    w: float
    caption: str
    credit: str = Field(min_length=1)
    mid: str


class ArticleEvent(_Event):
    type: Literal["article"]
    pub: str
    date: str
    headline: str
    hl: Optional[str] = None
    sub: str
    note: str

    @model_validator(mode="after")
    def _hl_in_headline(self) -> "ArticleEvent":
        if self.hl and self.hl not in self.headline:
            raise ValueError(f"article hl 이 헤드라인에 없다: {self.hl!r}")
        return self


# ------------------------------------------------------------------ 패널 (문구 = 데이터, D25)
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimedText(_Strict):
    text: str
    t0: float
    t1: float


class PanelActor(_Strict):
    pid: str
    flag: str
    label: str
    role: str
    accent: Accent


class RefusalRow(_Strict):
    flag: str
    label: str
    t_refuse: float
    hl: bool = False


class _Panel(_Event):
    type: Literal["panel"]
    title: str


class PanelRefusal(_Panel):
    kind: Literal["refusal"]
    actor: PanelActor
    rows: list[RefusalRow] = Field(min_length=1)
    demand_label: str
    refuse_label: str
    quote_bottom: TimedText
    quote_actor: TimedText


class FlagLabel(_Strict):
    flag: str
    label: str


class StatementJoiner(_Strict):
    flag: str
    label: str
    role: str
    t_join: float


class PanelStatement(_Panel):
    kind: Literal["statement"]
    subtitle: Optional[str] = None
    signers: list[FlagLabel] = Field(min_length=1)
    joiner: StatementJoiner


class TimelineBand(_Strict):
    start: str
    end: str
    label: str
    col: ColorName
    t_show: float


class TimelineItem(_Strict):
    date: str
    label: str
    col: ColorName
    side: Literal[-2, -1, 1, 2]
    t: float
    dim: bool = False


class PanelTimeline(_Panel):
    kind: Literal["timeline"]
    subtitle: Optional[str] = None
    start: str
    end: str
    band: Optional[TimelineBand] = None
    events: list[TimelineItem] = Field(min_length=1)


class PrecedentPerson(_Strict):
    pid: str
    flag: str
    caption: str


class PrecedentCard(_Strict):
    year: str
    title: str
    lines: list[str]
    t0: float
    hl: bool = False
    person: Optional[PrecedentPerson] = None


class PanelPrecedent(_Panel):
    kind: Literal["precedent"]
    subtitle: Optional[str] = None
    cards: list[PrecedentCard] = Field(min_length=1, max_length=4)


class VersusItem(_Strict):
    text: str
    t: float


class VersusSide(_Strict):
    title: str
    items: list[VersusItem] = Field(min_length=1)
    src: str


class PanelVersus(_Panel):
    kind: Literal["versus"]
    sides: list[VersusSide] = Field(min_length=2, max_length=2)  # 양측 같은 무게(G4)

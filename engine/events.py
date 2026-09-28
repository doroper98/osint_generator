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


class _Panel(_Event):
    type: Literal["panel"]
    title: str


class RelationNode(_Strict):
    """관계 패널 노드 = 뱃지 하나. group 이 배치 열을 정한다(요구자 한쪽, 대상 세로 열 — 08 §3 규칙 3)."""

    id: str
    group: Literal["source", "target"]
    kind: Literal["person", "flag", "emblem"]
    pid: Optional[str] = None
    flag: Optional[str] = None
    img: Optional[str] = None
    label: str
    role: Optional[str] = None
    accent: Accent = "muted"

    @model_validator(mode="after")
    def _kind_fields(self) -> "RelationNode":
        need = {"person": ("pid", "flag"), "flag": ("flag",), "emblem": ("img",)}[self.kind]
        missing = [f for f in need if getattr(self, f) is None]
        if missing:
            raise ValueError(f"relation node kind={self.kind} 에 필요한 필드 없음: {missing}")
        return self


def _edge_style(v: str) -> str:
    styles = load_rules().panels.relation.styles
    if v not in styles:
        raise ValueError(f"관계선 스타일 {v!r} 는 rules panels.relation.styles 에 없다: {sorted(styles)}")
    return v


EdgeStyle = Annotated[str, AfterValidator(_edge_style)]


class RelationEdge(_Strict):
    src: str
    dst: str
    style: EdgeStyle


class RelationStateChange(_Strict):
    """선 하나의 상태 변화 — at 은 단어 앵커 시각(at_word, 08 §3 규칙 5)."""

    src: str
    dst: str
    at: float
    style: EdgeStyle
    label: str = ""


class RelationQuote(_Strict):
    text: str
    t0: float
    t1: float
    at: Literal["bottom", "source"]


class PanelRelation(_Panel):
    """관계 패널(08 §3·§11-2). v3 P_refusal 은 이 모델의 한 인스턴스다."""

    kind: Literal["relation"]
    subtitle: Optional[str] = None
    nodes: list[RelationNode] = Field(min_length=2)
    edges: list[RelationEdge] = Field(min_length=1)
    state_changes: list[RelationStateChange] = Field(default_factory=list)
    edge_label: Optional[str] = None
    quotes: list[RelationQuote] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refs(self) -> "PanelRelation":
        ids = [n.id for n in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError(f"relation 노드 id 중복: {ids}")
        pairs = {(e.src, e.dst) for e in self.edges}
        for e in self.edges:
            for end in (e.src, e.dst):
                if end not in ids:
                    raise ValueError(f"relation 선 끝 {end!r} 가 노드에 없다")
        for c in self.state_changes:
            if (c.src, c.dst) not in pairs:
                raise ValueError(f"상태 변화 {c.src}→{c.dst} 에 해당하는 선이 없다")
        if any(q.at == "source" for q in self.quotes) and not any(n.group == "source" for n in self.nodes):
            raise ValueError("quote at=source 인데 source 노드가 없다")
        return self


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
    side: Optional[Literal[-3, -2, -1, 1, 2, 3]] = None   # 없으면 자동 층 배치(D-0032 작업 3)
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

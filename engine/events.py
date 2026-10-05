"""연출 이벤트 계약 — 타입별 Pydantic 모델 (v2.1.0, 02 §2.4, 15 P10).

`direction.yaml`(engine/direction)이 만든 이벤트(dict)는 렌더 전에 전부 여기서 검증된다. 모르는 필드·빠진 필드·
레지스트리에 없는 색 이름은 렌더 시작 전 오류다(`extra="forbid"`, 15 P6).
패널 문구는 이벤트 필드(D25), 패널 좌표·크기·타이밍·색은 `engine/panels/*.py`.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

import re

from engine.style import C
from rules import load_rules

DATE_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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
    """지점 마커. 지도 앵커 lon·lat, 또는 시간축 핀 앵커 date(YYYY-MM-DD)·lane(레인 id) — 둘 중 하나(v4.3.0 D-0084 작업 4·D-0085).
    어느 무대 앵커인지는 attach_world 가 무대에 물어 검사한다(다른 무대의 키 = 오류)."""

    DROP_NONE: ClassVar[tuple[str, ...]] = ("lon", "lat", "date", "lane")   # 쓰지 않은 무대의 앵커 쌍은 dict 에 남기지 않는다(지도 이벤트 dict = v4.2.0 과 같음)

    type: Literal["marker"]
    lon: Optional[float] = None
    lat: Optional[float] = None
    date: Optional[str] = None
    lane: Optional[str] = None
    label: str
    sub: str = ""
    side: Literal["right", "left", "top", "bottom"] = "right"
    hl: bool = False
    icon: Literal["dot", "boom"] = "dot"

    @model_validator(mode="after")
    def _anchor(self) -> "MarkerEvent":
        geo = (self.lon is not None, self.lat is not None)
        tl = (self.date is not None, self.lane is not None)
        if not ((all(geo) and not any(tl)) or (all(tl) and not any(geo))):
            raise ValueError("marker 앵커는 lon·lat(지도) 또는 date·lane(시간축) 중 한 쌍")
        if self.date is not None and not DATE_ISO_RE.match(self.date):
            raise ValueError(f"marker date 는 YYYY-MM-DD: {self.date!r}")
        return self



class SeriesEvent(_Event):
    """시리즈 레이어(v4.3.0 D-0084 작업 4) — 값은 데이터 레코드 data/series/<series_id> 에서만(연출은 숫자를 주지 않는다, 20 §5.1).
    시간축 무대 전용. key·axis·slot 은 load_project 가 채운다(레인 안 순번 — 연출이 쓰면 오류)."""

    type: Literal["series"]
    lane: str
    series_id: str
    style: Literal["step", "line", "band"]
    color_by: Literal["fixed", "change"] = "fixed"   # v4.4.0 D-0091 ② — change: 레코드 값 변화로 달마다 장르 색 의미 hike·cut·hold(코드 계산)
    upper_id: Optional[str] = None   # v4.4.0 D-0090 작업 2 — band: series_id = 아래 끝 레코드, upper_id = 위 끝 레코드(목표 범위 띠)
    grow: bool = True
    col: ColorName = "gold"
    key: Optional[int] = None      # 코드가 채움(load_project.prepare_series)
    axis: Optional[bool] = None
    slot: Optional[int] = None

    @model_validator(mode="after")
    def _band(self) -> "SeriesEvent":
        if (self.style == "band") != (self.upper_id is not None):
            raise ValueError("series: style band 는 upper_id(위 끝 레코드)가 필요하고, step·line 은 upper_id 를 쓰지 않는다")
        if self.upper_id == self.series_id:
            raise ValueError("series band: upper_id 가 series_id 와 같다")
        return self

    def record_ids(self) -> list[str]:
        return [self.series_id] + ([self.upper_id] if self.upper_id else [])


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
    """뱃지. 지도 앵커 lon·lat, 또는 시간축 앵커 date·lane(v4.4.0 D-0090 작업 4 — 배치 슬롯이 시간축에서 date·lane 을 돌려준다). 한 쌍만."""

    DROP_NONE: ClassVar[tuple[str, ...]] = ("lon", "lat", "date", "lane", "over_panel", "screen")   # 쓰지 않은 앵커 쌍·패널 위 자리는 dict 에 남기지 않는다(지도 뱃지 dict = v4.3.0 과 같음)

    type: Literal["badge"]
    lon: Optional[float] = None
    lat: Optional[float] = None
    date: Optional[str] = None
    lane: Optional[str] = None
    kind: Literal["person", "flag", "emblem"]
    pid: Optional[str] = None
    flag: Optional[str] = None
    img: Optional[str] = None
    R: Optional[float] = None        # v4.8.0 D-0101 §1 — 없으면 인물은 적응 크기, 국기·휘장은 rules badge.R_other(옛 기본 30 리터럴)
    label: str = ""
    role: Optional[str] = None
    accent: Accent = "gold"
    side: Optional[Literal["right"]] = None
    over_panel: Optional[bool] = None                     # v4.8.0 D-0104 D2(c) — 배치 슬롯(panel_badge)이 채운다: 패널 층 위, 화면 고정
    screen: Optional[tuple[float, float]] = None

    @model_validator(mode="after")
    def _anchor(self) -> "BadgeEvent":
        geo = (self.lon is not None, self.lat is not None)
        tl = (self.date is not None, self.lane is not None)
        if self.over_panel and self.screen is not None and not any(geo) and not any(tl):
            return self   # v5.1.0 D-0123 — backdrop 무대 화면 고정 뱃지(앵커 없음, 배치 슬롯이 채운다)
        if not ((all(geo) and not any(tl)) or (all(tl) and not any(geo))):
            raise ValueError("badge 앵커는 lon·lat(지도) 또는 date·lane(시간축) 중 한 쌍 — 시간축에서는 place 슬롯을 쓴다")
        if self.date is not None and not DATE_ISO_RE.match(self.date):
            raise ValueError(f"badge date 는 YYYY-MM-DD: {self.date!r}")
        return self

    @model_validator(mode="after")
    def _kind_fields(self) -> "BadgeEvent":
        need = {"person": ("pid", "flag"), "flag": ("flag",), "emblem": ("img",)}[self.kind]
        missing = [f for f in need if getattr(self, f) is None]
        if missing:
            raise ValueError(f"badge kind={self.kind} 에 필요한 필드 없음: {missing}")
        return self


class CutoutEvent(_Event):
    """지도 컷아웃 — 이미지·라벨·출처 줄은 미디어 레지스트리에서만(D-0036, 15 P3)."""

    type: Literal["cutout"]
    mid: str
    lon: float
    lat: float
    w: float


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


class CascadeItem(BaseModel):
    """겹침 카드 카드 하나 — at = 등장 시각(앵커는 direction 이 초로 푼다). flag = 국기 코드(좌상단 원). 문구는 원고 문장의 사실만."""

    model_config = ConfigDict(extra="forbid")

    at: float
    flag: str
    date: str = Field(min_length=1)
    title: str = Field(min_length=1)
    line: Optional[str] = None
    accent: Accent = "gold"


class CascadeEvent(_Event):
    """v5.2.0 겹침 카드(cascade — 사용자 제안·재구성 2026-10-01, v5.3.0 D-0139 채택 — 사용자 결정 D116·D117). 지도 배경은 고정한 채 사건 카드를 왼쪽부터 비스듬히 겹쳐 쌓는다.
    지금 말하는 사건 = 맨 앞·크게, 언급이 지나간 사건 = 뒤로 물러나 작아지고 앞 카드에 덮여 국기·날짜만 보인다(engine/cascade.py).
    items 는 at 오름차순. 뒤 카드가 rules cascade.max_back 을 넘으면 가장 오래된 카드가 왼쪽으로 밀려 나간다."""

    type: Literal["cascade"]
    items: list[CascadeItem] = Field(min_length=1)

    @model_validator(mode="after")
    def _items(self) -> "CascadeEvent":
        ats = [i.at for i in self.items]
        if ats != sorted(ats):
            raise ValueError("cascade items 는 at 오름차순이어야 한다(왼쪽부터 쌓인다)")
        if not (self.t0 - 0.05 <= ats[0] and ats[-1] <= self.t1):
            raise ValueError(f"cascade items at {ats[0]:.2f}~{ats[-1]:.2f} 가 이벤트 구간 {self.t0:.2f}~{self.t1:.2f} 밖")
        return self


class QuoteEvent(_Event):
    """v5.4.0 인물 발언 인용(정규 — 사용자 결정 2026-10-02, engine/quote.py). 오른쪽 위 카드 대신
    지도 위 덮개 + 가운데 초상(pid, 없으면 국기) + 세리프 인용문(따옴표는 코드가 그린다 — text 에 넣지 않는다) + 작은 이름·매체·날짜."""

    type: Literal["quote"]
    pid: Optional[str] = None          # 인물 엔티티(초상). 없으면 flag 원
    flag: str                          # 인물 뱃지 바탕 국기 / pid 없을 때 국기 원
    speaker: str = Field(min_length=1)
    role: Optional[str] = None
    text: str = Field(min_length=1)
    src: Optional[str] = None          # 매체(예: 로이터)
    date: Optional[str] = None         # 화면 날짜(예: 2026. 10. 01)
    accent: Accent = "gold"
    pos: Literal["center", "upper", "lower"] = "center"   # v5.3.1 — 맞선 인용: A = upper(왼쪽 위), B = lower(오른쪽 아래)

    @model_validator(mode="after")
    def _no_marks(self) -> "QuoteEvent":
        if any(c in self.text for c in "“”\"「」"):
            raise ValueError("quote text 에 따옴표를 넣지 않는다 — 코드가 그린다")
        return self


class PhotoEvent(_Event):
    """사진 카드 — 파일·캡션·출처 줄은 미디어 레지스트리에서만. 연출이 문자열을 주면 모델 오류(extra=forbid, D-0036)."""

    type: Literal["photo"]
    mid: str
    x: Optional[float] = None      # 없으면 배치 슬롯 기본값(engine.placement, rules placement.auto_media — 14 §10.3-5)
    y: Optional[float] = None
    w: Optional[float] = None

    @model_validator(mode="after")
    def _xyw_together(self) -> "PhotoEvent":
        if len({self.x is None, self.y is None, self.w is None}) != 1:
            raise ValueError("photo x·y·w 는 모두 주거나 모두 비운다")
        return self


class ClipEvent(_Event):
    type: Literal["clip"]
    mid: str
    x: Optional[float] = None
    y: Optional[float] = None
    w: Optional[float] = None

    @model_validator(mode="after")
    def _xyw_together(self) -> "ClipEvent":
        if len({self.x is None, self.y is None, self.w is None}) != 1:
            raise ValueError("clip x·y·w 는 모두 주거나 모두 비운다")
        return self


class BackdropEvent(_Event):
    """backdrop 무대 배경 사진(v5.1.0 D-0121 §B·D-0123) — img = 미디어 레지스트리 id(kind photo·rights_clear). 연출이 장면마다 고른다(P8).
    블러·dim·crossfade 수치는 rules stage_backdrop. 캡션 바 없음(장식), 크레딧은 credits.yaml media 참조."""

    type: Literal["backdrop"]
    img: str = Field(min_length=1)


class IslandEvent(_Event):
    """아일랜드(v5.1.0 D-0123 §1·D-0126 Q1 A) — backdrop 무대 위 내용물 상자. kind chart = 시간축 뷰포트(카메라 = stage: timeline 숏).
    box = rules island.boxes 이름(연출은 픽셀을 다루지 않는다 — place 는 배치 슬롯 키라 쓰지 않는다). 사진·기사·패널·프리미티브 아일랜드는 각자의 이벤트 타입이다."""

    type: Literal["island"]
    kind: Literal["chart"]
    box: str = "center"

    @model_validator(mode="after")
    def _box(self) -> "IslandEvent":
        boxes = load_rules().island.boxes
        if self.box not in boxes:
            raise ValueError(f"island box {self.box!r} 가 rules island.boxes {sorted(boxes)} 에 없다")
        return self


class ArticleEvent(_Event):
    """기사 프레스 v2(v5.1.0 D-0121 §C) — 매체·날짜·원문/번역 헤드라인·부제는 레지스트리(kind article)에서만."""

    type: Literal["article"]
    mid: str
    theme: Optional[Literal["dark", "light"]] = None   # v5.1.0 D-0121 §C — 없으면 rules article_card.theme_default. 연출이 고른다(P8)
    press: Optional[str] = None                         # 프레스 사진(미디어 레지스트리 photo·rights_clear). 없으면 블러 무대 폴백

    DROP_NONE: ClassVar[tuple[str, ...]] = ("theme", "press")


class PostEvent(_Event):
    """X 게시물 카드(v3.2.0, 18 §5) — 계정명·핸들·시각·번역·검증 라벨은 프로젝트 `intake/sources.json` 에서만(D25와 같은 원칙).
    연출은 소스 id·형광펜 구절·원문 한 줄 여부·자리만 정한다."""

    type: Literal["post"]
    src: str = Field(pattern=r"^src_x_[a-z0-9_]+$")
    hl: Optional[str] = None             # 번역문 안 핵심 구절(부분 문자열)
    quote: bool = False                  # 원문 한 줄(15단어 미만일 때만)
    at: Literal["card", "panel"] = "card"


# ------------------------------------------------------------------ 패널 (문구 = 데이터, D25)
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimedText(_Strict):
    text: str
    t0: float
    t1: float


class _Primitive(_Event):
    """프리미티브 봉투(v4.2.0, 20 §4.2) — 데이터 필드는 engine/primitives/<id>.py SCHEMA. 모델은 engine.primitives.event_model 이 합친다."""

    type: Literal["primitive"]
    id: str


class ChartAxisMeta(_Strict):
    """정직성 메타 덮어쓰기(v4.3.0 D-0087 보정 2) — 막대·이중 축·로그 척도처럼 지금 렌더러가 없는 축 성질을 선언한다.
    값이 있는 필드만 engine.honesty.ChartMeta 를 덮는다. 새 수치 패널은 이 메타로 정직성 검사를 받는다."""

    kind: Optional[str] = None
    baseline: Optional[float] = None
    axes: Optional[Literal[1, 2]] = None
    axis_labels: Optional[list[str]] = None
    axis_colors: Optional[list[ColorName]] = None
    log_scale: Optional[bool] = None
    log_label: Optional[bool] = None
    unit_label: Optional[str] = None


class _Panel(_Event):
    DROP_NONE: ClassVar[tuple[str, ...]] = ("chart",)   # 없으면 dict 에 남기지 않는다(기존 패널 dict = v4.2.0 과 같음)

    type: Literal["panel"]
    title: str
    chart: Optional[ChartAxisMeta] = None   # v4.3.0 D-0087 — 정직성 메타(선택)


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


class PrecedentFootnote(_Strict):
    """v5.6.0 사용자 요청(2026-10-05 "해결 조약에 대한 설명이나 풋노트가 자막을 가리지 않는 선에서") — 카드 아래 작은 글씨 주석.
    sources = 근거 claim(출처 없는 수치 금지, C0). 자막 겹침·폭은 검사 panel_overflow 가 본다."""

    lines: list[str] = Field(min_length=1, max_length=2)
    t0: float
    sources: list[str] = Field(min_length=1)


class PanelPrecedent(_Panel):
    kind: Literal["precedent"]
    subtitle: Optional[str] = None
    cards: list[PrecedentCard] = Field(min_length=1, max_length=4)
    footnote: Optional[PrecedentFootnote] = None
    DROP_NONE: ClassVar[tuple[str, ...]] = ("footnote",)   # 주석 없는 연도 카드 dict = 이전과 같음


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


# ------------------------------------------------------------------ v2 번들 차트 (v2.5.0, D-0032 작업 5, 08 §8·§9)
class ChartProvenance(_Strict):
    """08 §9 — verified + 출처가 있으면 태그 없음. 아니면 '추정'(출처 있음) / '추정 · 출처 미기재'."""

    verification: Literal["verified", "estimated"]
    sources: list[str] = Field(default_factory=list)
    # 사실 검증 상태(C9, docs/06 §6) — 기록용. v4.5.0(D85)부터 패널에 라벨을 그리지 않는다(엔딩 카드 마지막 줄 건수만)
    claim_status: Optional[Literal["verified", "corroborated", "unverified", "disputed"]] = None   # v3.2.0 — 18 §2 status(라벨은 규칙 표)


class _Chart(_Panel):
    subtitle: Optional[str] = None
    provenance: ChartProvenance


class PanelDots(_Chart):
    """도트 매트릭스 — 100 칸 중 highlight 칸을 강조(비율·규모)."""

    kind: Literal["dots"]
    highlight: int = Field(ge=1, le=100)
    big: str                       # 큰 숫자(예: "1")
    unit: str = ""                 # 큰 숫자 옆 단위(예: "%")
    caption: str
    detail: str = ""
    note_label: str = ""
    note_value: str = ""
    note_caption: str = ""


class GanttTask(_Strict):
    label: str
    note: str = ""
    start: str
    end: str
    col: ColorName


class GanttToday(_Strict):
    date: str
    label: str


class PanelGantt(_Chart):
    kind: Literal["gantt"]
    axis_start: str                # YYYY-01-01
    axis_end: str
    tasks: list[GanttTask] = Field(min_length=1, max_length=4)
    today: Optional[GanttToday] = None


class DualSeries(_Strict):
    label: str
    col: ColorName
    values: list[float] = Field(min_length=2)
    decimals: int = Field(default=2, ge=0, le=3)


class PanelDualLine(_Chart):
    kind: Literal["dual_line"]
    y_min: float
    y_max: float
    y_step: float = Field(gt=0)
    y_prefix: str = ""
    unit: Optional[str] = None     # v4.3.0 D-0087 보정 1 — 값 단위(rules data.units). units_visible = unit 또는 y_prefix(data.unit_prefixes)
    x_labels: list[str] = Field(min_length=2)
    x_label_rotate: bool = False   # v5.3.1 사용자 제안(2026-10-02) — 촘촘한 날짜 라벨(주간 등)은 기울여 겹침 없이(각도 = rules panels.charts.dual_line.x_label_rot_rad)
    series: list[DualSeries] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def _lengths(self) -> "PanelDualLine":
        if self.unit is not None and self.unit not in load_rules().data.units:
            raise ValueError(f"dual_line unit {self.unit!r} 는 rules data.units 에 없다")
        for s in self.series:
            if len(s.values) != len(self.x_labels):
                raise ValueError(f"dual_line 계열 {s.label!r} 값 {len(s.values)}개 ≠ x 라벨 {len(self.x_labels)}개")
            if not all(self.y_min <= v <= self.y_max for v in s.values):
                raise ValueError(f"dual_line 계열 {s.label!r} 값이 y 범위 [{self.y_min}, {self.y_max}] 밖")
        return self


class ForkBranch(_Strict):
    head: str
    body: str = ""
    col: ColorName


class PanelFork(_Panel):
    kind: Literal["fork"]
    subtitle: Optional[str] = None
    origin: str
    branches: list[ForkBranch] = Field(min_length=2, max_length=3)
    provenance: Optional[ChartProvenance] = None


class PanelChecklist(_Panel):
    kind: Literal["checklist"]
    subtitle: Optional[str] = None
    items: list[str] = Field(min_length=1, max_length=4)
    footer: str = ""
    provenance: Optional[ChartProvenance] = None


class NetworkNode(_Strict):
    """엔티티 레지스트리 뱃지만 — 문자 원(휘장 없는 기관을 글자로 그린 v2 방식)은 쓰지 않는다(08 §3.1, 지적 1)."""

    id: str
    col: Literal["left", "center", "right"]
    kind: Literal["person", "flag", "emblem"]
    pid: Optional[str] = None
    flag: Optional[str] = None
    img: Optional[str] = None
    label: str
    role: Optional[str] = None
    accent: Accent = "muted"
    big: bool = False              # 중심 인물(뱃지 크게)

    @model_validator(mode="after")
    def _kind_fields(self) -> "NetworkNode":
        need = {"person": ("pid", "flag"), "flag": ("flag",), "emblem": ("img",)}[self.kind]
        missing = [f for f in need if getattr(self, f) is None]
        if missing:
            raise ValueError(f"network node kind={self.kind} 에 필요한 필드 없음: {missing}")
        return self


def _network_style(v: str) -> str:
    styles = load_rules().panels.charts.network.styles
    if v not in styles:
        raise ValueError(f"network 선 종류 {v!r} 는 rules panels.charts.network.styles 에 없다: {sorted(styles)}")
    return v


class NetworkEdge(_Strict):
    src: str
    dst: str
    type: Annotated[str, AfterValidator(_network_style)]
    label: str = ""


class NetworkMention(_Strict):
    """내레이션이 노드 이름을 부를 때(at_word) 금색 펄스 — 08 §3 규칙 5."""

    node: str
    at: float


class PanelNetwork(_Chart):
    kind: Literal["network"]
    nodes: list[NetworkNode] = Field(min_length=2)
    edges: list[NetworkEdge] = Field(min_length=1)
    mentions: list[NetworkMention] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refs(self) -> "PanelNetwork":
        col = {n.id: n.col for n in self.nodes}
        if len(col) != len(self.nodes):
            raise ValueError("network 노드 id 중복")
        for e in self.edges:
            for end in (e.src, e.dst):
                if end not in col:
                    raise ValueError(f"network 선 끝 {end!r} 가 노드에 없다")
            if col[e.src] == col[e.dst]:
                raise ValueError(f"network 선 {e.src}→{e.dst}: 같은 열끼리는 잇지 않는다(수평 접선 곡선, 08 §3 규칙 3)")
        for m in self.mentions:
            if m.node not in col:
                raise ValueError(f"network mention {m.node!r} 가 노드에 없다")
        return self

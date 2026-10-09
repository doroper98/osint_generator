"""CampaignSpec — 전황 작전도 스케치의 사실·연출 값(D-0140 §3, D-0145 §2).

화면 수치는 `rules sketch.campaign`. 여기는 좌표·시각·문구·데이터 참조만. 병력 같은 수치 필드는 두지 않는다(SK-H1, D-0145 §6).
스키마 단계 검사: SK-G3(제대·병종), 조각 참조 형식. SK-G1(정합 잔차)·SK-G2(포위망 다각형)·SK-H5·SK-R1 은 sketch/campaign/checks.py.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator

from sketch.common.spec import SketchSpec, _Strict

ECHELONS = ("XXXX", "XXX", "XX")       # 군 · 군단 · 사단
ARMS = ("inf", "arm", "cav")           # 보병 · 기갑 · 기병
PIECE_REF = re.compile(r"^[^:]+:(axis|soviet):\d+$")   # "층:편:번호"
LonLat = tuple[float, float]


class Ramp(_Strict):
    """시각 t 부터 sec 동안 from_ → to(smooth). 여러 개면 곱한다."""

    t: float
    sec: float = Field(gt=0)
    from_: float = Field(default=1.0, alias="from", ge=0, le=1)
    to: float = Field(ge=0, le=1)


def _piece(v: str) -> str:
    if not PIECE_REF.match(v):
        raise ValueError(f"조각 참조 {v!r} — '층:편:번호'(예 1123:axis:10)")
    return v


class Nation(_Strict):
    color: str               # engine.style 색 토큰
    label: str               # 범례 이름
    light_name: bool = False  # 부대 이름을 밝은 글자색으로(rules campaign.light_name_rgb — 진한 빨강 위 가독)


class Unit(_Strict):
    nation: str
    echelon: str
    arm: str
    name: str
    lon: float
    lat: float
    t: float = Field(ge=0)
    fade: list[Ramp] = Field(default_factory=list)   # 무너진 부대 흐림

    @field_validator("echelon")
    @classmethod
    def _ech(cls, v: str) -> str:
        if v not in ECHELONS:
            raise ValueError(f"SK-G3 제대 {v!r} — {ECHELONS} 중 하나")
        return v

    @field_validator("arm")
    @classmethod
    def _arm(cls, v: str) -> str:
        if v not in ARMS:
            raise ValueError(f"SK-G3 병종 {v!r} — {ARMS} 중 하나")
        return v


class FrontLayer(_Strict):
    """날짜별 전선 묶음 — 조각마다 추축(파랑)·소련(빨강) 이중선. grow = (시작, 초) 동안 자란다."""

    date: str
    pieces: list[str] = Field(min_length=1)
    grow: tuple[float, float]
    dim: list[Ramp] = Field(default_factory=list)
    dashed: bool = False

    @field_validator("pieces")
    @classmethod
    def _p(cls, v: list[str]) -> list[str]:
        return [_piece(x) for x in v]


class StyleEntry(_Strict):
    stroke: str
    width: float
    dash: str = ""
    layer: str
    side: str


class Graticule(_Strict):
    lons: list[float] = Field(min_length=2)
    lats: list[float] = Field(min_length=2)
    stroke: str
    width: float
    dash: str = ""


class Reference(_Strict):
    file: str
    rights: str = "RIGHTS.json"


class Fronts(_Strict):
    file: str                      # prep_georef 산출(fronts.json)
    reference: Reference           # 참고 작전도(D139 — 데이터 파일, 권리는 프로젝트 RIGHTS.json)
    source: str
    style_map: list[StyleEntry] = Field(min_length=1)
    graticule: Graticule
    layers: list[FrontLayer] = Field(min_length=1)


class BuildStep(_Strict):
    """포위망 레시피 한 단계 — 조각(piece) 또는 직접 점(points). 조각은 경도 하한 거르기·역순·가장 가까운 점부터 자르기."""

    piece: Optional[str] = None
    points: Optional[list[LonLat]] = None
    lon_min: Optional[float] = None
    lon_min_of: Optional[str] = None        # 다른 조각의 첫 점 경도를 하한으로
    start_near: Optional[str] = None        # 다른 조각의 마지막 점에 가장 가까운 점부터
    reverse: bool = False

    @model_validator(mode="after")
    def _one(self) -> "BuildStep":
        if (self.piece is None) == (self.points is None):
            raise ValueError("포위망 단계는 piece 와 points 중 하나")
        for v in (self.piece, self.lon_min_of, self.start_near):
            if v is not None:
                _piece(v)
        return self


class Pocket(_Strict):
    name: str
    build: list[BuildStep] = Field(min_length=1)
    show: list[Ramp] = Field(min_length=1)


class Arrow(_Strict):
    name: str
    pts: list[LonLat] = Field(min_length=2)
    t0: float
    t1: float

    @model_validator(mode="after")
    def _t(self) -> "Arrow":
        if self.t1 <= self.t0:
            raise ValueError(f"화살표 {self.name}: t1 ≤ t0")
        return self


class Arrows(_Strict):
    color: str
    dim: list[Ramp] = Field(default_factory=list)
    label_end: float
    items: list[Arrow] = Field(min_length=1)


class Place(_Strict):
    name: str
    now: Optional[str] = None        # 현재 이름(부제)
    lon: float
    lat: float


class RiverLabel(_Strict):
    name: str
    lon: float
    lat: float


class DateMark(_Strict):
    t: float = Field(ge=0)
    text: str


class Tag(_Strict):
    text: str
    at: list[LonLat] = Field(min_length=1)    # 같은 태그를 여러 곳에
    dy: float = 0
    t0: float
    t1: float
    fin: float = Field(gt=0)
    fout: float = Field(gt=0)
    color: str


class Pincer(_Strict):
    lon: float
    lat: float
    t: float
    t_end: float
    text: str
    tag_t: float


class Legend(_Strict):
    t0: float
    t1: float
    order: list[str] = Field(min_length=1)
    caption: str


class SourceNote(_Strict):
    text: str
    t0: float
    t1: float


class Notes(_Strict):
    source_lines: list[SourceNote] = Field(default_factory=list)
    end_title: str
    end_note: str
    end_sec: float = Field(gt=0)


class CampaignSpec(SketchSpec):
    kind: Literal["campaign"]
    nations: dict[str, Nation] = Field(min_length=1)
    units: list[Unit] = Field(default_factory=list)
    fronts: Fronts
    pockets: list[Pocket] = Field(default_factory=list)
    arrows: Optional[Arrows] = None
    places_t: float = 0.0
    places: list[Place] = Field(default_factory=list)
    rivers_label: list[RiverLabel] = Field(default_factory=list)
    dates: list[DateMark] = Field(min_length=1)
    tags: list[Tag] = Field(default_factory=list)
    pincer: Optional[Pincer] = None
    legend: Optional[Legend] = None
    notes: Notes
    sheet_times: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def _refs(self) -> "CampaignSpec":
        bad = sorted({u.nation for u in self.units} - set(self.nations))
        if bad:
            raise ValueError(f"units 의 nation {bad} 가 nations 에 없다")
        if self.legend and set(self.legend.order) - set(self.nations):
            raise ValueError("legend.order 에 nations 밖 코드")
        ts = [d.t for d in self.dates]
        if ts != sorted(ts) or ts[0] != 0:
            raise ValueError("dates 는 t = 0 부터 오름차순")
        if self.date != self.dates[0].text:
            raise ValueError("date(첫 화면 날짜) = dates[0].text")
        bad_t = [s for s in self.sheet_times if not 0 <= s < self.duration_sec]
        if bad_t:
            raise ValueError(f"sheet_times {bad_t} 가 길이 밖")
        return self

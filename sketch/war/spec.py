"""WarSpec — 전쟁사 화면 스케치의 사실·연출 값(v7.4.0 전쟁사 W3·W4, back_and_forth D-0600 §5·§6).

한 spec 이 작전 지도(넓은 숏)와 전술 무대(같은 좌표계 확대 숏)를 함께 갖는다 — 무대 전환 = 카메라 연속(새 캔버스 없음).
화면 수치는 `rules sketch.war`. 여기는 좌표·시각·문구·자료 참조만. 병력 같은 수치는 화면 문구에 쓰지 않는다(SK-H1).

- 날짜: `dates[].date` = EraDate 꼴(`-216.08.02` = 기원전 216년 8월 2일). 뱃지 문구는 schemas.era_date.badge_text(rules hud.date_badge.era_format)
- 부대: `symbol` ∈ rules war_history.symbol_sets[이 영상 시대].units — 시대 밖 부호는 SK-W1(= [symbol-set-mixed]) hard
- 부대 위치·모양 = 키프레임(시각마다 중심·방위·정면 폭·종심 km). 키 사이는 부드럽게 옮긴다(한 번에 튀지 않음). 전부 개략
- 지명: `pleiades` id 면 좌표는 Pleiades(ancient_geo/places.json) 값, 아니면 lon·lat + 출처 줄 '개략'. `toponymy` = 지명 유래 레코드 id
- 증거 카드: `mid` = 프로젝트 media.json(MediaAsset 레코드 — 작품·기록·사진) — 당대/후대 라벨·추정 표기는 코드(schemas.war_history)
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator

from schemas.era_date import validate_era_str
from sketch.common.spec import SketchSpec, _Strict

LonLat = tuple[float, float]


class EraMark(_Strict):
    t: float = Field(ge=0)
    date: str

    @field_validator("date")
    @classmethod
    def _d(cls, v: str) -> str:
        return validate_era_str(v)


class Faction(_Strict):
    token: str               # 색 토큰(rules war_history.faction_badge.tokens)
    name: str                # 코드 조판 진영명(휘장을 지어내지 않는다)


class UnitKey(_Strict):
    t: float = Field(ge=0)
    lon: float
    lat: float
    heading: float = 0.0     # 정면 방위(도, 북 = 0, 시계 방향)
    length_km: float = Field(gt=0)   # 정면 폭(개략)
    depth_km: float = Field(gt=0)    # 종심(개략)


class WarUnit(_Strict):
    faction: str
    symbol: str
    name: str = ""
    keys: list[UnitKey] = Field(min_length=1)
    t_out: Optional[float] = None    # 이 시각부터 사라짐(무너짐·포위 섬멸 표현이 아니라 화면 정리)

    @model_validator(mode="after")
    def _keys(self) -> "WarUnit":
        ts = [k.t for k in self.keys]
        if ts != sorted(ts) or len(set(ts)) != len(ts):
            raise ValueError(f"부대 {self.name or self.symbol}: 키 시각은 겹치지 않는 오름차순 {ts}")
        return self


class WarPlace(_Strict):
    name: str
    now: Optional[str] = None        # 현재 이름
    pleiades: Optional[str] = None   # Pleiades id — 좌표는 ancient_geo/places.json
    lon: Optional[float] = None
    lat: Optional[float] = None
    toponymy: Optional[str] = None   # 지명 유래 레코드 id(projects/<pid>/toponymy.yaml)
    t: float = 0.0
    t_out: Optional[float] = None    # 이 시각부터 사라짐(증거 카드 구간 정리)

    @model_validator(mode="after")
    def _where(self) -> "WarPlace":
        if (self.pleiades is None) == (self.lon is None or self.lat is None):
            raise ValueError(f"지명 {self.name}: pleiades id 와 lon·lat 중 정확히 하나")
        return self


class WarRiver(_Strict):
    name: str
    pts: list[LonLat] = Field(min_length=2)
    label_at: LonLat
    t: float = 0.0


class WarRoute(_Strict):
    name: str
    faction: str
    pts: list[LonLat] = Field(min_length=2)
    t0: float
    t1: float
    t_out: Optional[float] = None


class Evidence(_Strict):
    mid: str                          # media.json 레코드
    t0: float
    t1: float
    side: Literal["left", "right"] = "right"


class Quote(_Strict):
    """사료 인용 — 화면 문구는 우리 번역, 원문(영역본 문장 그대로)·locator·영역본 권리를 함께 남긴다."""

    t0: float
    t1: float
    text: str = Field(min_length=1)          # 한국어 번역(화면)
    original: str = Field(min_length=1)      # 영역본 문장 그대로
    locator: str = Field(min_length=1)       # 예: 폴리비오스 『역사』 III.117.1
    translation: str = Field(min_length=1)   # 예: W. R. Paton(1922, Loeb)
    translation_url: str = Field(min_length=1)
    translation_license: str = Field(min_length=1)


class SourceNote(_Strict):
    text: str
    t0: float
    t1: float


class Notes(_Strict):
    source_lines: list[SourceNote] = Field(default_factory=list)
    end_title: str
    end_note: str
    end_sec: float = Field(gt=0)


class WarSpec(SketchSpec):
    kind: Literal["war"]
    dates: list[EraMark] = Field(min_length=1)
    factions: dict[str, Faction] = Field(min_length=2)
    units: list[WarUnit] = Field(default_factory=list)
    places: list[WarPlace] = Field(default_factory=list)
    rivers: list[WarRiver] = Field(default_factory=list)
    routes: list[WarRoute] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    quotes: list[Quote] = Field(default_factory=list)
    legend_t: tuple[float, float] = (0.0, 0.0)
    notes: Notes
    sheet_times: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def _refs(self) -> "WarSpec":
        fs = set(self.factions)
        bad = sorted({u.faction for u in self.units} - fs) + sorted({r.faction for r in self.routes} - fs)
        if bad:
            raise ValueError(f"factions 에 없는 진영 {bad}")
        ts = [d.t for d in self.dates]
        if ts != sorted(ts) or ts[0] != 0:
            raise ValueError("dates 는 t = 0 부터 오름차순")
        if self.date != self.dates[0].date:
            raise ValueError("date(첫 화면 날짜) = dates[0].date")
        bad_t = [s for s in self.sheet_times if not 0 <= s < self.duration_sec]
        if bad_t:
            raise ValueError(f"sheet_times {bad_t} 가 길이 밖")
        return self

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
from schemas.war_units import Faction, LonLat, UnitKey, WarPlace, WarRiver, WarUnit, faction_errors  # noqa: F401 — 공용 부대 모델(R-0322), 스케치 쪽 이름 그대로
from sketch.common.spec import SketchSpec, _Strict


class EraMark(_Strict):
    t: float = Field(ge=0)
    date: str

    @field_validator("date")
    @classmethod
    def _d(cls, v: str) -> str:
        return validate_era_str(v)


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
    ancient_roads_t: Optional[tuple[float, float]] = None   # AWMC 가도(ancient_geo/roads.json, 영상 시대에 쓰이던 길만) 보이는 구간
    notes: Notes
    sheet_times: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def _refs(self) -> "WarSpec":
        if any(k.t is None for u in self.units for k in u.keys):
            raise ValueError("스케치 부대 키프레임은 t(초)만 — 문장 앵커(at)는 본편 forces 파일")
        errs = faction_errors(self.factions, self.units, tuple(r.faction for r in self.routes))
        if errs:
            raise ValueError(errs[0])
        ts = [d.t for d in self.dates]
        if ts != sorted(ts) or ts[0] != 0:
            raise ValueError("dates 는 t = 0 부터 오름차순")
        if self.date != self.dates[0].date:
            raise ValueError("date(첫 화면 날짜) = dates[0].date")
        bad_t = [s for s in self.sheet_times if not 0 <= s < self.duration_sec]
        if bad_t:
            raise ValueError(f"sheet_times {bad_t} 가 길이 밖")
        return self

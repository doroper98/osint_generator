"""전쟁사 부대 기록 — 진영·부대 키프레임·지명·강(v7.4.0 전쟁사, back_and_forth D-0614·R-0322).

스케치(`sketch.war.spec.WarSpec`)와 본편 terrain3d 무대가 같은 모델을 쓴다(사본 두 벌 금지). 화면 수치는 rules,
여기는 좌표·시각·이름·자료 참조만. 위치·크기는 전부 개략(축척 아님).

- 부대: `symbol` ∈ rules war_history.symbol_sets[이 영상 시대].units. 위치·모양 = 키프레임(시각마다 중심·방위·정면 폭·종심 km)
- 지명: `pleiades` id 면 좌표는 Pleiades(ancient_geo/places.json), 아니면 lon·lat. `toponymy` = 지명 유래 레코드 id
- 진영 휘장: `emblem` = assets/emblems/registry.json reconstructions 키(유물 근거 재작도만). 비대칭이면 다른 진영에 사유
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

LonLat = tuple[float, float]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Faction(_Strict):
    token: str               # 색 토큰(rules war_history.faction_badge.tokens)
    name: str                # 코드 조판 진영명(휘장을 지어내지 않는다)
    emblem: Optional[str] = None                 # v2(D-0606 A) — assets/emblems/registry.json reconstructions 키(유물 근거 재작도만)
    emblem_absent_reason: Optional[str] = None   # 다른 진영에 휘장이 있는데 이 진영에 없으면 사유 필수(비대칭 기록)


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


def faction_errors(factions: dict[str, Faction], units: list[WarUnit], extra_refs: tuple[str, ...] = ()) -> list[str]:
    """진영 참조·휘장 비대칭 사유 — 스케치·본편 공용 검증(문구 그대로)."""
    fs = set(factions)
    out = []
    bad = sorted({u.faction for u in units} - fs) + sorted(set(extra_refs) - fs)
    if bad:
        out.append(f"factions 에 없는 진영 {bad}")
    if any(f.emblem for f in factions.values()):   # 비대칭 = 사유 기록(D-0606 A)
        miss = sorted(k for k, f in factions.items() if not f.emblem and not f.emblem_absent_reason)
        if miss:
            out.append(f"휘장 없는 진영 {miss}: emblem_absent_reason(사유) 필수 — 다른 진영에 휘장이 있다")
    return out


class WarForces(_Strict):
    """본편 terrain3d 무대의 부대 기록 파일(direction stage_config.terrain3d.forces). schema_version 1."""

    schema_version: int = 1
    factions: dict[str, Faction] = Field(min_length=2)
    units: list[WarUnit] = Field(default_factory=list)
    places: list[WarPlace] = Field(default_factory=list)
    rivers: list[WarRiver] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refs(self) -> "WarForces":
        errs = faction_errors(self.factions, self.units)
        if errs:
            raise ValueError("; ".join(errs))
        return self


__all__ = ["Faction", "LonLat", "UnitKey", "WarForces", "WarPlace", "WarRiver", "WarUnit", "faction_errors"]

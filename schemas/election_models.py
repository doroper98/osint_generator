"""선거 결과 데이터 파일 모델 (v7.4.0, back_and_forth D-0290 §4-3).

정본 = 프로젝트 `data/state_results.yaml`(schema_version 1). 이 파일 하나가 `area` 이벤트 검사([area-data-mismatch]),
패널 수치, 엔딩 카드 출처의 기준이다. 수치는 출처 URL·조회 시각과 함께 적고, AP 등 콜이 없으면 status counting 이다
(확정 안 된 결과를 확정처럼 칠하지 않는다, D-0290 §7).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Party = Literal["dem", "rep", "none"]
Status = Literal["called", "counting"]


class RaceResult(BaseModel):
    """한 레이스(상원·주지사·하원 지역구) 결과."""

    model_config = ConfigDict(extra="forbid")

    winner: Optional[str] = None            # 확정 승자(counting 이면 None)
    winner_party: Party
    loser: Optional[str] = None
    leader: Optional[str] = None            # counting 일 때 앞선 후보(화면에 확정처럼 칠하지 않는다)
    pct: Optional[tuple[float, float]] = None   # (승자 또는 선두, 2위) 득표율 %
    pct_as_of: Optional[str] = None          # 득표율 집계 시각·집계율(예 "NBC 98.8% 집계, 11/4")
    status: Status
    called_by: Optional[str] = None          # 콜 주체(AP·NBC·CNN 등). called 면 필수
    flip: bool = False                       # 당이 바뀐 자리(뒤집힘)
    source_url: str = Field(min_length=8)
    retrieved_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}")
    note: Optional[str] = None

    @model_validator(mode="after")
    def _consistent(self) -> "RaceResult":
        if self.status == "called":
            if self.winner_party == "none" or not self.winner or not self.called_by:
                raise ValueError("status called 면 winner·winner_party(dem|rep)·called_by 필수")
        elif self.winner_party != "none" or self.winner:
            raise ValueError("status counting 이면 winner_party none·winner 없음(선두는 leader)")
        return self


class HouseFlip(RaceResult):
    district: str = Field(pattern=r"^[A-Z]{2}-\d{1,2}$")   # 예 MI-7


class StateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)          # 한글 주 이름
    senate: Optional[RaceResult] = None
    governor: Optional[RaceResult] = None
    house_flips: list[HouseFlip] = Field(default_factory=list)


class StateResultsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    as_of: str = Field(min_length=10)        # 파일 전체 기준 시각(KST)
    country: Literal["US"] = "US"
    states: dict[str, StateResult]           # 키 = ISO 3166-2(US-TX)

    @model_validator(mode="after")
    def _keys(self) -> "StateResultsFile":
        bad = [k for k in self.states if not k.startswith(self.country + "-")]
        if bad:
            raise ValueError(f"states 키는 {self.country}-XX(ISO 3166-2): {bad}")
        return self

    def race(self, code: str, race: str) -> Optional[RaceResult]:
        st = self.states.get(code)
        return None if st is None else getattr(st, race)


def load_state_results(path: Path) -> StateResultsFile:
    """data/state_results.yaml → 모델. 없거나 틀리면 예외(조용한 폴백 금지, P6)."""
    return StateResultsFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


__all__ = ["HouseFlip", "RaceResult", "StateResult", "StateResultsFile", "load_state_results"]

"""스케치 spec 공통 계약(Pydantic v2, extra=forbid) — D-0140 §3·§4.

spec = 사실·연출 값(좌표·시각·발표 수치·문구). 화면 수치는 `rules/video_rules.yaml sketch:`(D130).
종류별 spec(`MissileSpec`·`CampaignSpec`)은 이 베이스를 상속한다(S1·S3). 모르는 키는 로드 오류(15 P6).
provenance(`out/sketch_provenance.json`, P5) 계약도 여기 둔다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

SPEC_FILE = "sketch.yaml"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Shot(_Strict):
    """카메라 숏 — t0 에 이동 시작, t1 에 도착(t0 = t1 이면 이동 없음). 중심 경위도·화면 가로 폭 w(경도 °)."""

    t0: float = Field(ge=0)
    t1: float = Field(ge=0)
    lon: float = Field(ge=-180, le=180)
    lat: float = Field(gt=-85, lt=85)
    w: float = Field(gt=0)

    @model_validator(mode="after")
    def _order(self) -> "Shot":
        if self.t1 < self.t0:
            raise ValueError(f"숏 t1({self.t1}) < t0({self.t0})")
        return self


class SourceLine(_Strict):
    """엔딩 자료 카드 한 줄(출처). url 은 있으면 기록만(화면엔 text)."""

    text: str = Field(min_length=1)
    url: Optional[str] = None


class MediaItem(_Strict):
    """화면에 쓰는 이미지·도해. 권리는 프로젝트 RIGHTS.json 항목이 정본(SK-R1)."""

    file: str = Field(min_length=1)
    credit: str = Field(min_length=1)
    license: str = Field(min_length=1)
    caption: str = ""
    t0: float = Field(ge=0)
    t1: float = Field(ge=0)


class SketchSpec(_Strict):
    """모든 스케치 spec 의 공통 머리. 종류별 블록은 하위 클래스가 더한다."""

    schema_version: Literal[1]
    kind: str = Field(min_length=1)
    title: str = Field(min_length=1)
    date: str = Field(min_length=1)          # 화면 모서리 날짜(유일한 모서리 요소, C0)
    duration_sec: float = Field(gt=0)
    sources: list[SourceLine] = Field(min_length=1)
    shots: list[Shot] = Field(min_length=1)
    media: list[MediaItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _shots(self) -> "SketchSpec":
        if self.shots[0].t0 != 0:
            raise ValueError(f"첫 숏은 t0 = 0 이어야 한다(현재 {self.shots[0].t0})")
        starts = [s.t0 for s in self.shots]
        if starts != sorted(starts) or len(set(starts)) != len(starts):
            raise ValueError(f"숏 t0 는 겹치지 않고 오름차순이어야 한다: {starts}")
        for a, b in zip(self.shots, self.shots[1:]):
            if a.t1 > b.t0:
                raise ValueError(f"숏 이동 끝 {a.t1} 이 다음 숏 시작 {b.t0} 뒤")
        if self.shots[-1].t1 > self.duration_sec:
            raise ValueError(f"마지막 숏 이동 끝 {self.shots[-1].t1} > 길이 {self.duration_sec}")
        return self


S = TypeVar("S", bound=SketchSpec)


def load_spec(project: Path, model: type[S]) -> S:
    """`projects/<pid>/sketch.yaml` → spec 모델. 파일이 없거나 형식이 틀리면 예외(조용한 폴백 없음, P6)."""
    path = project / SPEC_FILE
    if not path.is_file():
        raise FileNotFoundError(f"spec 없음: {path}")
    return model.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------- provenance(P5)
class DataFile(_Strict):
    path: str
    sha1: str
    source: str
    license: str


class ComputedNumber(_Strict):
    """화면에 쓴 기하 계산값(D136) — 발표값이 아니다. 식·입력을 함께 남긴다."""

    key: str
    value: float
    shown: str
    formula: str
    inputs: dict[str, float] = Field(default_factory=dict)


class CheckFinding(_Strict):
    id: str                       # SK-H1 … SK-G3
    message: str


class CheckRecord(_Strict):
    ran: list[str] = Field(default_factory=list)     # 실제로 돈 검사 ID
    hard: list[CheckFinding] = Field(default_factory=list)
    warnings: list[CheckFinding] = Field(default_factory=list)


class RenderRecord(_Strict):
    profile: str
    frames: int = Field(ge=0)
    duration_sec: float = Field(ge=0)
    elapsed_sec: float = Field(ge=0)


class SketchProvenance(_Strict):
    """`out/sketch_provenance.json` — 이번 스케치에 실제로 돈 단계만(15 P5). 돌지 않은 단계는 None."""

    schema_version: Literal[1] = 1
    kind: str
    spec_sha1: str
    rules_hash: str
    data_files: list[DataFile] = Field(default_factory=list)
    features_drawn: dict[str, int] = Field(default_factory=dict)
    approximations: list[str] = Field(default_factory=list)
    numbers_shown: list[str] = Field(default_factory=list)
    numbers_computed: list[ComputedNumber] = Field(default_factory=list)
    checks: CheckRecord = Field(default_factory=CheckRecord)
    render: Optional[RenderRecord] = None

"""데이터 레코드 `data/series/<series_id>.yaml` — Pydantic 계약 (v4.3.0, docs/handoff/20 §5.1, back_and_forth D-0084 작업 1).

모든 수치 시리즈는 레코드로 남긴다. 차트는 이 레코드에서 직접 그린다(20 §5.1 "데이터에서 직접").
20 §5.1 YAML(series_id·source·retrieved_at·transform·as_of·revision_note) 그대로 + unit·frequency·license·source_url·values
+ license_note(출처 페이지의 라이선스 표기 원문 — 권리 기록, C9).

허용 목록은 `rules data`(15 P3 — 코드 상수 금지). 목록 밖 값·날짜 역순·as_of > retrieved_at = 로드 오류(15 P6).
- `unit` ∈ `rules data.units`, `license` ∈ `rules data.licenses_allowed`, `frequency` ∈ `rules data.frequencies`.
- `source_url` 의 도메인 ∈ `rules data.sources_allowed`.
- `transform.op` ∈ `rules data.transforms`, `transform.formula` = 그 규칙 문구(식은 한 곳 — 레코드는 사본을 들고 다닌다).
- `values` 날짜는 엄격히 증가, monthly 면 매월 1일·한 달 간격(빈 달 없음).
- `as_of`(YYYY-MM, 화면 "YYYY년 M월 기준") = 마지막 값의 달, 그리고 as_of 달의 첫날 ≤ retrieved_at.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from rules import load_rules

AS_OF_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
SERIES_ID_RE = re.compile(r"^[A-Z0-9_]+$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SeriesTransform(_Strict):
    """코드가 받은 원자료에 한 변환. op = `rules data.transforms` 키, formula = 그 규칙 문구."""

    op: str
    formula: str

    @model_validator(mode="after")
    def _registered(self) -> "SeriesTransform":
        tr = load_rules().data.transforms
        if self.op not in tr:
            raise ValueError(f"transform.op {self.op!r} 는 rules data.transforms 에 없다: {sorted(tr)}")
        if self.formula != tr[self.op]:
            raise ValueError(f"transform.formula 가 rules data.transforms.{self.op} 문구와 다르다: {self.formula!r} ≠ {tr[self.op]!r}")
        return self


class SeriesRecord(_Strict):
    """시리즈 하나의 레코드 + 값. 값은 `<series_id>.csv` 에서 로더(data/series.py)가 채운다."""

    series_id: str
    source: str                                  # 출처 줄(예: "FRED(세인트루이스 연은) · 원출처 연준 이사회 H.15")
    source_url: str
    retrieved_at: date
    transform: SeriesTransform
    as_of: str                                   # YYYY-MM — 마지막 값의 달
    revision_note: Optional[str] = None          # "잠정치는 이후 수정될 수 있음"
    unit: str
    frequency: str
    license: str
    license_note: str                            # 출처 페이지의 라이선스 표기 원문(예: "Public Domain: Citation Requested")
    values: list[tuple[date, float]] = Field(min_length=2)

    @field_validator("series_id")
    @classmethod
    def _sid(cls, v: str) -> str:
        if not SERIES_ID_RE.match(v):
            raise ValueError(f"series_id 는 대문자·숫자·밑줄: {v!r}")
        return v

    @field_validator("unit")
    @classmethod
    def _unit(cls, v: str) -> str:
        units = load_rules().data.units
        if v not in units:
            raise ValueError(f"unit {v!r} 는 rules data.units 에 없다: {units}")
        return v

    @field_validator("license")
    @classmethod
    def _license(cls, v: str) -> str:
        ok = load_rules().data.licenses_allowed
        if v not in ok:
            raise ValueError(f"license {v!r} 는 rules data.licenses_allowed 에 없다: {ok}")
        return v

    @field_validator("frequency")
    @classmethod
    def _freq(cls, v: str) -> str:
        ok = load_rules().data.frequencies
        if v not in ok:
            raise ValueError(f"frequency {v!r} 는 rules data.frequencies 에 없다: {ok}")
        return v

    @field_validator("source_url")
    @classmethod
    def _source(cls, v: str) -> str:
        u = urlparse(v)
        ok = load_rules().data.sources_allowed
        if u.scheme != "https" or u.hostname not in ok:
            raise ValueError(f"source_url 도메인 {u.hostname!r}(https) 는 rules data.sources_allowed 에 없다: {ok}")
        return v

    @field_validator("as_of")
    @classmethod
    def _as_of(cls, v: str) -> str:
        if not AS_OF_RE.match(v):
            raise ValueError(f"as_of 는 YYYY-MM: {v!r}")
        return v

    @model_validator(mode="after")
    def _dates(self) -> "SeriesRecord":
        ds = [d for d, _ in self.values]
        for a, b in zip(ds, ds[1:]):
            if b <= a:
                raise ValueError(f"values 날짜가 증가하지 않는다: {a} → {b}")
        if self.frequency == "monthly":
            bad = [d for d in ds if d.day != 1]
            if bad:
                raise ValueError(f"monthly 값 날짜는 매월 1일: {bad[:3]}")
            gaps = [(a, b) for a, b in zip(ds, ds[1:]) if (b.year * 12 + b.month) - (a.year * 12 + a.month) != 1]
            if gaps:
                raise ValueError(f"monthly 값에 빈 달이 있다: {gaps[:3]}")
        last = ds[-1]
        if self.as_of != f"{last.year:04d}-{last.month:02d}":
            raise ValueError(f"as_of {self.as_of} ≠ 마지막 값의 달 {last:%Y-%m}")
        y, m = (int(x) for x in self.as_of.split("-"))
        if date(y, m, 1) > self.retrieved_at:
            raise ValueError(f"as_of {self.as_of} 가 retrieved_at {self.retrieved_at} 보다 늦다")
        return self

    # --- 조회
    @property
    def start(self) -> date:
        return self.values[0][0]

    @property
    def end(self) -> date:
        return self.values[-1][0]

    def between(self, d0: date, d1: date) -> list[tuple[date, float]]:
        return [(d, v) for d, v in self.values if d0 <= d <= d1]

    def as_of_label(self) -> str:
        """화면 표기 — "YYYY년 M월 기준"(20 §5.1)."""
        y, m = (int(x) for x in self.as_of.split("-"))
        return f"{y}년 {m}월 기준"


__all__ = ["SeriesRecord", "SeriesTransform"]

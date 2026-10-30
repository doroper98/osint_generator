"""데이터 레코드 `data/series/<series_id>.yaml` — Pydantic 계약 (v4.3.0, docs/handoff/20 §5.1, back_and_forth D-0084 작업 1).

모든 수치 시리즈는 레코드로 남긴다. 차트는 이 레코드에서 직접 그린다(20 §5.1 "데이터에서 직접").
20 §5.1 YAML(series_id·source·retrieved_at·transform·as_of·revision_note) 그대로 + unit·frequency·license·source_url·values
+ license_note(출처 페이지의 라이선스 표기 원문 — 권리 기록, C9).

허용 목록은 `rules data`(15 P3 — 코드 상수 금지). 목록 밖 값·날짜 역순·as_of > retrieved_at = 로드 오류(15 P6).
- `unit` ∈ `rules data.units`, `license` ∈ `rules data.licenses_allowed`, `frequency` ∈ `rules data.frequencies`.
- `source_url` 의 도메인 ∈ `rules data.sources_allowed`.
- `transform.op` ∈ `rules data.transforms`, `transform.formula` = 그 규칙 문구(식은 한 곳 — 레코드는 사본을 들고 다닌다).
- `values` 날짜는 엄격히 증가, monthly 면 매월 1일·한 달 간격. 빈 달은 `missing` 에 적힌 것만(D-0086 A — 보간 금지).
- `as_of`(YYYY-MM, 화면 "YYYY년 M월 기준") = 마지막 값의 달, 그리고 as_of 달의 첫날 ≤ retrieved_at.
- v7.4.0 D-0278 §4.2(E3): `source_kind filing`(공시 원문 표 — 값마다 `filings`, 환산은 `rules data.filing_scales` 로 다시 계산해 대조),
  `frequency quarterly`(값 날짜 = 분기 마지막 날, 빈 분기는 missing 에) · `daily`(거래일 — 휴장일은 빈 날이 아니다),
  `issued_on`(가이던스·예상치처럼 미래 기간을 가리키는 값 — as_of 는 발표 달, 값 날짜는 retrieved_at 뒤여도 된다).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, Optional
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


class ValueCitation(_Strict):
    """v7.3.0 D232 U4 — 보도 인용값 하나의 출처(press_cited). 값 날짜마다 하나. note = 환산·범위·'미만' 등 화면 주석."""

    date: date                     # 값 날짜(레코드 values 와 같은 날짜)
    outlet: str = Field(min_length=1)   # 매체·보고서(예: "IEA OMR 2026-05", "Vortexa via Bloomberg")
    pub_date: date                 # 인용 보도·보고서 날짜
    url: str = Field(min_length=1)
    note: Optional[str] = None     # 예: "환산(2.85 Mt)", "4 미만(로이터 산정)", "범위 1.4~1.5 중간"
    open: bool = False             # 상한·하한 표기 값("4 미만") — 패널에 빈 점(open marker)으로 그린다

    @field_validator("url")
    @classmethod
    def _https(cls, v: str) -> str:
        if urlparse(v).scheme != "https":
            raise ValueError(f"cited url 은 https: {v!r}")
        return v


class ValueFiling(_Strict):
    """v7.4.0 D-0278 §4.2(E3) — 공시 값 하나의 출처(source_kind filing). 값 날짜마다 하나.

    form = 양식("8-K Ex.99.1", "10-Q", "S-1", "분기보고서", "연결재무제표기준영업(잠정)실적(공정공시)"),
    number = EDGAR accession 또는 DART rcept_no, item = 표의 행 이름(원문 그대로), locator = 표 위치(표 번호·열 이름 등),
    raw_value·raw_unit = 표에 적힌 값과 단위(rules data.filing_scales 키) — 로더가 환산을 다시 계산해 values 와 대조한다."""

    date: date
    form: str = Field(min_length=1)
    number: str = Field(min_length=1)
    filed_on: date
    item: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    url: str = Field(min_length=1)
    raw_value: float
    raw_unit: str
    raw_md5: Optional[str] = None   # tools/fetch_filing.py 가 받은 원문(raw/<number>.htm|json)의 md5

    @field_validator("url")
    @classmethod
    def _domain(cls, v: str) -> str:
        u = urlparse(v)
        ok = load_rules().data.sources_allowed
        if u.scheme != "https" or u.hostname not in ok:
            raise ValueError(f"filing url 도메인 {u.hostname!r}(https) 는 rules data.sources_allowed 에 없다: {ok}")
        return v

    @field_validator("raw_unit")
    @classmethod
    def _scale(cls, v: str) -> str:
        sc = load_rules().data.filing_scales
        if v not in sc:
            raise ValueError(f"filing raw_unit {v!r} 는 rules data.filing_scales 에 없다: {sorted(sc)}")
        return v

    def scaled(self) -> tuple[str, float]:
        """(화면 단위, 환산 값) — rules data.filing_scales."""
        sc = load_rules().data.filing_scales[self.raw_unit]
        return sc.to, round(self.raw_value * sc.factor, sc.digits)


class MissingValue(_Strict):
    """원자료에 값이 없는 날짜(D-0086 A). 그리지도 채우지도 않는다(보간 금지) — 화면에는 끊김 + "자료 없음" 표시."""

    date: date
    note: str = Field(min_length=1)


class ScatterColumn(_Strict):
    """산점 레코드의 열 하나(v4.4.0 D-0090 작업 2) — 예: 점도표의 "2026" 열 = 참가자별 전망값(정렬). 중앙값은 코드가 계산."""

    label: str = Field(min_length=1)
    values: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def _sorted(self) -> "ScatterColumn":
        if self.values != sorted(self.values):
            raise ValueError(f"scatter 열 {self.label!r} 값은 오름차순(로더가 정렬해 채운다)")
        return self

    def median(self) -> float:
        import statistics  # noqa: PLC0415

        return float(statistics.median(self.values))


class SeriesRecord(_Strict):
    """시리즈 하나의 레코드 + 값. 값은 `<series_id>.csv` 에서 로더(data/series.py)가 채운다.

    v4.4.0(D-0090 작업 2): `kind: scatter` — 발표 한 번의 열별 값 목록(점도표 = 참가자별 전망). values 대신 columns,
    frequency = release, as_of = 발표 달(released). CSV 헤더 `column,value`."""

    kind: Literal["series", "scatter"] = "series"
    source_kind: Literal["fetched", "press_cited", "filing"] = "fetched"   # v7.3.0 D232 U4 — press_cited = 보도 인용값(코드가 받지 않음, cited 필수) · filing = v7.4.0 공시(filings 필수)

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
    missing: list[MissingValue] = Field(default_factory=list)   # v4.3.0 D-0086 — 적힌 날짜만 빈 값 허용
    values: list[tuple[date, float]] = Field(default_factory=list)   # series: 2개 이상(_dates)
    columns: list[ScatterColumn] = Field(default_factory=list)       # v4.4.0 scatter 전용
    released: Optional[date] = None                                  # v4.4.0 scatter 전용 — 발표일
    cited: list[ValueCitation] = Field(default_factory=list)         # v7.3.0 press_cited 전용 — 값 날짜마다 하나
    filings: list[ValueFiling] = Field(default_factory=list)         # v7.4.0 filing 전용 — 값 날짜마다 하나
    issued_on: Optional[date] = None                                 # v7.4.0 — 미래 기간 값(가이던스·예상치)의 발표일. as_of = 이 날의 달

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

    @model_validator(mode="after")
    def _source(self) -> "SeriesRecord":
        """fetched = source_url 도메인 ∈ sources_allowed(코드가 받는 곳). press_cited = 값마다 cited·transform·license press_cited(D232 U4)."""
        u = urlparse(self.source_url)
        if self.source_kind != "filing" and self.filings:
            raise ValueError("filings 는 source_kind filing 레코드만")
        if self.source_kind == "filing":
            if self.cited or self.transform.op != "filing" or self.license != "public_filing":
                raise ValueError("filing 레코드는 transform.op filing·license public_filing, cited 없음")
            if u.scheme != "https" or u.hostname not in load_rules().data.sources_allowed:
                raise ValueError(f"source_url 도메인 {u.hostname!r}(https) 는 rules data.sources_allowed 에 없다")
            if sorted(f.date for f in self.filings) != [d for d, _ in self.values]:
                raise ValueError(f"filing 값마다 filings 하나(날짜 일치): values {[str(d) for d, _ in self.values]} ↔ filings {[str(f.date) for f in self.filings]}")
            by = dict(self.values)
            for f in self.filings:
                unit, v = f.scaled()
                if unit != self.unit:
                    raise ValueError(f"filing {f.date}: 원단위 {f.raw_unit} → {unit} ≠ 레코드 단위 {self.unit}")
                if v != by[f.date]:
                    raise ValueError(f"filing {f.date}: 원값 {f.raw_value} {f.raw_unit} 환산 {v} ≠ 값 {by[f.date]}(손으로 고친 값 금지, P6)")
                if f.filed_on > self.retrieved_at:
                    raise ValueError(f"filing {f.date}: 제출일 {f.filed_on} 가 retrieved_at {self.retrieved_at} 보다 늦다")
            return self
        if self.source_kind == "press_cited":
            if u.scheme != "https":
                raise ValueError(f"source_url 은 https: {self.source_url!r}")
            if self.transform.op != "press_cited" or self.license != "press_cited":
                raise ValueError("press_cited 레코드는 transform.op·license 가 press_cited(코드가 받지 않은 값)")
            if sorted(c.date for c in self.cited) != [d for d, _ in self.values]:
                raise ValueError(f"press_cited 값마다 cited 하나(날짜 일치): values {[str(d) for d, _ in self.values]} ↔ cited {[str(c.date) for c in self.cited]}")
            return self
        ok = load_rules().data.sources_allowed
        if u.scheme != "https" or u.hostname not in ok:
            raise ValueError(f"source_url 도메인 {u.hostname!r}(https) 는 rules data.sources_allowed 에 없다: {ok}")
        if self.transform.op == "press_cited" or self.license == "press_cited":
            raise ValueError("transform/license press_cited 는 source_kind press_cited 레코드만")
        if self.cited and self.transform.op != "chart_close":
            raise ValueError("cited 는 press_cited 레코드(값 출처)·chart_close 레코드(급변일 보도 확인)만")
        if self.transform.op == "chart_close":
            self._price_outliers()
        return self

    @field_validator("as_of")
    @classmethod
    def _as_of(cls, v: str) -> str:
        if not AS_OF_RE.match(v):
            raise ValueError(f"as_of 는 YYYY-MM: {v!r}")
        return v

    @model_validator(mode="after")
    def _dates(self) -> "SeriesRecord":
        if self.kind == "scatter":
            return self._scatter()
        n_min = 1 if self.frequency == "quarterly" else 2   # v7.4.0 — 분기 레코드는 한 분기(예상치·가이던스 한 열)도 된다
        if len(self.values) < n_min or self.columns or self.released is not None:
            raise ValueError(f"series 레코드는 values {n_min}개 이상, columns·released 없음(scatter 전용)")
        ds = [d for d, _ in self.values]
        for a, b in zip(ds, ds[1:]):
            if b <= a:
                raise ValueError(f"values 날짜가 증가하지 않는다: {a} → {b}")
        if self.frequency == "monthly":
            bad = [d for d in ds if d.day != 1]
            if bad:
                raise ValueError(f"monthly 값 날짜는 매월 1일: {bad[:3]}")
            miss = {m.date for m in self.missing}
            bad = sorted(miss & set(ds))
            if bad:
                raise ValueError(f"missing 날짜에 값이 있다: {bad}")
            out = sorted(d for d in miss if not ds[0] < d < ds[-1])
            if out:
                raise ValueError(f"missing 날짜 {out} 가 값 구간({ds[0]}~{ds[-1]}) 안쪽이 아니다")
            gaps = []
            for a, b in zip(ds, ds[1:]):
                k = a.year * 12 + a.month
                between = [date((k + j) // 12, (k + j) % 12 + 1, 1) for j in range(b.year * 12 + b.month - k - 1)]
                if [d for d in between if d not in miss]:
                    gaps.append((a, b))
            if gaps:
                raise ValueError(f"monthly 값에 missing 에 적히지 않은 빈 달이 있다(조용한 드롭 금지, D-0086): {gaps[:3]}")
        if self.frequency == "quarterly":
            self._quarterly(ds)
        if self.frequency == "daily":
            bad = [d for d in ds if d.weekday() >= 5]
            if bad or self.missing:
                raise ValueError(f"daily 값은 거래일(주말 없음)·missing 없음(휴장일은 빈 날이 아니다): 주말 {bad[:3]}")
        last = self.issued_on or ds[-1]
        if self.issued_on is not None and self.frequency != "quarterly":
            raise ValueError("issued_on 은 quarterly 레코드(가이던스·예상치)만")
        if self.as_of != f"{last.year:04d}-{last.month:02d}":
            raise ValueError(f"as_of {self.as_of} ≠ 마지막 값의 달 {last:%Y-%m}")
        y, m = (int(x) for x in self.as_of.split("-"))
        if date(y, m, 1) > self.retrieved_at:
            raise ValueError(f"as_of {self.as_of} 가 retrieved_at {self.retrieved_at} 보다 늦다")
        return self

    def _price_outliers(self) -> None:
        """[price-outlier] — 일별 종가 하루 변동 ≥ rules data.price_outlier_pct 인 날은 cited(보도 확인) 필수. cited 는 그런 날만."""
        pct = load_rules().data.price_outlier_pct
        jumps = {d1: (v1 / v0 - 1) * 100 for (_d0, v0), (d1, v1) in zip(self.values, self.values[1:]) if v0 and abs(v1 / v0 - 1) * 100 >= pct}
        cited = {c.date for c in self.cited}
        bad = sorted(set(jumps) - cited)
        if bad:
            raise ValueError("[price-outlier] 하루 변동 ≥ " + f"{pct}% 인데 보도 확인(cited)이 없다: "
                             + ", ".join(f"{d} {jumps[d]:+.1f}%" for d in bad) + " — 보도로 확인하거나 기간에서 뺀다(G4)")
        extra = sorted(cited - set(jumps))
        if extra:
            raise ValueError(f"chart_close cited 는 급변일에만: {extra}")

    def _quarterly(self, ds: list[date]) -> None:
        """분기 마지막 날만, 빈 분기는 missing 에 적힌 것만(D-0086 — 보간 금지)."""
        ends = {(3, 31), (6, 30), (9, 30), (12, 31)}
        bad = [d for d in ds if (d.month, d.day) not in ends]
        miss = {m.date for m in self.missing}
        bad += [d for d in miss if (d.month, d.day) not in ends]
        if bad:
            raise ValueError(f"quarterly 값·missing 날짜는 분기 마지막 날(3/31·6/30·9/30·12/31): {bad[:3]}")
        if miss & set(ds):
            raise ValueError(f"missing 날짜에 값이 있다: {sorted(miss & set(ds))}")
        qi = [d.year * 4 + (d.month - 1) // 3 for d in ds]
        have = set(qi) | {d.year * 4 + (d.month - 1) // 3 for d in miss}
        gaps = [q for q in range(qi[0], qi[-1] + 1) if q not in have]
        if gaps:
            raise ValueError(f"quarterly 값에 missing 에 적히지 않은 빈 분기가 있다(조용한 드롭 금지): {[f'{q // 4}Q{q % 4 + 1}' for q in gaps[:3]]}")

    def filing(self, d: date) -> Optional[ValueFiling]:
        return next((f for f in self.filings if f.date == d), None)

    def _scatter(self) -> "SeriesRecord":
        if not self.columns or self.values or self.missing or self.released is None:
            raise ValueError("scatter 레코드는 columns·released 필수, values·missing 없음")
        if self.frequency != "release":
            raise ValueError(f"scatter 레코드 frequency 는 release: {self.frequency!r}")
        labels = [c.label for c in self.columns]
        if len(set(labels)) != len(labels):
            raise ValueError(f"scatter 열 이름 중복: {labels}")
        if self.as_of != f"{self.released:%Y-%m}":
            raise ValueError(f"scatter as_of {self.as_of} ≠ 발표 달 {self.released:%Y-%m}")
        if self.released > self.retrieved_at:
            raise ValueError(f"released {self.released} 가 retrieved_at {self.retrieved_at} 보다 늦다")
        return self

    def column(self, label: str) -> ScatterColumn:
        for c in self.columns:
            if c.label == label:
                return c
        raise KeyError(f"{self.series_id}: 열 {label!r} 없음 — {[c.label for c in self.columns]}")

    # --- 조회
    @property
    def start(self) -> date:
        return self.values[0][0]

    @property
    def end(self) -> date:
        return self.values[-1][0]

    def missing_dates(self) -> list[date]:
        return sorted(m.date for m in self.missing)

    def between(self, d0: date, d1: date) -> list[tuple[date, float]]:
        return [(d, v) for d, v in self.values if d0 <= d <= d1]

    def citation(self, d: date) -> Optional[ValueCitation]:
        return next((c for c in self.cited if c.date == d), None)

    def as_of_label(self) -> str:
        """화면 표기 — "YYYY년 M월 기준"(20 §5.1)."""
        y, m = (int(x) for x in self.as_of.split("-"))
        return f"{y}년 {m}월 기준"


__all__ = ["MissingValue", "ScatterColumn", "SeriesRecord", "SeriesTransform", "ValueCitation", "ValueFiling"]

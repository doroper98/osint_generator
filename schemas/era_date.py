"""EraDate — 기원전까지 다루는 날짜형 (v7.4.0 전쟁사 트랙 W1, back_and_forth D-0600 §3·D-0307 §2).

문장 날짜·자산 제작 연대·뱃지 표기의 **유일한 파서**다. 다른 모듈은 날짜 정규식을 따로 두지 않고 여기를 부른다
(`tests/anti_inertia/test_era_date_single_parser.py`).

문자열 꼴(원고 `date`, rules `script_schema.date_formats`):
- 서기: `YYYY` · `YYYY.MM` · `YYYY.MM.DD` (옛 꼴 그대로)
- 기원전: `-YYYY` · `-YYYY.MM` · `-YYYY.MM.DD` — **역사 표기**(`-216` = 기원전 216년). 모델 값은 천문 연도(기원전 216 = −215)
- 대략: `c.-YYYY` · `c.YYYY` (연도만, 뱃지는 세기 단위로 내림)
- 기간: `A~B` (A·B 는 위의 대략 아닌 꼴, A ≤ B)

일 수·정렬은 역법과 무관하게 그레고리력을 앞으로 늘린 연속 일수(율리우스 일 번호)로 센다. 기원전 날짜는
`datetime.date` 로 담을 수 없기 때문이다. 달력 표기(`calendar`)는 기록용이다(D-0307 §2).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

Precision = Literal["day", "month", "year", "circa", "period"]
Calendar = Literal["roman", "julian", "gregorian", "unknown"]

_ONE = r"(-)?(\d{1,4})(?:\.(\d{2})(?:\.(\d{2}))?)?"
_SINGLE_RE = re.compile(rf"^{_ONE}$")
_CIRCA_RE = re.compile(r"^c\.(-)?(\d{1,4})$")
_MEDIA_NOTE_RE = re.compile(r"(\d{4})\.\s?(\d{1,2})\.\s?(\d{1,2})")   # 화면 출처 줄 날짜("2026. 07. 07")
_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")                       # 레지스트리 ISO 날짜
_GREGORIAN_FROM = 1583   # 그레고리력 시행(1582.10) 뒤 첫 해 — 파서가 붙이는 달력 표기의 경계(기록용)
_MONTHS = 12
_CENTURY = 100


class EraDateError(ValueError):
    pass


class EraDate(BaseModel):
    """한 시점 또는 기간. `astronomical_year` 는 천문 연도(서기 1 = 1, 기원전 1 = 0, 기원전 216 = −215)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    astronomical_year: int
    month: Optional[int] = Field(default=None, ge=1, le=_MONTHS)
    day: Optional[int] = Field(default=None, ge=1, le=31)
    precision: Precision
    calendar: Calendar = "unknown"
    end: Optional["EraDate"] = None

    @model_validator(mode="after")
    def _shape(self) -> "EraDate":
        if self.day is not None and self.month is None:
            raise ValueError("일이 있으면 월도 있어야 한다")
        want = "day" if self.day is not None else "month" if self.month is not None else None
        if self.precision == "period":
            if self.end is None or self.end.precision in ("period", "circa"):
                raise ValueError("기간(period)은 end(대략·기간이 아닌 한 시점)가 필요하다")
            if self.end.day_number() < self.start_day_number():
                raise ValueError("기간 끝이 시작보다 앞이다")
        elif self.end is not None:
            raise ValueError("end 는 기간(period)에만")
        elif self.precision == "circa" and want is not None:
            raise ValueError("대략(circa)은 연도만")
        elif self.precision in ("day", "month") and want != self.precision:
            raise ValueError(f"정밀도 {self.precision} 와 월·일 값이 맞지 않는다")
        elif self.precision == "year" and want is not None:
            raise ValueError("정밀도 year 는 월·일 없음")
        return self

    # ── 연도 ──
    @property
    def bce(self) -> bool:
        return self.astronomical_year <= 0

    @property
    def historical_year(self) -> int:
        """역사 표기 연도(기원전이면 기원전 몇 년인지의 양수)."""
        return self.astronomical_year if not self.bce else 1 - self.astronomical_year

    # ── 일 수·정렬 ──
    def start_day_number(self) -> int:
        return _jdn(self.astronomical_year, self.month or 1, self.day or 1)

    def day_number(self) -> int:
        """정렬·간격용 연속 일수 — 기간이면 시작점."""
        return self.start_day_number()

    def __lt__(self, other: "EraDate") -> bool:
        return self.day_number() < other.day_number()

    def __le__(self, other: "EraDate") -> bool:
        return self.day_number() <= other.day_number()

    def days_to(self, other: "EraDate") -> int:
        return other.day_number() - self.day_number()

    def years_between(self, other: "EraDate") -> float:
        """other − self 를 연 단위로(월 정밀도까지, 사진·작품 연대 차 판정용)."""
        return (other.astronomical_year - self.astronomical_year) + ((other.month or 1) - (self.month or 1)) / _MONTHS

    def to_date(self) -> Optional[date]:
        """서기 날짜면 `datetime.date`(빠진 월·일 = 1), 기원전이면 None."""
        if self.astronomical_year < 1:
            return None
        return date(self.astronomical_year, self.month or 1, self.day or 1)

    def iso(self) -> str:
        """보고용 ISO 꼴(빠진 월·일 = 1). 서기는 `str(datetime.date)` 와 같다."""
        y = self.astronomical_year
        return f"{'-' if y < 0 else ''}{abs(y):04d}-{self.month or 1:02d}-{self.day or 1:02d}"


EraDate.model_rebuild()


def _jdn(y: int, m: int, d: int) -> int:
    """그레고리력 연장 율리우스 일 번호(천문 연도). 기원전 4800 년 뒤면 정수 나눗셈이 바르다."""
    a = (14 - m) // _MONTHS
    yy = y + 4800 - a
    mm = m + _MONTHS * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // _CENTURY + yy // 400 - 32045


def _calendar_for(astro: int) -> Calendar:
    return "gregorian" if astro >= _GREGORIAN_FROM else "unknown"


def _astro(minus: Optional[str], digits: str) -> int:
    y = int(digits)
    if y == 0:
        raise EraDateError("연도 0 은 없다(기원전 1년 다음이 서기 1년)")
    return 1 - y if minus else y


ROMAN_SUFFIX = "R"   # v7.4.0 D-0610 ④ — '-216.08.02R' = 로마력(율리우스력 환산이 아님). 뱃지에 rules era_format.roman_suffix


def _single(s: str) -> EraDate:
    roman = s.endswith(ROMAN_SUFFIX)
    if roman:
        s = s[: -len(ROMAN_SUFFIX)]
    m = _SINGLE_RE.match(s)
    if not m:
        raise EraDateError(f"날짜 형식이 아니다: {s!r}")
    astro = _astro(m.group(1), m.group(2))
    mo = int(m.group(3)) if m.group(3) else None
    dy = int(m.group(4)) if m.group(4) else None
    if mo is not None and not 1 <= mo <= _MONTHS:
        raise EraDateError(f"월이 범위 밖: {s!r}")
    if dy is not None:
        if not 1 <= dy <= _days_in_month(astro, mo):
            raise EraDateError(f"일이 범위 밖: {s!r}")
    prec: Precision = "day" if dy is not None else "month" if mo is not None else "year"
    if roman and dy is None:
        raise EraDateError(f"로마력 표시(R)는 일까지 적은 날짜에만: {s!r}R")
    return EraDate(astronomical_year=astro, month=mo, day=dy, precision=prec, calendar="roman" if roman else _calendar_for(astro))


def _days_in_month(astro: int, mo: int) -> int:
    nxt = _jdn(astro + 1, 1, 1) if mo == _MONTHS else _jdn(astro, mo + 1, 1)
    return nxt - _jdn(astro, mo, 1)


def parse_era_date(s: str) -> EraDate:
    """문자열 → EraDate. 형식이 아니면 EraDateError(ValueError)."""
    s = str(s).strip()
    c = _CIRCA_RE.match(s)
    if c:
        astro = _astro(c.group(1), c.group(2))
        return EraDate(astronomical_year=astro, precision="circa", calendar=_calendar_for(astro))
    if "~" in s:
        a, _, b = s.partition("~")
        start, end = _single(a), _single(b)
        try:
            return EraDate(astronomical_year=start.astronomical_year, month=start.month, day=start.day,
                           precision="period", calendar=start.calendar, end=end)
        except ValueError as ex:
            raise EraDateError(f"기간 형식 {s!r}: {ex}") from ex
    return _single(s)


def is_era_date(s: str) -> bool:
    try:
        parse_era_date(s)
    except ValueError:
        return False
    return True


def validate_era_str(v: str) -> str:
    """Pydantic field_validator 용 — 통과하면 원문 그대로 돌려준다."""
    try:
        parse_era_date(v)
    except ValueError as ex:
        raise ValueError(f"날짜 형식 {v!r} — YYYY / YYYY.MM / YYYY.MM.DD / -YYYY(기원전) / c.-YYYY(대략) / A~B(기간): {ex}") from ex
    return v


def day_date(s: str) -> Optional[date]:
    """일 단위 서기 날짜면 `datetime.date`, 그 밖(월·연·대략·기간·기원전)은 None — 사진 촬영일 대조용."""
    d = parse_era_date(s)
    return d.to_date() if d.precision == "day" else None


def media_shot_date(file_note: str, iso: str) -> Optional[date]:
    """사진·영상 촬영일 — 화면 출처 줄의 연·월·일, 없으면 레지스트리 ISO 날짜. 일 단위로 못 읽으면 None."""
    for rx, s in ((_MEDIA_NOTE_RE, file_note or ""), (_ISO_RE, iso or "")):
        m = rx.search(s)
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


# ── 뱃지 표기 (rules hud.date_badge.era_format) ──
def _fill(tpl: str, **kw: int) -> str:
    for k, v in kw.items():
        tpl = tpl.replace("{" + k + "}", str(v))
    return tpl


def _legacy(s: str) -> str:
    """서기 네 자리 연도 꼴의 옛 표기('2026. 07. 07') — 골든 바이트 동일."""
    return s.replace(".", ". ") if len(s) > 4 else s


def _point_text(d: EraDate, raw: str, fmt) -> str:  # noqa: ANN001 — rules EraFormat
    if not d.bce and len(raw.split(".")[0].lstrip("-")) == 4:
        return _legacy(raw)
    pre = fmt.bce_prefix if d.bce else fmt.ce_prefix
    if d.precision == "day":
        body = _fill(fmt.day, y=d.historical_year, m=d.month, d=d.day)
    elif d.precision == "month":
        body = _fill(fmt.month, y=d.historical_year, m=d.month)
    else:
        body = _fill(fmt.year, y=d.historical_year)
    return pre + body


def badge_text(s: str, fmt=None) -> str:  # noqa: ANN001 — rules EraFormat
    """원고 날짜 문자열 → 화면 뱃지 문구. 서기 네 자리 꼴은 옛 표기 그대로, 기원전·대략·기간은 rules era_format."""
    d = parse_era_date(s)
    if fmt is None:
        from rules import load_rules  # noqa: PLC0415

        fmt = load_rules().hud.date_badge.era_format
    if d.precision == "circa":
        cent = (d.historical_year - 1) // _CENTURY + 1
        return (fmt.bce_prefix if d.bce else fmt.circa_ce_prefix) + _fill(fmt.circa, c=cent)
    if d.precision == "period":
        a, _, b = s.strip().partition("~")
        e = d.end
        assert e is not None
        if d.month is None and e.month is None and d.bce == e.bce:
            pre = fmt.bce_prefix if d.bce else fmt.ce_prefix
            if not d.bce and len(a) == 4 and len(b) == 4:
                return a + fmt.period_sep + b
            return pre + _fill(fmt.period_years, y0=d.historical_year, y1=e.historical_year)
        start = EraDate(astronomical_year=d.astronomical_year, month=d.month, day=d.day,
                        precision="day" if d.day else "month" if d.month else "year")
        return _point_text(start, a, fmt) + fmt.period_sep + _point_text(e, b, fmt)
    out = _point_text(d, s.strip().removesuffix(ROMAN_SUFFIX), fmt)
    return out + fmt.roman_suffix if d.calendar == "roman" else out

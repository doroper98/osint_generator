"""era_numeral — 화면 가운데 큰 연도 숫자(옅게, 굴러 바뀜) (v7.4.0, 사용자 결정 UF-401 ③ — 영상 분석 보고
docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md §4 D7).

목적: 수십 년을 건너뛰는 이야기에서 "지금 몇 년의 일인가"를 화면 한가운데 큰 숫자로 옅게 깔고, 이야기가 해를 넘길 때
숫자가 위로 굴러 바뀐다(1976년 → 1979년 → 1980년). 레퍼런스는 인물 표지 뒤에 이 숫자를 깔아 시점 이동을 소리 없이 알렸다.
모서리 날짜 뱃지(hud.date_badge)는 문장 날짜를 작게 그대로 두고, 이 요소는 장면의 시대를 크게 보인다 — 모서리가 아니다(C0 모서리 = 날짜만과 충돌 없음).
기존 요소로 안 되는 이유: date_badge 는 모서리 작은 글자, precedent(연도 카드)는 전면 덮개 카드다. 지도를 가리지 않는 옅은 큰 숫자는 없다.

불변 층(20 §1.1): 숫자 문구(`steps[].label`)는 네 자리 연도를 품어야 한다(원고 문장 날짜에서 온다 — 지어낸 연도 금지).
판독 최소 크기 이상(큰 글자라 해당 없음). 지도 위 요소를 밀어내지 않는다 — 예약 상자는 점 하나(배경 글자, 뱃지·카드 회피 대상 아님).
등장: 페이드. 바뀜: 옛 숫자가 roll_px 위로 사라지고 새 숫자가 아래에서 올라온다(roll_sec, ease_out).
색 의미: 장르 프로필 color_semantics `secondary_text`(옅은 보조 글자). 크기·알파·위치 = rules primitives.era_numeral.
"""

from __future__ import annotations

import re
from typing import Optional

import cairo
from pydantic import BaseModel, ConfigDict, Field, field_validator

from engine.style import PRIMITIVES
from engine.timebase import ease_out, window
from engine.typography import text

L = PRIMITIVES["era_numeral"]
COLOR_KEYS: tuple[str, ...] = ("secondary_text",)
AXIS = "none"
_YEAR = re.compile(r"\d{4}")


class Step(BaseModel):
    """숫자 하나 — 시각 t(연출 앵커 → 초)부터 이 문구."""

    model_config = ConfigDict(extra="forbid")

    t: float
    label: str = Field(min_length=1)

    @field_validator("label")
    @classmethod
    def _year(cls, v: str) -> str:
        if not _YEAR.search(v):
            raise ValueError(f"era_numeral 문구 {v!r} 에 네 자리 연도가 없다 — 원고 문장 날짜의 해만 쓴다")
        if len(v) > L.label_chars_max:
            raise ValueError(f"era_numeral 문구 {v!r} {len(v)}자 > label_chars_max {L.label_chars_max}")
        return v


class EraNumeral(BaseModel):
    """데이터 모양 — 이벤트 필드(봉투 type·id·t0·t1 밖)."""

    model_config = ConfigDict(extra="forbid")

    steps: list[Step] = Field(description=f"연도 문구 1~{L.steps_max}개(시간 순, 첫 t = 이벤트 t0 이후). 예: 1976년 → 1979년 → 1980년")
    x: Optional[float] = None        # 가운데 x(설계 px). 없으면 rules primitives.era_numeral.x
    y: Optional[float] = None        # 기준선 y. 없으면 rules primitives.era_numeral.y

    @field_validator("steps")
    @classmethod
    def _steps(cls, v: list[Step]) -> list[Step]:
        if not 1 <= len(v) <= L.steps_max:
            raise ValueError(f"steps {len(v)}개 — 1~{L.steps_max}")
        if any(b.t <= a.t for a, b in zip(v, v[1:])):
            raise ValueError("steps 는 시간 순(같은 시각 금지)")
        return v


SCHEMA = EraNumeral


def current(e: dict, t: float) -> tuple[int, float]:
    """(지금 숫자 번호, 바뀜 진행 0~1). 첫 숫자 전이면 (0, 1)."""
    k = 0
    for i, s in enumerate(e["steps"]):
        if t >= s["t"]:
            k = i
    if k == 0:
        return 0, 1.0
    return k, ease_out((t - e["steps"][k]["t"]) / L.roll_sec)


def draw(ctx: cairo.Context, view: object, t: float, e: dict, style: object) -> tuple[float, float, float, float]:
    """옅은 큰 숫자 — 바뀌는 동안 옛 숫자는 위로 사라지고 새 숫자가 아래에서 올라온다. 예약 상자 = 점 하나(배경 글자)."""
    x = L.x if e.get("x") is None else e["x"]
    y = L.y if e.get("y") is None else e["y"]
    box = (x, y, x, y)
    a = window(t, e["t0"], e["t1"], L.fade_sec, L.fade_sec)
    if a <= 0:
        return box
    col = style.color("secondary_text")   # type: ignore[attr-defined]
    k, p = current(e, t)
    base = col[-1] * L.alpha * a
    if p < 1 and k > 0:
        text(ctx, e["steps"][k - 1]["label"], x, y - L.roll_px * p, L.size, "disp", col[:-1], base * (1 - p), 0, "c")
    text(ctx, e["steps"][k]["label"], x, y + L.roll_px * (1 - p), L.size, "disp", col[:-1], base * p, 0, "c")
    return box


PREVIEW_FIXTURE: dict = {
    "type": "primitive",
    "id": "era_numeral",
    "t0": 0.0,
    "t1": 9.0,
    "steps": [{"t": 0.0, "label": "1976년"}, {"t": 3.0, "label": "1979년"}, {"t": 6.0, "label": "1980년"}],
}

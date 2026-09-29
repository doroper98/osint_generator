"""dot_plot — 점도표(참가자별 전망 점) (v4.4.0, docs/handoff/20 §3·§5.2·§10 "점도표", back_and_forth D-0090 작업 3).

목적: FOMC 참가자 한 명 한 명의 금리 전망을 열(연도)마다 점으로 보여 주고, 열의 중앙값을 표시한다.
데이터: scatter 데이터 레코드(`data/series/<record>`, transform sep_dots — 연준 SEP 그림 2 표에서 코드가 만든다).
연출은 점 값을 주지 않는다 — 레코드 id 와 보여 줄 열만 고른다(20 §5.1 "데이터에서 직접"). 중앙값도 코드가 계산한다.
기존 요소로 안 되는 이유: 패널 `dots` 는 항목별 점 하나(값 하나)이고, 같은 열에 여러 점이 쌓이는 분포·중앙값 표시가 없다.
series 는 시간 연속 값이라 "한 발표의 참가자별 전망"을 담지 못한다.

불변 층(20 §1.1·§5.2): "참가자별 전망이며 약속이 아님" 고정 문구(rules primitives.dot_plot.note — 연출이 바꿀 수 없다),
출처·기준 시점 줄(레코드에서), 단위 표시(눈금 라벨 %), 판독 최소 크기(rules layout_480p.min_font_px 이상 — glyph_size 검사 대상).
등장: 페이드 + 짧은 슬라이드, 점은 열마다 차례로(05 "요소는 하나씩"). 크기·색 = rules primitives.dot_plot(색은 팔레트 토큰).
정직성(AXIS value): 계열 1, 단위 %, 기준 시점 = 레코드 as_of, 출처 줄 표시 — `engine.honesty` 가 chart_meta 로 검사한다.
배치: 카드와 같은 오른쪽 슬롯(`place: card_right`, 세로 = y 또는 카드 기본 y).
"""

from __future__ import annotations

import math
from typing import Optional

import cairo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.style import C, CARD, CARD_BG, PRIMITIVES, W_OUT
from engine.timebase import ease_out, window
from engine.typography import rrect, text, tw

L = PRIMITIVES["dot_plot"]
COLOR_KEYS: tuple[str, ...] = ()   # 색 의미 없음 — 점·중앙값은 팔레트 토큰(rules primitives.dot_plot.dot_color·median_color)
AXIS = "value"                      # 정직성 검사 대상(rules qa_checks.chart_targets, engine/honesty.py)


class DotPlot(BaseModel):
    """데이터 모양 — 이벤트 필드(봉투 type·id·t0·t1 밖)."""

    model_config = ConfigDict(extra="forbid")

    record: str                                   # scatter 데이터 레코드 id(예: SEP_20260916)
    tag: str                                      # 머리(예: "FOMC 참가자 금리 전망 · 2026년 9월")
    columns: Optional[list[str]] = Field(default=None, min_length=1)   # 보여 줄 열(레코드 열 이름). 없으면 전부
    y: Optional[float] = None                     # 세로 위치(설계 px). 없으면 카드 기본 y

    @field_validator("tag")
    @classmethod
    def _filled(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("빈 문자열 — dot_plot 머리는 필수")
        return v

    @model_validator(mode="after")
    def _record(self) -> "DotPlot":
        rec = _record(self.record)
        have = [c.label for c in rec.columns]
        bad = [c for c in (self.columns or []) if c not in have]
        if bad:
            raise ValueError(f"dot_plot 열 {bad} 가 레코드 {self.record} 에 없다: {have}")
        return self


SCHEMA = DotPlot


def _record(rid: str):  # noqa: ANN202 — schemas.data_models.SeriesRecord
    from data.series import load_series  # noqa: PLC0415

    rec = load_series(rid)
    if rec.kind != "scatter":
        raise ValueError(f"dot_plot 레코드 {rid} 는 scatter 가 아니다(kind {rec.kind})")
    return rec


def columns(e: dict) -> list:  # noqa: ANN401 — ScatterColumn 목록
    rec = _record(e["record"])
    want = e.get("columns") or [c.label for c in rec.columns]
    return [rec.column(c) for c in want]


def value_range(cols: list) -> tuple[float, float]:  # noqa: ANN001
    """눈금 범위 — 모든 점을 담는 tick_step 배수(아래·위 한 칸 여유). 0 에서 시작하지 않는다(막대가 아닌 점 — 20 §5.3 은 막대 규칙)."""
    lo = min(v for c in cols for v in c.values)
    hi = max(v for c in cols for v in c.values)
    s = L.tick_step
    return math.floor(lo / s) * s - s, math.ceil(hi / s) * s + s


def fmt(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def source_line(e: dict) -> str:
    rec = _record(e["record"])
    return f"{rec.source} · {rec.as_of_label()}"


def col_label(label: str) -> str:
    """열 이름 화면 표기 — 레코드 원문 "Longer run" 은 "장기"(연준 SEP 용어의 우리말)."""
    return "장기" if label == "Longer run" else label


def layout(e: dict) -> tuple[float, float, float, float]:
    """(x0, y0, 높이, 점 영역 위 y) — 제자리 상자."""
    plot_top = L.pad_top + L.head_gap + L.plot_gap
    h = plot_top + L.plot_h + L.col_label_gap + L.src_gap + L.pad_bottom
    return W_OUT - L.w - CARD.x_right_margin, e.get("y") or CARD.y, h, plot_top


def chart_meta(e: dict) -> dict:
    """정직성 메타(engine.honesty) — 계열 1(한 발표), 단위 %, 기준 시점 = 레코드 as_of, 출처 줄은 늘 그린다."""
    rec = _record(e["record"])
    return {"series_count": 1, "units": [rec.unit], "unit_label": rec.unit, "as_of": rec.as_of, "source_shown": True}


def draw(ctx: cairo.Context, view: object, t: float, e: dict, style: object) -> tuple[float, float, float, float]:
    """상자: 머리 · 고정 문구 · 점 영역(왼쪽 눈금 %, 열마다 점 쌓기 + 중앙값 선) · 열 이름 · 출처 줄."""
    x0, y0, h, plot_top = layout(e)
    box = (x0, y0, x0 + L.w, y0 + h)
    a = window(t, e["t0"], e["t1"], L.fade_sec, L.fade_sec)
    if a <= 0:
        return box
    x = x0 + (1 - ease_out((t - e["t0"]) / L.fade_sec)) * L.slide_px
    muted, white = C["muted"], C["white"]
    rrect(ctx, x, y0, L.w, h, L.radius)
    ctx.set_source_rgba(*CARD_BG[:-1], CARD_BG[-1] * a)
    ctx.fill()
    ctx.set_source_rgba(*muted, a)
    ctx.rectangle(x, y0 + L.bar_inset, L.bar_w, h - L.bar_inset * 2)
    ctx.fill()
    text(ctx, e["tag"], x + L.pad_x, y0 + L.pad_top, L.tag_size, "sansb", muted, a, 0, "l", spacing=L.tag_spacing)
    text(ctx, L.note, x + L.pad_x, y0 + L.pad_top + L.head_gap, L.note_size, "sansm", C["gold"], a, 0, "l")
    cols = columns(e)
    lo, hi = value_range(cols)
    py0, py1 = y0 + plot_top, y0 + plot_top + L.plot_h
    px0, px1 = x + L.pad_x + L.axis_w, x + L.w - L.pad_x

    def vy(v: float) -> float:
        return py1 - (v - lo) / (hi - lo) * (py1 - py0)

    n_ticks = int(round((hi - lo) / L.tick_step))
    for k in range(n_ticks + 1):
        v = lo + k * L.tick_step
        yy = vy(v)
        ctx.move_to(px0, yy)
        ctx.line_to(px1, yy)
        ctx.set_source_rgba(*white, L.grid_alpha * a)
        ctx.set_line_width(1)
        ctx.stroke()
        if k % L.tick_label_every == 0:
            text(ctx, fmt(v) + "%", px0 - L.tick_label_dx, yy + L.tick_size * L.legend_rise, L.tick_size, "mono", muted, a, 0, "r")
    cw = (px1 - px0) / len(cols)
    most = max(max(c.values.count(v) for v in c.values) for c in cols)
    step = min(L.dot_r * 2 + L.dot_gap, cw / most)   # 한 값에 몰린 점이 열 폭을 넘으면 간격을 줄인다(겹쳐도 옆 열로 넘지 않게)
    for i, c in enumerate(cols):
        cx = px0 + cw * i + cw / 2
        ca = a * min(1.0, max(0.0, (t - e["t0"] - L.fade_sec - i * L.dot_stagger_sec / len(cols)) / L.fade_sec + 1))
        groups: dict[float, int] = {}
        for v in c.values:
            groups[v] = groups.get(v, 0) + 1
        for v, k in groups.items():
            for j in range(k):
                dx = (j * 2 - (k - 1)) * step / 2
                ctx.arc(cx + dx, vy(v), L.dot_r, 0, 2 * math.pi)
                ctx.set_source_rgba(*C[L.dot_color], L.dot_alpha * ca)
                ctx.fill()
        m = c.median()
        ctx.move_to(cx - L.median_half, vy(m))
        ctx.line_to(cx + L.median_half, vy(m))
        ctx.set_source_rgba(*C[L.median_color], ca)
        ctx.set_line_width(L.median_w)
        ctx.stroke()
        text(ctx, col_label(c.label), cx, py1 + L.col_label_gap, L.col_size, "sansm", white, a, 0, "c")
    mw = tw(ctx, L.median_label, L.median_size, "sansm")
    ly = y0 + L.pad_top + L.head_gap - L.median_size * L.legend_rise
    ctx.move_to(px1 - mw - L.tick_label_dx - L.median_half * 2, ly)
    ctx.line_to(px1 - mw - L.tick_label_dx, ly)
    ctx.set_source_rgba(*C[L.median_color], a)
    ctx.set_line_width(L.median_w)
    ctx.stroke()
    text(ctx, L.median_label, px1, y0 + L.pad_top + L.head_gap, L.median_size, "sansm", muted, a, 0, "r")
    text(ctx, source_line(e), x + L.pad_x, y0 + h - L.pad_bottom, CARD.src_size, "sans", muted, a, 0, "l")
    return box


PREVIEW_FIXTURE: dict = {
    "type": "primitive",
    "id": "dot_plot",
    "t0": 0.0,
    "t1": 8.0,
    "record": "SEP_20260916",
    "tag": "FOMC 참가자 금리 전망 · 2026년 9월",
}

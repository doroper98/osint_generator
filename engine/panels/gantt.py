"""패널 gantt — 기간 겹침 (v2.5.0, v2 render2 `P_gantt`, 08 §8). 수치는 `panels.charts.gantt`."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.panels import skin_panel
from engine.panels.base import chart
from engine.style import C
from engine.timebase import clamp01, ease_out, smooth
from engine.typography import rrect, text
from rules import load_rules

AXIS = "date"   # v4.3.0 D-0087 — 축 종류(날짜 축만(값 축 없음)). 정직성 검사 적용 = rules qa_checks.chart_targets
G = load_rules().panels.charts.gantt
SP = skin_panel.P


def _d(s: str) -> date:
    return date(*map(int, s.split("-")))


def _draw_skin(ctx: cairo.Context, lt: float, e: dict, a: float, fx: Callable[[str], float]) -> None:
    """v7.4.0 C0.0 3a — 가는 잉크 축·눈금, 연도 mono 잉크 tertiary, 줄 사이 가는 선, 얇은 회색 직각 막대(강조 계열만 강조색),
    이름 잉크 primary·설명 tertiary, 오늘 선 = 강조색 점선 하나. 시각·자리는 종전 그대로(막대 가운데 = 옛 막대 가운데)."""
    x0, x1 = G.x[0], min(G.x[1], SP.x1)
    d0, d1 = _d(e["axis_start"]), _d(e["axis_end"])
    skin_panel.hline(ctx, x0, x1, G.axis_y, a, SP.axis.alpha, SP.axis.w)
    for yr in range(d0.year, d1.year + 1):
        x = fx(date(yr, 1, 1).isoformat())
        ctx.new_path()
        ctx.move_to(x, G.axis_y - G.tick_h / 2)
        ctx.line_to(x, G.axis_y + G.tick_h / 2)
        ctx.set_source_rgba(*skin.INK, SP.axis.alpha * a)
        ctx.set_line_width(SP.axis.w)
        ctx.stroke()
        skin_panel.meta(ctx, str(yr), x, G.axis_y + SP.gantt_year_dy, a, "c")   # 축 위(카드 아래 끝 안)
    n = len(e["tasks"])
    for i, tk in enumerate(e["tasks"]):
        y = G.row_y0 + i * G.row_dy
        f = ease_out((lt - G.grow_start_sec - i * G.grow_step_sec) / G.grow_sec)
        if f <= 0:
            continue
        la = a * clamp01(f * 2)
        if i < n - 1:
            skin_panel.hline(ctx, SP.x0, x1, y + (G.bar_h + G.row_dy) / 2, la)
        text(ctx, tk["label"], x0 + G.label_dx, y + G.label_dy, G.label_size, "sansb", skin.INK, la, 0, "r")
        text(ctx, tk["note"], x0 + G.label_dx, y + G.note_dy, G.note_size, "sansm", skin.INK3, la, 0, "r")
        bx0, bx1 = fx(tk["start"]), fx(tk["end"])
        ctx.rectangle(bx0, y + (G.bar_h - SP.gantt_bar_h) / 2, max(G.bar_min_w, (bx1 - bx0) * f), SP.gantt_bar_h)
        ctx.set_source_rgba(*skin_panel.mark(tk["col"], skin_panel.BAR), a)
        ctx.fill()
    td = e.get("today")
    if td:
        tx = fx(td["date"])
        tf = a * smooth((lt - G.today_sec) / G.today_fade_sec)
        ctx.set_dash(G.today_dash)
        ctx.set_source_rgba(*skin.ACCENT_SHAPE, tf)
        ctx.set_line_width(SP.line.w)
        ctx.move_to(tx, G.today_top)
        ctx.line_to(tx, G.axis_y + G.tick_h / 2)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, td["label"], tx, G.today_top + G.today_label_dy, G.today_label_size, "sansb", skin.ACCENT_INK, tf, 0, "c")


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    x0, x1 = G.x
    if skin.active():   # skin — 오른쪽 끝을 카드 내용 끝(skin.panel.x1) 안으로(옛 810 = 상자 가장자리)
        x1 = min(x1, SP.x1)
    d0, d1 = _d(e["axis_start"]), _d(e["axis_end"])

    def fx(s: str) -> float:
        return x0 + (_d(s) - d0).days / (d1 - d0).days * (x1 - x0)

    if skin.active():
        _draw_skin(ctx, lt, e, a, fx)
        return
    ctx.set_source_rgba(*C["white"], G.axis_alpha * a)
    ctx.rectangle(x0, G.axis_y, x1 - x0, 1)
    ctx.fill()
    for yr in range(d0.year, d1.year + 1):
        x = fx(date(yr, 1, 1).isoformat())
        ctx.rectangle(x, G.axis_y - G.tick_h / 2, 1, G.tick_h)
        ctx.fill()
        text(ctx, str(yr), x, G.axis_y + G.year_dy, G.year_size, "sansm", C["muted"], a, 0, "c")
    for i, tk in enumerate(e["tasks"]):
        y = G.row_y0 + i * G.row_dy
        f = ease_out((lt - G.grow_start_sec - i * G.grow_step_sec) / G.grow_sec)
        if f <= 0:
            continue
        la = a * clamp01(f * 2)
        text(ctx, tk["label"], x0 + G.label_dx, y + G.label_dy, G.label_size, "sansb", C["white"], la, 0, "r")
        text(ctx, tk["note"], x0 + G.label_dx, y + G.note_dy, G.note_size, "sansm", C["muted"], la, 0, "r")
        bx0, bx1 = fx(tk["start"]), fx(tk["end"])
        rrect(ctx, bx0, y, max(G.bar_min_w, (bx1 - bx0) * f), G.bar_h, G.bar_r)
        ctx.set_source_rgba(*C[tk["col"]], G.bar_alpha * a)
        ctx.fill()
    td = e.get("today")
    if td:
        tx = fx(td["date"])
        tf = a * smooth((lt - G.today_sec) / G.today_fade_sec)
        ctx.set_dash(G.today_dash)
        ctx.set_source_rgba(*C["gold"], G.today_alpha * tf)
        ctx.set_line_width(G.today_width)
        ctx.move_to(tx, G.today_top)
        ctx.line_to(tx, G.axis_y + G.tick_h / 2)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, td["label"], tx, G.today_top + G.today_label_dy, G.today_label_size, "sansb", C["gold"], tf,
             G.today_label_halo, "c")

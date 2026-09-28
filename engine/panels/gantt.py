"""패널 gantt — 기간 겹침 (v2.5.0, v2 render2 `P_gantt`, 08 §8). 수치는 `panels.charts.gantt`."""

from __future__ import annotations

from datetime import date

import cairo

from engine.context import RenderCtx
from engine.panels.base import chart
from engine.style import C
from engine.timebase import clamp01, ease_out, smooth
from engine.typography import rrect, text
from rules import load_rules

G = load_rules().panels.charts.gantt


def _d(s: str) -> date:
    return date(*map(int, s.split("-")))


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    x0, x1 = G.x
    d0, d1 = _d(e["axis_start"]), _d(e["axis_end"])

    def fx(s: str) -> float:
        return x0 + (_d(s) - d0).days / (d1 - d0).days * (x1 - x0)

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

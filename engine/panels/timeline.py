"""패널 timeline — 날짜 축 위 사건 (v2.1.0, render3 `P_timeline`). 사건·기간·표시 시각은 이벤트 필드(D25)."""

from __future__ import annotations

import math
from datetime import date

import cairo

from engine.context import RenderCtx
from engine.panels.base import panel_title
from engine.style import C
from engine.timebase import ease_io, ease_out, smooth
from engine.typography import text


def _d(s: str) -> date:
    return date(*map(int, s.split("-")))


def _months(start: date, end: date) -> list[date]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(date(y, m, 1))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    panel_title(ctx, a, e["title"], e.get("subtitle"))
    X0, X1, Y = 80, 774, 262  # noqa: N806
    d0, d1 = _d(e["start"]), _d(e["end"])

    def fx(s: str) -> float:
        return X0 + (_d(s) - d0).days / (d1 - d0).days * (X1 - X0)

    k = ease_io(lt / 1.2)
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.set_line_width(1.4)
    ctx.move_to(X0, Y)
    ctx.line_to(X0 + (X1 - X0) * k, Y)
    ctx.stroke()
    for md in _months(d0, d1):
        x = fx(md.isoformat())
        if x <= X0 + (X1 - X0) * k:
            ctx.rectangle(x, Y - 4, 1, 8)
            ctx.set_source_rgba(1, 1, 1, 0.35 * a)
            ctx.fill()
            text(ctx, f"{md.month}월", x + 3, Y + 22, 10.5, "sansm", C["muted"], a * 0.9, 0, "l")
    band = e.get("band")
    if band:
        ca = a * smooth((t - band["t_show"]) / 0.6)
        if ca > 0:
            x0, x1 = fx(band["start"]), fx(band["end"])
            ctx.rectangle(x0, Y - 7, x1 - x0, 14)
            ctx.set_source_rgba(*C[band["col"]], 0.18 * ca)
            ctx.fill()
            text(ctx, band["label"], (x0 + x1) / 2, Y + 40, 10.5, "sansm", C[band["col"]], ca, 2, "c")
    cur = None
    for ev in e["events"]:
        f = smooth((t - ev["t"]) / 0.5)
        if f <= 0:
            continue
        d = ev["date"]
        side = ev["side"]
        cur = d
        x = fx(d)
        c_ = C[ev["col"]]
        al = a * f * (0.55 if ev.get("dim") else 1)
        L = 44 if abs(side) == 1 else 96  # noqa: N806
        yy = Y - L if side < 0 else Y + L
        ctx.set_source_rgba(*c_, al * 0.8)
        ctx.set_line_width(1.2)
        ctx.move_to(x, Y)
        ctx.line_to(x, Y + (yy - Y) * ease_out(f))
        ctx.stroke()
        ctx.arc(x, Y, 4.5, 0, 2 * math.pi)
        ctx.set_source_rgba(*c_, al)
        ctx.fill()
        mm, dd = d[5:7].lstrip("0"), d[8:].lstrip("0")
        ty = yy - 18 if side < 0 else yy + 14
        text(ctx, f"{mm}.{dd}", x, ty, 11, "mono", c_, al, 2.4, "c")
        text(ctx, ev["label"], x, ty + (14 if side < 0 else 15), 11.5, "sansb", (1, 1, 1), al, 2.4, "c")
    if cur:
        x = fx(cur)
        ctx.set_source_rgba(*C["gold"], 0.35 * a)
        ctx.set_line_width(1)
        ctx.set_dash([2, 3])
        ctx.move_to(x, 118)
        ctx.line_to(x, 400)
        ctx.stroke()
        ctx.set_dash([])

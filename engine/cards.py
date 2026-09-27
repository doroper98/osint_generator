"""정보 카드 — 태그·큰 숫자·줄·출처 (v2.1.0, render3 `draw_card`)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, W_OUT
from engine.timebase import ease_out, window
from engine.typography import font, rrect, text, tw


def draw_card(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.45, 0.45)
    if a <= 0.01:
        return
    slide = (1 - ease_out((t - e["t0"]) / 0.55)) * 30
    lines = e.get("lines") or []
    acc = C[e["accent"]]
    wdt = 230
    font(ctx, "sansm", 13)
    for s_ in lines:
        wdt = max(wdt, ctx.text_extents(s_).x_advance + 44)
    wdt = max(wdt, tw(ctx, e["tag"], 10.5, "sansb") + 44)
    bh = 0
    if e.get("bigs"):
        bw = 0
        for big, cap in e["bigs"]:
            bw += max(tw(ctx, big, 30, "disp"), tw(ctx, cap, 11, "sansm")) + 26
        wdt = max(wdt, bw + 20)
        bh = 62
    if e.get("src"):
        wdt = max(wdt, tw(ctx, e["src"], 9.5, "sans") + 40)
    h = 42 + bh + 21 * len(lines) + (18 if e.get("src") else 0)
    x = W_OUT - wdt - 24 + slide
    y = e.get("y") or 70
    rrect(ctx, x, y, wdt, h, 5)
    ctx.set_source_rgba(0.05, 0.06, 0.09, 0.86 * a)
    ctx.fill()
    ctx.set_source_rgba(*acc, a)
    ctx.rectangle(x, y + 10, 3, h - 20)
    ctx.fill()
    text(ctx, e["tag"], x + 18, y + 23, 10.5, "sansb", acc, a, 0, "l", spacing=0.4)
    yy = y + 32
    if e.get("bigs"):
        xx = x + 18
        for big, cap in e["bigs"]:
            text(ctx, big, xx, yy + 32, 30, "disp", (1, 1, 1), a, 0, "l")
            text(ctx, cap, xx, yy + 50, 11, "sansm", C["muted"], a, 0, "l")
            xx += max(tw(ctx, big, 30, "disp"), tw(ctx, cap, 11, "sansm")) + 26
        yy += bh
    for i, s_ in enumerate(lines):
        text(ctx, s_, x + 18, yy + 17 + 21 * i, 13, "serifb" if e.get("quote") else "sansm", (0.94, 0.92, 0.9), a, 0, "l")
    if e.get("src"):
        text(ctx, e["src"], x + 18, y + h - 12, 9.5, "sans", C["muted"], a * 0.9, 0, "l")

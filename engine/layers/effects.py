"""선박 점·폭발 (v2.1.0, render3 `draw_ships, draw_boom`)."""

from __future__ import annotations

import math

import cairo
from engine.context import RenderCtx
from engine.projection import View
from engine.style import C
from engine.timebase import clamp01, ease_out, window


def draw_ships(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.8, 0.6)
    for wx, wy, ph in view.stage.sea_points(tuple(e["box"]), e["n"], e["seed"]):
        if t < e["t0"] + ph * 1.6:
            continue
        x, y = view.to_screen(wx, wy)
        tw_ = 0.6 + 0.4 * math.sin(t * 2 + ph * 9)
        ctx.arc(x, y, 1.7, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.82, 0.5, 0.85 * a * tw_)
        ctx.fill()


def draw_boom(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.05, 0.8)
    x, y = view.to_screen(*e["world"])
    lt = t - e["t0"]
    for k in range(3):
        r = 6 + 50 * ease_out((lt - k * 0.12) / 1.2)
        ctx.arc(x, y, max(r, 0.1), 0, 2 * math.pi)
        ctx.set_source_rgba(*C["amber"], 0.6 * a * (1 - clamp01(lt / 1.6)))
        ctx.set_line_width(2)
        ctx.stroke()

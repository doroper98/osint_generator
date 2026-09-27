"""암전(dip) — 1초 검은 화면, 가운데서 카메라 cut (v2.1.0, render3 render_frame 의 dip 칠)."""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.timebase import clamp01


def draw_dip(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    d = math.sin(math.pi * clamp01((t - e["t0"]) / (e["t1"] - e["t0"])))
    ctx.set_source_rgba(0, 0, 0, 0.93 * d)
    ctx.paint()

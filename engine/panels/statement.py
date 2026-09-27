"""패널 statement — 공동성명 서명국 + 동참국 (v2.1.0, render3 `P_statement`)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.badges import badge_at
from engine.panels.base import panel_title
from engine.style import C, W_OUT
from engine.timebase import smooth


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    panel_title(ctx, a, e["title"], e.get("subtitle"))
    for i, s in enumerate(e["signers"]):
        x = 110 + i * 92
        badge_at(ctx, R, x, 230, dict(kind="flag", flag=s["flag"], R=24, t0=e["t0"] + 0.5 + i * 0.22, label=s["label"],
                                      accent="muted"), t, a)
    j = e["joiner"]
    tj = max(e["t0"] + 2.2, j["t_join"])
    badge_at(ctx, R, W_OUT / 2, 345, dict(kind="flag", flag=j["flag"], R=30, t0=tj, label=j["label"], role=j["role"],
                                          accent="gold"), t, a)
    ka = a * smooth((t - tj) / 0.5)
    ctx.set_source_rgba(*C["gold"], 0.5 * ka)
    ctx.set_line_width(1)
    ctx.set_dash([3, 4])
    ctx.move_to(110, 292)
    ctx.line_to(W_OUT - 190, 292)
    ctx.stroke()
    ctx.set_dash([])

"""국가 채움 강조 (v2.1.0, render3 `draw_country`)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.borders import path_rings
from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.style import C
from engine.timebase import window


def draw_country(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.8, 0.6)
    col = C[e["col"]]
    if a <= 0.01:
        return
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    for code in e["codes"]:
        ctx.new_path()
        if not path_rings(ctx, view, view.stage.bord[lod].get(code, [])):
            continue
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgba(*col, e["a"] * a)
        ctx.fill_preserve()
        for wd, al in ((6, 0.07), (2.6, 0.2), (1.1, 0.85)):
            ctx.set_source_rgba(*col, al * a)
            ctx.set_line_width(wd)
            ctx.stroke_preserve()
        ctx.new_path()

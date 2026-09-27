"""국경·행정구역 선 (v2.1.0, render3 `path_rings, draw_borders`). LOD: w<22 이면 fine, 행정구역은 w<24 에서 페이드 인."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.projection import View
from engine.timebase import smooth


def path_rings(ctx: cairo.Context, view: View, rings: list, min_px: float = 1.0) -> int:
    n = 0
    for uv, mn, mx in rings:
        if not view.visible(mn, mx) or (mx - mn).max() * view.s < min_px:
            continue
        pts = view.uvs(uv)
        ctx.move_to(*pts[0])
        for x, y in pts[1:]:
            ctx.line_to(x, y)
        ctx.close_path()
        n += 1
    return n


def draw_borders(ctx: cairo.Context, R: RenderCtx, view: View) -> None:  # noqa: N803
    lod = "fine" if view.w < 22 else "coarse"
    ctx.new_path()
    for _k, rings in R.assets.bord[lod].items():
        path_rings(ctx, view, rings)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(0.82, 0.86, 0.92, 0.36 if view.w < 40 else 0.26)
    ctx.set_line_width(0.75)
    ctx.stroke()
    a = 0.3 * smooth((24 - view.w) / 10)
    if a > 0.01:
        ctx.set_dash([2.5, 2.5])
        for _k, lst in R.assets.adm.items():
            ctx.new_path()
            for ad in lst:
                path_rings(ctx, view, ad["rings"], 2)
            ctx.set_source_rgba(0.8, 0.84, 0.9, a)
            ctx.set_line_width(0.55)
            ctx.stroke()
        ctx.set_dash([])

"""국경·행정구역 선 (v2.1.0, render3 `path_rings, draw_borders`). LOD(`engine.stage.MERCATOR_LOD`): w<22 이면 fine, 행정구역은 w<24 에서 페이드 인.

v4.1.0: MercatorStage.render_base 가 부른다. 선은 무대가 미리 월드 좌표로 바꾼 고리(stage.bord·adm)다(D-0076 작업 2)."""

from __future__ import annotations

import cairo

from typing import TYPE_CHECKING

from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.timebase import smooth

if TYPE_CHECKING:
    from engine.stage import MercatorStage


def path_rings(ctx: cairo.Context, view: View, rings: list, min_px: float = 1.0) -> int:
    n = 0
    for uv, mn, mx in rings:
        if not view.visible(mn, mx) or (mx - mn).max() * view.s < min_px:
            continue
        pts = view.to_screen_arr(uv)
        ctx.move_to(*pts[0])
        for x, y in pts[1:]:
            ctx.line_to(x, y)
        ctx.close_path()
        n += 1
    return n


def draw_borders(ctx: cairo.Context, stage: "MercatorStage", view: View) -> None:
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    ctx.new_path()
    for _k, rings in stage.bord[lod].items():
        path_rings(ctx, view, rings)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ba = LOD["border_alpha"]
    ctx.set_source_rgba(0.82, 0.86, 0.92, ba["near"] if view.w < ba["below_w"] else ba["far"])
    ctx.set_line_width(0.75)
    ctx.stroke()
    af = LOD["admin_lines_fade"]
    a = af["alpha"] * smooth((af["w"] - view.w) / af["span"])
    if a > 0.01:
        ctx.set_dash([2.5, 2.5])
        for _k, lst in stage.adm.items():
            ctx.new_path()
            for ad in lst:
                path_rings(ctx, view, ad["rings"], 2)
            ctx.set_source_rgba(0.8, 0.84, 0.9, a)
            ctx.set_line_width(0.55)
            ctx.stroke()
        ctx.set_dash([])

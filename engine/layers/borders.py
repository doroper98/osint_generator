"""국경·행정구역 선 (v2.1.0, render3 `path_rings, draw_borders`). LOD(`engine.stage.MERCATOR_LOD`): w<22 이면 fine, 행정구역은 w<24 에서 페이드 인.

v4.1.0: MercatorStage.render_base 가 부른다. 선은 무대가 미리 월드 좌표로 바꾼 고리(stage.bord·adm)다(D-0076 작업 2)."""

from __future__ import annotations

import cairo

from typing import TYPE_CHECKING

from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.style import BORDER_GLOW as BG
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


def draw_border_glow(ctx: cairo.Context, stage: "MercatorStage", view: View, t: float) -> None:
    """v5.3.1 국경선 글로우(시안 — 사용자 제안 2026-10-02, valdai-2026 한정; 켜기 = direction stage_config.mercator.border_glow).
    국경선(draw_borders 와 같은 LOD 고리, 행정구역 선 제외) 위에 옅은 빛(rules border_glow.halo)을 상시 깔고, 짧은 빛 조각(run_seg_px)이
    run_period_px 간격으로 선을 따라 run_speed_px/초로 천천히 흐른다(cairo 대시 오프셋). 수치는 전부 rules border_glow."""
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    ctx.save()
    ctx.new_path()
    for _k, rings in stage.bord[lod].items():
        path_rings(ctx, view, rings)
    path = ctx.copy_path()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for w, a in BG.halo:
        ctx.new_path()
        ctx.append_path(path)
        ctx.set_source_rgba(*BG.rgb, a)
        ctx.set_line_width(w)
        ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_dash([BG.run_seg_px, BG.run_period_px - BG.run_seg_px], -BG.run_speed_px * t)
    for w, a in BG.run_layers:
        ctx.new_path()
        ctx.append_path(path)
        ctx.set_source_rgba(*BG.rgb, a)
        ctx.set_line_width(w)
        ctx.stroke()
    ctx.restore()

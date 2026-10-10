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


def path_lines(ctx: cairo.Context, view: View, lines: list, min_px: float = 1.0) -> int:
    """열린 선(국경·해안 구간, v5.18.0) — path_rings 와 같되 닫지 않는다."""
    n = 0
    for uv, mn, mx in lines:
        if not view.visible(mn, mx) or (mx - mn).max() * view.s < min_px:
            continue
        pts = view.to_screen_arr(uv)
        ctx.move_to(*pts[0])
        for x, y in pts[1:]:
            ctx.line_to(x, y)
        n += 1
    return n


def border_path(ctx: cairo.Context, stage: "MercatorStage", view: View, lod: str) -> None:
    """국경 경로 — 테마에 coast 가 있으면 공유 변만(v5.18.0 D-0161 §2), 없으면 종전처럼 모든 국가 고리."""
    ctx.new_path()
    if stage.theme.coast is not None:
        path_lines(ctx, view, stage.line_split(lod)["border"], 0.0)
        return
    for _k, rings in stage.bord[lod].items():
        path_rings(ctx, view, rings)


def draw_borders(ctx: cairo.Context, stage: "MercatorStage", view: View) -> None:
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    co = stage.theme.coast
    if co is not None:   # v5.18.0 D-0161 §2(가이드 23 §14) — 해안은 밝고 얇은 물빛 선, 국경 아래에 먼저
        ctx.new_path()
        path_lines(ctx, view, stage.line_split(lod)["coast"])
        ctx.set_source_rgba(*co.rgb, co.alpha if co.alpha is not None else 1.0)
        ctx.set_line_width(co.width)
        ctx.stroke()
    border_path(ctx, stage, view, lod)
    bo, ad_ = stage.theme.border, stage.theme.admin   # v5.13.0 D-0153 Q0-2 — 지도 테마 선 색·폭(rules geo.themes.<테마>.map)
    ba = LOD["border_alpha"]
    ctx.set_source_rgba(*bo.rgb, (ba["near"] if view.w < ba["below_w"] else ba["far"]) if bo.alpha is None else bo.alpha)
    ctx.set_line_width(bo.width)
    ctx.stroke()
    af = LOD["admin_lines_fade"]
    a = (af["alpha"] if ad_.alpha is None else ad_.alpha) * smooth((af["w"] - view.w) / af["span"])
    if a > 0.01:
        ctx.set_dash(ad_.dash)
        for _k, lst in stage.adm.items():
            ctx.new_path()
            for ad in lst:
                path_rings(ctx, view, ad["rings"], 2)
            ctx.set_source_rgba(*ad_.rgb, a)
            ctx.set_line_width(ad_.width)
            ctx.stroke()
        ctx.set_dash([])


def draw_border_glow(ctx: cairo.Context, stage: "MercatorStage", view: View, t: float) -> None:
    """v5.3.1 국경선 글로우(시안 — 사용자 제안 2026-10-02, valdai-2026 한정; 켜기 = direction stage_config.mercator.border_glow).
    국경선(draw_borders 와 같은 LOD 고리, 행정구역 선 제외) 위에 옅은 빛(rules border_glow.halo)을 상시 깔고, 짧은 빛 조각(run_seg_px)이
    run_period_px 간격으로 선을 따라 run_speed_px/초로 천천히 흐른다(cairo 대시 오프셋). 수치는 전부 rules border_glow."""
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    ctx.save()
    border_path(ctx, stage, view, lod)   # v5.18.0 — 해안을 분리한 테마는 국경(공유 변)에만 글로우
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

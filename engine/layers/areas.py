"""국가 채움 강조 (v2.1.0, render3 `draw_country`). fill flag = 국기 채움(v7.4.0 UF-900 R2, engine/layers/flag_fill)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.borders import path_rings
from engine.layers.flag_fill import draw_flag_fill
from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.stage import skin_map
from engine.style import ELEM, SKIN, map_c
from engine.timebase import window


def draw_country(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    if e.get("fill") == "flag":   # v7.4.0 UF-900 R2 — 단색 채움 dict 에는 fill 칸이 없다(옛 모양, 아래 경로 바이트 동일)
        draw_flag_fill(ctx, R, view, t, e)
        return
    a = window(t, e["t0"], e["t1"], *ELEM["country"])   # v7.4.0 UF-159 ×1.5
    col = map_c(view.stage, e["col"])   # v5.18.0 D-0161 §3
    if a <= 0.01:
        return
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    cf = SKIN.map.color_fill
    on = skin_map(view.stage)   # v7.4.0 4b — skin 지도: 옅은 틴트(a ≤ alpha_max) + 가는 의미색 윤곽 한 줄(발광 겹 없음)
    fill_a = min(e["a"], cf.alpha_max) if on else e["a"]
    for code in e["codes"]:
        ctx.new_path()
        if not path_rings(ctx, view, view.stage.bord[lod].get(code, [])):
            continue
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgba(*col, fill_a * a)
        ctx.fill_preserve()
        for wd, al in (((cf.outline_w, cf.outline_a),) if on else ((6, 0.07), (2.6, 0.2), (1.1, 0.85))):
            ctx.set_source_rgba(*col, al * a)
            ctx.set_line_width(wd)
            ctx.stroke_preserve()
        ctx.new_path()

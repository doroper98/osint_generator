"""국가 채움 강조 (v2.1.0, render3 `draw_country`) · 1급 행정구역(주) 채움 `draw_area`(v7.4.0 D-0290)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.borders import path_rings
from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.style import map_c
from engine.timebase import window
from rules import load_rules

AREA = load_rules().area   # 모듈 로드 때 한 번(프레임마다 YAML 을 다시 읽지 않는다)


def draw_country(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.8, 0.6)
    col = map_c(view.stage, e["col"])   # v5.18.0 D-0161 §3
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


def draw_area(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    """v7.4.0 back_and_forth D-0290 §3-3 — 1급 행정구역(주) 채움. 항목마다 t0 + delay 에 페이드 등장, t1 에 퇴장.
    채움 알파 = rules area.alpha_bands[band], 외곽선 = rules area.outline(draw_country 와 같은 3단), 개표 중(counting) = 채움 위 사선 빗금.
    고리는 stage.adm_rings(code) — 옛 geo.pkl·없는 code 면 StageError(조용히 건너뛰지 않는다, P6)."""
    A = AREA  # noqa: N806
    for it in e["items"]:
        a = window(t, e["t0"] + it["delay"], e["t1"], A.fade_sec, A.fade_sec)
        rings = view.stage.adm_rings(e["country"], it["code"])
        if a <= 0.01:
            continue
        col = map_c(view.stage, it["col"])
        ctx.new_path()
        if not path_rings(ctx, view, rings):
            continue
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        path = ctx.copy_path()
        ctx.set_source_rgba(*col, A.alpha_bands[it["band"]] * a)
        ctx.fill()
        if it["status"] == "counting":
            _hatch(ctx, path, col, a, A.hatch)
        for wd, al in A.outline:
            ctx.new_path()
            ctx.append_path(path)
            ctx.set_source_rgba(*col, al * a)
            ctx.set_line_width(wd)
            ctx.stroke()
        ctx.new_path()


def _hatch(ctx: cairo.Context, path: object, col: tuple, a: float, H: object) -> None:  # noqa: N803
    """개표 중 빗금 — 경로 안으로 잘라 45° 사선(간격·두께·알파 = rules area.hatch)."""
    ctx.save()
    ctx.new_path()
    ctx.append_path(path)
    ctx.clip()
    x0, y0, x1, y1 = ctx.clip_extents()
    ctx.new_path()
    k = x0 - (y1 - y0)
    while k < x1:
        ctx.move_to(k, y1)
        ctx.line_to(k + (y1 - y0), y0)
        k += H.spacing
    ctx.set_source_rgba(*col, H.alpha * a)
    ctx.set_line_width(H.width)
    ctx.stroke()
    ctx.restore()

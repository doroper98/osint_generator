"""도로 레이어 (v7.4.0, back_and_forth D-0229 §2.1-2, UF-106). Natural Earth 10m roads(공개 도메인).

NE `type` → 등급(geo.prep_geometry.ROAD_CLASS): Major Highway = motorway, Secondary Highway = trunk, Road = primary.
단일 stroke, casing·glow 없음(가이드 23 §15). 스타일 = rules geo.themes.<테마>.map.roads,
폭 LOD = engine.stage.MERCATOR_LOD roads_fade(motorway 는 motorway_w, 그 밖은 w 아래에서 span 동안 페이드 인).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import cairo

from engine.layers.borders import path_lines
from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.timebase import smooth

if TYPE_CHECKING:
    from engine.stage import MercatorStage

ROAD_DRAW_ORDER = ("primary", "trunk", "motorway")   # 굵은 등급을 위에


def road_alpha(w: float, cls: str) -> float:
    rf = LOD["roads_fade"]
    th = rf["motorway_w"] if cls == "motorway" else rf["w"]
    return smooth((th - w) / rf["span"])


def draw_roads(ctx: cairo.Context, stage: "MercatorStage", view: View) -> int:
    """보이는 도로 선 수를 돌려준다(provenance map_layers.roads)."""
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    n = 0
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for cls in ROAD_DRAW_ORDER:
        f = road_alpha(view.w, cls)
        if f <= 0.01:
            continue
        ctx.new_path()
        k = path_lines(ctx, view, stage.roads[lod][cls], 0.0)
        if not k:
            continue
        st = getattr(stage.theme.roads, cls)
        ctx.set_source_rgba(*st.rgb, st.alpha * f)
        ctx.set_line_width(st.width)
        ctx.stroke()
        n += k
    return n

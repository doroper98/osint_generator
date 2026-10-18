"""강 레이어 (v7.4.0, back_and_forth D-0229 §2.1-2, UF-106). Natural Earth 10m rivers_lake_centerlines(공개 도메인).

그리기 순서(가이드 23 §15 "국경이 가장 분명"): 지형 → 강 → 도로 → 국경·행정선 → 지명. 단일 stroke, casing·glow 없음.
스타일 = rules geo.themes.<테마>.map.rivers, 폭 LOD = engine.stage.MERCATOR_LOD rivers_fade(큰 강 major_w, 작은 강 minor_w 아래에서 span 동안 페이드 인).
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


def river_alpha(w: float, cls: str) -> float:
    """폭 w 에서 등급 cls(major|minor) 의 LOD 배율 0~1 — smooth((문턱 − w) / span)."""
    rf = LOD["rivers_fade"]
    return smooth((rf[f"{cls}_w"] - w) / rf["span"])


def draw_rivers(ctx: cairo.Context, stage: "MercatorStage", view: View) -> int:
    """보이는 강 선 수를 돌려준다(provenance map_layers.rivers)."""
    st = stage.theme.rivers
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    n = 0
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for cls in ("major", "minor"):
        f = river_alpha(view.w, cls)
        if f <= 0.01:
            continue
        ctx.new_path()
        k = path_lines(ctx, view, stage.rivers[lod][cls], 0.0)
        if not k:
            continue
        ctx.set_source_rgba(*st.rgb, getattr(st, f"alpha_{cls}") * f)
        ctx.set_line_width(getattr(st, f"width_{cls}"))
        ctx.stroke()
        n += k
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    return n

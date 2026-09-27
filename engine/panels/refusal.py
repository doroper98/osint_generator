"""패널 refusal — 요구와 거절의 관계선 (v2.1.0, render3 `P_refusal`). 문구·인물·국가·거절 시각은 이벤트 필드(D25)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.badges import badge_at
from engine.panels.base import edge_curve, panel_title
from engine.style import C, W_OUT
from engine.timebase import ease_io, smooth, window
from engine.typography import text


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    panel_title(ctx, a, e["title"])
    ux, uy = 235, 262
    act = e["actor"]
    badge_at(ctx, R, ux, uy, dict(kind="person", pid=act["pid"], flag=act["flag"], R=36, t0=e["t0"] + 0.4,
                                  label=act["label"], role=act["role"], accent=act["accent"]), t, a)
    for i, row in enumerate(e["rows"]):
        fx, fy = 590, 138 + i * 62
        t0 = e["t0"] + 1.0 + i * 0.2
        badge_at(ctx, R, fx, fy, dict(kind="flag", flag=row["flag"], R=19, t0=t0, label=row["label"], side="right",
                                      accent="gold" if row.get("hl") else "muted"), t, a)
        et0 = 2.2 + i * 0.75
        prog = ease_io((lt - et0) / 1.3)
        if prog > 0:
            red = smooth((t - row["t_refuse"]) / 0.5)
            col = tuple(C["gold"][j] * (1 - red) + C["ru"][j] * red for j in range(3))
            pts = edge_curve(ux + 40, uy, fx - 26, fy, prog)
            ctx.new_path()
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            if red > 0.5:
                ctx.set_dash([4, 4])
            ctx.set_source_rgba(*col, (0.8 - 0.25 * red) * a)
            ctx.set_line_width(1.5)
            ctx.stroke()
            ctx.set_dash([])
            if red > 0:
                text(ctx, e["refuse_label"], fx + 78, fy + 5, 12, "sansb", C["ru"], a * red, 2.4, "l")
    if lt > 0:
        text(ctx, e["demand_label"], 400, 150, 11, "sansb", C["gold"], a * smooth((lt - 3.2) / 0.5), 2.4, "c")
    qb_ = e["quote_bottom"]
    qa = a * window(t, qb_["t0"], qb_["t1"], 0.4, 0.4)
    if qa > 0:
        text(ctx, qb_["text"], W_OUT / 2, 414, 13, "serifb", (1, 1, 1), qa, 3, "c")
    qa_ = e["quote_actor"]
    qb = a * window(t, qa_["t0"], qa_["t1"], 0.4, 0.4)
    if qb > 0:
        text(ctx, qa_["text"], ux, uy + 92, 12.5, "serifb", C[act["accent"]], qb, 3, "c")

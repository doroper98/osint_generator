"""패널 versus — 두 입장 병렬, 같은 무게 (v2.1.0, render3 `P_versus`, G4 양측 균형)."""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.panels.base import panel_title
from engine.style import C
from engine.timebase import smooth
from engine.typography import rrect, text

_COLS = (("teal", 60), ("amber", 450))  # 왼쪽·오른쪽 기둥의 색·x (v3 합격 값)


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    panel_title(ctx, a, e["title"])
    for (cname, x), side in zip(_COLS, e["sides"]):
        col = C[cname]
        items = side["items"]
        fa = a * smooth((t - items[0]["t"] + 0.6) / 0.5)
        if fa <= 0:
            continue
        rrect(ctx, x, 120, 344, 262, 6)
        ctx.set_source_rgba(0.07, 0.08, 0.12, 0.92 * fa)
        ctx.fill()
        ctx.set_source_rgba(*col, fa)
        ctx.rectangle(x, 120, 344, 3)
        ctx.fill()
        text(ctx, side["title"], x + 22, 156, 16, "sansb", col, fa, 0, "l")
        for i, it in enumerate(items):
            ia = a * smooth((t - it["t"]) / 0.45)
            ctx.arc(x + 26, 196 + i * 50 - 5, 3, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, ia)
            ctx.fill()
            text(ctx, it["text"], x + 38, 196 + i * 50, 13.5, "serifb", (1, 1, 1), ia, 0, "l")
        text(ctx, side["src"], x + 22, 366, 10, "sans", C["muted"], fa, 0, "l")

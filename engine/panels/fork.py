"""패널 fork — 시나리오 분기 (v2.5.0, v2 render2 `P_fork`, 08 §8). 수치는 `panels.charts.fork`."""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.layers.routes import glow_line
from engine.panels.base import chart
from engine.style import C
from engine.timebase import ease_io, smooth
from engine.typography import rrect, text
from rules import load_rules

AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
F = load_rules().panels.charts.fork


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    ox, oy = F.origin
    ctx.arc(ox, oy, F.origin_r, 0, 2 * math.pi)
    ctx.set_source_rgba(*C["gold"], a)
    ctx.fill()
    text(ctx, e["origin"], ox, oy + F.origin_label_dy, F.origin_label_size, "sansb", C["gold"], a, F.origin_label_halo, "c")
    nb = len(e["branches"])
    for i, br in enumerate(e["branches"]):
        col = C[br["col"]]
        ty = F.card_y0 + (i + (3 - nb) / 2) * F.card_dy     # 갈래 2개면 가운데 두 자리
        f = ease_io((lt - F.grow_start_sec - i * F.grow_step_sec) / F.grow_sec)
        if f <= 0:
            continue
        pts = [(ox + (F.branch_x - ox) * s * f, oy + (ty - oy) * smooth(s * f)) for s in np.linspace(0, 1, F.samples)]
        glow_line(ctx, np.array(pts), col, a, F.line_width)
        ca = a * smooth((lt - F.card_start_sec - i * F.grow_step_sec) / F.card_fade_sec)
        rrect(ctx, F.card_x, ty - F.card_h / 2, F.card_w, F.card_h, F.card_r)
        ctx.set_source_rgba(*F.card_rgb, F.card_alpha * ca)
        ctx.fill()
        ctx.set_source_rgba(*col, ca)
        ctx.rectangle(F.card_x, ty - F.card_h / 2, F.card_bar_w, F.card_h)
        ctx.fill()
        text(ctx, br["head"], F.card_x + F.head.x, ty + F.head.y, F.head.size, "sansb", C["white"], ca, 0, "l")
        text(ctx, br["body"], F.card_x + F.body.x, ty + F.body.y, F.body.size, "sansm", C["muted"], ca, 0, "l")

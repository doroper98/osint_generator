"""패널 dual_line — 두 계열 추세 (v2.5.0, v2 render2 `P_dual`, 08 §8). 수치는 `panels.charts.dual_line`."""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.layers.routes import glow_line
from engine.panels.base import chart
from engine.style import C
from engine.timebase import clamp01, ease_io
from engine.typography import text
from rules import load_rules

AXIS = "value"   # v4.3.0 D-0087 — 축 종류(값 축). 정직성 검사 적용 = rules qa_checks.chart_targets
L = load_rules().panels.charts.dual_line


def _fmt(v: float, prefix: str, decimals: int) -> str:
    return f"{prefix}{v:.{decimals}f}"


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    X0, X1 = L.x  # noqa: N806
    Y0, Y1 = L.y  # noqa: N806
    lo, hi = e["y_min"], e["y_max"]

    def fy(v: float) -> float:
        return Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)

    for k in range(round((hi - lo) / e["y_step"]) + 1):
        v = lo + k * e["y_step"]
        ctx.set_source_rgba(*C["white"], L.grid_alpha * a)
        ctx.rectangle(X0, fy(v), X1 - X0, 1)
        ctx.fill()
        text(ctx, _fmt(v, e["y_prefix"], 0), X0 + L.tick_dx, fy(v) + L.tick_dy, L.tick_size, "sansm", C["muted"], a, 0, "r")
    n = len(e["x_labels"])
    xs = [X0 + L.x_pad + (X1 - X0 - 2 * L.x_pad) * i / (n - 1) for i in range(n)]
    for x, s_ in zip(xs, e["x_labels"]):
        text(ctx, s_, x, Y1 + L.x_label_dy, L.x_label_size, "sansm", C["muted"], a, 0, "c")
    for si, ser in enumerate(e["series"]):
        col = C[ser["col"]]
        pts = [(xs[i], fy(y)) for i, y in enumerate(ser["values"])]
        prog = ease_io((lt - L.draw_start_sec - si * L.draw_step_sec) / L.draw_sec)
        if prog <= 0:
            continue
        dense = []
        for i in range(len(pts) - 1):
            for s in np.linspace(0, 1, L.samples, endpoint=False):
                dense.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * s, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * s))
        dense.append(pts[-1])
        sub = dense[:max(2, int(len(dense) * prog))]
        glow_line(ctx, np.array(sub), col, a, L.line_width)
        for i, p in enumerate(pts):
            if len(sub) >= i * L.samples + 1:
                ctx.arc(p[0], p[1], L.point_r, 0, 2 * math.pi)
                ctx.set_source_rgba(*col, a)
                ctx.fill()
                dy = L.value_dy_above if si == 0 else L.value_dy_below
                text(ctx, _fmt(ser["values"][i], "", ser["decimals"]), p[0], p[1] + dy, L.value_size, "sansb", col, a,
                     L.value_halo, "c")
        text(ctx, ser["label"], X1 + L.name_dx, pts[-1][1] + L.name_dy, L.name_size, "sansb", col,
             a * clamp01(prog * 3 - 2), L.value_halo, "l")

"""진격 화살표 — 꼬리가 가늘고 머리 쪽이 굵은 반투명 띠 + 화살촉, 경로를 따라 자란다(prog). 원본: 4d9dc65 `uranus_sketch.arrow`·`draw_arrows`."""

from __future__ import annotations

import cairo
import numpy as np

from engine.layers.routes import catmull
from engine.projection import View
from engine.style import C
from engine.timebase import clamp01, ease_io, smooth
from sketch.campaign.fronts import ramps
from sketch.campaign.spec import CampaignSpec
from sketch.common.draw import SK, polyline, world
from sketch.common.geodesy import NORMAL_EPS

AR, F = SK.campaign.arrow, SK.fade


def arrow(ctx: cairo.Context, view: View, pts: list, prog: float, a: float, col: tuple) -> tuple[float, float] | None:
    """화살표 하나. 자란 길이 = 전체 화면 길이 × prog. 띠 가운데 점을 돌려준다(라벨 자리)."""
    if a <= F.min_alpha or prog <= F.black_min:
        return None
    S = view.to_screen_arr(catmull(world(np.array(pts)).tolist(), AR.spline))
    seg = np.linalg.norm(np.diff(S, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    k = int(np.searchsorted(L, L[-1] * prog))
    if k < 2:
        return None
    P = S[:k]
    d = np.gradient(P, axis=0)
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), NORMAL_EPS)
    u = np.linspace(0, 1, len(P))
    h0, h1 = AR.half
    half = h0 + h1 * u
    left, right = P + nrm * half[:, None], P - nrm * half[:, None]
    tip_dir = (P[-1] - P[-2]) / max(np.linalg.norm(P[-1] - P[-2]), NORMAL_EPS)
    tip = P[-1] + tip_dir * AR.tip
    ctx.new_path()
    polyline(ctx, left)
    ctx.line_to(*(P[-1] + nrm[-1] * AR.wing))
    ctx.line_to(*tip)
    ctx.line_to(*(P[-1] - nrm[-1] * AR.wing))
    for p in right[::-1]:
        ctx.line_to(*p)
    ctx.close_path()
    g = cairo.LinearGradient(*P[0], *tip)
    a0, a1 = AR.alpha
    g.add_color_stop_rgba(0, *col, a0 * a)
    g.add_color_stop_rgba(1, *col, a1 * a)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.set_source_rgba(*AR.edge_rgb, AR.edge_alpha * a)
    ctx.set_line_width(AR.edge_w)
    ctx.stroke()
    mid = P[len(P) // 2]
    return float(mid[0]), float(mid[1])


class ArrowLayer:
    def __init__(self, spec: CampaignSpec) -> None:
        self.spec = spec
        self.drawn: dict[str, int] = {}

    def draw(self, ctx: cairo.Context, view: View, t: float, labels: list) -> None:
        A = self.spec.arrows
        if A is None:
            return
        col = C[A.color]
        for it in A.items:
            prog = ease_io(clamp01((t - it.t0) / (it.t1 - it.t0)))
            a = smooth((t - it.t0) / AR.appear) * ramps(A.dim, t)
            mid = arrow(ctx, view, [tuple(p) for p in it.pts], prog, a, col)
            if mid:
                self.drawn["arrow"] = self.drawn.get("arrow", 0) + 1
                if prog > AR.label_from:
                    la = smooth((t - it.t0 - (it.t1 - it.t0) * AR.label_from) / AR.label_in) * (1 - smooth((t - A.label_end) / AR.label_out))
                    labels.append((it.name, mid, la))

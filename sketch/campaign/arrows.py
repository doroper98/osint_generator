"""진격 화살표 — 꼬리가 가늘고 머리 쪽이 굵은 반투명 띠 + 화살촉, 경로를 따라 자란다(prog). 원본: 4d9dc65 `uranus_sketch.arrow`·`draw_arrows`.

v5.12.0(D-0154 S5, 사용자 지적 "애니메이션이 드문드문"): 원본은 자란 길이를 스플라인 꼭짓점 단위(`searchsorted` 정수)로 잘라
끝이 꼭짓점 사이 길이만큼 건너뛰었다. 이제 끝점은 호 길이 보간(꼭짓점 k·k+1 사이 분수 위치 e)이고, 띠 폭·라벨 자리도 e 기준이다.
완성 상태는 원본과 같게 둔다: 원본은 prog = 1 에서도 `searchsorted`(왼쪽) 때문에 마지막 꼭짓점을 그리지 않았다 → 같은 자리에서
경로를 자르고(`drawn_path`), 라벨 자리 = 분수 위치 (e + 1) / 2(완성 때 원본 `len(P) // 2` 와 같음). 그래서 완성된 화살표는 픽셀 동일.
"""

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


def at_index(S: np.ndarray, e: float) -> np.ndarray:
    """꼭짓점 분수 위치 e 의 점(꼭짓점 사이 선형)."""
    i = min(int(e), len(S) - 1)
    f = e - i
    return S[i] if f <= 0 or i + 1 >= len(S) else S[i] + (S[i + 1] - S[i]) * f


def drawn_path(S: np.ndarray) -> np.ndarray:
    """원본이 완성 때 그린 꼭짓점들(마지막 꼭짓점 앞까지 — searchsorted 왼쪽 규칙)."""
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))])
    return S[: int(np.searchsorted(L, L[-1]))]


def grown(S: np.ndarray, prog: float) -> tuple[np.ndarray, np.ndarray, float] | None:
    """화면 경로 S 를 길이 × prog 까지 자른다 → (꼭짓점 + 보간 끝점, 띠 폭 매개 u, 끝의 분수 위치 e). 너무 짧으면 None."""
    seg = np.linalg.norm(np.diff(S, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    target = L[-1] * prog
    i = int(np.searchsorted(L, target, side="right")) - 1
    i = min(max(i, 0), len(S) - 1)
    f = (target - L[i]) / seg[i] if i < len(seg) and seg[i] > NORMAL_EPS else 0.0
    e = i + f
    if e < 1:
        return None
    P = S[: i + 1]
    if f * (seg[i] if i < len(seg) else 0.0) > NORMAL_EPS:
        P = np.vstack([P, at_index(S, e)])
    u = np.append(np.arange(i + 1) / e, [1.0])[: len(P)]
    return P, u, e


def arrow(ctx: cairo.Context, view: View, pts: list, prog: float, a: float, col: tuple) -> tuple[float, float] | None:
    """화살표 하나. 자란 길이 = 전체 화면 길이 × prog(호 길이 보간). 띠 가운데 점을 돌려준다(라벨 자리)."""
    if a <= F.min_alpha or prog <= F.black_min:
        return None
    S = drawn_path(view.to_screen_arr(catmull(world(np.array(pts)).tolist(), AR.spline)))
    g_ = grown(S, prog)
    if g_ is None:
        return None
    P, u, e = g_
    if len(P) < 2:
        return None
    d = np.gradient(P, axis=0)
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), NORMAL_EPS)
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
    mid = at_index(S, (e + 1) * 0.5)
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

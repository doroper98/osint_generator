"""패널 공통 — 덮개·제목·곡선 (v2.1.0, render3 `panel_title, edge_curve, draw_panel`)."""

from __future__ import annotations

from typing import Callable

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.style import PANEL, C, W_OUT
from engine.timebase import window
from engine.typography import text
from rules import load_rules

_CHARTS = load_rules().panels.charts

PanelFn = Callable[[cairo.Context, RenderCtx, float, dict, float], None]


def panel_title(ctx: cairo.Context, a: float, s: str, sub: str | None = None) -> None:
    text(ctx, s, W_OUT / 2, PANEL.title_y, PANEL.title_size, "serifb", (1, 1, 1), a, 0, "c")
    if sub:
        text(ctx, sub, W_OUT / 2, PANEL.subtitle_y, PANEL.subtitle_size, "sansm", C["muted"], a, 0, "c")


def edge_curve(x0: float, y0: float, x1: float, y1: float, prog: float, n: int = 36) -> np.ndarray:
    cx = (x0 + x1) / 2
    pts = []
    for s in np.linspace(0, prog, n):
        pts.append(((1 - s) ** 3 * x0 + 3 * (1 - s) ** 2 * s * cx + 3 * (1 - s) * s * s * cx + s ** 3 * x1,
                    (1 - s) ** 3 * y0 + 3 * (1 - s) ** 2 * s * y0 + 3 * (1 - s) * s * s * y1 + s ** 3 * y1))
    return np.array(pts)


def panel_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], PANEL.fade_sec, PANEL.fade_sec)


def draw_panel_cover(ctx: cairo.Context, a: float) -> None:
    ctx.set_source_rgba(0.025, 0.03, 0.045, PANEL.cover_alpha * a)
    ctx.paint()


def make_panel_renderer(fn: PanelFn) -> Callable[[cairo.Context, RenderCtx, float, dict], None]:
    """덮개를 칠한 뒤 종류별 본문을 그린다 — v3 draw_panel 과 같은 순서."""

    def render(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
        a = panel_alpha(t, e)
        if a <= 0.01:
            return
        draw_panel_cover(ctx, a)
        fn(ctx, R, t, e, a)

    render.__name__ = f"panel_{fn.__name__}"
    return render


def prov_tag_text(pv: dict | None) -> str | None:
    """08 §9 — verified + 출처 있음이면 None(태그 없음). v3 사실 패널처럼 provenance 가 없는 패널도 None."""
    if pv is None:
        return None
    if pv["verification"] == "verified" and pv["sources"]:
        return None
    return "추정" if pv["sources"] else "추정 · 출처 미기재"


def prov_tag(ctx: cairo.Context, e: dict, a: float) -> str | None:
    """추정/출처 태그(v2 `prov_tag` 공통화). 그린 문구를 돌려준다(provenance panels.used[].tag)."""
    s = prov_tag_text(e.get("provenance"))
    if s is None or a <= 0.01:
        return s
    from engine.typography import rrect, tw  # noqa: PLC0415

    T = _CHARTS.prov_tag  # noqa: N806
    w = tw(ctx, s, T.size, "sansb")
    x = W_OUT - T.x_right
    col = C[T.color]
    rrect(ctx, x - w - T.pad_x, T.y + T.box_dy, w + T.pad_x, T.h, T.r)
    ctx.set_source_rgba(*col, T.alpha * a)
    ctx.set_line_width(T.line_width)
    ctx.stroke()
    text(ctx, s, x - T.pad_x / 2, T.y + T.text_dy, T.size, "sansb", col, a, 0, "r")
    return s

"""선박 점·폭발 (v2.1.0, render3 `draw_ships, draw_boom`)."""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.projection import View
from engine.style import C
from engine.timebase import clamp01, ease_out, window


def _ship_points(R: RenderCtx, box: tuple[float, float, float, float], n: int, seed: int) -> list:  # noqa: N803
    """육지를 피한 무작위 선박 위치(v3: rng 4, 150점, 페르시아만 상자). 컨텍스트 캐시에 한 번만 만든다."""
    key = f"ships:{box}:{n}:{seed}"
    if key not in R.cache:
        from shapely.geometry import Point, Polygon
        from shapely.prepared import prep

        land = [prep(Polygon(r)) for k, rs in R.assets.geo["fine"].items() for r in rs if len(r) > 3]
        rng = np.random.default_rng(seed)
        pts = []
        while len(pts) < n:
            lo, la = rng.uniform(box[0], box[1]), rng.uniform(box[2], box[3])
            p = Point(lo, la)
            if not any(L.contains(p) for L in land):
                pts.append((lo, la, rng.uniform(0, 1)))
        R.cache[key] = pts
    return R.cache[key]


def draw_ships(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.8, 0.6)
    for lo, la, ph in _ship_points(R, tuple(e["box"]), e["n"], e["seed"]):
        if t < e["t0"] + ph * 1.6:
            continue
        x, y = view.xy(lo, la)
        tw_ = 0.6 + 0.4 * math.sin(t * 2 + ph * 9)
        ctx.arc(x, y, 1.7, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.82, 0.5, 0.85 * a * tw_)
        ctx.fill()


def draw_boom(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.05, 0.8)
    x, y = view.xy(e["lon"], e["lat"])
    lt = t - e["t0"]
    for k in range(3):
        r = 6 + 50 * ease_out((lt - k * 0.12) / 1.2)
        ctx.arc(x, y, max(r, 0.1), 0, 2 * math.pi)
        ctx.set_source_rgba(*C["amber"], 0.6 * a * (1 - clamp01(lt / 1.6)))
        ctx.set_line_width(2)
        ctx.stroke()

"""항로·유조선·봉쇄선 (v2.1.0, render3 `catmull, route_uv, glow_line, tanker, draw_route, draw_tanker_loop, draw_barrier`)."""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.projection import View, ym
from engine.style import C
from engine.timebase import ease_io, ease_out, smooth, window
from engine.typography import text


def catmull(pts: list, n: int = 10) -> np.ndarray:
    P_ = [pts[0]] + list(pts) + [pts[-1]]  # noqa: N806
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = map(np.array, P_[i - 1:i + 3])
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(np.array(P_[-2]))
    return np.array(out)


def route_uv(pts: list) -> np.ndarray:
    uv = [(lo, ym(la)) for lo, la in pts]
    return catmull(uv, 12)


def glow_line(ctx: cairo.Context, S_: np.ndarray, col: tuple, a: float, w: float, dash: list | None = None) -> None:  # noqa: N803
    ctx.new_path()
    ctx.move_to(*S_[0])
    for x, y in S_[1:]:
        ctx.line_to(x, y)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash:
        ctx.set_dash(dash)
    for wd, al in ((w * 4.5, 0.08), (w * 2.2, 0.22), (w, 0.95)):
        ctx.set_source_rgba(*col, al * a)
        ctx.set_line_width(wd)
        ctx.stroke_preserve()
    ctx.new_path()
    ctx.set_dash([])


def tanker(ctx: cairo.Context, x: float, y: float, ang: float, a: float, sc: float = 1.0) -> None:
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(sc, sc)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 15)
    g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.45 * a)
    g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 15, 0, 2 * math.pi)
    ctx.fill()
    ctx.new_path()
    ctx.move_to(9, 0)
    ctx.line_to(5, -3)
    ctx.line_to(-8, -3)
    ctx.line_to(-8, 3)
    ctx.line_to(5, 3)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill_preserve()
    ctx.set_source_rgba(0, 0, 0, 0.5 * a)
    ctx.set_line_width(0.6)
    ctx.stroke()
    ctx.rectangle(-7, -2, 3, 4)
    ctx.set_source_rgba(0.2, 0.25, 0.3, a)
    ctx.fill()
    ctx.restore()


def draw_route(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.35, 0.6)
    if a <= 0.01:
        return
    if "uv" not in e:
        e["uv"] = route_uv(e["pts"])
    S_ = view.uvs(e["uv"])  # noqa: N806
    prog = ease_io((t - e["t0"]) / e["grow"]) if e["grow"] > 0.05 else 1
    n = max(2, int(len(S_) * prog))
    sub = S_[:n]
    col = C[e["col"]]
    glow_line(ctx, sub, col, a * (0.75 if e.get("glow_only") else 1), 1.9, dash=[5, 4] if e.get("dashed") else None)
    if e.get("ship") and len(sub) > 1:
        (x0, y0), (x1, y1) = sub[-2], sub[-1]
        tanker(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a)
    if e.get("dashed") and prog >= 0.98:
        (x0, y0), (x1, y1) = sub[-2], sub[-1]
        ang = math.atan2(y1 - y0, x1 - x0)
        ctx.new_path()
        ctx.move_to(x1 + math.cos(ang) * 3, y1 + math.sin(ang) * 3)
        for s_ in (2.5, -2.5):
            ctx.line_to(x1 - math.cos(ang + s_ / 6) * 9, y1 - math.sin(ang + s_ / 6) * 9)
        ctx.close_path()
        ctx.set_source_rgba(*col, a)
        ctx.fill()
    if e.get("label") and prog >= 0.99:
        x, y = S_[len(S_) // 2]
        text(ctx, e["label"], x, y - 11, 11.5, "sansb", col, a * smooth((t - e["t0"] - e["grow"]) / 0.4), 3, "c")


def draw_tanker_loop(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.6, 0.6)
    if "uv" not in e:
        e["uv"] = route_uv(e["pts"])
    S_ = view.uvs(e["uv"])  # noqa: N806
    for k in range(3):
        f = ((t - e["t0"]) / 26.0 + k / 3) % 1.0
        i = int(f * (len(S_) - 2))
        (x0, y0), (x1, y1) = S_[i], S_[i + 1]
        tanker(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a * 0.95, 0.85)


def draw_barrier(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.4, 0.5)
    k = ease_out((t - e["t0"]) / 0.8)
    x0, y0 = view.xy(*e["p0"])
    x1, y1 = view.xy(*e["p1"])
    xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    glow_line(ctx, np.array([[x0, y0], [xe, ye]]), C["ru"], a, 3.2)
    if k > 0.95:
        text(ctx, e["label"], (x0 + x1) / 2 - 12, (y0 + y1) / 2 + 4, 12.5, "sansb", C["ru"], a, 3, "r")

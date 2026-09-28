"""지점 마커 (v2.1.0, render3 `icon, draw_marker`). 차지한 영역은 R.reserved 에 올려 라벨이 피한다."""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.projection import View
from engine.style import C, H_OUT, W_OUT
from engine.timebase import ease_out, smooth, window
from engine.typography import text, tw


def marker_label_alpha(box: tuple[float, float, float, float], zones: list) -> float:
    from engine.reserved import marker_label_alpha as f  # noqa: PLC0415 — 순환 회피

    return f(box, zones)


def icon(ctx: cairo.Context, kind: str, x: float, y: float, col: tuple, a: float) -> None:
    if kind == "boom":
        ctx.new_path()
        for k in range(10):
            ang = k * math.pi / 5 + 0.2
            r1, r2 = (9, 4) if k % 2 == 0 else (6, 3)
            ctx.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1)
            ctx.line_to(x + math.cos(ang + math.pi / 10) * r2, y + math.sin(ang + math.pi / 10) * r2)
        ctx.close_path()
        ctx.set_source_rgba(*C["amber"], a)
        ctx.fill()
    else:
        ctx.arc(x, y, 3.3, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6 * a)
        ctx.set_line_width(1)
        ctx.stroke()


_SIDE = {"right": (12, 4, "l"), "left": (-12, 4, "r"), "top": (0, -14, "c"), "bottom": (0, 22, "c")}


def draw_marker(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.35, 0.5)
    if a <= 0.01:
        return
    x, y = view.xy(e["lon"], e["lat"])
    lt = t - e["t0"]
    if x < -80 or x > W_OUT + 80 or y < -40 or y > H_OUT + 40:
        return
    col = C["gold"] if e.get("hl") else C["white"]
    for k in range(2):
        f = ((lt * 0.5) + k / 2) % 1.0
        r = 4 + 20 * ease_out(f)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*col, 0.5 * (1 - f) * a)
        ctx.set_line_width(1.3)
        ctx.stroke()
    icon(ctx, e.get("icon") or "dot", x, y, col, a * ease_out(lt / 0.3))
    side = e.get("side") or "right"
    la = a * smooth((lt - 0.2) / 0.4)
    dx, dy, anc = _SIDE[side]
    w = tw(ctx, e["label"], 13, "sansb") + 20
    box = (x - 14 if anc != "r" else x - w, y - 16, x + w if anc != "r" else x + 14, y + 26)
    la *= marker_label_alpha(box, R.zones)   # 카드 뒤 라벨은 흐린다 — 점은 사실 위치라 그대로(D-0033)
    text(ctx, e["label"], x + dx, y + dy, 13, "sansb", (1, 1, 1), la, 3.2, anc)
    if e.get("sub"):
        text(ctx, e["sub"], x + dx, y + dy + 15, 10.5, "sansm", C["gold"], la, 3, anc)
    R.reserved.append(box)

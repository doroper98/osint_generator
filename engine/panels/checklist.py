"""패널 checklist — 확인된 사실(체크 2획 애니메이션) (v2.5.0, v2 render2 `P_check`, 08 §8). 수치는 `panels.charts.checklist`."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.panels.base import chart
from engine.style import C
from engine.timebase import ease_out, smooth
from engine.typography import rrect, text
from rules import load_rules

K = load_rules().panels.charts.checklist


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    b = K.box
    for i, s_ in enumerate(e["items"]):
        y = K.y0 + i * K.dy
        t_i = K.appear_start_sec + i * K.appear_step_sec
        f = smooth((lt - t_i) / K.appear_sec)
        if f <= 0:
            continue
        top = y + K.box_top_dy
        rrect(ctx, K.box_x, top, b, b, K.box_r)
        ctx.set_source_rgba(*C["green"], K.box_alpha * f * a)
        ctx.fill()
        ck = ease_out((lt - t_i - K.check_delay_sec) / K.check_sec)
        (p0x, p0y), (p1x, p1y), (p2x, p2y) = ((K.box_x + px, top + py) for px, py in K.check_points)
        short = min(1, ck * 2)                  # 앞 절반 = 짧은 획, 뒤 절반 = 긴 획
        ctx.new_path()
        ctx.move_to(p0x, p0y)
        ctx.line_to(p0x + (p1x - p0x) * short, p0y + (p1y - p0y) * short)
        if ck > 1 / 2:
            k = (ck - 1 / 2) * 2
            ctx.line_to(p1x + (p2x - p1x) * k, p1y + (p2y - p1y) * k)
        ctx.set_source_rgba(*C["green"], a)
        ctx.set_line_width(K.check_width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        text(ctx, s_, K.text_x, y, K.text_size, "sansb", C["white"], f * a, 0, "l")
    if e["footer"]:
        fb = a * smooth((lt - K.footer_sec) / K.footer_fade_sec)
        text(ctx, e["footer"], K.text_x, K.footer_y, K.footer_size, "serif", C["muted"], fb, 0, "l")

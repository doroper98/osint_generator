"""패널 checklist — 확인된 사실(체크 2획 애니메이션) (v2.5.0, v2 render2 `P_check`, 08 §8). 수치는 `panels.charts.checklist`.

v7.4.0 UF-400·UF-401(영상 분석 D11) — style open: 가설·후보 목록. 번호 칸을 먼저 비워 보이고 at 시각에 채운다(체크 없음)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.panels.base import chart
from engine.style import C
from engine.timebase import ease_out, smooth
from engine.typography import rrect, text
from rules import load_rules

AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
K = load_rules().panels.charts.checklist


def _draw_open(ctx: cairo.Context, t: float, e: dict, a: float) -> None:
    """열린 칸: 번호 칸(점선 테두리)이 차례로 나타나고, at[i] 에 칸이 채워지며 문구가 들어온다. 체크 표시 없음."""
    O = K.open  # noqa: N806
    lt = t - e["t0"]
    at = e.get("at") or [e["t0"] + K.appear_start_sec + i * K.appear_step_sec for i in range(len(e["items"]))]
    for i, s_ in enumerate(e["items"]):
        y = K.y0 + i * K.dy
        ra = a * smooth((lt - O.reveal_start_sec - i * O.reveal_step_sec) / O.reveal_fade_sec)
        if ra <= 0:
            continue
        top = y + K.box_top_dy - (O.slot_h - K.box) / 2
        fa = smooth((t - at[i]) / O.fill_fade_sec)
        rrect(ctx, K.box_x, top, O.slot_w, O.slot_h, O.slot_r)
        if fa > 0:
            ctx.set_source_rgba(*C["white"], O.fill_alpha * fa * ra)
            ctx.fill_preserve()
        ctx.set_source_rgba(*C["white"], O.slot_line_alpha * ra)
        ctx.set_line_width(O.slot_line_w)
        ctx.set_dash(O.slot_dash if fa < 1 else [])
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, str(i + 1), K.box_x + K.box / 2, y, O.num_size, "sansb", C["muted"], ra, 0, "c")
        text(ctx, s_, K.text_x, y, K.text_size, "sansb", C["white"], fa * ra, 0, "l")


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    if e.get("style") == "open":
        _draw_open(ctx, t, e, a)
        if e["footer"]:
            text(ctx, e["footer"], K.text_x, K.footer_y, K.footer_size, "serif", C["muted"],
                 a * smooth((t - e["t0"] - K.footer_sec) / K.footer_fade_sec), 0, "l")
        return
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

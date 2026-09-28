"""우상단 날짜 배지 — 모서리의 유일한 요소 (v2.1.0, render3 `draw_date`, 09 §4, C0 "모서리에는 날짜만")."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, DATE_BADGE, W_OUT
from engine.timebase import smooth
from engine.typography import text

Box = tuple[float, float, float, float]


def date_box() -> Box:
    """날짜 배지가 차지하는 화면 상자(x0, y0, x1, y1) — 가장 긴 날짜('YYYY. MM. DD')를 덮는 폭. 예약 영역 판정의 유일한 정의
    (미디어 배치 슬롯 후보·checks overlap 이 같이 쓴다, v3.6.0 NB23)."""
    B = DATE_BADGE  # noqa: N806
    return (W_OUT - B.x_right - B.size * 8, 0, W_OUT, B.underline_y + 2)


def draw_date(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    tb = R.tb
    sid = tb.cur_sentence(t)
    if sid is None or tb.in_fullcard(t):
        return
    d = tb.sent[sid].date
    prev = None
    t_ch = 0.0
    for s_ in tb.order:
        if tb.sent[s_].t0 - 0.3 > t:
            break
        if tb.sent[s_].date != prev:
            prev = tb.sent[s_].date
            t_ch = tb.sent[s_].t0 - 0.3
    B = DATE_BADGE  # noqa: N806
    k = smooth((t - t_ch) / B.slide_sec)
    a = 0.95 * k
    txt = d.replace(".", ". ") if len(d) > 4 else d
    w = text(ctx, txt, W_OUT - B.x_right, B.y - (1 - k) * B.slide_px, B.size, B.font, (1, 1, 1), a, 3, "r")
    ctx.set_source_rgba(*C["gold"], 0.9 * a)
    ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
    ctx.fill()

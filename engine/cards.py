"""정보 카드 — 태그·큰 숫자·줄·출처 (v2.1.0, render3 `draw_card`)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, CARD, W_OUT
from engine.timebase import ease_out, window
from engine.typography import font, rrect, text, tw


def card_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec)


def card_geom(ctx: cairo.Context, e: dict) -> tuple[float, float, float, float, float]:
    """카드 상자 (x, y, 폭, 높이, 큰 숫자 줄 높이) — 슬라이드 전 제자리. RESERVED 영역(D-0033)과 그리기가 같이 쓴다."""
    K = CARD  # noqa: N806
    lines = e.get("lines") or []
    wdt = K.min_w
    font(ctx, "sansm", K.line_size)
    for s_ in lines:
        wdt = max(wdt, ctx.text_extents(s_).x_advance + 44)
    wdt = max(wdt, tw(ctx, e["tag"], K.tag_size, "sansb") + 44)
    bh = 0
    if e.get("bigs"):
        bw = 0
        for big, cap in e["bigs"]:
            bw += max(tw(ctx, big, K.big_size, "disp"), tw(ctx, cap, 11, "sansm")) + 26
        wdt = max(wdt, bw + 20)
        bh = 62
    if e.get("src"):
        wdt = max(wdt, tw(ctx, e["src"], K.src_size, "sans") + 40)
    h = 42 + bh + 21 * len(lines) + (18 if e.get("src") else 0)
    return W_OUT - wdt - K.x_right_margin, e.get("y") or K.y, wdt, h, bh


def draw_card(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    K = CARD  # noqa: N806
    a = card_alpha(t, e)
    if a <= 0.01:
        return
    slide = (1 - ease_out((t - e["t0"]) / 0.55)) * K.slide_px
    lines = e.get("lines") or []
    acc = C[e["accent"]]
    x0, y, wdt, h, bh = card_geom(ctx, e)
    x = x0 + slide
    rrect(ctx, x, y, wdt, h, 5)
    ctx.set_source_rgba(0.05, 0.06, 0.09, 0.86 * a)
    ctx.fill()
    ctx.set_source_rgba(*acc, a)
    ctx.rectangle(x, y + 10, 3, h - 20)
    ctx.fill()
    text(ctx, e["tag"], x + 18, y + 23, K.tag_size, "sansb", acc, a, 0, "l", spacing=0.4)
    yy = y + 32
    if e.get("bigs"):
        xx = x + 18
        for big, cap in e["bigs"]:
            text(ctx, big, xx, yy + 32, K.big_size, "disp", (1, 1, 1), a, 0, "l")
            text(ctx, cap, xx, yy + 50, 11, "sansm", C["muted"], a, 0, "l")
            xx += max(tw(ctx, big, K.big_size, "disp"), tw(ctx, cap, 11, "sansm")) + 26
        yy += bh
    for i, s_ in enumerate(lines):
        text(ctx, s_, x + 18, yy + 17 + 21 * i, K.line_size, "serifb" if e.get("quote") else "sansm", (0.94, 0.92, 0.9), a,
             0, "l")
    if e.get("src"):
        text(ctx, e["src"], x + 18, y + h - 12, K.src_size, "sans", C["muted"], a * 0.9, 0, "l")

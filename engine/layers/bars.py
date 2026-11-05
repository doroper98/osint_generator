"""후보별 득표율 막대 상자 `bars` (v7.4.0 back_and_forth D-0303 §3, 사용자 의견 UF-170).

"주별 선거 결과를 보여줄때 막대그래프로 직관적으로 인지할 수 있도록" — 지도 위 그 주 옆 작은 상자에 2~3줄 가로 막대.
막대 길이 = pct/100 × 막대 폭(모든 주가 같은 축척 — 한 세계, UF-135·138). 수치·크기·타이밍은 rules `bars`(코드 리터럴 없음, P3).
자리 = `bars_box`(연출 side 가 화면 안이면 그대로, 아니면 rules bars.side_order 차례로 첫 맞는 자리) — 렌더·검사가 같은 함수를 쓴다.
차지한 상자는 R.reserved 에 올려 지명이 피한다(마커와 같은 방식).
"""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.projection import View
from engine.style import H_OUT, W_OUT, map_c, map_halo
from engine.timebase import ease_out, window
from engine.typography import HALO_RGB, text
from rules import load_rules

B = load_rules().bars
SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from   # 자막 구역 위에서 멈춘다
DATE_BOX = (702.0, 0.0, float(W_OUT), 56.0)   # 날짜 뱃지 자리(checks badge_clipped 와 같은 상자)


def box_size(e: dict) -> tuple[float, float]:
    """상자 (폭, 높이) — 줄 수에 따라."""
    return B.box_w, B.pad * 2 + len(e["rows"]) * B.row_h + B.src_h


def _place(side: str, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    if side == "right":
        x0, y0 = x + B.gap_px, y - h / 2
    elif side == "left":
        x0, y0 = x - B.gap_px - w, y - h / 2
    elif side == "below":
        x0, y0 = x - w / 2, y + B.gap_px
    else:   # above
        x0, y0 = x - w / 2, y - B.gap_px - h
    return x0, y0, x0 + w, y0 + h


def _fits(b: tuple[float, float, float, float]) -> bool:
    m = B.safe_margin_px
    if b[0] < m or b[2] > W_OUT - m or b[1] < m or b[3] > SUB_Y - m:
        return False
    return not (b[0] < DATE_BOX[2] and b[2] > DATE_BOX[0] and b[1] < DATE_BOX[3] and b[3] > DATE_BOX[1])


def bars_box(view: View, e: dict) -> tuple[tuple[float, float, float, float], bool]:
    """(상자, 화면 안 여부). 연출 side 를 먼저, 안 맞으면 side_order 차례(결정적)."""
    x, y = view.to_screen(e["lon"], e["lat"])
    w, h = box_size(e)
    order = [e.get("side") or "right"] + [s for s in B.side_order if s != (e.get("side") or "right")]
    for s in order:
        b = _place(s, x, y, w, h)
        if _fits(b):
            return b, True
    return _place(order[0], x, y, w, h), False


def _round_rect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def draw_bars(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], B.fade_sec, B.fade_sec)
    if a <= 0.01:
        return
    (x0, y0, x1, y1), _ = bars_box(view, e)
    w, h = x1 - x0, y1 - y0
    st = view.stage
    halo = map_halo(st) or HALO_RGB
    ink = map_c(st, "white")
    _round_rect(ctx, x0, y0, w, h, B.radius)
    ctx.set_source_rgba(*halo, B.bg_a * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink, 0.18 * a)
    ctx.set_line_width(0.8)
    ctx.stroke()
    bx = x0 + B.pad + B.name_w
    bw = w - B.pad * 2 - B.name_w - B.pct_w
    for i, r in enumerate(e["rows"]):
        cy = y0 + B.pad + i * B.row_h + B.row_h / 2
        text(ctx, r["name"], x0 + B.pad, cy + B.name_size * 0.36, B.name_size, "sansb", ink, a, 0, "l")
        ctx.rectangle(bx, cy - B.bar_h / 2, bw, B.bar_h)   # 100 % 자리(축척 기준선)
        ctx.set_source_rgba(*ink, B.track_a * a)
        ctx.fill()
        g = ease_out(max(0.0, min(1.0, (t - e["t0"] - i * B.row_stagger_sec) / B.grow_sec)))
        ln = bw * r["pct"] / 100.0 * g
        col = map_c(st, r["col"])
        ctx.rectangle(bx, cy - B.bar_h / 2, ln, B.bar_h)
        ctx.set_source_rgba(*col, a)
        ctx.fill()
        if e["status"] == "counting" and ln > 0:   # 개표 중 = 막대 끝 점선(확정처럼 보이지 않게)
            ctx.set_dash(list(B.counting_dash))
            ctx.move_to(bx + ln, cy - B.bar_h / 2 - 1.5)
            ctx.line_to(bx + ln, cy + B.bar_h / 2 + 1.5)
            ctx.set_source_rgba(*ink, a)
            ctx.set_line_width(1.0)
            ctx.stroke()
            ctx.set_dash([])
        text(ctx, f"{r['pct']:.1f}%", x1 - B.pad, cy + B.pct_size * 0.36, B.pct_size, "sansb", ink, a * (0.35 + 0.65 * g), 0, "r")
    src = e["src"] + (f" · {B.counting_note}" if e["status"] == "counting" else "")
    text(ctx, src, x0 + B.pad, y1 - B.pad + 1, B.src_size, "sansm", ink, 0.72 * a, 0, "l")
    R.reserved.append((x0, y0, x1, y1))


__all__ = ["bars_box", "box_size", "draw_bars"]

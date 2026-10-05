"""지점 마커 (v2.1.0, render3 `icon, draw_marker`). 차지한 영역은 R.reserved 에 올려 라벨이 피한다.

v5.2.0 back_and_forth D-0133 §1 — 차트 아일랜드 안 마커(`in_island`)만: 라벨 글자 상자가 상자 가장자리 − island.chart.label_flip_pad 를
넘으면 점 반대쪽에 붙이고(오른쪽 → 왼쪽), 그래도 넘치면 상자 안으로 클램프(`island_label`). 지도·시간축 무대 마커는 무변경(골든).
"""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.projection import View
from engine.style import C, ISLAND, W_OUT
from engine.timebase import ease_out, smooth, window
from engine.typography import text, tw
from rules import load_rules

MK = load_rules().layout_480p.marker   # v4.8.0 D-0101 §3 — 라벨·부제 글자(옛 리터럴 13·10.5)


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


def marker_box(ctx: cairo.Context, e: dict, x: float, y: float, with_sub: bool = False) -> tuple[float, float, float, float]:
    """점·라벨이 차지하는 상자. 예약 영역(R.reserved)은 v3 그대로 라벨 폭만(골든 불변).
    with_sub=True 는 화면 밖 검사용 — 부제가 라벨보다 길면 그 폭까지(D-0049 쟁점 4)."""
    side = e.get("side") or "right"
    anc = _SIDE[side][2]
    w = tw(ctx, e["label"], MK.label_size, "sansb") + 20
    if with_sub and e.get("sub"):
        w = max(w, tw(ctx, e["sub"], MK.sub_size, "sansm") + 20)
    if with_sub and anc == "c":   # v5.6.0 RENDER-AP-009 — 위·아래 라벨은 점 가운데 정렬로 그려진다(검사 상자도 그대로)
        dy = _SIDE[side][1]
        x0, x1 = _span(side, x, label_w(ctx, e), center_clamp(ctx, e, x))
        y0 = min(y - 16, y + dy - MK.label_size)
        y1 = max(y + 16, y + dy + (MK.sub_dy + MK.sub_size * 0.3 if e.get("sub") else MK.label_size * 0.3))
        return (min(x0 - 4, x - 14), y0, max(x1 + 4, x + 14), y1)
    return (x - 14 if anc != "r" else x - w, y - 16, x + w if anc != "r" else x + 14, y + 26)


_FLIP = {"right": "left", "left": "right"}


CENTER_PAD = 4.0   # v5.6.0 RENDER-AP-009 — 위·아래(가운데 정렬) 라벨이 화면 가장자리에서 잘리지 않게 안쪽으로 미는 여백(px)


def center_clamp(ctx: cairo.Context, e: dict, x: float) -> float:
    """위·아래 라벨(가운데 정렬)이 화면 밖으로 나가면 안쪽으로 미는 x 이동. 점은 사실 위치라 그대로, 글자만 민다(D-0033 원칙)."""
    side = e.get("side") or "right"
    if _SIDE[side][2] != "c":
        return 0.0
    x0, x1 = _span(side, x, label_w(ctx, e))
    if x0 < CENTER_PAD:
        return CENTER_PAD - x0
    if x1 > W_OUT - CENTER_PAD:
        return W_OUT - CENTER_PAD - x1
    return 0.0


def label_w(ctx: cairo.Context, e: dict) -> float:
    """라벨·부제 글자 폭(같은 기준점·같은 정렬로 그린다 — 넓은 쪽)."""
    w = tw(ctx, e["label"], MK.label_size, "sansb")
    return max(w, tw(ctx, e["sub"], MK.sub_size, "sansm")) if e.get("sub") else w


def _span(side: str, x: float, w: float, shift: float = 0.0) -> tuple[float, float]:
    dx, _, anc = _SIDE[side]
    x0 = x + dx + shift - (w if anc == "r" else w / 2 if anc == "c" else 0)
    return x0, x0 + w


def island_label(ctx: cairo.Context, e: dict, x: float, vw: float) -> tuple[str, float, str]:
    """아일랜드 마커 라벨 자리(D-0133 §1) → (side, x 이동, 처리 none|flip|clamp). vw = 상자 폭(뷰포트)."""
    pad = ISLAND.chart.label_flip_pad
    side = e.get("side") or "right"
    w = label_w(ctx, e)
    x0, x1 = _span(side, x, w)
    if x0 >= pad and x1 <= vw - pad:
        return side, 0.0, "none"
    how = "none"
    if side in _FLIP:
        f0, f1 = _span(_FLIP[side], x, w)
        if f0 >= pad and f1 <= vw - pad:
            return _FLIP[side], 0.0, "flip"
        if (x1 > vw - pad and side == "right") or (x0 < pad and side == "left"):
            side, x0, x1, how = _FLIP[side], f0, f1, "flip"
    lo, hi = pad, vw - pad - w
    shift = (max(lo, min(x0, hi)) if hi >= lo else lo) - x0   # 폭이 상자보다 넓으면 왼쪽 여백에 붙는다(넘친 오른쪽은 검사가 잡는다)
    return side, shift, "clamp" if abs(shift) > 1e-6 else how


def island_label_rect(ctx: cairo.Context, e: dict, x: float, y: float, vw: float) -> tuple[float, float, float, float, str]:
    """아일랜드 마커 라벨·부제 글자 상자(상자 좌표 x0, y0, x1, y1)와 처리 — checks island_label_clip·overlap 이 렌더와 같은 자리를 잰다."""
    side, shift, how = island_label(ctx, e, x, vw)
    x0, x1 = _span(side, x, label_w(ctx, e), shift)
    by = y + _SIDE[side][1]
    bot = by + MK.sub_dy + MK.sub_size * 0.25 if e.get("sub") else by + MK.label_size * 0.25
    return x0, by - MK.label_size, x1, bot, how


def draw_marker(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.35, 0.5)
    if a <= 0.01:
        return
    x, y = view.to_screen(*e["world"])
    lt = t - e["t0"]
    if x < -80 or x > view.vw + 80 or y < -40 or y > view.vh + 40:
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
    side, shift = e.get("side") or "right", 0.0
    if e.get("in_island"):   # v5.2.0 D-0133 §1 — 아일랜드 상자 밖으로 나가는 라벨은 반대쪽·클램프(상자 좌표, view.vw = 상자 폭)
        side, shift, _ = island_label(ctx, e, x, view.vw)
    else:
        shift = center_clamp(ctx, e, x)
    la = a * smooth((lt - 0.2) / 0.4)
    dx, dy, anc = _SIDE[side]
    box = marker_box(ctx, {**e, "side": side} if side != (e.get("side") or "right") else e, x + shift, y)
    la *= marker_label_alpha(box, R.zones)   # 카드 뒤 라벨은 흐린다 — 점은 사실 위치라 그대로(D-0033)
    text(ctx, e["label"], x + dx + shift, y + dy, MK.label_size, "sansb", (1, 1, 1), la, 3.2, anc)
    if e.get("sub"):
        text(ctx, e["sub"], x + dx + shift, y + dy + MK.sub_dy, MK.sub_size, "sansm", C["gold"], la, 3, anc)
    R.reserved.append(box)

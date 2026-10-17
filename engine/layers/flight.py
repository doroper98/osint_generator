"""비행 이벤트 — 출발 발광 · 점선 꼬리선 · 아이콘 · 착탄 링 · 위성 인셋 (v7.3.0, back_and_forth D-0206 §4).

개략 표현이다(사용자 결정 D232 U3-a): 비행 시간은 거리와 무관하게 `rules flight.dur_sec`, 출발 위치는 점·라벨 없는 발광,
꼬리선은 점선. 착탄 링은 `effects.draw_boom` 을 그대로 부른다(새 링 모양 금지 — v3 합격 문법).
수치는 전부 `rules/video_rules.yaml flight` 에서 읽는다(tests/anti_inertia/test_no_magic_numbers).
"""

from __future__ import annotations

import math
from typing import Callable, Optional

import cairo

from engine.context import RenderCtx
from engine.layers.effects import draw_boom
from engine.layers.media import draw_inset
from engine.projection import View
from engine.style import map_c
from engine.timebase import ease_out, window
from rules import load_rules

F = load_rules().flight

Pt = tuple[float, float]


def hit_time(e: dict) -> float:
    """착탄 시각 = t0 + dur_sec(코드 계산, P8)."""
    return e["t0"] + F.dur_sec


def bezier(s: Pt, c: Pt, e: Pt, u: float) -> Pt:
    v = 1 - u
    return (v * v * s[0] + 2 * v * u * c[0] + u * u * e[0], v * v * s[1] + 2 * v * u * c[1] + u * u * e[1])


def control(s: Pt, e: Pt) -> Pt:
    """2차 베지어 제어점 — 중점 + 법선 × 화면 거리 × bulge_ratio."""
    dx, dy = e[0] - s[0], e[1] - s[1]   # 법선(−dy, dx)/d × d × bulge_ratio
    return ((s[0] + e[0]) / 2 - dy * F.bulge_ratio, (s[1] + e[1]) / 2 + dx * F.bulge_ratio)


def _icon(ctx: cairo.Context, kind: str, rgb: tuple) -> None:
    I = F.icon  # noqa: N806
    pts = I.shapes[kind]
    sc = I.size_px[kind] / (max(abs(p[1]) for p in pts) * 2)
    ctx.move_to(pts[0][0] * sc, pts[0][1] * sc)
    for p in pts[1:]:
        ctx.line_to(p[0] * sc, p[1] * sc)
    ctx.close_path()
    ctx.set_source_rgba(0, 0, 0, I.halo_alpha)
    ctx.set_line_width(I.halo)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*rgb[:3], 1)
    ctx.fill()
    for a, b in I.body_lines.get(kind, []):
        ctx.move_to(a[0] * sc, a[1] * sc)
        ctx.line_to(b[0] * sc, b[1] * sc)
    if I.body_lines.get(kind):
        ctx.set_source_rgba(0, 0, 0, I.body_line.alpha)
        ctx.set_line_width(I.body_line.width)
        ctx.stroke()


def inset_box(e: dict, x: float, y: float) -> tuple[float, float, float, float]:
    """표적 화면 점(x, y) 기준 인셋 상자(x0, y0, w, h) — side 방향으로 gap_px 떨어진 자리."""
    I = F.inset  # noqa: N806
    w = I.w_px
    h = w * I.h_ratio
    side = (e.get("inset") or {}).get("side", "up")
    if side == "up":
        return x - w / 2, y - I.gap_px - h, w, h
    if side == "down":
        return x - w / 2, y + I.gap_px, w, h
    if side == "left":
        return x - I.gap_px - w, y - h / 2, w, h
    return x + I.gap_px, y - h / 2, w, h


def inset_alpha(t: float, e: dict) -> float:
    th = hit_time(e)
    return window(t, th - F.inset.lead_sec, th + F.inset.hold_sec + F.impact_sec, *F.inset.fade)


InsetDrawer = Callable[[cairo.Context, RenderCtx, tuple[float, float, float, float], float, dict], None]


def draw_flight(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict,  # noqa: N803
                inset_drawer: Optional[InsetDrawer] = None) -> None:
    t0 = e["t0"]
    th = hit_time(e)
    rgb = map_c(view.stage, e.get("col", "amber"))
    s = view.to_screen(*e["world_origin"])
    end = view.to_screen(*e["world"])
    c = control(s, end)
    fade = window(t, e["t0"] - F.origin.pulse_sec, e["t1"], 0, F.trail.fade_sec)
    # 1) 출발 발광(점·라벨 없음)
    O = F.origin  # noqa: N806
    if t0 - O.pulse_sec <= t <= t0 + O.out_sec:
        a = window(t, t0 - O.pulse_sec, t0 + O.out_sec, O.fade_in_sec, O.out_sec)
        br = 1 - O.breath + O.breath * math.sin((t - t0) * 2 * math.pi / O.pulse_sec)
        g = cairo.RadialGradient(s[0], s[1], 0, s[0], s[1], O.r_px)
        g.add_color_stop_rgba(0, *rgb[:3], O.alpha * a * br)
        g.add_color_stop_rgba(1, *rgb[:3], 0)
        ctx.set_source(g)
        ctx.arc(s[0], s[1], O.r_px, 0, 2 * math.pi)
        ctx.fill()
    # 2) 꼬리선(점선 = 개략) — 출발 후 자라고 착탄 뒤 fade_sec 에 사라진다
    p = ease_out((t - t0) / F.dur_sec) if t >= t0 else 0.0
    T = F.trail  # noqa: N806
    ta = T.alpha * fade * (1.0 if t < th else max(0.0, 1 - (t - th) / T.fade_sec))
    if p > 0 and ta > 0:
        ctx.move_to(*s)
        for i in range(1, F.samples + 1):
            ctx.line_to(*bezier(s, c, end, p * i / F.samples))
        ctx.set_dash(list(T.dash))
        ctx.set_line_width(T.width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*rgb[:3], ta)
        ctx.stroke()
        ctx.set_dash([])
    # 3) 아이콘(진행 방향으로 회전)
    if 0 < p < 1:
        x, y = bezier(s, c, end, p)
        x2, y2 = bezier(s, c, end, min(1.0, p + F.heading_du))
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(math.atan2(y2 - y, x2 - x) + math.pi / 2)
        _icon(ctx, e["kind"], rgb)
        ctx.restore()
    # 4) 착탄 링 = boom 과 같은 링(새 모양 금지)
    if e.get("impact", True) and th <= t <= th + F.impact_sec:
        draw_boom(ctx, R, view, t, {"t0": th, "t1": th + F.impact_sec, "world": e["world"]})
    # 5) 위성 인셋
    if e.get("inset"):
        ia = inset_alpha(t, e)
        if ia > 0:
            box = inset_box(e, *end)
            (inset_drawer or draw_inset)(ctx, R, box, ia, e)
            R.reserved.append((box[0], box[1] - F.inset.caption_dy - F.inset.caption_size, box[0] + box[2], box[1] + box[3]))

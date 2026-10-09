"""층 5: 고도 단면 패널 — 고각 궤적(개념 곡선 × 발표 정점), 기준선, 두 기관 발표를 나란히 같은 무게로.
docs/handoff/22 §2.3. 원본: 4d9dc65 `sketch_d1.draw_profile`. 수치 = rules sketch.profile, 문구·발표값 = spec.profile·announced.
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.layers.routes import glow_line
from engine.style import C
from engine.timebase import clamp01, ease_io, ease_out, smooth, window
from engine.typography import rrect, text
from sketch.common.draw import SK, WHITE
from sketch.missile.numbers import Numbers
from sketch.missile.shape import loft
from sketch.missile.spec import MissileSpec

P, F = SK.profile, SK.fade


class ProfileLayer:
    def __init__(self, spec: MissileSpec, nums: Numbers) -> None:
        self.spec = spec
        self.nums = nums
        self.drawn: dict[str, int] = {}

    def draw(self, ctx: cairo.Context, t: float) -> None:
        pr = self.spec.profile
        if pr is None:
            return
        a = window(t, pr.t0, pr.t1, P.in_sec, P.in_sec)
        if a <= P.min_alpha:
            return
        TX = P.text
        ctx.set_source_rgba(*F.end_bg, P.dim_alpha * a)
        ctx.paint()
        x, y, w, h = P.rect
        x += (1 - ease_out(clamp01((t - pr.t0) / P.in_sec))) * P.slide_px
        rrect(ctx, x, y, w, h, P.radius)
        ctx.set_source_rgba(*P.bg[:3], P.bg[3] * a)
        ctx.fill()
        px = x + P.pad_x
        text(ctx, pr.title, px, y + TX.title.dy, TX.title.size, TX.title.font, WHITE, a, TX.title.halo)
        text(ctx, pr.sub, px, y + TX.sub.dy, TX.sub.size, TX.sub.font, C["muted"], a, TX.sub.halo)
        il, it, ir, ib = P.plot_inset
        gx0, gy0, gx1, gy1 = x + il, y + it, x + w - ir, y + ib
        amax = P.alt_max_km
        tk, ax = TX.tick, TX.axis
        ctx.set_line_width(P.grid_w)
        for alt in P.alt_ticks_km:
            yy = gy1 - (gy1 - gy0) * alt / amax
            ctx.move_to(gx0, yy)
            ctx.line_to(gx1, yy)
            ctx.set_source_rgba(*WHITE, (P.zero_alpha if alt == 0 else P.grid_alpha) * a)
            ctx.stroke()
            text(ctx, f"{int(alt):,}", gx0 - P.tick_dx, yy + P.tick_dy, tk.size, tk.font, C["muted"], a, tk.halo, "r")
        text(ctx, pr.alt_axis, gx0 - P.tick_dx, gy0 - P.axis_title_dy, ax.size, ax.font, C["muted"], a, ax.halo, "r")
        rmax = P.range_max_km
        for rng in P.range_ticks_km:
            xx = gx0 + (gx1 - gx0) * rng / rmax
            text(ctx, f"{int(rng):,}", xx, gy1 + P.range_tick_dy, tk.size, tk.font, C["muted"], a, tk.halo, "c")
        text(ctx, pr.range_axis, gx1, gy1 + P.axis_label_dy, ax.size, ax.font, C["muted"], a, ax.halo, "r")
        # 기준선(예: 국제우주정거장 고도)
        rf = TX.ref
        yy = gy1 - (gy1 - gy0) * pr.reference.km.v / amax
        ctx.move_to(gx0, yy)
        ctx.line_to(gx1, yy)
        ctx.set_dash(P.ref_dash)
        ctx.set_source_rgba(*C[P.ref_color], P.ref_alpha * a)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, self.nums.fill(pr.reference.label), gx1 - P.ref_label_dx, yy - P.ref_label_dy, rf.size, rf.font,
             C[P.ref_color], a, rf.halo, "r")
        # 궤적(개념 곡선 × 발표 거리·정점)
        cv = self.spec.announced[pr.curve].values
        rng_km, apo_km = cv["range_km"].v, cv["apogee_km"].v
        prog = ease_io(clamp01((t - pr.t0 - P.grow_delay) / P.grow_sec))
        n = P.curve_points
        u = np.linspace(0, 1, n)[: max(2, int(n * prog))]
        pts = np.column_stack([gx0 + (gx1 - gx0) * u * rng_km / rmax, gy1 - (gy1 - gy0) * loft(u) * apo_km / amax])
        glow_line(ctx, pts, C[self.spec.launch.color], a, P.curve_w)
        self.drawn["profile_curve"] = self.drawn.get("profile_curve", 0) + 1
        pa = smooth((t - pr.t0 - P.apex_delay) / P.apex_in) * a
        axp, ayp = gx0 + (gx1 - gx0) * 0.5 * rng_km / rmax, gy1 - (gy1 - gy0) * apo_km / amax
        ctx.arc(axp, ayp, P.apex_r, 0, 2 * math.pi)
        ctx.set_source_rgba(*C["gold"], pa)
        ctx.fill()
        ap = TX.apex
        text(ctx, self.nums.fill(pr.apex_label), axp + P.apex_dx, ayp + P.apex_dy, ap.size, ap.font, C["gold"], pa, ap.halo)
        nt = TX.note
        text(ctx, pr.note, px, gy1 + P.axis_label_dy, nt.size, nt.font, C["muted"], a, nt.halo, role="source")
        # 두 기관 나란히(같은 무게)
        ta = smooth((t - pr.t0 - P.rows_delay) / P.rows_in) * a
        y0, first, step = P.rows_dy
        ty = y + y0
        wh, rw = TX.who, TX.row
        for i, (key, ag) in enumerate(self.spec.announced.items()):
            cx = px + i * (w - 2 * P.pad_x) / len(self.spec.announced)
            text(ctx, ag.who, cx, ty, wh.size, wh.font, C[ag.color], ta, wh.halo)
            for j, r in enumerate(ag.rows):
                text(ctx, self.nums.fill(r), cx, ty + first + j * step, rw.size, rw.font, WHITE, ta, rw.halo)

"""층 3: 발사·궤적·착탄 — 발사 기호, 지상 투영(대원) 궤적, 비행 경과 계기, 착탄 불확실성 영역(SK-H2)과 기준점 거리선.
docs/handoff/22 §2.3. 원본: 4d9dc65 `sketch_d1.draw_launch`·`draw_track`·`draw_impact`.

화면 숫자는 `Numbers` 포맷터를 거친 발표값뿐이다(SK-H1). 계산한 대원 거리는 그리지 않는다.
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.layers.routes import glow_line
from engine.projection import View
from engine.style import C
from engine.timebase import clamp01, ease_io, ease_out, smooth, window
from engine.typography import text, tw
from sketch.common.draw import SK, WHITE, Overlay, polyline, world
from sketch.common.geodesy import dest, gc_path
from sketch.missile.numbers import Numbers
from sketch.missile.spec import MissileSpec

L, T = SK.launch_track_impact, SK.text


class LaunchLayer:
    def __init__(self, spec: MissileSpec, nums: Numbers) -> None:
        self.spec = spec
        self.nums = nums
        tr = spec.track
        self.launch = (spec.launch.lon, spec.launch.lat)
        self.ref = (tr.ref.lon, tr.ref.lat)
        self.impact = dest(tr.ref.lon, tr.ref.lat, tr.bearing_deg, tr.distance_km)
        self.track_ll = gc_path(self.launch, self.impact, L.track_points)
        self.drawn: dict[str, int] = {}

    def _note(self, key: str) -> None:
        self.drawn[key] = self.drawn.get(key, 0) + 1

    def pulse(self, t: float) -> float:
        """착탄 뒤 EEZ 강조 세기(spec.eez.pulse 나라)."""
        lt = t - self.spec.track.t1
        if lt < 0:
            return 0.0
        d0, d_in, d1, d_out = L.pulse
        return clamp01((lt - d0) / d_in) * (1 - clamp01((lt - d1) / d_out))

    def draw_launch(self, ctx: cairo.Context, view: View, t: float, dim: float, ov: Overlay) -> None:
        sp = self.spec.launch
        lt = t - sp.t
        if lt <= 0:
            return
        col = C[sp.color]
        a = smooth(lt / L.launch_appear) * dim
        x, y = view.to_screen(*world(np.array([self.launch]))[0])
        r0, dr = L.launch_ring
        for k in range(L.launch_rings):
            f = ((lt * L.launch_ring_rate) + k / L.launch_rings) % 1
            ctx.arc(x, y, r0 + dr * ease_out(f), 0, 2 * math.pi)
            ctx.set_source_rgba(*col, L.launch_ring_alpha * (1 - f) * a)
            ctx.set_line_width(L.launch_ring_w)
            ctx.stroke()
        up, half, down = L.launch_tri       # 발사 기호: 위로 향한 삼각형
        ctx.move_to(x, y - up)
        ctx.line_to(x + half, y + down)
        ctx.line_to(x - half, y + down)
        ctx.close_path()
        ctx.set_source_rgba(*col, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*WHITE, a)
        ctx.set_line_width(L.launch_tri_w)
        ctx.stroke()
        self._note("launch_symbol")
        la = smooth((lt - L.launch_label_delay) / L.launch_label_in) * dim
        w = max(tw(ctx, sp.label, T.label.size, T.label.font), tw(ctx, sp.sub, T.label_sub.size, T.label_sub.font))
        gap, alt_dx, alt_dy, dy = L.launch_label
        if x - gap - w < T.label_edge_margin:   # 왼쪽 공간이 모자라면 점 오른쪽으로(라벨이 기호를 덮지 않게)
            ov.label2(x + alt_dx, y + alt_dy, la, sp.label, sp.sub, sub_col=col, anchor="l")
        else:
            ov.label2(x - gap, y + dy, la, sp.label, sp.sub, sub_col=col, anchor="r")

    def draw_track(self, ctx: cairo.Context, view: View, t: float, dim: float) -> None:
        tr = self.spec.track
        if t < tr.t0:
            return
        col = C[self.spec.launch.color]
        prog = ease_io(clamp01((t - tr.t0) / (tr.t1 - tr.t0)))
        S = view.to_screen_arr(world(self.track_ll))
        n = max(2, int(round(1 + (len(S) - 1) * prog)))
        glow_line(ctx, S[:n], col, dim, L.track_w)
        self._note("track")
        if prog < 1:
            hx, hy = S[n - 1]
            r = L.head_r
            c_a, stop, mid_a = L.head_stops
            g = cairo.RadialGradient(hx, hy, 0, hx, hy, r)
            g.add_color_stop_rgba(0, *WHITE, c_a * dim)
            g.add_color_stop_rgba(stop, *col, mid_a * dim)
            g.add_color_stop_rgba(1, *col, 0)
            ctx.set_source(g)
            ctx.arc(hx, hy, r, 0, 2 * math.pi)
            ctx.fill()
        # 비행 경과 계기(화면 고정) — 거리는 계산값을 보이지 않는다. 착탄 뒤 발표값만
        a = window(t, tr.t0, tr.t1 + tr.hud.hold_sec, L.hud_in, L.hud_out) * dim
        x = L.hud_x
        y_label, y_clock, y_range, y_note = L.hud_y
        H, V, R, N = T.hud, T.hud_value, T.hud_range, T.hud_note
        text(ctx, tr.hud.label, x, y_label, H.size, H.font, C["muted"], a, H.halo, role="hud")
        text(ctx, self.nums.clock(tr.flight_sec * prog), x, y_clock, V.size, V.font, WHITE, a, V.halo)
        text(ctx, self.nums.fill(tr.hud.range_line), x, y_range, R.size, R.font, C[L.range_color],
             a * smooth((t - tr.t1) / L.hud_range_in), R.halo)
        text(ctx, tr.hud.note, x, y_note, N.size, N.font, C["muted"], N.alpha * a, N.halo, role="source")

    def draw_impact(self, ctx: cairo.Context, view: View, t: float, dim: float, ov: Overlay) -> None:
        tr = self.spec.track
        lt = t - tr.t1
        if lt <= 0:
            return
        col = C[L.impact_color]
        a = smooth(lt / L.impact_appear) * dim
        ix, iy = view.to_screen(*world(np.array([self.impact]))[0])
        fl = math.exp(-lt * L.flash_decay)   # 번쩍임(한 번)
        if fl > L.flash_min:
            r = L.flash_r
            g = cairo.RadialGradient(ix, iy, 0, ix, iy, r)
            g.add_color_stop_rgba(0, *L.flash_rgb, L.flash_alpha * fl * dim)
            g.add_color_stop_rgba(1, *col, 0)
            ctx.set_source(g)
            ctx.arc(ix, iy, r, 0, 2 * math.pi)
            ctx.fill()
        # 불확실성 영역: "약 ○km" → 점이 아니라 반경 원(SK-H2)
        step = L.impact_ring_step_deg
        rad = tr.uncertainty_km * ease_out(clamp01(lt / L.impact_grow_sec))
        ring = view.to_screen_arr(world(np.array([dest(self.impact[0], self.impact[1], b, rad)
                                                  for b in np.arange(0, 360 + step, step)])))
        ctx.new_path()
        polyline(ctx, ring, close=True)
        ctx.set_source_rgba(*col, L.impact_fill_alpha * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*col, L.impact_edge_alpha * a)
        ctx.set_dash(L.impact_dash)
        ctx.set_line_width(L.impact_edge_w)
        ctx.stroke()
        ctx.set_dash([])
        if tr.uncertainty_km > 0:
            self._note("impact_area")
        # 기준점과 거리선
        ma = smooth((lt - L.ref_delay) / L.ref_in) * dim
        ox, oy = view.to_screen(*world(np.array([self.ref]))[0])
        m = L.ref_line_points
        seg = view.to_screen_arr(world(gc_path(self.impact, self.ref, m)))
        k = int(2 + (m - 2) * ease_io(clamp01((lt - L.ref_delay) / L.ref_grow_sec)))
        glow_line(ctx, seg[:k], WHITE, L.ref_line_alpha * ma, L.ref_line_w, dash=L.ref_line_dash)
        ctx.arc(ox, oy, L.ref_dot_r, 0, 2 * math.pi)
        ctx.set_source_rgba(*WHITE, ma)
        ctx.fill()
        P, D = T.ref_name, T.ref_distance
        text(ctx, tr.ref.name, ox + P.dx, oy + P.dy, P.size, P.font, WHITE, ma, P.halo)   # type: ignore[operator]
        mx, my = seg[m // 2]
        text(ctx, self.nums.fill("{track.distance_km}"), mx, my + D.dy, D.size, D.font, C[L.range_color],
             smooth((lt - L.ref_mid_delay) / L.ref_mid_in) * dim, D.halo, "c")
        la = smooth((lt - L.impact_label_delay) / L.impact_label_in) * dim
        dx, dy, tag_dy = L.impact_label
        ov.label2(ix + dx, iy + dy, la, tr.impact.label, self.nums.fill(tr.impact.sub), sub_col=col, anchor="c")
        tg = smooth((lt - L.impact_tag_delay) / L.impact_tag_in) * dim
        if tg > L.min_alpha:
            ov.tag(tr.impact.tag, ix, iy + tag_dy, C[tr.impact.tag_color], tg, anchor="c")

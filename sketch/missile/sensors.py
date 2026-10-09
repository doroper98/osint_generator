"""층 2: 탐지 자산 — 위치 공개 레이더(기준점 + 부채꼴), 위치 비공개(기준점 없음 · 여러 겹 흐림 · 개념도 태그),
이동 자산(위치 예시 기호 · 범위 없음). docs/handoff/22 §2.4, SK-H3. 원본: 4d9dc65 `sketch_d1.draw_sensor`·`draw_aegis`.

수치 = rules sketch.sensors, 사실·시각·문구 = spec.sensors.
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.layers.routes import glow_line
from engine.projection import View
from engine.stage import ym
from engine.style import C
from engine.timebase import clamp01, ease_out, smooth
from sketch.common.draw import SK, WHITE, Overlay, polyline, world
from sketch.common.geodesy import bearing, dest, sector
from sketch.missile.numbers import Numbers
from sketch.missile.spec import MissileSpec, Sensor

S_ = SK.sensors


class SensorLayer:
    def __init__(self, spec: MissileSpec, nums: Numbers) -> None:
        self.spec = spec
        self.nums = nums
        self.launch = (spec.launch.lon, spec.launch.lat)
        self.drawn: dict[str, int] = {}

    def _note(self, key: str) -> None:
        self.drawn[key] = self.drawn.get(key, 0) + 1

    def _brg(self, s: Sensor) -> float:
        return s.bearing_deg if s.bearing_deg is not None else bearing((s.lon, s.lat), self.launch)

    def draw(self, ctx: cairo.Context, view: View, t: float, sens_dim: float, ov: Overlay) -> None:
        radars = [s for s in self.spec.sensors if s.kind == "radar"]
        for s in radars:
            later = [o for o in radars if o.t > s.t and t > o.t]
            focus = S_.focus_dim if later and t < self.spec.dim.sensors_focus_end else 1
            self._radar(ctx, view, t, s, sens_dim * focus, ov)
        for s in self.spec.sensors:
            if s.kind == "ship":
                self._ship(ctx, view, t, s, sens_dim, ov)

    def _sector_screen(self, view: View, at: tuple[float, float], brg: float, s: Sensor, km: float) -> np.ndarray:
        return view.to_screen_arr(world(sector(at, brg, s.az_width_deg, km, S_.sector_points)))   # type: ignore[arg-type]

    def _radar(self, ctx: cairo.Context, view: View, t: float, s: Sensor, dim: float, ov: Overlay) -> None:
        lt = t - s.t
        if lt <= 0:
            return
        grow = ease_out(clamp01(lt / S_.grow_sec))
        a = smooth(lt / S_.appear_sec) * dim
        brg = self._brg(s)
        col = C[s.color]
        at = (s.lon, s.lat)
        if s.range_km is not None:
            km = s.range_km * grow
            if s.location_public:
                self._public(ctx, view, s, at, brg, km, col, a, lt)
            else:
                self._undisclosed(ctx, view, s, at, brg, km, col, a)
        elif s.location_public:
            self._site(ctx, view, s, col, a)
        self._labels(t, s, lt, dim, view, ov)

    def _site(self, ctx: cairo.Context, view: View, s: Sensor, col: tuple, a: float) -> tuple[float, float]:
        """기준점(위치 공개 자산만, SK-H3). 그린 자산 이름을 provenance 에 남긴다."""
        at = (s.lon, s.lat)
        cx, cy = view.to_screen(at[0], ym(at[1]))
        ctx.arc(cx, cy, S_.site_r, 0, 2 * math.pi)
        ctx.set_source_rgba(*WHITE, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*col, a)
        ctx.set_line_width(S_.site_w)
        ctx.stroke()
        self._note(f"sensor_point:{s.name}")
        return cx, cy

    def _public(self, ctx: cairo.Context, view: View, s: Sensor, at: tuple[float, float], brg: float, km: float,
                col: tuple, a: float, lt: float) -> None:
        poly = self._sector_screen(view, at, brg, s, km)
        ctx.new_path()
        polyline(ctx, poly, close=True)
        cx, cy = view.to_screen(at[0], ym(at[1]))
        rmax = max(np.hypot(poly[:, 0] - cx, poly[:, 1] - cy))
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, max(rmax, 1))
        g.add_color_stop_rgba(0, *col, S_.fill_alpha[0] * a)
        g.add_color_stop_rgba(1, *col, S_.fill_alpha[1] * a)
        ctx.set_source(g)
        ctx.fill_preserve()
        ctx.set_source_rgba(*col, S_.edge_alpha * a)
        ctx.set_line_width(S_.edge_w)
        ctx.stroke()
        w = s.az_width_deg
        n = S_.tick_points
        for frac in S_.tick_fracs:   # 거리 눈금 호
            arc = view.to_screen_arr(world(np.array([dest(at[0], at[1], brg - w / 2 + w * i / (n - 1), km * frac)
                                                     for i in range(n)])))
            glow_line(ctx, arc, col, S_.tick_alpha * a, S_.tick_w, dash=S_.tick_dash)
        # 스캔 빔: 부채꼴 안을 천천히 쓸고 지나간다(영상미, 사실 정보 아님)
        sweep = brg - w / 2 + w * (0.5 + 0.5 * math.sin(lt * S_.scan_rate))
        tip = view.to_screen(*world(np.array([dest(at[0], at[1], sweep, km)]))[0])
        ctx.move_to(cx, cy)
        ctx.line_to(*tip)
        ctx.set_source_rgba(*col, S_.scan_alpha * a)
        ctx.set_line_width(S_.scan_w)
        ctx.stroke()
        self._site(ctx, view, s, col, a)
        self._note("sensor_range")

    def _undisclosed(self, ctx: cairo.Context, view: View, s: Sensor, at: tuple[float, float], brg: float, km: float,
                     col: tuple, a: float) -> None:
        """위치 비공개 — 기준점을 찍지 않는다. 시작점을 흐린 여러 겹으로 그려 '어딘가'임을 보인다(SK-H3)."""
        for dx, dy in S_.undisclosed_offsets:
            poly = self._sector_screen(view, (at[0] + dx, at[1] + dy), brg, s, km)
            ctx.new_path()
            polyline(ctx, poly, close=True)
            ctx.set_source_rgba(*col, S_.undisclosed_fill_alpha * a)
            ctx.fill()
        poly = self._sector_screen(view, at, brg, s, km)
        glow_line(ctx, poly[1:-1], col, S_.undisclosed_edge_alpha * a, S_.undisclosed_edge_w, dash=S_.undisclosed_dash)
        cx, cy = view.to_screen(at[0], ym(at[1]))
        r = S_.undisclosed_glow_r
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        g.add_color_stop_rgba(0, *col, S_.undisclosed_glow_alpha * a)
        g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.fill()
        self._note("sensor_range_concept")

    def _next_t(self, s: Sensor) -> float:
        later = [o.t for o in self.spec.sensors if o.t > s.t]
        return min(later) if later else math.inf

    def _labels(self, t: float, s: Sensor, lt: float, dim: float, view: View, ov: Overlay) -> None:
        la = smooth((lt - S_.label_delay) / S_.label_in) * dim * (1 - smooth((t - self.spec.dim.sensors_labels_end) / S_.label_out))
        lx, ly = view.to_screen(s.label_at[0], ym(s.label_at[1]))   # type: ignore[index]
        anc = "l" if s.side == "r" else "r"
        col = C[s.color]
        full = 1 - smooth((t - self._next_t(s)) / S_.full_out)   # 다음 자산이 나오면 부제·태그는 물러나고 이름만 남는다
        if full > S_.full_min:
            ov.label2(lx, ly, la * full, s.name, self.nums.fill(s.sub, s) if s.sub else None, sub_col=col, anchor=anc)
            if s.tag:
                ov.tag(s.tag, lx, ly + S_.tag_dy, C["amber"], la * full, anchor=anc)
        if full < 1 - S_.full_min:
            ov.label2(lx, ly, la * (1 - full) * S_.short_alpha, s.name, None, anchor=anc)

    def _ship(self, ctx: cairo.Context, view: View, t: float, s: Sensor, dim: float, ov: Overlay) -> None:
        """이동 자산 — 위치는 예시(기호), 탐지 범위 비공개라 범위를 그리지 않는다."""
        lt = t - s.t
        if lt <= 0:
            return
        a = smooth(lt / S_.appear_sec) * dim
        x, y = view.to_screen(s.lon, ym(s.lat))
        r0, dr = S_.ship_ring
        for k in range(S_.ship_rings):
            f = ((lt * S_.ship_ring_rate) + k / S_.ship_rings) % 1
            ctx.arc(x, y, r0 + dr * ease_out(f), 0, 2 * math.pi)
            ctx.set_source_rgba(*C[s.color], S_.ship_ring_alpha * (1 - f) * a)
            ctx.set_line_width(S_.ship_ring_w)
            ctx.stroke()
        ctx.save()
        ctx.translate(x, y)
        ctx.move_to(*S_.ship_shape[0])
        for p in S_.ship_shape[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.rectangle(*S_.ship_bridge)
        ctx.set_source_rgba(*WHITE, a)
        ctx.fill()
        ctx.restore()
        self._note("ship_symbol")
        la = smooth((lt - S_.ship_label_delay) / S_.label_in) * dim * (1 - smooth((t - self.spec.dim.sensors_labels_end) / S_.label_out))
        dx, dy, tag_dy = S_.ship_label
        ov.label2(x + dx, y + dy, la, s.name, self.nums.fill(s.sub, s) if s.sub else None, sub_col=C[s.color])
        ov.tag(s.tag, x + dx, y + tag_dy, C["amber"], la)   # type: ignore[arg-type]

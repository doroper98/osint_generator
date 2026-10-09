"""3D 전환 장면 — 지구본 래스터 위에 국경·EEZ·지상/고각 궤적·레이더 볼륨·라벨·수평선 최소 고도 패널(D-0143).
원본: 4d9dc65 `globe3d.Scene.frame_3d`·`labels`. 2D 장면과의 교차 전환은 `sketch.common.render.CrossfadeScene`.

장치 px 로 그린다: 글자·배치 = 설계 px × k(출력 프로파일), 선 굵기·대시·점 반지름 = 값 × 출력 높이 / px_ref_height.
화면 숫자: 발표값은 포맷터(`Numbers.fill`), 수평선 패널의 거리·고도는 기하 계산값(`Numbers.computed`, D136 — numbers_computed).
"""

from __future__ import annotations

import math
from pathlib import Path

import cairo
import numpy as np

from engine.style import C, CARD_BG, DATE_BADGE, output_profile
from engine.timebase import clamp01, ease_io, smooth, window
from engine.typography import rrect, text, tw
from rules import load_rules
from sketch.common.draw import WHITE
from sketch.common.render import BGRA
from sketch.common.geodesy import gc_dist, horizon_altitude, to_local
from sketch.missile.globe import CameraPath3D, Cam, Keys, border_rings, draw_volume, load_textures, polyline, radar_volume, render_globe, visible
from sketch.missile.numbers import Numbers
from sketch.missile.scene import MissileScene
from sketch.missile.shape import loft
from sketch.missile.spec import MissileSpec, Sensor

SK = load_rules().sketch
G, F, T, L = SK.globe, SK.fade, SK.text, SK.launch_track_impact
ASSETS = "assets"
HORIZON_FORMULA = "R·(1/cos(d/R) − 1), d = gc_dist(자산, 발사 지점), R = 6371 km"


class GlobeScene:
    def __init__(self, spec: MissileSpec, project: Path, flat: MissileScene) -> None:
        g = spec.globe
        if g is None:
            raise ValueError("spec 에 globe 블록이 없다")
        self.spec, self.g, self.flat = spec, g, flat
        self.nums: Numbers = flat.nums
        self.out = flat.out
        self.kpx = self.out.k
        self.lw = self.out.height / G.px_ref_height
        default = output_profile(None).name
        detail = project / ASSETS if self.out.name == default else project / ASSETS / f"res_{self.out.name}"
        self.tex = load_textures(project / g.texture_project / ASSETS, detail)
        self.cen = tuple(g.center)
        last = spec.shots[-1]
        keys = Keys(g.t_2d, g.t_x, g.t_k0, g.t_k1, g.t_side0, g.t_side1, g.t_fly0, g.t_fly1, g.duration_sec)
        self.path = CameraPath3D(keys, last.lat, last.w * (1 - SK.camera.push_in[spec.kind]), self.out.width, self.out.height)
        self.launch = (spec.launch.lon, spec.launch.lat)
        self.track = flat.launch.track_ll
        apogee = spec.announced[spec.profile.curve].values["apogee_km"].v   # type: ignore[union-attr]
        self.alt = loft(np.linspace(0, 1, len(self.track))) * apogee
        self.radars = [s for s in spec.sensors if s.el_deg is not None]
        self.bord = border_rings(flat.stage.assets.geo["coarse"])
        pulse = next(f for f in flat.eez.feat if f["kind"] == "eez" and f["code"] == spec.eez.pulse) if spec.eez.pulse else None
        self.eez_lines = [np.asarray(ln) for ln in pulse["lines"] if len(ln) > G.eez_min_pts] if pulse else []
        self.drawn: dict[str, int] = {}
        self.focal: list[tuple[float, float]] = []        # SK-C1(3D) 입력: (t, 초점 거리)
        self.anchors: list[tuple[float, np.ndarray, np.ndarray]] = []   # (t, 화면 좌표 2×2, 보임)

    def _note(self, key: str) -> None:
        self.drawn[key] = self.drawn.get(key, 0) + 1

    def local(self, lon: np.ndarray, lat: np.ndarray, alt: np.ndarray, k: float) -> np.ndarray:
        return to_local(self.cen, lon, lat, alt, k)   # type: ignore[arg-type]

    def frame(self, t: float) -> bytes:
        g = self.g
        k = self.path.k_at(max(t, g.t_k0))
        cam = self.path.cam(t)
        base = render_globe(cam, k, self.tex, cam.rays(), self.cen)   # type: ignore[arg-type]
        W, H = self.out.width, self.out.height
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        arr = np.ndarray((H, W, BGRA), np.uint8, surf.get_data())
        arr[:, :, 0], arr[:, :, 1], arr[:, :, 2] = base[:, :, 2], base[:, :, 1], base[:, :, 0]
        surf.mark_dirty()
        ctx = cairo.Context(surf)
        lw = self.lw
        for ring in self.bord:
            P = self.local(ring[:, 0], ring[:, 1], np.zeros(len(ring)), k)
            polyline(ctx, cam, P, k, G.border_rgb, G.border_alpha, G.border_w * lw, glow=False)
        for ln in self.eez_lines:
            P = self.local(ln[:, 0], ln[:, 1], np.zeros(len(ln)), k)
            polyline(ctx, cam, P, k, C[self.spec.eez.nations[self.spec.eez.pulse].color], G.eez_alpha, G.eez_w * lw,   # type: ignore[index]
                     dash=[d * lw for d in G.eez_dash], glow=False)
        col = C[self.spec.launch.color]
        # 지상 궤적(2D 와 같은 선) — 곡률 전환 내내 유지
        Gt = self.local(self.track[:, 0], self.track[:, 1], np.zeros(len(self.track)), k)
        w0, w1 = G.track_w
        polyline(ctx, cam, Gt, k, col, G.track_alpha_side if t > g.t_side0 else 1, (w0 if t < g.t_side0 else w1) * lw)
        self._record_anchors(t, cam, Gt, k)
        vols = [radar_volume(s, self.launch, self.cen, k) for s in self.radars]   # type: ignore[arg-type]
        lead, vin = G.volume_in
        va = smooth((t - (g.t_k1 - lead)) / vin)
        prog = ease_io(clamp01((t - g.t_fly0) / (g.t_fly1 - g.t_fly0)))
        n = max(2, int(round(1 + (len(self.track) - 1) * prog)))
        A3 = self.local(self.track[:, 0], self.track[:, 1], self.alt, k)
        if va > F.min_alpha:
            for s, vol in zip(self.radars, vols):
                draw_volume(ctx, cam, vol, k, C[s.color], va, 0, lw)
            self._note("radar_volume")
        ta = smooth((t - (g.t_side0 + G.alt_delay)) / G.alt_in)
        if ta > F.min_alpha:
            m = n if t >= g.t_fly0 else len(self.track)
            for i in range(0, m, G.curtain_step):
                polyline(ctx, cam, np.vstack([Gt[i], A3[i]]), k, col, G.curtain_alpha * ta, G.curtain_w * lw, glow=False)
            if t < g.t_fly0:   # 비행 전: 전체 궤적을 흐린 점선으로 예고
                polyline(ctx, cam, A3, k, col, G.preview_alpha * ta, G.preview_w * lw, dash=[d * lw for d in G.preview_dash], glow=False)
            else:
                polyline(ctx, cam, A3[:n], k, col, ta, G.flown_w * lw)
                self._note("lofted_track")
                if prog < 1:
                    self._head(ctx, cam, A3[n - 1:n], k, col)
        self._labels(ctx, cam, k, t, vols, prog, A3, Gt)
        surf.flush()
        return bytes(np.ndarray((H, W, BGRA), np.uint8, surf.get_data()).copy())

    def _head(self, ctx: cairo.Context, cam: Cam, head: np.ndarray, k: float, col: tuple) -> None:
        S, front = cam.project(head)
        if not (front[0] and visible(cam, head, k)[0]):
            return
        hx, hy = float(S[0, 0]), float(S[0, 1])
        r = G.head_r * self.lw
        c_a, stop, mid_a = L.head_stops
        grad = cairo.RadialGradient(hx, hy, 0, hx, hy, r)
        grad.add_color_stop_rgba(0, *WHITE, c_a)
        grad.add_color_stop_rgba(stop, *col, mid_a)
        grad.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(grad)
        ctx.arc(hx, hy, r, 0, 2 * math.pi)
        ctx.fill()

    def _record_anchors(self, t: float, cam: Cam, Gt: np.ndarray, k: float) -> None:
        """SK-C1(3D, D135) 입력 — 발사점·착탄점(지상 궤적 양 끝) 화면 좌표와 초점 거리."""
        P = Gt[[0, -1]]
        S, front = cam.project(P)
        self.anchors.append((t, S, front & visible(cam, P, k)))
        self.focal.append((t, cam.f))

    # ---------------------------------------------------------------- 라벨·패널·계기
    def _label(self, ctx: cairo.Context, s: str, x: float, y: float, a: float, sub: str | None, sub_col: tuple,
               anchor: str = "l", avoid: tuple[float, float, float, float] | None = None) -> None:
        """이름 + 부제. 검토본 결함 수정(D-0143 §0): 글자가 화면 위로 잘리지 않게 위 여백 안으로, 패널(avoid)에 덮이면 패널 아래로."""
        kp, Lb, Sb = self.kpx, G.label, G.label_sub
        top = (T.label_edge_margin + Lb.size) * kp
        w = max(tw(ctx, s, Lb.size * kp, Lb.font), tw(ctx, sub, Sb.size * kp, Sb.font) if sub else 0)
        x0 = x - w if anchor == "r" else (x - w / 2 if anchor == "c" else x)
        y = max(y, top)
        if avoid is not None:
            ax0, ay0, ax1, ay1 = avoid
            bottom = y + (Sb.dy + Sb.size) * kp if sub else y
            if x0 < ax1 and x0 + w > ax0 and y - Lb.size * kp < ay1 and bottom > ay0:
                y = ay1 + (T.label_edge_margin + Lb.size) * kp
                self._note("label_moved_below_panel")
        text(ctx, s, x, y, Lb.size * kp, Lb.font, WHITE, a, Lb.halo * kp, anchor)
        if sub:
            text(ctx, sub, x, y + Sb.dy * kp, Sb.size * kp, Sb.font, sub_col, a, Sb.halo * kp, anchor)

    def panel_box(self) -> tuple[float, float, float, float]:
        """수평선 패널 상자(장치 px)."""
        kp = self.kpx
        right, top, padl, padt, pw, ph = G.panel_rect
        x0, y0 = self.out.width - right * kp - padl * kp, top * kp - padt * kp
        return x0, y0, x0 + pw * kp, y0 + ph * kp

    def _at(self, cam: Cam, P: np.ndarray, k: float) -> tuple[float, float, bool]:
        S, f = cam.project(P[None, :])
        return float(S[0, 0]), float(S[0, 1]), bool(f[0] and visible(cam, P[None, :], k)[0])

    def _labels(self, ctx: cairo.Context, cam: Cam, k: float, t: float, vols: list, prog: float,
                A3: np.ndarray, Gt: np.ndarray) -> None:
        g, sp, kp = self.g, self.spec, self.kpx
        la = smooth((t - (g.t_side0 + G.label_delay)) / G.label_in)
        lead, pin = G.panel_in
        pa = smooth((t - g.t_side1 + lead) / pin)
        avoid = self.panel_box() if pa > F.min_alpha else None
        lab = g.labels
        for P, (dx, dy), main, sub, sub_col, anc in (
                (Gt[0], G.label_launch, sp.launch.label, lab.launch_sub, C[sp.launch.color], "r"),
                (Gt[-1], G.label_impact, sp.track.impact.label, lab.impact_sub, C[sp.track.impact.tag_color], "l"),
                (A3[len(A3) // 2], G.label_apex, self.nums.fill(lab.apex), lab.apex_sub, C["gold"], "l")):
            x, y, ok = self._at(cam, P, k)
            if ok and la > F.min_alpha:
                self._label(ctx, main, x + dx * self.lw, y + dy * self.lw, la, sub, sub_col, anc, avoid)   # 오프셋은 원본 장치 px
        lead, end, fin, fout = G.radar_label
        ra = window(t, g.t_k1 - lead, g.t_side0 + end, fin, fout)
        for s, vol in zip(self.radars, vols):
            x, y, ok = self._at(cam, vol["base"], k)
            if ok and ra > F.min_alpha and s.globe_label:
                dx, dy, anc = s.globe_label
                self._label(ctx, s.globe_name or s.name, x + dx * kp, y + dy * kp, ra, self.nums.fill(lab.radar_sub, s), C[s.color], anc)
        if pa > F.min_alpha:
            self._panel(ctx, pa)
        fl0, fl1 = G.hud_in
        fa = window(t, g.t_fly0, g.duration_sec, fl0, fl1)
        hx = G.hud_x * kp
        y0, y1 = G.hud_y
        Hd, Hv = T.hud, T.hud_value
        text(ctx, sp.track.hud.label, hx, y0 * kp, Hd.size * kp, Hd.font, C["muted"], fa, Hd.halo * kp)
        text(ctx, self.nums.clock(sp.track.flight_sec * prog), hx, y1 * kp, Hv.size * kp, Hv.font, WHITE, fa, Hv.halo * kp)
        na = smooth((t - g.t_side1) / G.notes_in)
        Sx = T.source
        for note, ny in zip(g.hud_notes, G.notes_y):
            text(ctx, self.nums.fill(note), G.notes_x * kp, ny * kp, Sx.size * kp, Sx.font, C["muted"], G.notes_alpha * na,
                 G.notes_halo * kp)
        B = DATE_BADGE   # 날짜(모서리 유일 요소)
        text(ctx, sp.date, self.out.width - B.x_right * kp, B.y * kp, B.size * kp, B.font, WHITE, F.date_alpha, F.date_halo * kp, "r")

    def seam_offsets(self) -> np.ndarray:
        """2D → 3D 이음새(D-0144): 2D 마지막 프레임(handoff_2d_t + t_2d × handoff_rate)과 첫 3D 프레임(t_2d)에서
        발사점·착탄점(지상 궤적 양 끝) 화면 좌표 차 |Δx|·|Δy|(설계 px, 2×2)."""
        from engine.projection import View   # noqa: PLC0415
        from engine.stage import ym          # noqa: PLC0415

        g, out = self.g, self.out
        ends = self.track[[0, -1]]
        view = View(self.flat.stage, np.array(self.flat.camera.at(g.handoff_2d_t + g.t_2d * G.handoff_rate)))
        s2 = np.array([view.to_screen(lon, ym(lat)) for lon, lat in ends])
        cam = self.path.cam(g.t_2d)
        s3, _ = cam.project(self.local(ends[:, 0], ends[:, 1], np.zeros(len(ends)), self.path.k_at(g.t_k0)))
        s3 = (s3 - np.array([out.pad_x, 0])) / out.k
        return np.abs(s2 - s3)

    def horizon_rows(self) -> list[tuple[Sensor, float, float]]:
        """(자산, 지표 거리 km, 수평선 최소 고도 km) — SK-H6 대조 대상."""
        out = []
        for s in self.radars:
            d = gc_dist((s.lon, s.lat), self.launch)
            out.append((s, d, horizon_altitude(d)))
        return out

    def _panel(self, ctx: cairo.Context, pa: float) -> None:
        """발사 지점 상공이 각 레이더 수평선 위로 보이기 시작하는 최소 고도(거리·지구 반지름만의 기하, D136)."""
        kp, P = self.kpx, self.g.panel
        right, top, padl, padt, pw, ph = G.panel_rect
        px, py = self.out.width - right * kp, top * kp
        rrect(ctx, px - padl * kp, py - padt * kp, pw * kp, ph * kp, G.panel_radius * kp)
        ctx.set_source_rgba(*CARD_BG[:3], G.panel_alpha * pa)
        ctx.fill()
        Tt = G.panel_title
        text(ctx, P.title, px, py + Tt.dy * kp, Tt.size * kp, Tt.font, WHITE, pa, Tt.halo * kp)
        r0, step = G.panel_rows
        ddx, ddy, dr = G.panel_dot
        Nm, Ds, Al = G.panel_name, G.panel_dist, G.panel_alt
        for j, (s, d, h) in enumerate(self.horizon_rows()):
            yy = py + (r0 + step * j) * kp
            ctx.arc(px + ddx * kp, yy + ddy * kp, dr * kp, 0, 2 * math.pi)
            ctx.set_source_rgba(*C[s.color], pa)
            ctx.fill()
            text(ctx, s.short or s.name, px + Nm.dx * kp, yy, Nm.size * kp, Nm.font, WHITE, pa, Nm.halo * kp)   # type: ignore[operator]
            inputs = {"sensor_lon": s.lon, "sensor_lat": s.lat, "launch_lon": self.launch[0], "launch_lat": self.launch[1]}
            ds = self.nums.computed(f"horizon.distance_km:{s.name}", d, "km", "gc_dist(자산, 발사 지점)", inputs)
            hs = self.nums.computed(f"horizon.altitude_km:{s.name}", h, "km", HORIZON_FORMULA, dict(inputs, d_km=d), approx=True)
            text(ctx, P.distance_fmt.replace("{value}", ds), px + Ds.dx * kp, yy, Ds.size * kp, Ds.font, C["muted"], pa,   # type: ignore[operator]
                 Ds.halo * kp)
            text(ctx, P.altitude_fmt.replace("{value}", hs), px + Al.dx * kp, yy, Al.size * kp, Al.font, C[s.color], pa,   # type: ignore[operator]
                 Al.halo * kp, "r")
        for st, note in ((G.panel_note, P.note), (G.panel_note2, P.note2)):
            if note:
                text(ctx, note, px, py + st.dy * kp, st.size * kp, st.font, C["muted"], pa, st.halo * kp)   # type: ignore[operator]
        self._note("horizon_panel")
        if P.note:
            self._note("horizon_panel_note")

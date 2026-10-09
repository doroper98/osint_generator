"""3D 지구본 기하·카메라·래스터·레이더 볼륨(D-0143 §1) — 원본: 4d9dc65 `projects/d1_missile_sketch/globe3d.py`.

원리
- 곡률 전환: 접점 c 에서 접하는 반지름 kR 구를 그린다(geodesy.to_local — 거리·방위 보존). k 를 k_max → 1 로 줄이면 지도가 휘어 지구본이 된다.
- 배경 지형: 엔진 geo.prep 티어 — 전 지구 텍스처(spec globe.texture_project) 위에 프로젝트 상세 티어(출력 해상도)를 얹는다.
- 레이더 볼륨: 방위 폭·고각 범위·거리로 만든 부채 볼륨(개념값). 가시 판정은 기하만 본다(굴절·RCS·운용 모드 무시).
수치 = rules sketch.globe(설계 px 는 출력 프로파일 k 배 — 이 모듈은 장치 px 로 그린다).
"""

from __future__ import annotations

import math
import pickle
from dataclasses import dataclass
from pathlib import Path

import cairo
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

from engine.stage import ym
from engine.timebase import clamp01, ease_io, smooth
from rules import load_rules
from sketch.common.geodesy import EARTH_KM, bearing, dest_arr, merc_y_deg, to_local
from sketch.missile.spec import Sensor

G = load_rules().sketch.globe
BYTE_MAX = float(np.iinfo(np.uint8).max)
X_AXIS, Y_AXIS, Z_AXIS = np.eye(3)


# ---------------------------------------------------------------- 지형 텍스처
class Tex:
    """geo.prep 티어 한 장(가장 세밀한 레벨) — 경위도 → 색 표본."""

    def __init__(self, tiers_pkl: Path, base_dir: Path, name: str) -> None:
        with open(tiers_pkl, "rb") as fh:
            T = pickle.load(fh)[name]
        self.lv = max(T["levels"])
        self.lon0, self.lon1, self.lat0, self.lat1 = T["lon0"], T["lon1"], T["lat0"], T["lat1"]
        self.y_top = ym(self.lat1)
        self.img = np.asarray(Image.open(base_dir / f"base_{name}_{self.lv}.png").convert("RGB"), dtype=np.float32)

    def sample(self, lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        lat_c = np.clip(lat, -G.tex_lat_clip, G.tex_lat_clip)
        yy = (self.y_top - merc_y_deg(lat_c)) * self.lv
        xx = (lon - self.lon0) * self.lv
        e = G.tex_edge_deg
        ok = (lon >= self.lon0 + e) & (lon <= self.lon1 - e) & (lat >= self.lat0 + e) & (lat <= self.lat1 - e)
        out = np.stack([map_coordinates(self.img[:, :, c], [yy, xx], order=1, mode="nearest") for c in range(3)], axis=1)
        return out, ok


def load_textures(globe_assets: Path, detail_assets: Path) -> list[Tex]:
    """거친 것 → 세밀한 것 순(전 지구 W → 상세 W → 상세 K)."""
    names = G.texture_tiers
    return [Tex(globe_assets / "tiers.pkl", globe_assets, names[0])] + \
        [Tex(detail_assets / "tiers.pkl", detail_assets, n) for n in names[1:]]


# ---------------------------------------------------------------- 카메라
class Cam:
    """핀홀 카메라(장치 px). up 은 화면 위 방향 힌트(전방과 거의 평행하면 z 축으로 바꾼다)."""

    def __init__(self, pos: np.ndarray, target: np.ndarray, fov_deg: float, up: np.ndarray, w: int, h: int) -> None:
        self.pos = np.asarray(pos, float)
        self.w, self.h = w, h
        f = np.asarray(target, float) - self.pos
        self.fwd = f / np.linalg.norm(f)
        up0 = np.asarray(up, float)
        if abs(np.dot(up0 / np.linalg.norm(up0), self.fwd)) > G.up_parallel:
            up0 = Z_AXIS
        r = np.cross(self.fwd, up0)
        self.right = r / np.linalg.norm(r)
        self.up = np.cross(self.right, self.fwd)
        self.f = (w / 2) / math.tan(math.radians(fov_deg) / 2)

    def rays(self) -> np.ndarray:
        xs = (np.arange(self.w) + 0.5 - self.w / 2) / self.f
        ys = -(np.arange(self.h) + 0.5 - self.h / 2) / self.f
        gx, gy = np.meshgrid(xs, ys)
        d = self.fwd[None, None, :] + gx[..., None] * self.right[None, None, :] + gy[..., None] * self.up[None, None, :]
        return (d / np.linalg.norm(d, axis=2, keepdims=True)).reshape(-1, 3)

    def project(self, P: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        v = P - self.pos
        z = v @ self.fwd
        zz = np.maximum(z, G.z_eps)
        return np.column_stack([self.w / 2 + self.f * (v @ self.right) / zz,
                                self.h / 2 - self.f * (v @ self.up) / zz]), z > G.z_near_km


def visible(cam: Cam, P: np.ndarray, k: float) -> np.ndarray:
    """카메라 → 점 선분이 구(지구)에 먼저 막히지 않는가."""
    c = -k * EARTH_KM * Z_AXIS
    d = P - cam.pos
    L = np.linalg.norm(d, axis=1)
    d = d / L[:, None]
    oc = cam.pos - c
    b = d @ oc
    cc = oc @ oc - (k * EARTH_KM) ** 2
    disc = b * b - cc
    t_hit = -b - np.sqrt(np.maximum(disc, 0))
    near, far = G.occlusion_margin_km
    return ~((disc > 0) & (t_hit > near) & (t_hit < L - far))


@dataclass(frozen=True)
class Keys:
    """연출 키프레임 시각(spec globe)."""

    t_2d: float
    t_x: float
    t_k0: float
    t_k1: float
    t_side0: float
    t_side1: float
    t_fly0: float
    t_fly1: float
    duration: float


class CameraPath3D:
    """A(2D 숏과 같은 수직 하향) → B(높이 올라가며 기울임) → C(남쪽 옆 시점) → 느린 옆 이동."""

    def __init__(self, keys: Keys, center_lat: float, width_deg: float, w: int, h: int) -> None:
        self.k = keys
        self.w, self.h = w, h
        width_km = width_deg * G.km_per_deg * math.cos(math.radians(center_lat))
        hA = width_km / 2 / math.tan(math.radians(G.fov_deg) / 2)
        self.A = (hA * Z_AXIS, np.zeros(3), G.fov_deg)
        self.B = (np.array(G.key_b.pos_km), np.array(G.key_b.target_km), G.fov_side_deg)
        self.C = (np.array(G.key_c.pos_km), np.array(G.key_c.target_km), G.fov_side_deg)

    def k_at(self, t: float) -> float:
        u = ease_io(clamp01((t - self.k.t_k0) / (self.k.t_k1 - self.k.t_k0)))
        return math.exp(math.log(G.k_max) * (1 - u))

    def pose(self, t: float) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
        K, A, B, Cc = self.k, self.A, self.B, self.C
        if t <= K.t_k0:
            p, tg, f = A
        elif t <= K.t_k1:
            u = ease_io((t - K.t_k0) / (K.t_k1 - K.t_k0))
            p, tg, f = A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u
        elif t <= K.t_side1:
            u = ease_io((t - K.t_side0) / (K.t_side1 - K.t_side0))
            p, tg, f = B[0] + (Cc[0] - B[0]) * u, B[1] + (Cc[1] - B[1]) * u, B[2] + (Cc[2] - B[2]) * u
        else:
            u = (t - K.t_side1) / (K.duration - K.t_side1)
            p, tg, f = Cc[0] + G.side_drift_km * X_AXIS * smooth(u), Cc[1], Cc[2]   # 느린 옆 이동(패럴랙스)
        up = Y_AXIS if t <= K.t_k0 + G.up_switch_sec else Z_AXIS
        if K.t_k0 < t <= K.t_k1:   # 하향(위 = 북) → 기울임(위 = 천정) 사이 업 벡터 보간
            u = ease_io((t - K.t_k0) / (K.t_k1 - K.t_k0))
            up = Y_AXIS * (1 - u) + Z_AXIS * u
        return p, tg, f, up

    def cam(self, t: float) -> Cam:
        p, tg, f, up = self.pose(t)
        return Cam(p, tg, f, up, self.w, self.h)


# ---------------------------------------------------------------- 지구 래스터
def render_globe(cam: Cam, k: float, tex: list[Tex], rays: np.ndarray, cen: tuple[float, float]) -> np.ndarray:
    """광선 × 구 교차 → 텍스처 표본 + 램버트·시야 그늘 + 테두리 빛, 구 밖은 우주 배경 + 대기 글로. RGB uint8(h, w, 3)."""
    rk = k * EARTH_KM
    c = -rk * Z_AXIS
    oc = cam.pos - c
    b = rays @ oc
    cc = oc @ oc - rk * rk
    disc = b * b - cc
    hit = disc > 0
    img = np.zeros((cam.w * cam.h, 3), np.float32)
    closest = np.sqrt(np.maximum(oc @ oc - b * b, 0))   # 광선이 구에 가장 가까이 가는 거리
    glow = np.clip(1 - (closest - rk) / (EARTH_KM * G.atmos_height), 0, 1) * (b < 0)
    img[:] = np.array(G.space_rgb, np.float32) + glow[:, None] ** G.atmos_pow * np.array(G.atmos_rgb, np.float32) * G.atmos_alpha
    if hit.any():
        t = -b[hit] - np.sqrt(disc[hit])
        Pt = cam.pos + rays[hit] * t[:, None]
        v = Pt - c
        th = np.arctan2(np.hypot(v[:, 0], v[:, 1]), v[:, 2])
        az = np.degrees(np.arctan2(v[:, 0], v[:, 1]))
        lon, lat = dest_arr(cen[0], cen[1], az, rk * th)
        col = np.zeros((len(lon), 3), np.float32)
        for tx in tex:                      # 거친 것 → 세밀한 것 순으로 덮는다
            s, ok = tx.sample(lon, lat)
            col[ok] = s[ok]
        n = v / rk
        light = np.array(G.light)
        light /= np.linalg.norm(light)
        lam = np.clip(n @ light, 0, 1)
        view_cos = np.clip(-(rays[hit] * n).sum(1), 0, 1)
        lb, lw, vb, vw, vp = G.shade
        shade = (lb + lw * lam) * (vb + vw * view_cos ** vp)
        rim = (1 - view_cos) ** G.rim_pow
        col = col * shade[:, None] + rim[:, None] * np.array(G.rim_rgb, np.float32) * G.rim_alpha
        img[hit] = col
    return np.clip(img, 0, BYTE_MAX).astype(np.uint8).reshape(cam.h, cam.w, 3)


# ---------------------------------------------------------------- 선 그리기(가림 처리)
def polyline(ctx: cairo.Context, cam: Cam, P: np.ndarray, k: float, col: tuple, a: float, wd: float,
             dash: list | None = None, glow: bool = True) -> None:
    """3D 점열 → 보이는 구간만 이어 그린다(구 뒤·카메라 뒤 점은 끊는다). glow = 세 겹 글로."""
    S, front = cam.project(P)
    vis = front & visible(cam, P, k)
    runs, cur = [], []
    for i in range(len(S)):
        if vis[i]:
            cur.append(S[i])
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    layers = [(wd * m, al) for m, al in G.glow_layers] if glow else [(wd, G.plain_alpha)]
    for run in runs:
        if len(run) < 2:
            continue
        for w_, al in layers:
            ctx.new_path()
            ctx.move_to(*run[0])
            for p in run[1:]:
                ctx.line_to(*p)
            if dash:
                ctx.set_dash(dash)
            ctx.set_source_rgba(*col, al * a)
            ctx.set_line_width(w_)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
            ctx.set_dash([])


def border_rings(coarse: dict) -> list[np.ndarray]:
    """엔진 거친 국경 고리 중 권역 안 것, 점 수를 줄여서(geo.prep 권역 상자로 잘린 가장자리 구간은 끊는다)."""
    (lo0, lo1), (la0, la1) = G.border_lon, G.border_lat
    bx0, bx1, by0, by1 = G.border_cut_box
    e = G.border_cut_eps
    out = []
    for rings in coarse.values():
        for ring in rings:
            a = np.asarray(ring, float)
            if len(a) < 3:
                continue
            if a[:, 0].max() < lo0 or a[:, 0].min() > lo1 or a[:, 1].max() < la0 or a[:, 1].min() > la1:
                continue
            a = a[:: max(1, len(a) // G.border_max_pts)]
            edge = (np.abs(a[:, 0] - bx0) < e) | (np.abs(a[:, 0] - bx1) < e) | (np.abs(a[:, 1] - by0) < e) | (np.abs(a[:, 1] - by1) < e)
            cut = np.where(edge[:-1] & edge[1:])[0]
            out += [seg for seg in np.split(a, cut + 1) if len(seg) >= 2]
    return out


# ---------------------------------------------------------------- 레이더 볼륨
def radar_volume(s: Sensor, launch: tuple[float, float], cen: tuple[float, float], k: float) -> dict:
    """부채 볼륨 테두리(아래 부채 · 바깥 껍질 · 위 부채). 레이더 국소 ENU 에서 직선 광선 → 국소 3D."""
    lon0, lat0 = s.lon, s.lat
    brg = s.bearing_deg if s.bearing_deg is not None else bearing((lon0, lat0), launch)
    w = s.az_width_deg
    el0, el1 = s.el_deg   # type: ignore[misc]
    az = np.radians(brg - w / 2 + w * np.linspace(0, 1, G.volume_az_n))   # type: ignore[operator]
    el_lo, el_hi = np.radians(el0), np.radians(el1)
    base = to_local(cen, np.array([lon0]), np.array([lat0]), np.array([0.0]), k)[0]
    cvec = base + k * EARTH_KM * Z_AXIS
    up = cvec / np.linalg.norm(cvec)
    north_ref = to_local(cen, np.array([lon0]), np.array([lat0 + G.north_ref_deg]), np.array([0.0]), k)[0] - base
    north = north_ref - up * (north_ref @ up)
    north /= np.linalg.norm(north)
    east = np.cross(north, up)
    rng = s.range_km

    def ray(a_: np.ndarray, e_: float) -> np.ndarray:
        d = (np.cos(e_) * (np.sin(a_)[:, None] * east + np.cos(a_)[:, None] * north) + np.sin(e_) * up)
        return base + d * rng

    els = np.linspace(el_lo, el_hi, G.volume_el_n)
    side = [np.array([ray(np.array([a]), e)[0] for e in els]) for a in (az[0], az[-1], az[len(az) // 2])]
    return dict(base=base, lower=ray(az, el_lo), upper=ray(az, el_hi), side_l=side[0], side_r=side[1], mid=side[2],
                up=up, north=north, east=east, brg=brg)


def in_volume(s: Sensor, vol: dict, P: np.ndarray) -> np.ndarray:
    """점들이 볼륨 안(거리·고각·방위 폭)인가."""
    v = P - vol["base"]
    rng = np.linalg.norm(v, axis=1)
    e = np.degrees(np.arcsin(np.clip((v @ vol["up"]) / np.maximum(rng, G.z_eps), -1, 1)))
    a = np.degrees(np.arctan2(v @ vol["east"], v @ vol["north"]))
    da = (a - vol["brg"] + 180) % 360 - 180
    el0, el1 = s.el_deg   # type: ignore[misc]
    return (rng <= s.range_km) & (e >= el0) & (e <= el1) & (np.abs(da) <= s.az_width_deg / 2)   # type: ignore[operator]


def draw_volume(ctx: cairo.Context, cam: Cam, vol: dict, k: float, col: tuple, a: float, lit: float, lw: float) -> None:
    """lw = 선 굵기·대시 배율(출력 높이 / px_ref_height)."""
    def fill_poly(P: np.ndarray, al: float) -> None:
        S, front = cam.project(P)
        if not front.all():
            return
        ctx.new_path()
        ctx.move_to(*S[0])
        for p in S[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.set_source_rgba(*col, al)
        ctx.fill()
    b = vol["base"][None, :]
    lo_a, lo_lit = G.volume_lower_alpha
    hi_a, hi_lit = G.volume_upper_alpha
    fill_poly(np.vstack([b, vol["lower"]]), (lo_a + lo_lit * lit) * a)
    fill_poly(np.vstack([b, vol["upper"]]), (hi_a + hi_lit * lit) * a)
    e_a, e_lit = G.volume_edge_alpha
    for edge in (np.vstack([b, vol["lower"][:1]]), np.vstack([b, vol["lower"][-1:]]), vol["lower"], vol["upper"],
                 vol["side_l"], vol["side_r"], np.vstack([b, vol["upper"][:1]]), np.vstack([b, vol["upper"][-1:]])):
        polyline(ctx, cam, edge, k, col, (e_a + e_lit * lit) * a, G.volume_edge_w * lw, glow=False)
    polyline(ctx, cam, vol["mid"], k, col, G.volume_mid_alpha * a, G.volume_mid_w * lw, dash=[d * lw for d in G.volume_mid_dash],
             glow=False)

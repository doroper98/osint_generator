"""Phase D1 3D 시제품 — 2D 지도 → 지구 곡면 전환, 실제 축척 고각 궤적, 레이더 탐지 볼륨(방위·고각).

    python projects/d1_missile_sketch/globe3d.py               → out/d1_globe_proto.mp4 + out/d1_globe_sheet.jpg
    python projects/d1_missile_sketch/globe3d.py --frames 3,8,12 → 정지 화면

원리
- 곡률 전환: 접점 c 에서 접하는 반지름 kR 구를 그린다. 구 위 점은 '접점에서의 방위·지표 거리'를 그대로 지구 좌표로 옮긴다
  (거리 보존). k → ∞ 면 평면(방위 등거리 지도), k = 1 이면 실제 지구. k 를 줄이면 지도가 휘어 지구본이 된다.
- 배경 지형: 엔진 geo.prep 티어(같은 지형 스타일) — 전 지구(globe_tex, ppd 8) 위에 동아시아 상세 티어(720p)를 얹는다.
- 궤적: 지상 투영(대원) + 고도 = 개념 곡선 × 정점 6,040.9km(일본 방위성). 축척은 실제(지구 반지름 6,371km 대비).
- 레이더 볼륨: 방위 폭·고각 범위·거리로 만든 부채 볼륨(개념값). 미사일이 볼륨 안이고 지구에 가리지 않을 때만 '가시'.
  가시 판정은 기하만 본다(대기 굴절·레이더 단면적·운용 모드 무시) — 화면에 표기.
"""

from __future__ import annotations

import argparse
import math
import pickle
import subprocess
import sys
from pathlib import Path

import cairo
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

PROJ = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ))
sys.path.insert(0, str(PROJ.parents[1]))

import sketch_d1 as K  # noqa: E402
from engine.stage import ym  # noqa: E402
from engine.style import C, FPS  # noqa: E402
from engine.timebase import clamp01, ease_io, ease_out, smooth, window  # noqa: E402
from engine.typography import rrect, text, tw  # noqa: E402

W, H = 1280, 720
SC = 1.5                      # 설계 px(854×480) → 720p
R = 6371.0
CEN = (132.9, 40.3)           # 접점 = 2D 궤적 숏 중심(sketch_d1 SHOTS[3])
TOTAL = 19.0
T_2D, T_X = 2.0, 1.0          # 2D 유지 → 교차 전환
T_K0, T_K1 = 3.0, 7.5         # 곡률 전환(k: K_MAX → 1)
K_MAX = 80.0
T_SIDE0, T_SIDE1 = 7.5, 11.0  # 옆 시점으로 이동
T_FLY0, T_FLY1 = 11.0, 16.5   # 미사일 비행(4,135초 압축)
APOGEE = 6040.9               # km, 일본 방위성
RADARS = [  # 개념값 — 방위 폭·고각 범위는 공개 정밀 사양 없음(화면 표기)
    dict(name="AN/TPY-2 · 성주", at=(128.28, 35.99), km=600, az_w=120, el=(0.0, 60.0), col="us"),
    dict(name="AN/TPY-2 · 샤리키", at=(140.32, 40.89), km=1000, az_w=120, el=(0.0, 60.0), col="teal"),
    dict(name="AN/TPY-2 · 교가미사키", at=(135.22, 35.76), km=1000, az_w=120, el=(0.0, 60.0), col="teal"),
]


# ---------------------------------------------------------------- 지형 텍스처
class Tex:
    def __init__(self, tiers_pkl: Path, base_dir: Path, name: str) -> None:
        T = pickle.load(open(tiers_pkl, "rb"))[name]
        self.lv = max(T["levels"])
        self.lon0, self.lon1, self.lat0, self.lat1 = T["lon0"], T["lon1"], T["lat0"], T["lat1"]
        self.y_top = ym(self.lat1)
        self.img = np.asarray(Image.open(base_dir / f"base_{name}_{self.lv}.png").convert("RGB"), dtype=np.float32)

    def sample(self, lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        lat_c = np.clip(lat, -84.9, 84.9)
        yy = (self.y_top - np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat_c) / 2)))) * self.lv
        xx = (lon - self.lon0) * self.lv
        ok = (lon >= self.lon0 + 0.05) & (lon <= self.lon1 - 0.05) & (lat >= self.lat0 + 0.05) & (lat <= self.lat1 - 0.05)
        out = np.stack([map_coordinates(self.img[:, :, c], [yy, xx], order=1, mode="nearest") for c in range(3)], axis=1)
        return out, ok


def load_textures() -> list[Tex]:
    g = PROJ / "globe_tex" / "assets"
    r = PROJ / "assets" / "res_720p"
    return [Tex(g / "tiers.pkl", g, "W"), Tex(r / "tiers.pkl", r, "W"), Tex(r / "tiers.pkl", r, "K")]


# ---------------------------------------------------------------- 측지 ↔ 국소 3D(접점 c 기준, x 동 y 북 z 위)
def dest_v(lon: float, lat: float, brg: np.ndarray, km: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p1, l1, b, d = math.radians(lat), math.radians(lon), np.radians(brg), km / R
    p2 = np.arcsin(np.clip(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(b), -1, 1))
    l2 = l1 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2))
    return (np.degrees(l2) + 540) % 360 - 180, np.degrees(p2)


def to_local(lon: np.ndarray, lat: np.ndarray, alt: np.ndarray, k: float) -> np.ndarray:
    """지구 점(경위도·고도 km) → 반지름 kR 구(접점 c, 거리·방위 보존) 위 국소 3D 좌표."""
    lon, lat, alt = np.atleast_1d(lon).astype(float), np.atleast_1d(lat).astype(float), np.atleast_1d(alt).astype(float)
    l1, p1, l2, p2 = math.radians(CEN[0]), math.radians(CEN[1]), np.radians(lon), np.radians(lat)
    h = np.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    d = 2 * R * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
    y = np.sin(l2 - l1) * np.cos(p2)
    x = math.cos(p1) * np.sin(p2) - math.sin(p1) * np.cos(p2) * np.cos(l2 - l1)
    az = np.arctan2(y, x)
    rk = k * R
    th = d / rk
    rr = rk + alt
    return np.column_stack([rr * np.sin(th) * np.sin(az), rr * np.sin(th) * np.cos(az), rr * np.cos(th) - rk])


# ---------------------------------------------------------------- 카메라
class Cam:
    def __init__(self, pos: np.ndarray, target: np.ndarray, fov_deg: float, roll_up: np.ndarray | None = None) -> None:
        self.pos = np.asarray(pos, float)
        f = np.asarray(target, float) - self.pos
        self.fwd = f / np.linalg.norm(f)
        up0 = np.array([0.0, 1.0, 0.0]) if roll_up is None else np.asarray(roll_up, float)
        if abs(np.dot(up0 / np.linalg.norm(up0), self.fwd)) > 0.999:
            up0 = np.array([0.0, 0.0, 1.0])
        r = np.cross(self.fwd, up0)
        self.right = r / np.linalg.norm(r)
        self.up = np.cross(self.right, self.fwd)
        self.f = (W / 2) / math.tan(math.radians(fov_deg) / 2)

    def rays(self) -> np.ndarray:
        xs = (np.arange(W) + 0.5 - W / 2) / self.f
        ys = -(np.arange(H) + 0.5 - H / 2) / self.f
        gx, gy = np.meshgrid(xs, ys)
        d = self.fwd[None, None, :] + gx[..., None] * self.right[None, None, :] + gy[..., None] * self.up[None, None, :]
        return (d / np.linalg.norm(d, axis=2, keepdims=True)).reshape(-1, 3)

    def project(self, P: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        v = P - self.pos
        z = v @ self.fwd
        return np.column_stack([W / 2 + self.f * (v @ self.right) / np.maximum(z, 1e-6),
                                H / 2 - self.f * (v @ self.up) / np.maximum(z, 1e-6)]), z > 1.0


def visible(cam: Cam, P: np.ndarray, k: float) -> np.ndarray:
    """카메라→점 선분이 구(지구)에 먼저 막히지 않는가."""
    c = np.array([0.0, 0.0, -k * R])
    o = cam.pos
    d = P - o
    L = np.linalg.norm(d, axis=1)
    d = d / L[:, None]
    oc = o - c
    b = d @ oc
    cc = oc @ oc - (k * R) ** 2
    disc = b * b - cc
    t_hit = -b - np.sqrt(np.maximum(disc, 0))
    return ~((disc > 0) & (t_hit > 1.0) & (t_hit < L - 5.0))


# ---------------------------------------------------------------- 지구 래스터
def render_globe(cam: Cam, k: float, tex: list[Tex], rays: np.ndarray) -> np.ndarray:
    rk = k * R
    c = np.array([0.0, 0.0, -rk])
    oc = cam.pos - c
    b = rays @ oc
    cc = oc @ oc - rk * rk
    disc = b * b - cc
    hit = disc > 0
    img = np.zeros((W * H, 3), np.float32)
    # 우주 배경 + 대기 글로(광선이 구에 가장 가까이 가는 거리)
    closest = np.sqrt(np.maximum(oc @ oc - b * b, 0))
    glow = np.clip(1 - (closest - rk) / (R * 0.05), 0, 1) * (b < 0)
    bg = np.array([5, 8, 14], np.float32)
    img[:] = bg + glow[:, None] ** 2.2 * np.array([70, 140, 220], np.float32) * 0.55
    if hit.any():
        t = -b[hit] - np.sqrt(disc[hit])
        Pt = cam.pos + rays[hit] * t[:, None]
        v = Pt - c
        th = np.arctan2(np.hypot(v[:, 0], v[:, 1]), v[:, 2])
        az = np.degrees(np.arctan2(v[:, 0], v[:, 1]))
        lon, lat = dest_v(CEN[0], CEN[1], az, rk * th)
        col = np.zeros((len(lon), 3), np.float32)
        for tx in tex:                      # 거친 것 → 세밀한 것 순으로 덮는다
            s, ok = tx.sample(lon, lat)
            col[ok] = s[ok]
        n = v / rk
        light = np.array([-0.35, -0.45, 0.82])
        light /= np.linalg.norm(light)
        lam = np.clip(n @ light, 0, 1)
        view_cos = np.clip(-(rays[hit] * n).sum(1), 0, 1)
        shade = (0.45 + 0.55 * lam) * (0.55 + 0.45 * view_cos ** 0.6)
        rim = (1 - view_cos) ** 3
        col = col * shade[:, None] + rim[:, None] * np.array([60, 120, 200], np.float32) * 0.35
        img[hit] = col
    return np.clip(img, 0, 255).astype(np.uint8).reshape(H, W, 3)


# ---------------------------------------------------------------- 그리기(cairo, 720p 장치 px)
def polyline(ctx: cairo.Context, cam: Cam, P: np.ndarray, k: float, col: tuple, a: float, wd: float,
             dash: list | None = None, glow: bool = True) -> None:
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
    for run in runs:
        if len(run) < 2:
            continue
        layers = ((wd * 4, 0.08), (wd * 2, 0.22), (wd, 0.95)) if glow else ((wd, 0.9),)
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


def label(ctx: cairo.Context, s: str, x: float, y: float, a: float, sub: str | None = None, col: tuple = (1, 1, 1),
          sub_col: tuple = C["gold"], anchor: str = "l") -> None:
    text(ctx, s, x, y, 13 * SC, "sansb", col, a, 3.2 * SC, anchor)
    if sub:
        text(ctx, sub, x, y + 17 * SC, 11.5 * SC, "sansm", sub_col, a, 3 * SC, anchor)


def borders(stage, lon_rng=(100, 160), lat_rng=(15, 60)) -> list[np.ndarray]:  # noqa: ANN001
    out = []
    for rings in stage.assets.geo["coarse"].values():
        for ring in rings:
            a = np.asarray(ring, float)
            if len(a) < 3:
                continue
            if a[:, 0].max() < lon_rng[0] or a[:, 0].min() > lon_rng[1] or a[:, 1].max() < lat_rng[0] or a[:, 1].min() > lat_rng[1]:
                continue
            a = a[:: max(1, len(a) // 400)]
            edge = ((np.abs(a[:, 0] - 105) < 0.05) | (np.abs(a[:, 0] - 165) < 0.05) | (np.abs(a[:, 1] - 18) < 0.05) | (np.abs(a[:, 1] - 56) < 0.05))
            cut = np.where(edge[:-1] & edge[1:])[0]   # geo.prep 권역 상자로 잘린 가장자리 구간
            for seg in np.split(a, cut + 1):
                seg = seg[~edge[: len(seg)]] if False else seg
                if len(seg) >= 2:
                    out.append(seg)
    return out


# ---------------------------------------------------------------- 궤적·레이더 기하
def los_index(r: dict) -> int:
    """미사일이 레이더 지평선 위로 올라오는 첫 궤적 점(실제 지구, 고각 ≥ 0°). 사양과 무관한 순수 기하."""
    P = to_local(TRACK[:, 0], TRACK[:, 1], ALT, 1.0)
    vol = radar_volume(r, 1.0)
    v = P - vol["base"]
    el = np.degrees(np.arcsin(np.clip((v @ vol["up"]) / np.linalg.norm(v, axis=1), -1, 1)))
    idx = np.where(el >= 0)[0]
    return int(idx[0]) if len(idx) else len(P)


TRACK = K.TRACK_LL                                  # 대원 지상 궤적(경위도), sketch_d1 과 같은 점
U = np.linspace(0, 1, len(TRACK))
ALT = K.loft(U) * APOGEE                            # 개념 곡선 × 발표 정점 고도


def radar_volume(r: dict, k: float, n_az: int = 25, n_el: int = 7) -> dict:
    """부채 볼륨의 테두리선(아래 부채 · 바깥 껍질 · 위 부채). 레이더 국소 ENU 에서 직선 광선 → 지구 좌표."""
    lon0, lat0 = r["at"]
    brg = K.bearing(r["at"], K.LAUNCH)
    az = np.radians(brg - r["az_w"] / 2 + r["az_w"] * np.linspace(0, 1, n_az))
    el_lo, el_hi = np.radians(r["el"][0]), np.radians(r["el"][1])
    base = to_local(np.array([lon0]), np.array([lat0]), np.array([0.0]), k)[0]
    # 레이더 지점의 국소 축(구 법선 기준)
    cvec = base - np.array([0.0, 0.0, -k * R])
    up = cvec / np.linalg.norm(cvec)
    north_ref = to_local(np.array([lon0]), np.array([lat0 + 0.01]), np.array([0.0]), k)[0] - base
    north = north_ref - up * (north_ref @ up)
    north /= np.linalg.norm(north)
    east = np.cross(north, up)

    def ray(a_: np.ndarray, e_: float, rng: float) -> np.ndarray:
        d = (np.cos(e_) * (np.sin(a_)[:, None] * east + np.cos(a_)[:, None] * north) + np.sin(e_) * up)
        return base + d * rng

    rng = r["km"]
    lower = ray(az, el_lo, rng)                       # 고각 0° 부채 끝(지표에서 점점 떠오른다 — 레이더 수평선)
    upper = ray(az, el_hi, rng)
    shell = [ray(np.array([a]), e, rng)[0] for a in (az[0], az[-1]) for e in np.linspace(el_lo, el_hi, n_el)]
    side_l = np.array([ray(np.array([az[0]]), e, rng)[0] for e in np.linspace(el_lo, el_hi, n_el)])
    side_r = np.array([ray(np.array([az[-1]]), e, rng)[0] for e in np.linspace(el_lo, el_hi, n_el)])
    mid = np.array([ray(np.array([az[len(az) // 2]]), e, rng)[0] for e in np.linspace(el_lo, el_hi, n_el)])
    return dict(base=base, lower=lower, upper=upper, side_l=side_l, side_r=side_r, mid=mid, up=up, north=north, east=east,
                brg=brg, shell=shell)


def in_volume(r: dict, vol: dict, P: np.ndarray) -> np.ndarray:
    v = P - vol["base"]
    rng = np.linalg.norm(v, axis=1)
    e = np.degrees(np.arcsin(np.clip((v @ vol["up"]) / np.maximum(rng, 1e-6), -1, 1)))
    a = np.degrees(np.arctan2(v @ vol["east"], v @ vol["north"]))
    da = (a - vol["brg"] + 180) % 360 - 180
    return (rng <= r["km"]) & (e >= r["el"][0]) & (e <= r["el"][1]) & (np.abs(da) <= r["az_w"] / 2)


def draw_volume(ctx: cairo.Context, cam: Cam, vol: dict, k: float, col: tuple, a: float, lit: float) -> None:
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
    fill_poly(np.vstack([b, vol["lower"]]), (0.10 + 0.12 * lit) * a)
    fill_poly(np.vstack([b, vol["upper"]]), (0.05 + 0.08 * lit) * a)
    for edge in (np.vstack([b, vol["lower"][:1]]), np.vstack([b, vol["lower"][-1:]]), vol["lower"], vol["upper"],
                 vol["side_l"], vol["side_r"], np.vstack([b, vol["upper"][:1]]), np.vstack([b, vol["upper"][-1:]])):
        polyline(ctx, cam, edge, k, col, (0.55 + 0.45 * lit) * a, 1.3, glow=False)
    polyline(ctx, cam, vol["mid"], k, col, 0.35 * a, 1.0, dash=[3, 4], glow=False)


LOS_IDX: dict = {}


def init_los() -> None:
    for r in RADARS:
        LOS_IDX[r["name"]] = los_index(r)


# ---------------------------------------------------------------- 연출(카메라 경로)
def k_at(t: float) -> float:
    u = ease_io(clamp01((t - T_K0) / (T_K1 - T_K0)))
    return math.exp(math.log(K_MAX) * (1 - u))


def cam_at(t: float) -> Cam:
    # A: 2D 숏과 같은 화면(수직 하향, 가로 폭 = 2D w 19.5° × cos 위도) — B: 높이 올라가며 기울임 — C: 남쪽 옆 시점
    width_km = 19.5 * 0.965 * 111.32 * math.cos(math.radians(CEN[1]))
    fov = 40.0
    hA = width_km / 2 / math.tan(math.radians(fov / 2))
    A = (np.array([0.0, 0.0, hA]), np.array([0.0, 0.0, 0.0]), fov)
    B = (np.array([0.0, -9000.0, 11000.0]), np.array([0.0, 0.0, -600.0]), 46.0)
    Cc = (np.array([1400.0, -19500.0, 4200.0]), np.array([-250.0, 0.0, 2900.0]), 46.0)
    if t <= T_K0:
        p, tg, f = A
    elif t <= T_K1:
        u = ease_io((t - T_K0) / (T_K1 - T_K0))
        p, tg, f = A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u
    elif t <= T_SIDE1:
        u = ease_io((t - T_SIDE0) / (T_SIDE1 - T_SIDE0))
        p, tg, f = B[0] + (Cc[0] - B[0]) * u, B[1] + (Cc[1] - B[1]) * u, B[2] + (Cc[2] - B[2]) * u
    else:
        u = (t - T_SIDE1) / (TOTAL - T_SIDE1)
        p, tg, f = Cc[0] + np.array([-900.0, 0, 0]) * smooth(u), Cc[1], Cc[2]   # 느린 옆 이동(패럴랙스)
    up = np.array([0.0, 1.0, 0.0]) if t <= T_K0 + 0.01 else np.array([0.0, 0.0, 1.0])
    if T_K0 < t <= T_K1:   # 하향(위=북) → 기울임(위=천정) 사이 업 벡터 보간
        u = ease_io((t - T_K0) / (T_K1 - T_K0))
        up = np.array([0.0, 1.0 - u, u])
    return Cam(p, tg, f, up)


# ---------------------------------------------------------------- 프레임
class Scene:
    def __init__(self) -> None:
        self.tex = load_textures()
        init_los()
        self.stage = K.build_stage()
        self.eez = K.EEZ()
        self.bord = borders(self.stage)
        jp = next(f for f in self.eez.feat if f["code"] == "JP")
        self.jp_lines = [np.asarray(ln) for ln in jp["lines"] if len(ln) > 8]

    def frame(self, t: float) -> np.ndarray:
        if t < T_2D:
            return self.frame_2d(K.T_TRACK1 + 3.0 + t * 0.3)
        g = self.frame_3d(t)
        if t < T_2D + T_X:
            a = smooth((t - T_2D) / T_X)
            f2 = self.frame_2d(K.T_TRACK1 + 3.0 + T_2D * 0.3).astype(np.float32)
            g = (f2 * (1 - a) + g.astype(np.float32) * a).astype(np.uint8)
        fa = 1 - min(smooth(t / 0.6), smooth((TOTAL - t) / 1.0))
        return (g.astype(np.float32) * (1 - fa)).astype(np.uint8)

    def frame_2d(self, t2: float) -> np.ndarray:
        buf, _ = K.render(self.stage, self.eez, t2)
        return np.frombuffer(bytes(buf), np.uint8).reshape(H, W, 4)[:, :, [2, 1, 0]].copy()

    def frame_3d(self, t: float) -> np.ndarray:
        k = k_at(max(t, T_K0))
        cam = cam_at(max(t, T_K0 - 0.001) if t >= T_2D else T_K0)
        base = render_globe(cam, k, self.tex, cam.rays())
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        arr = np.ndarray((H, W, 4), np.uint8, surf.get_data())
        arr[:, :, 0], arr[:, :, 1], arr[:, :, 2] = base[:, :, 2], base[:, :, 1], base[:, :, 0]
        surf.mark_dirty()
        ctx = cairo.Context(surf)
        for ring in self.bord:
            P = to_local(ring[:, 0], ring[:, 1], np.zeros(len(ring)), k)
            polyline(ctx, cam, P, k, (0.85, 0.88, 0.92), 0.35, 0.9, glow=False)
        for ln in self.jp_lines:
            P = to_local(ln[:, 0], ln[:, 1], np.zeros(len(ln)), k)
            polyline(ctx, cam, P, k, C["teal"], 0.7, 1.2, dash=[5, 4], glow=False)
        # 지상 궤적(2D 와 같은 선) — 곡률 전환 내내 유지
        G = to_local(TRACK[:, 0], TRACK[:, 1], np.zeros(len(TRACK)), k)
        polyline(ctx, cam, G, k, C["ru"], 0.55 if t > T_SIDE0 else 1.0, 2.2 if t < T_SIDE0 else 1.4)
        # 레이더 볼륨
        vols = [radar_volume(r, k) for r in RADARS]
        va = smooth((t - (T_K1 - 1.0)) / 1.0)
        prog = ease_io(clamp01((t - T_FLY0) / (T_FLY1 - T_FLY0)))
        n = max(2, int(round(1 + (len(TRACK) - 1) * prog)))
        A3 = to_local(TRACK[:, 0], TRACK[:, 1], ALT, k)
        head = A3[n - 1:n]
        lit = []
        for r, vol in zip(RADARS, vols):
            i_los = LOS_IDX[r["name"]]
            seen = t >= T_FLY0 and n - 1 >= i_los
            lit.append(seen)
            if va > 0.01:
                draw_volume(ctx, cam, vol, k, C[r["col"]], va, 0.0)
        # 3D 고각 궤적 + 고도 커튼
        ta = smooth((t - (T_SIDE0 + 1.2)) / 1.0)
        if ta > 0.01:
            m = n if t >= T_FLY0 else len(TRACK)
            for i in range(0, m, 8):
                polyline(ctx, cam, np.vstack([G[i], A3[i]]), k, C["ru"], 0.16 * ta, 1.0, glow=False)
            if t < T_FLY0:   # 비행 전: 전체 궤적을 흐린 점선으로 예고
                polyline(ctx, cam, A3, k, C["ru"], 0.35 * ta, 1.2, dash=[4, 5], glow=False)
            else:
                polyline(ctx, cam, A3[:n], k, C["ru"], ta, 2.4)
                if prog < 1:
                    S, front = cam.project(head)
                    if front[0] and visible(cam, head, k)[0]:
                        hx, hy = float(S[0, 0]), float(S[0, 1])
                        g = cairo.RadialGradient(hx, hy, 0, hx, hy, 22)
                        g.add_color_stop_rgba(0, 1, 1, 1, 0.95)
                        g.add_color_stop_rgba(0.3, *C["ru"], 0.6)
                        g.add_color_stop_rgba(1, *C["ru"], 0)
                        ctx.set_source(g)
                        ctx.arc(hx, hy, 22, 0, 2 * math.pi)
                        ctx.fill()
        self.labels(ctx, cam, k, t, vols, lit, prog, A3, G)
        surf.flush()
        out = np.ndarray((H, W, 4), np.uint8, surf.get_data())
        return out[:, :, [2, 1, 0]].copy()

    def labels(self, ctx: cairo.Context, cam: Cam, k: float, t: float, vols: list, lit: list, prog: float,
               A3: np.ndarray, G: np.ndarray) -> None:
        def at(P: np.ndarray) -> tuple[float, float, bool]:
            S, f = cam.project(P[None, :])
            ok = bool(f[0] and visible(cam, P[None, :], k)[0])
            return float(S[0, 0]), float(S[0, 1]), ok
        la = smooth((t - (T_SIDE0 + 1.6)) / 0.6)
        x, y, ok = at(G[0])
        if ok and la > 0.01:
            label(ctx, "평양 순안 일대", x - 14, y + 6, la, "발사", sub_col=C["ru"], anchor="r")
        x, y, ok = at(G[-1])
        if ok and la > 0.01:
            label(ctx, "착탄 추정 영역", x + 14, y + 6, la, "일본 EEZ 안", sub_col=C["teal"])
        top = A3[len(A3) // 2]
        x, y, ok = at(top)
        if ok and la > 0.01:
            label(ctx, "정점 약 6,040km", x + 16, y - 6, la, "일본 방위성 · 실제 축척", sub_col=C["gold"])
        ra = window(t, T_K1 - 0.6, T_SIDE0 + 1.6, 0.6, 0.6)
        offs = {"AN/TPY-2 · 성주": (-10, 30, "r"), "AN/TPY-2 · 샤리키": (12, -18, "l"), "AN/TPY-2 · 교가미사키": (12, 30, "l")}
        for r, vol in zip(RADARS, vols):
            x, y, ok = at(vol["base"])
            dx, dy, anc = offs[r["name"]]
            if ok and ra > 0.01:
                label(ctx, r["name"], x + dx * SC, y + dy * SC, ra, f"{r['km']:,}km · 방위 {r['az_w']}° · 고각 {r['el'][0]:.0f}~{r['el'][1]:.0f}°(개념)",
                      sub_col=C[r["col"]], anchor=anc)
        pa = smooth((t - T_SIDE1 + 0.4) / 0.6)
        if pa > 0.01:   # 오른쪽 패널: 발사 지점 상공이 각 레이더 수평선 위로 보이는 최소 고도(거리·지구 반지름만의 기하)
            px, py = W - 336 * SC, 292 * SC
            rrect(ctx, px - 12 * SC, py - 26 * SC, 322 * SC, 140 * SC, 8 * SC)
            ctx.set_source_rgba(0.05, 0.06, 0.09, 0.82 * pa)
            ctx.fill()
            text(ctx, "발사 지점 상공이 보이기 시작하는 고도", px, py - 6 * SC, 12 * SC, "sansb", (1, 1, 1), pa, 0)
            for j, r in enumerate(RADARS):
                yy = py + (20 + 22 * j) * SC
                d = K.gc_dist(r["at"], K.LAUNCH)
                h = R * (1 / math.cos(d / R) - 1)
                ctx.arc(px + 5 * SC, yy - 4 * SC, 4.5 * SC, 0, 2 * math.pi)
                ctx.set_source_rgba(*C[r["col"]], pa)
                ctx.fill()
                text(ctx, r["name"].replace("AN/TPY-2 · ", ""), px + 16 * SC, yy, 12 * SC, "sansm", (1, 1, 1), pa, 0)
                text(ctx, f"거리 {d:,.0f}km", px + 120 * SC, yy, 11 * SC, "sansm", C["muted"], pa, 0)
                text(ctx, f"약 {h:,.0f}km 위", px + 298 * SC, yy, 12 * SC, "sansb", C[r["col"]], pa, 0, "r")
            text(ctx, "지구 곡률(고각 0°)만 계산 · 굴절·탐지 성능과 별개", px, py + 92 * SC, 9.5 * SC, "sans", C["muted"], pa, 0)
            text(ctx, "먼 레이더일수록 발사 직후 저고도 구간을 수평선에 가려 못 본다", px, py + 106 * SC, 9.5 * SC, "sans", C["muted"], pa, 0)
        # 비행 계기 + 주석
        fa = window(t, T_FLY0, TOTAL, 0.4, 0.8)
        sec = int(K.FLIGHT_SEC * prog)
        text(ctx, "비행 경과", 32 * SC, 396 * SC, 11.5 * SC, "sansm", C["muted"], fa, 3 * SC)
        text(ctx, f"+{sec // 60:02d}:{sec % 60:02d}", 32 * SC, 424 * SC, 26 * SC, "mono", (1, 1, 1), fa, 3.5 * SC)
        na = smooth((t - T_SIDE1) / 0.6)
        text(ctx, "탐지 볼륨 = 공개 거리 + 개념 방위·고각(실제 운용 범위는 비공개)",
             14 * SC, 452 * SC, 9.5 * SC, "sans", C["muted"], 0.9 * na, 2 * SC)
        text(ctx, "궤적 높이 = 발표 정점 × 개념 곡선 · 지구 반지름 6,371km 와 같은 축척", 14 * SC, 468 * SC, 9.5 * SC, "sans",
             C["muted"], 0.9 * na, 2 * SC)
        # 날짜(모서리 유일 요소)
        text(ctx, "2022. 11. 18", W - 26 * SC, 40 * SC, 15 * SC, "mono", (1, 1, 1), 0.95, 3 * SC, "r")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default=None)
    args = ap.parse_args()
    out = PROJ / "out"
    out.mkdir(exist_ok=True)
    sc = Scene()
    if args.frames:
        for s in args.frames.split(","):
            Image.fromarray(sc.frame(float(s))).save(out / f"globe_{float(s):05.1f}.png")
            print(out / f"globe_{float(s):05.1f}.png", flush=True)
        return 0
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                           str(out / "d1_globe_proto.mp4")], stdin=subprocess.PIPE)
    cells = []
    marks = [1.0, 4.5, 6.5, 9.0, 12.5, 15.0, 17.5]
    for i in range(int(TOTAL * FPS)):
        t = i / FPS
        f = sc.frame(t)
        ff.stdin.write(f.tobytes())
        if any(abs(t - m) < 0.5 / FPS for m in marks):
            cells.append((Image.fromarray(f).resize((854, 480)), f"t={t:.1f}s"))
        if i % 48 == 0:
            print(f"{i}/{int(TOTAL * FPS)}", flush=True)
    ff.stdin.close()
    ff.wait()
    from engine.sheet import grid
    grid(cells, 2, out / "d1_globe_sheet.jpg", cell=(854, 480))
    print(out / "d1_globe_proto.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

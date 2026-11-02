"""terrain3d 무대 기하 — 지역 평면(m) 투영·부대 키프레임 보간·부대 윤곽(v7.4.0 전쟁사, back_and_forth D-0614·D-0615).

스케치(`sketch.war.terrain3d`·`sketch.war.units`)와 본편 terrain3d 구간(`engine.terrain3d_prep`)이 같은 함수를 쓴다(사본 금지).
수치는 rules(sketch.war.unit·sketch.war.terrain3d — 스케치와 본편이 같은 모양). 이 모듈은 engine.render·engine.project 를 import 하지 않는다
(스케치가 이 모듈을 쓴다 — tests/anti_inertia/test_sketch_no_literals (d) 방향).
"""

from __future__ import annotations

import math

import numpy as np

from engine.timebase import clamp01, smooth
from rules import load_rules
from schemas.war_units import UnitKey, WarUnit
from sketch.common.geodesy import dest   # 순수 수식(numpy) — 측지 전진 한 함수

RIGHT = 90
M_PER_DEG_LAT = 110540.0      # 지구 타원체 근사(위도 1도 m) — 지역 좌표 변환식 상수(geodesy 와 같은 수준)
M_PER_DEG_LON_EQ = 111320.0   # 적도 경도 1도 m


def hexs(rgb: tuple) -> str:
    return "#" + "".join(f"{int(round(c * 255)):02x}" for c in rgb[:3])


class Local:
    """경위도 ↔ 지역 평면 m(x 동쪽, z 남쪽). three.js: 북 = −z."""

    def __init__(self, lon0: float, lat0: float) -> None:
        self.lon0, self.lat0 = lon0, lat0
        self.kx = M_PER_DEG_LON_EQ * math.cos(math.radians(lat0))

    def xz(self, lon: float, lat: float) -> list[float]:
        return [round((lon - self.lon0) * self.kx, 2), round(-(lat - self.lat0) * M_PER_DEG_LAT, 2)]


def key_at(u: WarUnit, t: float) -> UnitKey:
    """시각 t 의 부대 상태 — 앞뒤 키 사이 smooth 보간(첫 키 전 = 첫 키, 마지막 키 뒤 = 마지막 키). 키 시각 t 는 초(앵커는 미리 풀어 둔다)."""
    turn_first = load_rules().sketch.war.unit.turn_first_deg
    ks = u.keys
    if t <= ks[0].t:
        return ks[0]
    for a, b in zip(ks, ks[1:]):
        if t < b.t:
            raw = clamp01((t - a.t) / (b.t - a.t))
            k = smooth(raw)
            dh = (b.heading - a.heading + 180) % 360 - 180
            kz = smooth(clamp01(raw * 2 - 1)) if abs(dh) > turn_first else k   # 큰 회전 = 방위 먼저, 크기는 뒤 절반(D-0602 ⑤)
            return UnitKey(t=t, lon=a.lon + (b.lon - a.lon) * k, lat=a.lat + (b.lat - a.lat) * k, heading=a.heading + dh * k,
                           length_km=a.length_km + (b.length_km - a.length_km) * kz, depth_km=a.depth_km + (b.depth_km - a.depth_km) * kz)
    return ks[-1]


def unit_poly(k: UnitKey) -> list[tuple[float, float]]:
    """정면 폭 × 종심 사각형(경위도) — 뒤-왼, 뒤-오른, 앞-오른, 앞-왼."""
    side = k.heading + RIGHT
    out = []
    for s_lat, s_dep in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lon, lat = dest(k.lon, k.lat, side if s_lat > 0 else side + 180, k.length_km / 2)
        out.append(dest(lon, lat, k.heading if s_dep > 0 else k.heading + 180, k.depth_km / 2))
    return out


def shape_poly(shape: str, rect: list[list[float]]) -> list[list[float]]:
    """2D 와 같은 윤곽(sketch.war.units) — rect = 뒤-왼, 뒤-오른, 앞-오른, 앞-왼(지역 m)."""
    r = np.array(rect)
    if shape == "wedge":
        tip = (r[2] + r[3]) / 2
        out = [r[0], r[1], r[1] + (tip - r[1]) * load_rules().sketch.war.unit.wedge_ratio, tip]
    elif shape == "triangle":
        out = [r[0], r[1], (r[2] + r[3]) / 2]
    else:
        out = list(r)
    return [[round(float(a), 2), round(float(b), 2)] for a, b in out]


def rank_posts(poly: list[list[float]], gap: float, limit: int) -> list[list[float]]:
    """윗면 대열 기둥 — 고정 간격 격자 중 윤곽 안 점(병력 비례 아님). 결정적(격자 순서)."""
    P = np.array(poly)  # noqa: N806
    c = P.mean(axis=0)
    Q = c + (P - c) * 0.85  # noqa: N806 — 가장자리에서 들인 윤곽
    lo, hi = P.min(axis=0), P.max(axis=0)

    def inside(x: float, z: float) -> bool:   # 짝홀 규칙
        hit = False
        for (x1, z1), (x2, z2) in zip(Q, np.roll(Q, -1, axis=0)):
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
                hit = not hit
        return hit

    inside_pts = [(x, z) for z in np.arange(lo[1] + gap / 2, hi[1], gap) for x in np.arange(lo[0] + gap / 2, hi[0], gap) if inside(x, z)]
    return [[round(float(a), 2), round(float(b), 2)] for a, b in inside_pts[:limit]]


__all__ = ["Local", "hexs", "key_at", "rank_posts", "shape_poly", "unit_poly"]

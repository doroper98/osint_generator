"""구면 측지 순수 함수(R = 6371 km) — 스케치 계층 공통(D-0140 §3).

엔진(`engine/`)은 경위도 산술을 하지 않는다(tests/anti_inertia/test_stage_isolation). 스케치는 엔진 밖이라
여기서 계산한다. 수식 모듈이라 숫자 리터럴 검사(test_sketch_no_literals b)에서 면제된다.
원본: 4d9dc65 `projects/d1_missile_sketch/sketch_d1.py` dest·bearing·gc_dist·gc_path·sector_ll, `globe3d.py` 수평선 패널 식.
"""

from __future__ import annotations

import math

import numpy as np

EARTH_KM: float = 6371.0

LonLat = tuple[float, float]


def dest(lon: float, lat: float, brg_deg: float, km: float) -> LonLat:
    """출발점에서 방위각(북 0°, 시계 방향)·지표 거리만큼 간 점(대원)."""
    p1, l1, b, d = math.radians(lat), math.radians(lon), math.radians(brg_deg), km / EARTH_KM
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(l2), math.degrees(p2)


def bearing(a: LonLat, b: LonLat) -> float:
    """a 에서 b 로 가는 첫 방위각(0~360°)."""
    l1, p1, l2, p2 = math.radians(a[0]), math.radians(a[1]), math.radians(b[0]), math.radians(b[1])
    y = math.sin(l2 - l1) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(l2 - l1)
    return math.degrees(math.atan2(y, x)) % 360


def gc_dist(a: LonLat, b: LonLat) -> float:
    """대원 거리 km(하버사인)."""
    l1, p1, l2, p2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def gc_path(a: LonLat, b: LonLat, n: int) -> np.ndarray:
    """두 점 사이 대원 경로 n 점(경위도 배열 n×2)."""
    if n < 2:
        raise ValueError(f"gc_path 점 수 n={n} — 2 이상이어야 한다")
    d, brg = gc_dist(a, b), bearing(a, b)
    return np.array([dest(a[0], a[1], brg, d * i / (n - 1)) for i in range(n)])


def sector(at: LonLat, brg: float, width_deg: float, km: float, n: int) -> np.ndarray:
    """부채꼴 다각형(중심 → 호 n 점 → 중심, 경위도 배열)."""
    if n < 2:
        raise ValueError(f"sector 호 점 수 n={n} — 2 이상이어야 한다")
    arc = [dest(at[0], at[1], brg - width_deg / 2 + width_deg * i / (n - 1), km) for i in range(n)]
    return np.array([at] + arc + [at])


def horizon_altitude(d_km: float) -> float:
    """지표 거리 d 떨어진 레이더의 고각 0° 시선이 그 지점 상공에서 지나는 높이 km = R(1/cos(d/R) − 1).

    사양·대기 굴절과 무관한 순수 기하(CONVENTIONS §3 "레이더 수평선 최소 고도").
    """
    th = d_km / EARTH_KM
    if not 0 <= th < math.pi / 2:
        raise ValueError(f"horizon_altitude 거리 {d_km} km — 0 이상 R·π/2 미만이어야 한다")
    return EARTH_KM * (1 / math.cos(th) - 1)


# ---------------------------------------------------------------- 배열판(3D 지구본, D-0143) — 원본: 4d9dc65 globe3d.py dest_v·to_local·Tex.sample
KM_PER_DEG: float = EARTH_KM * math.pi / 180


def dest_arr(lon: float, lat: float, brg: np.ndarray, km: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """dest 의 배열판(방위·거리 배열). 경도는 −180~180 으로 감는다."""
    p1, l1, b, d = math.radians(lat), math.radians(lon), np.radians(brg), np.asarray(km) / EARTH_KM
    p2 = np.arcsin(np.clip(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(b), -1, 1))
    l2 = l1 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2))
    return (np.degrees(l2) + 540) % 360 - 180, np.degrees(p2)


def to_local(cen: LonLat, lon: np.ndarray, lat: np.ndarray, alt: np.ndarray, k: float) -> np.ndarray:
    """지구 점(경위도·고도 km) → 접점 cen 에서 접하는 반지름 kR 구 위 국소 3D 좌표(x 동 · y 북 · z 위, km).

    구 위 점은 '접점에서의 방위·지표 거리'를 그대로 옮긴다(거리·방위 보존). k → ∞ 면 평면(방위 등거리 지도), k = 1 이면 실제 지구.
    """
    lon, lat, alt = np.atleast_1d(lon).astype(float), np.atleast_1d(lat).astype(float), np.atleast_1d(alt).astype(float)
    l1, p1, l2, p2 = math.radians(cen[0]), math.radians(cen[1]), np.radians(lon), np.radians(lat)
    h = np.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    d = 2 * EARTH_KM * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
    y = np.sin(l2 - l1) * np.cos(p2)
    x = math.cos(p1) * np.sin(p2) - math.sin(p1) * np.cos(p2) * np.cos(l2 - l1)
    az = np.arctan2(y, x)
    rk = k * EARTH_KM
    th = d / rk
    rr = rk + alt
    return np.column_stack([rr * np.sin(th) * np.sin(az), rr * np.sin(th) * np.cos(az), rr * np.cos(th) - rk])


def merc_y_deg(lat: np.ndarray) -> np.ndarray:
    """메르카토르 y(도 단위, engine.stage.ym 과 같은 식)의 배열판."""
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))

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

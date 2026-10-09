"""참고 작전도(SVG) 정합 — 선 스타일 묶음 추출 + 경위도 눈금 교차점 2차 다항 정합(D-0145 §1, SK-G1).

입력 = SVG 경로 + spec georef{style_map, graticule}. 출력 = 경위도로 옮긴 선 묶음(층 → 편 → 조각)과 강, 계수·잔차.
눈금: graticule.stroke·width 인 선 중 세로선 = 경도(lons 순, 서 → 동), 가로선 = 위도(lats 순, 북 → 남). 교차점 = 두 선의 가장 가까운 점 쌍 중점.
좌표 변환: (x, y) → [1, x, y, x², xy, y²] · coef 최소제곱(경도·위도 따로). 잔차 = 교차점에서 최대 |오차|(도).
원본: 4d9dc65 `projects/uranus_sketch/prep_uranus.py`. 수식 모듈이라 숫자 리터럴 검사(test_sketch_no_literals b)에서 면제.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from svgelements import SVG, Circle, Color, Shape

LENGTH_ERROR = 1e-2       # 경로 길이 근사 허용 오차(SVG 단위)
SAMPLE_STEP = 1.0         # 표본 간격(SVG 단위)
ROUND = 4                 # 경위도 소수 자릿수

StyleKey = tuple[str, float, str]   # (색 hex, 굵기, dasharray — 없으면 "")


def collect(svg_path: Path) -> dict[StyleKey, list[np.ndarray]]:
    """SVG 의 획 있는 도형을 (색, 굵기, 점선) 묶음별 표본 점열로."""
    groups: dict[StyleKey, list[np.ndarray]] = defaultdict(list)
    for e in SVG.parse(str(svg_path)).elements():
        if not isinstance(e, Shape) or e.stroke is None or e.stroke.value is None or Color(e.stroke).alpha == 0:
            continue
        try:
            L = e.length(error=LENGTH_ERROR)
        except Exception:  # noqa: BLE001 — 길이를 못 재는 장식 도형은 건너뛴다(원본 동작)
            continue
        dash = e.values.get("stroke-dasharray", "none")
        key = (Color(e.stroke).hex, round(e.stroke_width or 0, 2), "" if dash == "none" else dash)
        n = max(2, int(L / SAMPLE_STEP))
        groups[key].append(np.array([(p.x, p.y) for p in (e.point(t) for t in np.linspace(0, 1, n))]))
    return groups


def circle_centers(svg_path: Path) -> np.ndarray:
    """SVG 원 기호(도시 점 등) 중심 (N, 2) — 변환 적용된 외곽 상자 중심."""
    out = []
    for e in SVG.parse(str(svg_path)).elements():
        if isinstance(e, Circle):
            x0, y0, x1, y1 = e.bbox()
            out.append(((x0 + x1) / 2, (y0 + y1) / 2))
    return np.array(out, float).reshape(-1, 2)


@dataclass(frozen=True)
class Fit:
    coef_lon: np.ndarray
    coef_lat: np.ndarray
    residual_deg: float           # max(경도 잔차, 위도 잔차)
    residual_lon: float
    residual_lat: float


def _design(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])


def fit_graticule(lines: list[np.ndarray], lons: list[float], lats: list[float]) -> Fit:
    """눈금선 → 2차 다항 계수. 세로선 수 ≠ len(lons) 또는 가로선 수 ≠ len(lats) 면 오류(교차점이 모자라면 정합하지 않는다)."""
    vert = sorted([g for g in lines if abs(g[0, 0] - g[-1, 0]) < abs(g[0, 1] - g[-1, 1])], key=lambda g: g[:, 0].mean())
    hori = sorted([g for g in lines if abs(g[0, 0] - g[-1, 0]) >= abs(g[0, 1] - g[-1, 1])], key=lambda g: g[:, 1].mean())
    if len(vert) != len(lons) or len(hori) != len(lats):
        raise ValueError(f"SK-G1 눈금선 세로 {len(vert)}·가로 {len(hori)} — spec graticule 경도 {len(lons)}·위도 {len(lats)} 와 다르다"
                         f"(교차점 {len(vert) * len(hori)} / 필요 {len(lons) * len(lats)})")
    A, bl, bp = [], [], []
    for vi, v in enumerate(vert):
        for hi, h in enumerate(hori):
            d = np.linalg.norm(v[:, None, :] - h[None, :, :], axis=2)
            i, j = np.unravel_index(d.argmin(), d.shape)
            x, y = (v[i] + h[j]) / 2
            A.append([1, x, y, x * x, x * y, y * y])
            bl.append(lons[vi])
            bp.append(lats[hi])
    M = np.array(A)
    cl, *_ = np.linalg.lstsq(M, np.array(bl, float), rcond=None)
    cp, *_ = np.linalg.lstsq(M, np.array(bp, float), rcond=None)
    rl, rp = float(np.abs(M @ cl - bl).max()), float(np.abs(M @ cp - bp).max())
    return Fit(cl, cp, max(rl, rp), rl, rp)


def to_ll(P: np.ndarray, fit: Fit) -> np.ndarray:
    return coef_to_ll(P, fit.coef_lon, fit.coef_lat)


def coef_to_ll(P: np.ndarray, coef_lon: np.ndarray, coef_lat: np.ndarray) -> np.ndarray:
    """SVG 좌표 → 경위도(저장된 계수로 — fronts.json coef)."""
    A = _design(P[:, 0], P[:, 1])
    return np.column_stack([A @ np.asarray(coef_lon), A @ np.asarray(coef_lat)])


def georef(svg_path: Path, style_map: list[dict], graticule: dict) -> tuple[dict, Fit]:
    """스타일 표대로 선을 경위도로 옮긴 결과 {layers{층 → 편 → 조각[]}, rivers{편 → 조각[]}} 와 정합.
    style_map 항목 = {stroke, width, dash, layer, side}. layer == "river" 는 rivers 로."""
    groups = collect(svg_path)
    grid = groups.get((graticule["stroke"], round(graticule["width"], 2), graticule.get("dash", "")), [])
    fit = fit_graticule(grid, list(graticule["lons"]), list(graticule["lats"]))
    layers: dict = defaultdict(lambda: defaultdict(list))
    rivers: dict = defaultdict(list)
    for st in style_map:
        key = (st["stroke"], round(st["width"], 2), st.get("dash", ""))
        for P in groups.get(key, []):
            ll = np.round(to_ll(P, fit), ROUND).tolist()
            if st["layer"] == "river":
                rivers[st["side"]].append(ll)
            else:
                layers[st["layer"]][st["side"]].append(ll)
    return {"layers": {k: dict(v) for k, v in layers.items()}, "rivers": dict(rivers)}, fit

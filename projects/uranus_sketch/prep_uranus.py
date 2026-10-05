"""천왕성 작전 스케치 — 참고 작전도(SVG)의 전선·강을 경위도로 옮긴다.

    python projects/uranus_sketch/prep_uranus.py   → uranus.json

원본: ref_operation_uranus.svg = Wikimedia Commons "File:Operation Uranus.svg"(Lưu Ly, CC BY 3.0),
      러시아 국방부 victory.mil.ru 지도 023 을 다시 그린 것. 범례: 11.19 전선(굵은 이중선) · 11.23 전선(가는 이중선) · 11.30 전선(점선).
좌표 변환: 지도 안 경위도 눈금선(42·43·44°E × 48·49·50°N, 색 #c0edf2)의 교차점 9개로 2차 다항식을 최소제곱 적합.
전선은 원 지도를 그린 사람의 해석이며 축척 1:1,500,000 지도의 개략선이다 — 화면에 "개략" 표기.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from svgelements import SVG, Color, Shape

PROJ = Path(__file__).resolve().parent
SRC = PROJ / "ref_operation_uranus.svg"

# (색, 굵기, 점선) → 의미. 스타일 묶음을 그려 보고 범례와 대조해 정했다(스케치 확인 2026-10-05)
STYLE = {
    ("#100aea", 1.0, ""): ("1119", "axis"), ("#e80c2c", 1.0, ""): ("1119", "soviet"),
    ("#100aea", 0.5, ""): ("1123", "axis"), ("#e80c2c", 0.5, ""): ("1123", "soviet"),
    ("#100aea", 0.3, ""): ("1123", "axis"), ("#e80c2c", 0.3, ""): ("1123", "soviet"),
    ("#100aea", 0.3, "2, 1, 2, 1"): ("1130", "axis"), ("#e80c2c", 0.3, "2, 1, 2, 1"): ("1130", "soviet"),
    ("#100aea", 0.5, "2, 1, 2, 1"): ("1130", "axis"),
    ("#09bed1", 1.0, ""): ("river", "major"), ("#09bed1", 0.3, ""): ("river", "minor"),
}
GRID = ("#c0edf2", 0.2, "")


def collect() -> dict:
    groups: dict = defaultdict(list)
    for e in SVG.parse(str(SRC)).elements():
        if not isinstance(e, Shape) or e.stroke is None or e.stroke.value is None or Color(e.stroke).alpha == 0:
            continue
        try:
            L = e.length(error=1e-2)
        except Exception:  # noqa: BLE001 — 길이를 못 재는 장식 도형은 건너뛴다
            continue
        dash = e.values.get("stroke-dasharray", "none")
        key = (Color(e.stroke).hex, round(e.stroke_width or 0, 2), "" if dash == "none" else dash)
        n = max(2, int(L / 1.0))
        groups[key].append(np.array([(p.x, p.y) for p in (e.point(t) for t in np.linspace(0, 1, n))]))
    return groups


def fit(grid: list) -> tuple[np.ndarray, np.ndarray]:
    """눈금선 교차점 → (x, y) 2차 다항식 계수(경도·위도)."""
    vert = sorted([g for g in grid if abs(g[0, 0] - g[-1, 0]) < abs(g[0, 1] - g[-1, 1])], key=lambda g: g[:, 0].mean())
    hori = sorted([g for g in grid if abs(g[0, 0] - g[-1, 0]) >= abs(g[0, 1] - g[-1, 1])], key=lambda g: g[:, 1].mean())
    lons, lats = [42, 43, 44], [50, 49, 48]
    A, bl, bp = [], [], []
    for vi, v in enumerate(vert):
        for hi, h in enumerate(hori):
            # 두 선의 교차점(가장 가까운 점 쌍의 중점)
            d = np.linalg.norm(v[:, None, :] - h[None, :, :], axis=2)
            i, j = np.unravel_index(d.argmin(), d.shape)
            x, y = (v[i] + h[j]) / 2
            A.append([1, x, y, x * x, x * y, y * y])
            bl.append(lons[vi])
            bp.append(lats[hi])
    A = np.array(A)
    cl, *_ = np.linalg.lstsq(A, np.array(bl, float), rcond=None)
    cp, *_ = np.linalg.lstsq(A, np.array(bp, float), rcond=None)
    res = np.abs(A @ cl - bl).max(), np.abs(A @ cp - bp).max()
    print(f"눈금 적합 잔차(도): 경도 {res[0]:.4f} · 위도 {res[1]:.4f}")
    return cl, cp


def to_ll(P: np.ndarray, cl: np.ndarray, cp: np.ndarray) -> np.ndarray:
    x, y = P[:, 0], P[:, 1]
    A = np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])
    return np.column_stack([A @ cl, A @ cp])


def main() -> int:
    g = collect()
    cl, cp = fit(g[GRID])
    out: dict = {"schema_version": 1, "source": "Wikimedia Commons File:Operation Uranus.svg (Lưu Ly, CC BY 3.0) — "
                 "redrawn from victory.mil.ru map 023; georeferenced by 42–44°E × 48–50°N graticule",
                 "fronts": defaultdict(lambda: defaultdict(list)), "rivers": defaultdict(list)}
    for key, (what, side) in STYLE.items():
        for P in g.get(key, []):
            ll = np.round(to_ll(P, cl, cp), 4).tolist()
            if what == "river":
                out["rivers"][side].append(ll)
            else:
                out["fronts"][what][side].append(ll)
    for d, sides in out["fronts"].items():
        print(d, {s: len(v) for s, v in sides.items()})
    print("rivers", {k: len(v) for k, v in out["rivers"].items()})
    out["coef"] = {"lon": cl.tolist(), "lat": cp.tolist()}
    (PROJ / "uranus.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

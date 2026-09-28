"""자동 프레이밍 `frame_points(points, reserve)` (v3.3.0, docs/handoff/05 §2.1·§7-1, back_and_forth D-0056 작업 2).

장면에 나오는 장소(마커·뱃지·컷아웃·경로 꼭짓점)를 **모두 한 화면에** 넣는 최소 w 와 중심을 구한다.
- 각 장소는 화면에서 차지하는 상자(점 기준 위·아래·옆 px)를 가진다 — 뱃지는 머리·이름표까지(05 §2.1).
- 화면 안전 영역 = 가장자리 여백·위 여백(날짜 줄)·자막 영역 위. 예약 영역(카드·날짜 — RESERVED 와 같은 상자)에 걸리면 안 된다.
- 해상도 독립(05 §7-4): w 는 지도 단위. px 값은 480p 기준이고 출력 높이에 따라 k = H/480 로 늘린다.
  같은 입력이면 854×480 과 1280×720 에서 같은 (lon, lat, w) 가 나온다.
- 카메라 경계(티어 W)가 주어지면 View 와 같은 방식으로 클램프한 뒤 검사한다(클램프로 밀린 장소도 잡는다).
결정적이다. 제안만 한다 — 연출에 자동 적용하지 않는다(P8, D-0056 §1-5).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from engine.projection import lat_of, ym
from engine.style import H_OUT, W_OUT
from rules import load_rules

Box = tuple[float, float, float, float]
_R = load_rules()
FR = _R.camera.framing
_L = _R.layout_480p
BASE_H = _L.base.h


@dataclass(frozen=True)
class FramePoint:
    """장소 하나 — 경위도 + 480p 기준 화면 여유(px)."""

    lon: float
    lat: float
    up: float
    down: float
    side: float
    ref: str = ""


@dataclass
class FrameResult:
    lon: float
    lat: float
    w: float
    ok: bool                                   # 모든 장소가 안전 영역 안·예약 영역 밖
    boxes: dict[str, Box] = field(default_factory=dict)   # ref → 480p 화면 상자(검사·보고용)
    reason: str = ""


def marker_point(lon: float, lat: float, ref: str = "") -> FramePoint:
    m = FR.marker_px
    return FramePoint(lon, lat, m.up, m.down, m.side, ref)


def badge_point(lon: float, lat: float, r_px: float, ref: str = "") -> FramePoint:
    b = FR.badge_px
    return FramePoint(lon, lat, r_px * b.up_factor, b.down_px, r_px * b.side_factor, ref)


def plain_point(lon: float, lat: float, ref: str = "") -> FramePoint:
    p = FR.point_px
    return FramePoint(lon, lat, p.up, p.down, p.side, ref)


def default_reserve(width: float = W_OUT, height: float = H_OUT, card: bool = False) -> list[Box]:
    """예약 영역(480p 설계 좌표 → 출력 크기): 날짜 배지 + (그 장면에 카드가 뜨면) 우상단 카드 자리(08 §10,
    layout reserved_zones.card). 카드 자리는 카드가 떠 있을 때만 예약한다(RESERVED 와 같은 뜻, D-0033)."""
    k = height / BASE_H
    cz = _L.reserved_zones.card
    date = _R.hud.date_badge
    out: list[Box] = [(width - (date.x_right + date.size * 8) * k, 0, width, (date.underline_y + 2) * k)]
    if card:
        out.append((width - cz.x_from_right * k, cz.y[0] * k, width, cz.y[1] * k))
    return out


def _hit(a: Box, b: Box) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _clamp(lon: float, v: float, w: float, h: float, bounds: Optional[Box]) -> tuple[float, float, float]:
    """View 와 같은 클램프: bounds = (lon0, lat0, lon1, lat1) 티어 W."""
    if bounds is None:
        return lon - w / 2, v + h / 2, w
    lon0, lat0, lon1, lat1 = bounds
    vmin, vmax = ym(lat0), ym(lat1)
    u0 = min(max(lon - w / 2, lon0), lon1 - w)
    v1 = min(max(v + h / 2, vmin + h), vmax)
    return u0, v1, w


def place(points: list[FramePoint], lon: float, lat: float, w: float, *, width: float = W_OUT, height: float = H_OUT,
          reserve: Optional[list[Box]] = None, bounds: Optional[Box] = None) -> tuple[bool, dict[str, Box], str]:
    """이 카메라(lon, lat, w)에서 장소 상자들이 안전 영역 안·예약 영역 밖인가. 상자는 출력 px."""
    k = height / BASE_H
    h = w * height / width
    s = width / w
    u0, v1, _ = _clamp(lon, ym(lat), w, h, bounds)
    safe = (FR.margin_px * k, FR.top_px * k, width - FR.margin_px * k, _L.reserved_zones.subtitle.y_from * k - FR.margin_px * k)
    res = default_reserve(width, height) if reserve is None else reserve
    boxes: dict[str, Box] = {}
    for i, p in enumerate(points):
        x, y = (p.lon - u0) * s, (v1 - ym(p.lat)) * s
        b = (x - p.side * k, y - p.up * k, x + p.side * k, y + p.down * k)
        boxes[p.ref or f"p{i}"] = b
        if b[0] < safe[0] or b[1] < safe[1] or b[2] > safe[2] or b[3] > safe[3]:
            return False, boxes, f"{p.ref or i} 화면 밖(안전 영역)"
        if any(_hit(b, r) for r in res):
            return False, boxes, f"{p.ref or i} 예약 영역과 겹침"
    return True, boxes, ""


def frame_points(points: list[FramePoint], reserve: Optional[list[Box]] = None, *, width: float = W_OUT,
                 height: float = H_OUT, bounds: Optional[Box] = None, w_min: Optional[float] = None) -> FrameResult:
    """모든 장소가 보이는 최소 w 와 중심(05 §7-1). 후보 w 를 작은 것부터 로그 등간격으로 올리며, 각 w 에서
    가능한 중심 구간(모든 장소의 안전 영역 조건 교집합) 안 격자를 가운데부터 시험한다. 없으면 w_max 에서 ok=False."""
    if not points:
        raise ValueError("frame_points: 장소가 없다")
    k = height / BASE_H
    lo = max(FR.w_min, w_min or 0.0)
    ws = [math.exp(math.log(lo) + (math.log(FR.w_max) - math.log(lo)) * i / (FR.w_steps - 1)) for i in range(FR.w_steps)]
    safe_x0, safe_y0 = FR.margin_px * k, FR.top_px * k
    safe_x1, safe_y1 = width - FR.margin_px * k, _L.reserved_zones.subtitle.y_from * k - FR.margin_px * k
    last = ""
    for w in ws:
        s = width / w
        h = w * height / width
        # 중심 lon 구간: 각 점 x = (lon_p - (c - w/2)) * s 가 [safe_x0 + side, safe_x1 - side]
        cx_lo = max(p.lon + w / 2 - (safe_x1 - p.side * k) / s for p in points)
        cx_hi = min(p.lon + w / 2 - (safe_x0 + p.side * k) / s for p in points)
        # 중심 v 구간: y = (c_v + h/2 - v_p) * s 가 [safe_y0 + up, safe_y1 - down]
        cv_lo = max(ym(p.lat) - h / 2 + (safe_y0 + p.up * k) / s for p in points)
        cv_hi = min(ym(p.lat) - h / 2 + (safe_y1 - p.down * k) / s for p in points)
        if cx_lo > cx_hi or cv_lo > cv_hi:
            last = f"w {w:.1f}: 장소가 한 화면에 들어가지 않는다"
            continue
        n = FR.center_grid
        grid = sorted(((cx_lo + (cx_hi - cx_lo) * i / max(1, n - 1), cv_lo + (cv_hi - cv_lo) * j / max(1, n - 1))
                       for i in range(n) for j in range(n)),
                      key=lambda c: (abs(c[0] - (cx_lo + cx_hi) / 2) / max(1e-9, cx_hi - cx_lo + 1e-9)
                                     + abs(c[1] - (cv_lo + cv_hi) / 2) / max(1e-9, cv_hi - cv_lo + 1e-9), c))
        for cx, cv in grid:
            ok, boxes, why = place(points, cx, lat_of(cv), w, width=width, height=height, reserve=reserve, bounds=bounds)
            if ok:
                return FrameResult(round(cx, 4), round(lat_of(cv), 4), round(w, 4), True, _to480(boxes, k))
            last = f"w {w:.1f}: {why}"
    cx = sum(p.lon for p in points) / len(points)
    cv = sum(ym(p.lat) for p in points) / len(points)
    _, boxes, _ = place(points, cx, lat_of(cv), FR.w_max, width=width, height=height, reserve=reserve, bounds=bounds)
    return FrameResult(round(cx, 4), round(lat_of(cv), 4), FR.w_max, False, _to480(boxes, k), last)


def _to480(boxes: dict[str, Box], k: float) -> dict[str, Box]:
    return {r: tuple(round(v / k, 1) for v in b) for r, b in boxes.items()}  # type: ignore[misc]


__all__ = ["FramePoint", "FrameResult", "badge_point", "default_reserve", "frame_points", "marker_point", "place", "plain_point"]

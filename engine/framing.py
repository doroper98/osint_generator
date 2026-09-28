"""자동 프레이밍 `frame_points(points, reserve)` (v3.3.0, docs/handoff/05 §2.1·§7-1, back_and_forth D-0056 작업 2).

장면에 나오는 장소(마커·뱃지·컷아웃·경로 꼭짓점)를 **모두 한 화면에** 넣는 최소 w 와 중심을 구한다.
- 각 장소는 화면에서 차지하는 상자(점 기준 위·아래·옆 px)를 가진다 — 뱃지는 머리·이름표까지(05 §2.1).
- 화면 안전 영역 = 가장자리 여백·위 여백(날짜 줄)·자막 영역 위. 예약 영역(카드·날짜 — RESERVED 와 같은 상자)에 걸리면 안 된다.
- 해상도 독립(05 §7-4): w 는 월드 단위. px 값은 480p 기준이고 출력 높이에 따라 k = H/480 로 늘린다.
  같은 입력이면 854×480 과 1280×720 에서 같은 (x, y, w) 가 나온다.
- 카메라 경계(stage.bounds, 월드 사각형)가 주어지면 View 와 같은 방식으로 클램프한 뒤 검사한다(클램프로 밀린 장소도 잡는다).
- v4.1.0(D-0076 작업 3): 장소·중심·경계는 전부 **무대 월드 좌표**다. 앵커(경위도) 변환은 호출하는 쪽이 stage.to_world 로 한다.
결정적이다. 제안만 한다 — 연출에 자동 적용하지 않는다(P8, D-0056 §1-5).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from typing import Optional

from engine.style import H_OUT, W_OUT
from rules import load_rules

Box = tuple[float, float, float, float]
_R = load_rules()
FR = _R.camera.framing
_L = _R.layout_480p
BASE_H = _L.base.h
_EPS = sys.float_info.epsilon


@dataclass(frozen=True)
class FramePoint:
    """장소 하나 — 월드 좌표 + 점 기준 480p 화면 상자 여유(px): 왼쪽·위·오른쪽·아래. right/down 이 None 이면 대칭."""

    x: float
    y: float
    up: float
    down: float
    side: float
    ref: str = ""
    right: Optional[float] = None
    avoid_reserve: bool = True        # 경로 꼭짓점처럼 카드·자막 밑을 지나가도 되는 선의 점은 False(예약 영역은 뱃지·마커 몫, D-0033)

    @property
    def left(self) -> float:
        return self.side

    @property
    def rside(self) -> float:
        return self.side if self.right is None else self.right


def box_point(x: float, y: float, box: Box, ref: str = "") -> FramePoint:
    """렌더러 상자 함수(marker_box·badge_box 를 점 (0, 0) 에서 부른 값)로 만든 장소 — 비대칭 라벨까지 정확히."""
    bx0, by0, bx1, by1 = box
    return FramePoint(x, y, up=-by0, down=by1, side=-bx0, ref=ref, right=bx1)


@dataclass
class FrameResult:
    x: float                                   # 월드 중심(반올림 안 함 — 앵커 반올림은 호출 쪽, camera_suggest)
    y: float
    w: float
    ok: bool                                   # 모든 장소가 안전 영역 안·예약 영역 밖
    boxes: dict[str, Box] = field(default_factory=dict)   # ref → 480p 화면 상자(검사·보고용)
    reason: str = ""


def marker_point(x: float, y: float, ref: str = "") -> FramePoint:
    m = FR.marker_px
    return FramePoint(x, y, m.up, m.down, m.side, ref)


def badge_point(x: float, y: float, r_px: float, ref: str = "") -> FramePoint:
    b = FR.badge_px
    return FramePoint(x, y, r_px * b.up_factor, b.down_px, r_px * b.side_factor, ref)


def plain_point(x: float, y: float, ref: str = "", avoid_reserve: bool = True) -> FramePoint:
    p = FR.point_px
    return FramePoint(x, y, p.up, p.down, p.side, ref, avoid_reserve=avoid_reserve)


def default_reserve(width: float = W_OUT, height: float = H_OUT, card: bool = False) -> list[Box]:
    """예약 영역(480p 설계 좌표 → 출력 크기): 날짜 배지 + (그 장면에 카드가 뜨면) 우상단 카드 자리(08 §10,
    layout reserved_zones.card). 카드 자리는 카드가 떠 있을 때만 예약한다(RESERVED 와 같은 뜻, D-0033)."""
    k = height / BASE_H
    cz = _L.reserved_zones.card
    date = _R.hud.date_badge
    out: list[Box] = [(width - (date.x_right + date.size * FR.date_reserve_chars) * k, 0, width, (date.underline_y + 2) * k)]
    if card:
        out.append((width - cz.x_from_right * k, cz.y[0] * k, width, cz.y[1] * k))
    return out


def _hit(a: Box, b: Box) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _clamp(cx: float, cy: float, w: float, h: float, bounds: Optional[Box]) -> tuple[float, float, float]:
    """View 와 같은 클램프: bounds = 무대 월드 경계 (x0, y0, x1, y1)."""
    if bounds is None:
        return cx - w / 2, cy + h / 2, w
    bx0, by0, bx1, by1 = bounds
    x0 = min(max(cx - w / 2, bx0), bx1 - w)
    y1 = min(max(cy + h / 2, by0 + h), by1)
    return x0, y1, w


def place(points: list[FramePoint], cx: float, cy: float, w: float, *, width: float = W_OUT, height: float = H_OUT,
          reserve: Optional[list[Box]] = None, bounds: Optional[Box] = None,
          lenient: bool = False) -> tuple[bool, dict[str, Box], str]:
    """이 카메라(cx, cy, w — 월드 좌표)에서 장소 상자들이 안전 영역 안·예약 영역 밖인가. 상자는 출력 px.
    lenient=True 는 '화면 안(자막 위)'만 본다 — 현재 연출 평가용(렌더의 RESERVED 밀어내기가 카드 겹침을 따로 처리한다).
    lenient 에서 선의 점(avoid_reserve=False)은 자막 밑도 화면 안으로 본다(v3 경로는 자막 밑을 지나간다)."""
    k = height / BASE_H
    h = w * height / width
    s = width / w
    x0, y1, _ = _clamp(cx, cy, w, h, bounds)
    if lenient:
        safe = (0.0, 0.0, float(width), _L.reserved_zones.subtitle.y_from * k)
        res: list[Box] = []
    else:
        safe = (FR.margin_px * k, FR.top_px * k, width - FR.margin_px * k, _L.reserved_zones.subtitle.y_from * k - FR.margin_px * k)
        res = default_reserve(width, height) if reserve is None else reserve
    boxes: dict[str, Box] = {}
    for i, p in enumerate(points):
        x, y = (p.x - x0) * s, (y1 - p.y) * s
        b = (x - p.left * k, y - p.up * k, x + p.rside * k, y + p.down * k)
        boxes[p.ref or f"p{i}"] = b
        bottom = float(height) if lenient and not p.avoid_reserve else safe[3]
        if b[0] < safe[0] or b[1] < safe[1] or b[2] > safe[2] or b[3] > bottom:
            return False, boxes, f"{p.ref or i} 화면 밖(안전 영역)"
        if p.avoid_reserve and any(_hit(b, r) for r in res):
            return False, boxes, f"{p.ref or i} 예약 영역과 겹침"
    return True, boxes, ""


def frame_points(points: list[FramePoint], reserve: Optional[list[Box]] = None, *, width: float = W_OUT,
                 height: float = H_OUT, bounds: Optional[Box] = None, w_min: Optional[float] = None,
                 stage: object = None) -> FrameResult:
    """모든 장소가 보이는 최소 w 와 중심(05 §7-1). 후보 w 를 작은 것부터 로그 등간격으로 올리며, 각 w 에서
    가능한 중심 구간(모든 장소의 안전 영역 조건 교집합) 안 격자를 가운데부터 시험한다. 없으면 w_max 에서 ok=False.
    stage 를 주면 후보 중심을 앵커로 적었다가 다시 읽은 값(stage.to_world(**stage.from_world(c)))으로 시험한다 — 카메라는
    direction.yaml 에 앵커로 적히므로 그 값이 실제 카메라다(v3.3.0 의 lat_of → ym 왕복과 비트 단위로 같다, D-0076 작업 6)."""
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
        # 중심 x 구간: 각 점 화면 x = (x_p - (c - w/2)) * s 가 [safe_x0 + side, safe_x1 - side]
        cx_lo = max(p.x + w / 2 - (safe_x1 - p.rside * k) / s for p in points)
        cx_hi = min(p.x + w / 2 - (safe_x0 + p.left * k) / s for p in points)
        # 중심 y 구간: 화면 y = (c_y + h/2 - y_p) * s 가 [safe_y0 + up, safe_y1 - down]
        cv_lo = max(p.y - h / 2 + (safe_y0 + p.up * k) / s for p in points)
        cv_hi = min(p.y - h / 2 + (safe_y1 - p.down * k) / s for p in points)
        if cx_lo > cx_hi or cv_lo > cv_hi:
            last = f"w {w:.1f}: 장소가 한 화면에 들어가지 않는다"
            continue
        n = FR.center_grid
        grid = sorted(((cx_lo + (cx_hi - cx_lo) * i / max(1, n - 1), cv_lo + (cv_hi - cv_lo) * j / max(1, n - 1))
                       for i in range(n) for j in range(n)),
                      key=lambda c: (abs(c[0] - (cx_lo + cx_hi) / 2) / (cx_hi - cx_lo + _EPS)
                                     + abs(c[1] - (cv_lo + cv_hi) / 2) / (cv_hi - cv_lo + _EPS), c))
        for cx, cv in grid:
            ok, boxes, why = place(points, *_canon(stage, cx, cv), w, width=width, height=height, reserve=reserve, bounds=bounds)
            if ok:
                return FrameResult(cx, cv, round(w, 4), True, _to480(boxes, k))
            last = f"w {w:.1f}: {why}"
    cx = sum(p.x for p in points) / len(points)
    cv = sum(p.y for p in points) / len(points)
    _, boxes, _ = place(points, *_canon(stage, cx, cv), FR.w_max, width=width, height=height, reserve=reserve, bounds=bounds)
    return FrameResult(cx, cv, FR.w_max, False, _to480(boxes, k), last)


def _canon(stage: object, x: float, y: float) -> tuple[float, float]:
    return (x, y) if stage is None else stage.to_world(**stage.from_world(x, y))  # type: ignore[attr-defined]


def scale_class(w: float) -> Optional[str]:
    """카메라 w 가 속한 shot_grammar.w_guide 분류(05 §2.2 용도별 스케일). 구간 사이 값은 바로 아래 구간,
    가장 작은 하한보다 작으면 가장 작은 분류. w 가 양의 유한수가 아니면 None(분류 불명, D-0058 §2)."""
    if not (isinstance(w, (int, float)) and math.isfinite(w) and w > 0):
        return None
    lows = sorted(((v if isinstance(v, (int, float)) else v[0]), k) for k, v in _R.shot_grammar.w_guide.items())
    pick = lows[0][1]
    for lo, k in lows:
        if lo <= w:
            pick = k
    return pick


def context_floor(w: float) -> tuple[Optional[str], Optional[float]]:
    """(분류, 제안 w 하한 camera.framing.context_w_min[분류]) — 제안 엔진은 현재 스케일 분류 **틀 안**에서만 최적화한다."""
    k = scale_class(w)
    return k, (FR.context_w_min[k] if k is not None else None)


def _to480(boxes: dict[str, Box], k: float) -> dict[str, Box]:
    return {r: tuple(round(v / k, 1) for v in b) for r, b in boxes.items()}  # type: ignore[misc]


__all__ = ["FramePoint", "FrameResult", "badge_point", "box_point", "context_floor", "default_reserve", "frame_points", "marker_point",
           "place", "plain_point", "scale_class"]

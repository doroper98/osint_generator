"""스케치 공통 그리기 — 라벨·태그(예약 상자)·두 색 사선·점무늬·선(D-0140 §3).

수치는 `rules sketch.text`·`sketch.tag`·`sketch.eez` 만 읽는다(D130, test_sketch_no_literals). 색은 engine.style 토큰.
글자는 engine.typography.text·tw. 설계 px(480p) — 장치 배율은 렌더 진입의 ctx.scale 한 곳.
원본: 4d9dc65 `sketch_d1.py` label2·tag·hatch·crosshatch_dots·path_ll.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import cairo
import numpy as np

from engine.projection import View
from engine.stage import ym
from engine.style import W_OUT
from engine.typography import rrect, text, tw
from rules import load_rules

RGB = tuple[float, float, float]
Box = tuple[float, float, float, float]
WHITE: RGB = (1, 1, 1)

SK = load_rules().sketch


def world(ll: np.ndarray) -> np.ndarray:
    """경위도 배열(n×2) → 세계 좌표(경도, 메르카토르 y)."""
    ll = np.asarray(ll, dtype=float)
    return np.column_stack([ll[:, 0], [ym(v) for v in ll[:, 1]]])


def polyline(ctx: cairo.Context, pts: np.ndarray, close: bool = False) -> None:
    """화면 좌표 점들로 경로를 만든다(그리지는 않는다)."""
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def path_rings(ctx: cairo.Context, view: View, rings: Sequence[Sequence[Sequence[float]]]) -> None:
    """경위도 고리들 → 닫힌 경로(채우기 규칙은 호출자가 정한다)."""
    for ring in rings:
        polyline(ctx, view.to_screen_arr(world(np.array(ring))), close=True)


def hatch(ctx: cairo.Context, cols: Sequence[RGB], a: float, gap: float, wd: float) -> None:
    """현재 클립 안을 사선으로 채운다. 색이 둘 이상이면 번갈아 든다(중첩 주장 = 양쪽 색이 같은 무게, SK-H4)."""
    x0, y0, x1, y1 = ctx.clip_extents()
    h = y1 - y0
    s = x0 - h
    i = 0
    while s < x1:
        ctx.move_to(s, y1)
        ctx.line_to(s + h, y0)
        ctx.set_source_rgba(*cols[i % len(cols)], a)
        ctx.set_line_width(wd)
        ctx.stroke()
        s += gap
        i += 1


def dots(ctx: cairo.Context, col: RGB, a: float) -> None:
    """현재 클립 안 엇갈린 점무늬(공동 관리 수역). 간격·반지름 = rules sketch.eez.dots_*."""
    E = SK.eez
    x0, y0, x1, y1 = ctx.clip_extents()
    y, row = y0, 0
    while y < y1:
        x = x0 + (E.dots_gap / 2 if row % 2 else 0)
        while x < x1:
            ctx.arc(x, y, E.dots_r, 0, 2 * math.pi)
            ctx.new_sub_path()
            x += E.dots_gap
        y += E.dots_gap * E.dots_row
        row += 1
    ctx.set_source_rgba(*col, a)
    ctx.fill()


def _span(x: float, w: float, anchor: str) -> tuple[float, float]:
    return (x - w / 2, x + w / 2) if anchor == "c" else ((x - w, x) if anchor == "r" else (x, x + w))


class Overlay:
    """이번 프레임의 새 라벨·태그. 예약 상자(`reserved`)는 엔진 지명 라벨(MercatorStage.draw_labels)이 피하고,
    글자는 지명 라벨 뒤에 `flush()` 로 맨 위에 그린다. 프레임마다 새로 만든다(전역 상태 없음)."""

    def __init__(self, ctx: cairo.Context) -> None:
        self.ctx = ctx
        self.reserved: list[Box] = []
        self._deferred: list[Callable[[], None]] = []

    def defer(self, fn: Callable[[], None], box: Box | None = None) -> None:
        if box is not None:
            self.reserved.append(box)
        self._deferred.append(fn)

    def flush(self) -> None:
        for fn in self._deferred:
            fn()
        self._deferred.clear()

    def label2(self, x: float, y: float, a: float, main: str, sub: str | None = None, col: RGB = WHITE,
               sub_col: RGB = WHITE, anchor: str = "l") -> Box | None:
        """이름(굵게) + 부제 두 줄 라벨. 화면 밖으로 나가면 안쪽으로 민다. 예약 상자를 돌려준다."""
        T = SK.text
        L, Sb = T.label, T.label_sub
        ctx = self.ctx
        w = max(tw(ctx, main, L.size, L.font), tw(ctx, sub, Sb.size, Sb.font) if sub else 0)
        x0, x1 = _span(x, w, anchor)
        m = T.label_edge_margin
        shift = max(0.0, m - x0) - max(0.0, x1 - (W_OUT - m))
        x, x0, x1 = x + shift, x0 + shift, x1 + shift
        pad, up, down_sub, down = T.label_reserve_pad
        box = (x0 - pad, y - up, x1 + pad, y + (down_sub if sub else down))

        def draw() -> None:
            text(ctx, main, x, y, L.size, L.font, col, a, L.halo, anchor)
            if sub:
                text(ctx, sub, x, y + Sb.dy, Sb.size, Sb.font, sub_col, a, Sb.halo, anchor)
        self.defer(draw, box if a > SK.tag.reserve_min_alpha else None)
        return box

    def tag(self, s: str, x: float, y: float, col: RGB, a: float, anchor: str = "l") -> float:
        """작은 글자 태그(추정·개념 표시): 색 테두리 상자 + 글자. 폭을 돌려준다."""
        G = SK.tag
        ctx = self.ctx
        w = tw(ctx, s, G.size, G.font) + G.pad_w
        xx = x - w / 2 if anchor == "c" else (x - w if anchor == "r" else x)
        side, up, down = G.reserve
        box = (xx - side, y - up, xx + w + side, y + down)

        def draw() -> None:
            rrect(ctx, xx, y + G.box_dy, w, G.box_h, G.radius)
            ctx.set_source_rgba(*col, G.fill_alpha * a)
            ctx.fill_preserve()
            ctx.set_source_rgba(*col, G.edge_alpha * a)
            ctx.set_line_width(G.edge_w)
            ctx.stroke()
            text(ctx, s, xx + G.text_dx, y, G.size, G.font, col, a, G.halo, "l", role="tag")
        self.defer(draw, box if a > G.reserve_min_alpha else None)
        return w

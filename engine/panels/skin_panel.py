"""패널 안쪽의 디자인 시스템 판(v7.4.0 C0.0 3a, UF-906·UF-908) — skin 무대에서만 패널 모듈이 부른다.

흰 직각 카드(island.panel_box) 안: 왼쪽 정렬 sansb 제목 + 가는 선, 잉크 3단 글자(테두리 없음), 가는 선 줄·기둥 나눔, 작은 점 표식,
강조색 하나(rules skin.chart.accent_cols 의 색 이름만 강조, 나머지는 잉크). 수치 = rules skin.panel(코드 리터럴 0, 15 P3).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import cairo

from engine import skin
from engine.style import PANEL, SKIN, C, Color, hexc
from engine.typography import text, tw

P = SKIN.panel
WELL: Color = hexc(SKIN.surface.well)
BAR: Color = hexc(SKIN.surface.bar)
WHITE: Color = hexc(SKIN.surface.fill)


def is_accent(col_name: str | None) -> bool:
    """색 이름이 강조 계열인가(rules skin.chart.accent_cols — 한 화면 강조 하나)."""
    return col_name in SKIN.chart.accent_cols


def mark(col_name: str | None, base: Color = skin.INK2) -> Color:
    """도형 표식 색 — 강조 계열이면 강조(도형 톤), 아니면 base 잉크."""
    return skin.ACCENT_SHAPE if is_accent(col_name) else base


def ink(col_name: str | None, base: Color = skin.INK) -> Color:
    """글자 색 — 강조 계열이면 강조(글자 톤), 아니면 base 잉크."""
    return skin.ACCENT_INK if is_accent(col_name) else base


def side(col_name: str) -> Color:
    """의미색(두 입장·갈래) — 얇은 선·작은 점에만 쓴다(채운 상자 금지)."""
    return C[col_name]


def hline(ctx: cairo.Context, x0: float, x1: float, y: float, a: float, alpha: float | None = None, w: float | None = None) -> None:
    ctx.new_path()
    ctx.move_to(x0, y)
    ctx.line_to(x1, y)
    ctx.set_source_rgba(*skin.INK, (P.hair.alpha if alpha is None else alpha) * a)
    ctx.set_line_width(P.hair.w if w is None else w)
    ctx.stroke()


def vline(ctx: cairo.Context, x: float, y0: float, y1: float, a: float) -> None:
    ctx.new_path()
    ctx.move_to(x, y0)
    ctx.line_to(x, y1)
    ctx.set_source_rgba(*skin.INK, P.hair.alpha * a)
    ctx.set_line_width(P.hair.w)
    ctx.stroke()


def dot(ctx: cairo.Context, x: float, y: float, col: Color, a: float, r: float | None = None) -> None:
    ctx.new_path()
    ctx.arc(x, y, P.dot_r if r is None else r, 0, 2 * math.pi)
    ctx.set_source_rgba(*col, a)
    ctx.fill()


def stroke_path(ctx: cairo.Context, pts: Sequence[tuple[float, float]], col: Color, a: float, w: float,
                dash: Sequence[float] | None = None) -> None:
    """번짐 없는 잉크 선(glow_line 대신)."""
    if len(pts) < 2:
        return
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if dash:
        ctx.set_dash(list(dash))
    ctx.set_source_rgba(*col, a)
    ctx.set_line_width(w)
    ctx.stroke()
    ctx.set_dash([])


def meta(ctx: cairo.Context, s: str, x: float, y: float, a: float, anchor: str = "l", col: Color | None = None,
         size: float | None = None) -> float:
    """숫자·날짜(라틴) — mono 잉크 tertiary, 넓은 자간."""
    sz = P.meta.size if size is None else size
    return text(ctx, s, x, y, sz, P.meta.font, skin.INK3 if col is None else col, a, 0, anchor, spacing=P.meta.track * sz)


def label(ctx: cairo.Context, s: str, x: float, y: float, a: float, anchor: str = "l", col: Color | None = None,
          size: float | None = None) -> float:
    """한글 꼬리표 — sansm 잉크 secondary."""
    return text(ctx, s, x, y, P.label.size if size is None else size, P.label.font, skin.INK2 if col is None else col, a, 0, anchor)


def title(ctx: cairo.Context, a: float, s: str, sub: str | None = None) -> None:
    """제목(왼쪽 정렬 sansb 잉크 primary) + 부제(잉크 secondary) + 덩어리 아래 가는 선."""
    text(ctx, s, P.x0, PANEL.title_y, P.title.size, P.title.font, skin.INK, a, 0, "l")
    if sub:
        text(ctx, sub, P.x0, PANEL.subtitle_y, P.sub.size, P.sub.font, skin.INK2, a, 0, "l")
    hline(ctx, P.x0, P.x1, (PANEL.subtitle_y if sub else PANEL.title_y) + P.rule.dy, a, P.rule.alpha, P.rule.w)


def tag_box(ctx: cairo.Context, s: str) -> tuple[float, float, float, float]:
    """추정 태그 알약 상자(x0, y0, x1, y1) — 제목 줄 오른쪽 끝(x1)에 오른쪽 맞춤, 제목 글자 가운데 높이."""
    T = P.tag  # noqa: N806
    w = tw(ctx, s, T.size, T.font) + 2 * T.pad
    cy = PANEL.title_y - P.title.size * T.baseline_k
    return (P.x1 - w, cy - T.h / 2, P.x1, cy + T.h / 2)


def draw_tag(ctx: cairo.Context, s: str, a: float) -> None:
    T = P.tag  # noqa: N806
    x0, y0, x1, y1 = tag_box(ctx, s)
    skin.pill(ctx, (x0, y0, x1 - x0, y1 - y0), WELL, a)
    text(ctx, s, (x0 + x1) / 2, (y0 + y1) / 2 + T.size * T.baseline_k, T.size, T.font, skin.INK2, a, 0, "c")


def quote(ctx: cairo.Context, s: str, x: float, y: float, size: float, col: Color, a: float, anchor: str = "c") -> None:
    """발언 — 바탕 없는 잉크 글씨 + 흰 번짐(UF-907)."""
    Q = P.quote  # noqa: N806
    w = tw(ctx, s, size, Q.font)
    x0 = x - w / 2 if anchor == "c" else (x - w if anchor == "r" else x)
    skin.glow(ctx, lambda c: text(c, s, x, y, size, Q.font, col, a, 0, anchor), (x0, y - size, x0 + w, y + size / 3),
              blur=Q.glow_blur, alpha=Q.glow_alpha * a)

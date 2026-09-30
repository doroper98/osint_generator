"""패널 공통 — 덮개·제목·곡선 (v2.1.0, render3 `panel_title, edge_curve, draw_panel`)."""

from __future__ import annotations

from typing import Callable

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.style import PANEL, C, W_OUT
from engine.timebase import window
from engine.typography import text
from rules import load_rules

_TAG = load_rules().panels.prov_tag

PanelFn = Callable[[cairo.Context, RenderCtx, float, dict, float], None]


def panel_title(ctx: cairo.Context, a: float, s: str, sub: str | None = None) -> None:
    text(ctx, s, W_OUT / 2, PANEL.title_y, PANEL.title_size, "serifb", (1, 1, 1), a, 0, "c")
    if sub:
        text(ctx, sub, W_OUT / 2, PANEL.subtitle_y, PANEL.subtitle_size, "sansm", C["muted"], a, 0, "c")


def edge_curve(x0: float, y0: float, x1: float, y1: float, prog: float, n: int = 36) -> np.ndarray:
    cx = (x0 + x1) / 2
    pts = []
    for s in np.linspace(0, prog, n):
        pts.append(((1 - s) ** 3 * x0 + 3 * (1 - s) ** 2 * s * cx + 3 * (1 - s) * s * s * cx + s ** 3 * x1,
                    (1 - s) ** 3 * y0 + 3 * (1 - s) ** 2 * s * y0 + 3 * (1 - s) * s * s * y1 + s ** 3 * y1))
    return np.array(pts)


def panel_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], PANEL.fade_sec, PANEL.fade_sec)


def draw_panel_cover(ctx: cairo.Context, a: float) -> None:
    ctx.set_source_rgba(0.025, 0.03, 0.045, PANEL.cover_alpha * a)
    ctx.paint()


def make_panel_renderer(fn: PanelFn) -> Callable[[cairo.Context, RenderCtx, float, dict], None]:
    """덮개를 칠한 뒤 종류별 본문을 그린다 — v3 draw_panel 과 같은 순서."""

    def render(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
        a = panel_alpha(t, e)
        if a <= 0.01:
            return
        if getattr(getattr(R, "stage", None), "name", None) == "backdrop":   # v5.1.0 D-0126 Q4 A — backdrop 무대 위 패널 = 아일랜드 상자
            from engine.island import draw_frame  # noqa: PLC0415
            from engine.style import ISLAND  # noqa: PLC0415

            draw_frame(ctx, tuple(ISLAND.panel_box), a)
        else:
            draw_panel_cover(ctx, a)
        fn(ctx, R, t, e, a)

    render.__name__ = f"panel_{fn.__name__}"
    return render


def prov_tag_text(pv: dict | None) -> str | None:
    """08 §9 — verified + 출처 있음이면 None(태그 없음). v3 사실 패널처럼 provenance 가 없는 패널도 None."""
    if pv is None:
        return None
    if pv["verification"] == "verified" and pv["sources"]:
        return None
    return "추정" if pv["sources"] else "추정 · 출처 미기재"


def tag_row_y(e: dict) -> float:
    """태그 줄 기준선 — 제목(부제가 있으면 부제) 기준선 + y_offset_px (D-0034 anchor below_title)."""
    return (PANEL.subtitle_y if e.get("subtitle") else PANEL.title_y) + _TAG.y_offset_px


def body_shift(e: dict) -> float:
    """태그 줄(추정 태그)이 있는 패널만 본문을 내린다 — 모든 차트 같은 값(D-0034 §2)."""
    if prov_tag_text(e.get("provenance")) is None:
        return 0.0
    return _TAG.body_top_px_with_tag - _TAG.body_top_px


def tag_boxes(ctx: cairo.Context, e: dict) -> list[tuple[str, str, tuple[float, float, float, float]]]:
    """(문구, 색 이름, 상자) — 추정 태그 하나, 가운데 정렬. 사실 검증 라벨(provenance.claim_status)은 그리지 않는다
    (v4.5.0 D85, C9 — 기록만, 화면은 엔딩 카드 마지막 줄)."""
    from engine.typography import tw  # noqa: PLC0415

    T = _TAG  # noqa: N806
    s = prov_tag_text(e.get("provenance"))
    if s is None:
        return []
    w = tw(ctx, s, T.size, T.font) + T.pad_x
    x = W_OUT / 2 - w / 2
    y = tag_row_y(e)
    return [(s, T.color, (x, y + T.box_dy, x + w, y + T.box_dy + T.h))]


def prov_tag(ctx: cairo.Context, e: dict, a: float) -> str | None:
    """추정/출처 태그(v2 `prov_tag` 공통화, 08 §9). 위치는 제목 아래 가운데(D-0034). 검증 라벨은 그리지 않는다(v4.5.0 D85).
    그린 추정 태그 문구를 돌려준다(provenance panels.used[].prov_tag)."""
    from engine.typography import rrect  # noqa: PLC0415

    T = _TAG  # noqa: N806
    if a > 0.01:
        for s, cname, (x0, y0, x1, y1) in tag_boxes(ctx, e):
            col = C[cname]
            rrect(ctx, x0, y0, x1 - x0, y1 - y0, T.r)
            ctx.set_source_rgba(*col, T.alpha * a)
            ctx.set_line_width(T.border_px)
            ctx.stroke()
            text(ctx, s, (x0 + x1) / 2, y0 - T.box_dy, T.size, T.font, col, a, 0, "c")
    return prov_tag_text(e.get("provenance"))


def chart(body: PanelFn) -> PanelFn:
    """차트 패널 공통 머리 — 제목(중앙 상단) → 태그 줄 → 본문(태그 줄이 있으면 body_shift 만큼 아래로, D-0034 §2)."""

    def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
        panel_title(ctx, a, e["title"], e.get("subtitle"))
        prov_tag(ctx, e, a)
        ctx.save()
        ctx.translate(0, body_shift(e))
        body(ctx, R, t, e, a)
        ctx.restore()

    draw.__name__ = body.__name__
    return draw

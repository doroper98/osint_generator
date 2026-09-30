"""아일랜드 — backdrop 무대 위 내용물 상자 (v5.1.0, back_and_forth D-0123 §1·D-0126 Q1~Q4 A, 사용자 결정 D106·D108).

- 공통 상자: 둥근 모서리(radius)·반투명 바탕(stage_timeline.bg_rgb × fill_alpha)·흰 테두리(edge_alpha)·그림자.
  등장 = 슬라이드(layout_480p.card.slide_px) + 페이드(card.fade_sec) — 카드 규칙 재사용.
- 차트 아일랜드(island 이벤트 kind chart): 시간축 무대(TimelineStage)를 상자 안 뷰포트로 그린다(Q1 A). 카메라 = direction 의
  `stage: timeline` 숏(주 무대 backdrop 의 카메라는 `{}`). 레인 영역 = 상자 안 [pad_top, h − pad_bottom], 세로 척도 =
  min(lane_h, 영역 ÷ 레인 수)(Q2 A, `TimelineStage.fit_island`). 시간축 앵커 이벤트(series·date 핀)는 상자 안에서만 그린다.
- 겹침(checks island_overlap hard, Q3 A): 같은 순간 보이는 아일랜드 제자리 상자끼리 교차 > 0, 자막 구역 교차, 동시 수 > max_concurrent.
- backdrop 무대 위 패널은 덮개 대신 panel_box 아일랜드 상자(Q4 A). 수치는 전부 `rules island`(코드 리터럴 0).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Optional

import cairo

from engine.context import RenderCtx
from engine.projection import View
from engine.style import CARD, FPS, ISLAND, TIMELINE
from engine.timebase import ease_out, window
from engine.typography import rrect
from rules import load_rules

Box = tuple[float, float, float, float]   # x, y, 폭, 높이
SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from


def island_box(e: dict) -> Box:
    """차트 아일랜드 제자리 상자 — box(rules island.boxes 이름)."""
    return tuple(ISLAND.boxes[e.get("box") or "center"])  # type: ignore[return-value]


def island_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec)


def island_slide(t: float, e: dict) -> float:
    """등장 슬라이드 x 오프셋(카드와 같은 모양 — fade_sec 동안 slide_px → 0)."""
    return (1 - ease_out((t - e["t0"]) / CARD.fade_sec)) * CARD.slide_px


def draw_frame(ctx: cairo.Context, box: Box, a: float) -> None:
    """아일랜드 공통 상자 — 그림자·반투명 바탕·테두리."""
    x, y, w, h = box
    r = ISLAND.radius
    for d_, al in ISLAND.shadow:
        rrect(ctx, x - d_, y - d_ + d_ / 2, w + d_ * 2, h + d_ * 2, r + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()
    rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*TIMELINE.bg_rgb, ISLAND.fill_alpha * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, ISLAND.edge_alpha * a)
    ctx.set_line_width(ISLAND.edge_w)
    ctx.stroke()


def chart_view(chart: dict, t: float, box: Box) -> View:
    """차트 아일랜드 뷰 — 아일랜드 카메라(stage: timeline 숏)의 그 프레임, 뷰포트 = 상자 크기."""
    cams = chart["cams"]
    return View(chart["stage"], cams[min(len(cams) - 1, max(0, int(t * FPS)))], viewport=(box[2], box[3]))


def draw_island(ctx: cairo.Context, R: RenderCtx, view: Optional[View], t: float, e: dict) -> None:  # noqa: N803
    """island 이벤트 렌더러(무대 레이어 맨 앞). kind chart = 상자 + 시간축 뷰포트 + 시간축 앵커 이벤트."""
    a = island_alpha(t, e)
    if a <= 0.01:
        return
    x, y, w, h = island_box(e)
    x += island_slide(t, e)
    chart = R.cache["island_chart"]
    ctx.save()
    ctx.push_group()
    draw_frame(ctx, (x, y, w, h), 1.0)
    rrect(ctx, x, y, w, h, ISLAND.radius)
    ctx.clip()
    ctx.translate(x, y)
    v = chart_view(chart, t, (x, y, w, h))
    st = chart["stage"]
    st.render_base(ctx, v)
    zones = R.zones   # 카드 예약 영역을 상자 좌표로(마커 라벨 흐림 판정 — 화면 좌표 그대로면 어긋난다)
    R.zones = [replace(z, box=(z.box[0] - x, z.box[1] - y, z.box[2] - x, z.box[3] - y)) for z in zones]
    resolve: Callable[[Any], Any] = chart["resolve"]
    try:
        for typ in chart["order"]:
            for ce in chart["events"]:
                if ce["type"] == typ and ce["t0"] - 0.05 <= t <= ce["t1"] + 0.05:
                    resolve(ce).render(ctx, R, v, t, ce)
    finally:
        R.zones = zones
    st.draw_labels(ctx, v, [], 1.0)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ------------------------------------------------------------------ 겹침 검사(Q3 A)
def _panel_box() -> Box:
    return tuple(ISLAND.panel_box)  # type: ignore[return-value]


def island_boxes(events: list[dict], media_assets: dict, stage_name: str) -> list[tuple[str, float, float, Box]]:
    """아일랜드 목록 (이름, t0, t1, 제자리 상자). backdrop 무대 밖이면 [](지도·시간축 무대는 기존 규칙)."""
    if stage_name != "backdrop":
        return []
    from engine.media_plan import media_box  # noqa: PLC0415
    from engine.primitives import primitive_box  # noqa: PLC0415

    out: list[tuple[str, float, float, Box]] = []
    for e in events:
        typ = e["type"]
        if typ == "island":
            out.append((f"island {e['kind']} {e.get('box') or 'center'}", e["t0"], e["t1"], island_box(e)))
        elif typ in ("photo", "clip"):
            x0, y0, x1, y1 = media_box(e, media_assets)
            out.append((f"{typ} {e['mid']}", e["t0"], e["t1"], (x0, y0, x1 - x0, y1 - y0)))
        elif typ == "panel":
            out.append((f"panel {e['kind']}", e["t0"], e["t1"], _panel_box()))
        elif typ == "primitive":
            x0, y0, x1, y1 = primitive_box(e)
            out.append((f"primitive {e['id']}", e["t0"], e["t1"], (x0, y0, x1 - x0, y1 - y0)))
    return out


def _inter(a: Box, b: Box) -> float:
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def island_overlap(boxes: list[tuple[str, float, float, Box]]) -> list[str]:
    """`[island-overlap]` — 같은 순간 보이는 두 아일랜드 제자리 상자 교차 > 0, 자막 구역 교차, 동시 수 > max_concurrent."""
    out: list[str] = []
    for i, (na, a0, a1, ba) in enumerate(boxes):
        if ba[1] + ba[3] > SUB_Y:
            out.append(f"[island-overlap] {na} t={a0:.2f} 상자 아래 끝 {ba[1] + ba[3]:.0f} > 자막 구역 {SUB_Y:g}")
        for nb, b0, b1, bb in boxes[i + 1:]:
            if max(a0, b0) < min(a1, b1) and _inter(ba, bb) > 0:
                out.append(f"[island-overlap] {na} ↔ {nb} t={max(a0, b0):.2f}~{min(a1, b1):.2f} 교차 {_inter(ba, bb):.0f}px²")
    for t0 in sorted({b[1] for b in boxes}):
        n = sum(1 for _, a0, a1, _ in boxes if a0 <= t0 < a1)
        if n > ISLAND.max_concurrent:
            out.append(f"[island-overlap] t={t0:.2f} 동시 아일랜드 {n} > {ISLAND.max_concurrent}")
    return out


__all__ = ["chart_view", "draw_frame", "draw_island", "island_alpha", "island_box", "island_boxes", "island_overlap", "island_slide"]

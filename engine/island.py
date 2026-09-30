"""아일랜드 — backdrop 무대 위 내용물 상자 (v5.1.0, back_and_forth D-0123 §1·D-0126 Q1~Q4 A, 사용자 결정 D106·D108).

- 공통 상자: 둥근 모서리(radius)·반투명 바탕(stage_timeline.bg_rgb × fill_alpha)·흰 테두리(edge_alpha)·그림자.
  등장 = 슬라이드(layout_480p.card.slide_px) + 페이드(card.fade_sec) — 카드 규칙 재사용.
- 차트 아일랜드(island 이벤트 kind chart): 시간축 무대(TimelineStage)를 상자 안 뷰포트로 그린다(Q1 A). 카메라 = direction 의
  `stage: timeline` 숏(주 무대 backdrop 의 카메라는 `{}`). 레인 영역 = 상자 안 [pad_top, h − pad_bottom], 세로 척도 =
  min(lane_h, 영역 ÷ 레인 수)(Q2 A, `TimelineStage.fit_island`). 시간축 앵커 이벤트(series·date 핀)는 상자 안에서만 그린다.
- 겹침(checks island_overlap hard, Q3 A): 같은 순간 보이는 아일랜드 제자리 상자끼리 교차 > 0, 자막 구역 교차, 동시 수 > max_concurrent.
- backdrop 무대 위 패널은 덮개 대신 panel_box 아일랜드 상자(Q4 A). 수치는 전부 `rules island`(코드 리터럴 0).
- v5.2.0 D-0129 §B 주 아일랜드 상시(checks backdrop_main_missing hard): main_kinds 가 하나도 안 보이는 구간 > card_only_max_sec
  (타이틀·엔딩 카드·기사 구간 제외). §C 카드 ↔ 아일랜드 교차(checks card_island warning): 카드·게시물 카드 제자리 상자 ∩ 아일랜드 상자 > 0.
- v5.2.0 D-0133 §2·§3 마커 라벨(렌더러 `markers.island_label` 반전·클램프 뒤 글자 상자): 상자 밖 = checks island_label_clip hard
  `[island-label-clip]`, 같은 순간 같은 아일랜드의 시리즈 출처 줄 글자 상자와 교차 = island_label_overlap warning `[island-label-overlap]`.
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
    from engine.qa import event_name  # noqa: PLC0415 — 상세에 이벤트 이름(수정 워커가 지적 이벤트를 찾는 규칙, engine.qa.resolve_refs)

    out: list[tuple[str, float, float, Box]] = []
    for e in events:
        typ = e["type"]
        if typ == "island":
            out.append((f"island {e['kind']} {e.get('box') or 'center'}", e["t0"], e["t1"], island_box(e)))
        elif typ in ("photo", "clip"):
            x0, y0, x1, y1 = media_box(e, media_assets)
            out.append((f"{typ} {e['mid']}", e["t0"], e["t1"], (x0, y0, x1 - x0, y1 - y0)))
        elif typ == "panel":
            out.append((f"panel {e['kind']} {event_name(e)}".rstrip(), e["t0"], e["t1"], _panel_box()))
        elif typ == "primitive":
            x0, y0, x1, y1 = primitive_box(e)
            out.append((f"primitive {e['id']} {event_name(e)}".rstrip(), e["t0"], e["t1"], (x0, y0, x1 - x0, y1 - y0)))
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


# ------------------------------------------------------------------ 주 아일랜드 상시(v5.2.0 D-0129 §B)
def is_main(e: dict) -> bool:
    """주 아일랜드 이벤트인가 — island 이벤트는 kind(chart), 그 밖은 이벤트 type 이 rules island.main_kinds 안."""
    kinds = set(ISLAND.main_kinds)
    return (e.get("kind") in kinds) if e["type"] == "island" else e["type"] in kinds


def _merge(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def main_missing(events: list[dict], total: float, excluded: list[tuple[float, float]], stage_name: str) -> list[dict]:
    """backdrop 무대에서 주 아일랜드가 하나도 보이지 않는 구간 중 card_only_max_sec 초과 → [{t0, t1, sec}].
    excluded = 전면 카드(타이틀·엔딩) 구간. 기사 구간도 뺀다(화면 전체 조판). backdrop 무대가 아니거나 main_required 가 꺼지면 []."""
    if stage_name != "backdrop" or not ISLAND.main_required:
        return []
    cover = [(e["t0"], e["t1"]) for e in events if is_main(e) or e["type"] == "article"] + list(excluded)
    gaps: list[dict] = []
    t = 0.0
    for a, b in _merge([(max(0.0, a), min(total, b)) for a, b in cover if b > 0 and a < total]):
        if a - t > ISLAND.card_only_max_sec:
            gaps.append({"t0": round(t, 2), "t1": round(a, 2), "sec": round(a - t, 2)})
        t = max(t, b)
    if total - t > ISLAND.card_only_max_sec:
        gaps.append({"t0": round(t, 2), "t1": round(total, 2), "sec": round(total - t, 2)})
    return gaps


def main_missing_details(gaps: list[dict]) -> list[str]:
    return [f"[backdrop-main-missing] {g['t0']:.2f}-{g['t1']:.2f} {g['sec']:g}s — 주 아일랜드({'·'.join(ISLAND.main_kinds)}) 없음"
            f" > {ISLAND.card_only_max_sec:g}s(카드만 있는 구간 금지)" for g in gaps]


# ------------------------------------------------------------------ 카드 ↔ 아일랜드 교차(v5.2.0 D-0129 §C)
def card_overlap(events: list[dict], boxes: list[tuple[str, float, float, Box]]) -> list[dict]:
    """카드·게시물 카드 제자리 상자(engine.reserved.card_box)와 같은 순간 보이는 아일랜드 상자의 교차 > 0 → [{card, island, t0, t1, px2}]."""
    if not boxes:
        return []
    from engine.reserved import card_box  # noqa: PLC0415 — reserved → layers.article → style 순환 회피

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[dict] = []
    for e in events:
        if e["type"] not in ("card", "post") or (e["type"] == "post" and "post_box" not in e):
            continue
        x0, y0, x1, y1 = card_box(ctx, e)
        cb = (x0, y0, x1 - x0, y1 - y0)
        ref = f"post:{e['src']}" if e["type"] == "post" else f"card:{e.get('tag') or ''}"
        for name, a0, a1, ib in boxes:
            lo, hi = max(e["t0"], a0), min(e["t1"], a1)
            if lo < hi and _inter(cb, ib) > 0:
                out.append({"card": ref, "island": name, "t0": round(lo, 2), "t1": round(hi, 2), "px2": round(_inter(cb, ib))})
    return out


def card_overlap_details(rows: list[dict]) -> list[str]:
    return [f"[card-island] {r['card']} ↔ {r['island']} t={r['t0']:.2f}~{r['t1']:.2f} 교차 {r['px2']}px²" for r in rows]


# ------------------------------------------------------------------ 마커 라벨 ↔ 상자·출처 줄(v5.2.0 D-0133 §2·§3)
LABEL_STEP_FRAMES = 2   # 표본 간격(프레임) — 카메라가 움직이는 동안 라벨 자리가 바뀐다


def _source_rects(ctx: cairo.Context, chart: dict, v: View, t: float) -> list[tuple[str, Box]]:
    """같은 순간 차트 아일랜드의 시리즈 출처 줄 글자 상자(x0, y0, x1, y1) — layers.series._draw_source 와 같은 자리."""
    from engine.layers.series import source_line  # noqa: PLC0415
    from engine.typography import tw  # noqa: PLC0415

    L, S = TIMELINE.lane_label, TIMELINE.series  # noqa: N806
    st = chart["stage"]
    out: list[tuple[str, Box]] = []
    for e in chart["events"]:
        if e["type"] != "series" or not e["t0"] <= t <= e["t1"]:
            continue
        _, bot = st.lane_screen(v, st.lane_index(e["lane"]))
        by = bot - S.source_dy - S.source_step * e.get("slot", 0)
        s = source_line(e)
        out.append((e["lane"], (L.x, by - S.source_size, L.x + tw(ctx, s, S.source_size, S.source_font), by + S.source_size * 0.25)))
    return out


def label_check(events: list[dict], chart: dict) -> dict:
    """차트 아일랜드 안 마커 라벨을 표본 프레임마다 렌더와 같은 자리로 재어 → {label_clip: [...], label_overlap: [...], label_flip: n}.
    clip = 라벨이 보이는(알파 > 0.01) 순간 글자 상자가 아일랜드 상자에 걸치되 다 들어가지 않는다(반전·클램프 뒤). 마커마다 연속 구간 하나로 묶는다."""
    from engine.layers.markers import island_label_rect  # noqa: PLC0415
    from engine.timebase import smooth  # noqa: PLC0415

    isl = [e for e in events if e["type"] == "island"]
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    clips: list[dict] = []
    overlaps: list[dict] = []
    flips: set[str] = set()

    def add(rows: list[dict], key: dict, t: float, first: Optional[dict] = None) -> None:
        """같은 키의 연속 표본은 한 구간으로. first = 구간 첫 표본에서만 적는 값(글자 상자)."""
        if rows and all(rows[-1][k] == v_ for k, v_ in key.items()) and t - rows[-1]["t1"] <= LABEL_STEP_FRAMES / FPS + 0.011:
            rows[-1]["t1"] = round(t, 2)
        else:
            rows.append({**key, **(first or {}), "t0": round(t, 2), "t1": round(t, 2)})

    for e in chart["events"]:
        if e["type"] != "marker" or not e.get("label"):
            continue
        f0, f1 = int(e["t0"] * FPS), int(e["t1"] * FPS)
        for f in range(f0, f1 + 1, LABEL_STEP_FRAMES):
            t = f / FPS
            box_e = next((i for i in isl if i["t0"] <= t <= i["t1"]), None)
            la = window(t, e["t0"], e["t1"], 0.35, 0.5) * smooth((t - e["t0"] - 0.2) / 0.4)
            if box_e is None or la <= 0.01 or island_alpha(t, box_e) <= 0.01:
                continue
            bw, bh = island_box(box_e)[2:]
            v = chart_view(chart, t, island_box(box_e))
            x, y = v.to_screen(*e["world"])
            if x < -80 or x > v.vw + 80 or y < -40 or y > v.vh + 40:
                continue   # 렌더러도 그리지 않는다
            x0, y0, x1, y1, how = island_label_rect(ctx, e, x, y, bw)
            if how != "none":
                flips.add(e["label"])
            inside = x0 >= 0 and y0 >= 0 and x1 <= bw and y1 <= bh
            touches = x1 > 0 and y1 > 0 and x0 < bw and y0 < bh
            if touches and not inside:
                add(clips, {"label": e["label"], "island": box_e.get("box") or "center", "box": [round(bw), round(bh)]}, t,
                    {"rect": [round(x0), round(y0), round(x1), round(y1)]})
            for lane, (sx0, sy0, sx1, sy1) in _source_rects(ctx, chart, v, t):
                if min(x1, sx1) > max(x0, sx0) and min(y1, sy1) > max(y0, sy0):
                    add(overlaps, {"label": e["label"], "lane": lane}, t)
    return {"label_clip": clips, "label_overlap": overlaps, "label_flip": sorted(flips)}


def label_clip_details(rows: list[dict]) -> list[str]:
    return [f"[island-label-clip] marker {r['label']!r} t={r['t0']:.2f}~{r['t1']:.2f} 라벨 글자 상자 {r['rect']} 가 island chart {r['island']}"
            f" 상자 0~{r['box'][0]}×0~{r['box'][1]} 밖(반전·클램프 뒤)" for r in rows]


def label_overlap_details(rows: list[dict]) -> list[str]:
    return [f"[island-label-overlap] marker {r['label']!r} ↔ 레인 {r['lane']} 출처 줄 t={r['t0']:.2f}~{r['t1']:.2f}" for r in rows]


__all__ = ["card_overlap", "card_overlap_details", "chart_view", "draw_frame", "draw_island", "island_alpha", "island_box", "island_boxes", "island_overlap", "island_slide", "is_main", "label_check",
           "label_clip_details", "label_overlap_details", "main_missing", "main_missing_details"]

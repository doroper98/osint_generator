"""순위 가로 막대 층 — 구성 무대(structure) 안 `rank` 이벤트 렌더러 (v7.4.0, back_and_forth D-1003 §3).

층은 문장마다 하나(연출이 rank 이벤트 시작을 문장에 건다):
- bars  = 막대(0 에서 자람, 행마다 stagger) + 행 이름 + 행 끝 금액 + 머리 짧은 이름 + 0 기준선 + 출처 한 줄
- prior = 막대 위 속빈 세로 눈금(견줄 레코드, 같은 축척) + 첫 행 눈금 직접 태그("2026 본예산")
- delta = 행 끝 " · ±증감률"(증가 up · 감소 down 의미색) + 감소 행 막대 = 손실 A 면(UF-204)
- focus = 초점 행 하나만 accent 솔리드, 나머지 행 잉크 농도 × focus_dim
바닥 조판 정본(D-0328·D-0330): 막대 테두리 0, 바깥 끝 모서리만 stage_timeline.bars.top_radius, 범례 없음, 이중 축 없음.
글자는 화면 px 고정 크기(카메라가 확대해도 글자는 그대로, 막대·눈금 기하만 월드). 수치는 `rules stage_structure`.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

import cairo

from engine.style import C, STRUCTURE, TIMELINE
from engine.timebase import ease_out, smooth, window
from engine.typography import text, tw

if TYPE_CHECKING:
    from engine.context import RenderCtx
    from engine.projection import View
    from engine.stage_structure import Row, StructureStage

LAYERS: tuple[str, ...] = ("bars", "prior", "delta", "focus")
Rect = tuple[float, float, float, float]   # x0, y0, x1, y1(뷰포트 px)
DRAWN_TEXT: list[tuple[str, Rect]] = []    # 이 프레임에 그린 글자 상자(시험·겹침 검사 — 그리기 전에 비운다)


def _hbar(ctx: cairo.Context, xz: float, xe: float, y0: float, y1: float, r: float) -> None:
    """가로 막대 경로 — 0 쪽(xz)은 각, 바깥 끝(xe) 두 모서리만 반지름 r(D-0310 §1-2 를 가로로)."""
    w = xe - xz
    r = max(0.0, min(r, (y1 - y0) / 2, w))
    ctx.new_sub_path()
    ctx.move_to(xz, y0)
    ctx.line_to(xe - r, y0)
    ctx.arc(xe - r, y0 + r, r, -math.pi / 2, 0)
    ctx.arc(xe - r, y1 - r, r, 0, math.pi / 2)
    ctx.line_to(xz, y1)
    ctx.close_path()


def layer_alpha(events: list[dict], t: float, layer: str, row: Optional[str] = None) -> float:
    """그 순간 layer 층의 등장 정도(0~1). 같은 층 이벤트가 여럿이면 큰 값."""
    best = 0.0
    for e in events:
        if e["type"] != "rank" or e["layer"] != layer or (row is not None and e.get("row") != row):
            continue
        if layer == "bars":
            a = window(t, e["t0"], e["t1"], STRUCTURE.layer_in_sec, STRUCTURE.layer_in_sec)
        else:
            a = window(t, e["t0"], e["t1"], STRUCTURE.layer_in_sec, STRUCTURE.layer_in_sec) * smooth((t - e["t0"]) / STRUCTURE.layer_in_sec)
        best = max(best, a)
    return best


def _focus_row(events: list[dict], t: float) -> tuple[Optional[str], float]:
    best: tuple[Optional[str], float] = (None, 0.0)
    for e in events:
        if e["type"] == "rank" and e["layer"] == "focus":
            a = layer_alpha([e], t, "focus")
            if a > best[1]:
                best = (e["row"], a)
    return best


def _grow(t: float, e: dict, rank: int) -> float:
    return ease_out(max(0.0, min(1.0, (t - e["t0"] - rank * STRUCTURE.stagger_sec) / STRUCTURE.grow_sec)))


def _mix(a: tuple[float, float, float], b: tuple[float, float, float], k: float) -> tuple[float, float, float]:
    return tuple(x * (1 - k) + y * k for x, y in zip(a, b))  # type: ignore[return-value]


def fmt_amount(st: "StructureStage", v: float) -> str:
    return f"{v:,.{STRUCTURE.value_digits}f}{STRUCTURE.unit_suffix[st.record.unit]}"


def fmt_pct(p: float) -> str:
    return f"{p:+.{STRUCTURE.pct_digits}f}%"


def head_text(st: "StructureStage") -> str:
    return f"{st.stage_word(st.record)} {st.cfg.title} · {st.record.unit}"


def source_text(st: "StructureStage") -> str:
    recs = [st.record] + ([st.prior_record] if st.prior_record is not None else [])
    srcs = list(dict.fromkeys(r.source for r in recs))
    return " · ".join(srcs + [st.stage_word(r) for r in recs])


def _put(ctx: cairo.Context, name: str, s: str, x: float, y: float, size: float, font: str, col: tuple, a: float,
         anchor: str = "l") -> Rect:
    w = tw(ctx, s, size, font)
    x0 = x - w if anchor == "r" else x
    text(ctx, s, x0, y, size, font, col, a, STRUCTURE.label_halo, "l")
    m = TIMELINE.text_metrics
    r = (x0, y - size * m.ascent, x0 + w, y + size * (1 - m.ascent))
    if a > 0.01:
        DRAWN_TEXT.append((name, r))
    return r


def bar_rect(st: "StructureStage", view: "View", row: "Row", k: float = 1.0) -> Rect:
    """행의 막대 화면 상자(x0 = 0 기준선, x1 = 값 × k)."""
    yc = st.row_y(row.rank)
    half = st.bar_h / 2
    x0, y0 = view.to_screen(st.x_of(0.0), yc + half)
    x1, y1 = view.to_screen(st.x_of(row.value * k), yc - half)
    return x0, y0, x1, y1


def draw_rank(ctx: cairo.Context, R: "RenderCtx", view: "View", t: float, e: dict) -> None:  # noqa: N803
    """rank 이벤트 한 층. 다른 층의 상태(증감·초점)는 같은 무대 rank 이벤트 목록(R.cache island_structure)에서 읽는다."""
    st: "StructureStage" = view.stage  # type: ignore[assignment]
    evs = (R.cache.get("island_structure") or {}).get("events") or [e]
    {"bars": _draw_bars, "prior": _draw_prior, "delta": _draw_delta, "focus": _draw_focus}[e["layer"]](ctx, view, st, t, e, evs)


def _row_fill(st: "StructureStage", row: "Row", evs: list[dict], t: float) -> tuple[tuple[float, float, float], float]:
    S = STRUCTURE  # noqa: N806
    from engine.layers.series import bar_ink, loss_rgb  # noqa: PLC0415

    ink = bar_ink()
    alpha = S.ladder[min(row.rank, len(S.ladder) - 1)]
    col = ink
    if row.decreased:   # UF-204 A — 감소 행 = down 섞은 채도 낮은 면(증감 층이 뜨는 만큼)
        da = layer_alpha(evs, t, "delta")
        col, alpha = _mix(ink, loss_rgb(), da), alpha * (1 - da) + da
    fr, fa = _focus_row(evs, t)
    if fr is not None and fa > 0:
        if fr == row.id:
            col, alpha = _mix(col, C["gold"], fa), alpha * (1 - fa) + fa
        else:
            alpha *= 1 - fa * (1 - S.focus_dim)
    return col, alpha


def _draw_bars(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    S, B = STRUCTURE, TIMELINE.bars  # noqa: N806
    a = layer_alpha([e], t, "bars")
    if a <= 0.01:
        return
    txt = C["white"]
    zx, zy0 = view.to_screen(st.x_of(0.0), st.bh - st.row_top(0))
    _, zy1 = view.to_screen(st.x_of(0.0), st.bh - st.row_top(len(st.rows)))
    ctx.move_to(round(zx) + 0.5, zy0)
    ctx.line_to(round(zx) + 0.5, zy1)
    ctx.set_source_rgba(*txt, S.zero_alpha * a)
    ctx.set_line_width(S.zero_w)
    ctx.stroke()
    for row in st.rows:
        k = _grow(t, e, row.rank)
        if k <= 0:
            continue
        x0, y0, x1, y1 = bar_rect(st, view, row, k)
        col, al = _row_fill(st, row, evs, t)
        _hbar(ctx, x0, x1, y0, y1, B.top_radius)
        ctx.set_source_rgba(*col, al * a)
        ctx.fill()
        la = a * smooth(k)   # 이름은 막대가 자라면서 차오른다
        yb = (y0 + y1) / 2 + S.label_size * TIMELINE.text_metrics.mid_drop
        _put(ctx, f"label:{row.id}", row.label, zx - S.label_gap, yb, S.label_size, S.label_font, txt, la, "r")
        if k >= 1.0:
            _put(ctx, f"value:{row.id}", fmt_amount(st, row.value), value_x(st, view, row), yb, S.value_size, S.value_font,
                 txt if _focus_row(evs, t)[0] != row.id else C["gold"], a)


def value_x(st: "StructureStage", view: "View", row: "Row") -> float:
    """행 끝 라벨 x — 막대 끝과 눈금 오른쪽 끝 중 큰 쪽 + value_gap(눈금이 나중에 떠도 라벨이 움직이지 않는다)."""
    v = max(row.value, row.prior if row.prior is not None else row.value)
    x, _ = view.to_screen(st.x_of(v), 0.0)
    return x + (STRUCTURE.prior_w / 2 if row.prior is not None and row.prior >= row.value else 0.0) + STRUCTURE.value_gap


def _draw_prior(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    S = STRUCTURE  # noqa: N806
    a = layer_alpha([e], t, "prior")
    if a <= 0.01 or st.prior_record is None:
        return
    for row in st.rows:
        assert row.prior is not None
        yc = st.row_y(row.rank)
        cx, cy0 = view.to_screen(st.x_of(row.prior), yc + st.bar_h / 2)
        _, cy1 = view.to_screen(st.x_of(row.prior), yc - st.bar_h / 2)
        ctx.rectangle(cx - S.prior_w / 2, cy0 - S.prior_over, S.prior_w, cy1 - cy0 + S.prior_over * 2)
        ctx.set_source_rgba(*C["white"], S.prior_alpha * a)
        ctx.set_line_width(S.prior_line_w)
        ctx.stroke()
        if row.rank == 0:   # 직접 태그(범례 아님) — 첫 행 눈금 위
            tag = st.stage_word(st.prior_record)
            w = tw(ctx, tag, S.tag_size, S.tag_font)
            _put(ctx, "tag:prior", tag, cx - w / 2, cy0 - S.prior_over - S.tag_gap, S.tag_size, S.tag_font, C["muted"], a)


def _draw_delta(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    S = STRUCTURE  # noqa: N806
    a = layer_alpha([e], t, "delta")
    if a <= 0.01:
        return
    for row in st.rows:
        p = row.delta_pct
        if p is None:
            continue
        x0, y0, x1, y1 = bar_rect(st, view, row)
        yb = (y0 + y1) / 2 + S.label_size * TIMELINE.text_metrics.mid_drop
        x = value_x(st, view, row) + tw(ctx, fmt_amount(st, row.value), S.value_size, S.value_font)
        _put(ctx, f"delta:{row.id}", f" · {fmt_pct(p)}", x, yb, S.delta_size, S.delta_font, C["ru"] if p < 0 else C["green"], a)


def _draw_focus(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    """초점 층 자체는 그릴 것이 없다 — 막대 칠(_row_fill)·금액 색이 이 층의 등장 정도를 읽는다. 행 id 검사만."""
    if e["row"] not in st.by_id:
        raise ValueError(f"rank focus row {e['row']!r} 가 구성 무대 행에 없다")


def rows_band(view: "View") -> Rect:
    """행 띠(뷰포트 px) — 머리 줄 아래 ~ 출처 줄 위. 행은 이 안에만 그린다(확대해도 머리·출처와 겹침 0, D-1006)."""
    S, m = STRUCTURE, TIMELINE.text_metrics  # noqa: N806
    top = S.head_dy + S.head_size + S.head_size * (1 - m.ascent)
    bot = view.vh - S.source_dy - S.source_size * m.ascent
    return 0.0, top, view.vw, bot


def draw_structure(ctx: cairo.Context, R: "RenderCtx", view: "View", t: float, events: list[dict]) -> None:  # noqa: N803
    """구성 아일랜드 안 rank 층 전부 — 층 순서(LAYERS)대로. 행은 rows_band 안, 머리·출처 줄은 띠 밖(_draw_frame_text)."""
    DRAWN_TEXT.clear()
    bars = [ce for ce in events if ce["type"] == "rank" and ce["layer"] == "bars" and ce["t0"] - 0.05 <= t <= ce["t1"] + 0.05]
    x0, y0, x1, y1 = rows_band(view)
    ctx.save()
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.clip()
    for layer in LAYERS:
        for ce in events:
            if ce["type"] == "rank" and ce["layer"] == layer and ce["t0"] - 0.05 <= t <= ce["t1"] + 0.05:
                draw_rank(ctx, R, view, t, ce)
    ctx.restore()
    for ce in bars:
        _draw_frame_text(ctx, view, view.stage, t, ce)  # type: ignore[arg-type]


def _draw_frame_text(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict) -> None:
    """머리 짧은 이름·출처 한 줄 — 화면 고정(카메라와 무관), bars 층과 함께 등장."""
    S = STRUCTURE  # noqa: N806
    a = layer_alpha([e], t, "bars")
    if a <= 0.01:
        return
    _put(ctx, "head", head_text(st), 0.0, S.head_dy + S.head_size, S.head_size, S.head_font, C["muted"], a)
    _put(ctx, "source", source_text(st), 0.0, view.vh - S.source_dy, S.source_size, S.source_font, C["muted"], a)


def text_overlaps(rects: list[tuple[str, Rect]]) -> list[tuple[str, str]]:
    """글자 상자 교차 쌍(겹침 0 시험·검사)."""
    out = []
    for i, (na, a) in enumerate(rects):
        for nb, b in rects[i + 1:]:
            if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]):
                out.append((na, nb))
    return out


__all__ = ["DRAWN_TEXT", "LAYERS", "bar_rect", "draw_rank", "draw_structure", "fmt_amount", "fmt_pct", "head_text", "layer_alpha",
           "source_text", "text_overlaps", "value_x"]

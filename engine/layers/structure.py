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

LAYERS: tuple[str, ...] = ("bars", "prior", "delta", "focus", "total")
TOTAL_ROW = "total"   # D-1009 감독 판정 ② — focus 층 row: total = 총지출 줄을 초점 글자체로(문장 동안만), 행 초점과 같은 문법
Rect = tuple[float, float, float, float]   # x0, y0, x1, y1(뷰포트 px)
DRAWN_TEXT: list[tuple[str, Rect]] = []    # 이 프레임에 그린 글자 상자(시험·겹침 검사 — 그리기 전에 비운다)
DRAWN_STRINGS: list[tuple[str, str, float]] = []   # (이름, 문자열, 알파) — [spoken-number-visible] 이 읽는다(D-1008 §3)


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


def _grow(t: float, e: dict, rank: int) -> float:
    return ease_out(max(0.0, min(1.0, (t - e["t0"] - rank * STRUCTURE.stagger_sec) / STRUCTURE.grow_sec)))


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
        DRAWN_STRINGS.append((name, s, a))
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
    {"bars": _draw_bars, "prior": _draw_prior, "delta": _draw_delta, "focus": _draw_focus, "total": _draw_total}[e["layer"]](ctx, view, st, t, e, evs)


def focus_alpha(evs: list[dict], t: float, row_id: str) -> float:
    """그 행의 초점 등장 정도(그 행을 가리키는 focus 층 중 큰 값)."""
    return max((layer_alpha([e], t, "focus") for e in evs if e["type"] == "rank" and e["layer"] == "focus" and e["row"] == row_id),
               default=0.0)


def dim_of(evs: list[dict], t: float, row_id: str) -> float:
    """초점 아닌 행의 잉크 농도 배율 — 어느 행이든 초점이 뜨면 1 − fa × (1 − focus_dim). 초점 행은 1."""
    fa = max((layer_alpha([e], t, "focus") for e in evs if e["type"] == "rank" and e["layer"] == "focus" and e["row"] != row_id),
             default=0.0)
    return 1 - fa * (1 - STRUCTURE.focus_dim) if focus_alpha(evs, t, row_id) <= 0 else 1.0


def _seg(ctx: cairo.Context, st: "StructureStage", view: "View", row: "Row", v0: float, v1: float, rounded: bool) -> None:
    """같은 막대 위 구간 [v0, v1] 경로(막대 두께 그대로). rounded = 바깥 끝 모서리 둥글게(막대 끝과 같은 모양)."""
    yc = st.row_y(row.rank)
    x0, y0 = view.to_screen(st.x_of(v0), yc + st.bar_h / 2)
    x1, y1 = view.to_screen(st.x_of(v1), yc - st.bar_h / 2)
    if rounded:
        _hbar(ctx, x0, x1, y0, y1, TIMELINE.bars.top_radius)
    else:
        ctx.rectangle(x0, y0, x1 - x0, y1 - y0)


def _draw_bars(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    """막대(0 에서 자람) + 행 이름 + 행 끝 금액. 초점 행의 금액 라벨은 초점 라벨이 대신한다(1 − 초점 등장)."""
    from engine.layers.series import bar_ink  # noqa: PLC0415

    S, B = STRUCTURE, TIMELINE.bars  # noqa: N806
    a = layer_alpha([e], t, "bars")
    if a <= 0.01:
        return
    txt, ink = C["white"], bar_ink()
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
        _hbar(ctx, x0, x1, y0, y1, B.top_radius)
        ctx.set_source_rgba(*ink, S.ladder[min(row.rank, len(S.ladder) - 1)] * dim_of(evs, t, row.id) * a)
        ctx.fill()
        yb = (y0 + y1) / 2 + S.label_size * TIMELINE.text_metrics.mid_drop
        _put(ctx, f"label:{row.id}", row.label, zx - S.label_gap, yb, S.label_size, S.label_font, txt, a * smooth(k), "r")
        if k >= 1.0:
            _put(ctx, f"value:{row.id}", fmt_amount(st, row.value), value_x(st, view, row), yb, S.value_size, S.value_font, txt,
                 a * (1 - focus_alpha(evs, t, row.id)))


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
    """늘어난 구간(눈금 → 막대 끝)을 같은 막대 위에서 한 단계 밝게(D-1008 §1-3), 감소 구간(막대 끝 → 눈금) = 손실 A 면(UF-204),
    행 끝 " · ±증감률". 초점 행의 증감률 라벨은 초점 라벨이 대신한다."""
    from engine.layers.series import loss_rgb  # noqa: PLC0415

    S = STRUCTURE  # noqa: N806
    a = layer_alpha([e], t, "delta")
    if a <= 0.01:
        return
    for row in st.rows:
        p = row.delta_pct
        if p is None or row.prior is None:
            continue
        dim = dim_of(evs, t, row.id)
        if row.value >= row.prior:   # D-1009 — 늘어난 구간 = 의미색(up) 면(기본 구간과 휘도 차 ≥ 60 단계)
            _seg(ctx, st, view, row, row.prior, row.value, True)
            ctx.set_source_rgba(*C["green"], S.delta_seg_alpha * (dim if S.delta_seg_dim else 1.0) * a)
        else:
            _seg(ctx, st, view, row, row.value, row.prior, False)
            ctx.set_source_rgba(*loss_rgb(), dim * a)
        ctx.fill()
        x0, y0, x1, y1 = bar_rect(st, view, row)
        yb = (y0 + y1) / 2 + S.label_size * TIMELINE.text_metrics.mid_drop
        x = value_x(st, view, row) + tw(ctx, fmt_amount(st, row.value), S.value_size, S.value_font)
        _put(ctx, f"delta:{row.id}", f" · {fmt_pct(p)}", x, yb, S.delta_size, S.delta_font, C["ru"] if p < 0 else C["green"],
             a * (1 - focus_alpha(evs, t, row.id)))


def fmt_abs(st: "StructureStage", v: float) -> str:
    return f"{v:+,.{STRUCTURE.abs_digits}f}{STRUCTURE.unit_suffix[st.record.unit]}"


def focus_label(st: "StructureStage", row: "Row", metric: str, compare: "str | None" = None, note: "str | None" = None) -> tuple[str, str]:
    """초점 라벨 (큰 숫자, 작은 나머지) — metric amount = ("+27.6조", " · +22.8%"), rate = ("+29.7%", " · +9.4조").
    compare avg(D-1009) = 작은 줄이 예년 연평균 " · 2018~26 연평균 +8.7%"(기준이 다른 행이면 오류 — 보건·복지·고용·국방)."""
    ab, pc = row.delta_abs, row.delta_pct
    if ab is None or pc is None:
        raise ValueError(f"초점 행 {row.id}: 견줄 레코드(prior)가 없어 증감 라벨을 만들 수 없다")
    big = fmt_abs(st, ab) if metric == "amount" else fmt_pct(pc)
    if note is not None:   # 감독 지시(02:06Z) — 분야 안 사업 숫자(원고 문장 그대로)
        return big, f" · {note}"
    if compare == "avg":
        if row.avg_pct is None:
            raise ValueError(f"초점 행 {row.id}: 예년 연평균(avg_growth)이 없다 — 기준이 다른 행은 예년 비교를 하지 않는다")
        return big, f" · {st.avg_span()} {STRUCTURE.avg_word} {fmt_pct(row.avg_pct)}"
    return big, f" · {fmt_pct(pc) if metric == 'amount' else fmt_abs(st, ab)}"


def _draw_focus(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    """초점 행 하나(D-1008 §1-4·5): 0 → 눈금 구간 accent 옅게, 늘어난 구간 accent 솔리드, 행 끝 라벨 = 문장이 말하는 숫자를 크게."""
    S = STRUCTURE  # noqa: N806
    if e["row"] == TOTAL_ROW:   # 총지출 줄 초점은 _draw_total 이 그린다(머리 줄 자리, 행 띠 밖)
        if e["metric"] != "rate":
            raise ValueError("rank focus row total 은 metric rate 만(총지출 줄의 큰 숫자 = 증가율)")
        return
    if e["row"] not in st.by_id:
        raise ValueError(f"rank focus row {e['row']!r} 가 구성 무대 행에 없다")
    a = layer_alpha([e], t, "focus")
    if a <= 0.01:
        return
    row = st.by_id[e["row"]]
    acc = C["gold"]
    base = min(row.value, row.prior) if row.prior is not None else row.value
    _seg(ctx, st, view, row, 0.0, base, row.prior is None or row.prior >= row.value)
    ctx.set_source_rgba(*acc, S.focus_base_alpha * a)
    ctx.fill()
    if row.prior is not None and row.value > row.prior:
        _seg(ctx, st, view, row, row.prior, row.value, True)
        ctx.set_source_rgba(*acc, a)
        ctx.fill()
    big, rest = focus_label(st, row, e["metric"], e.get("compare"), e.get("note"))
    x0, y0, x1, y1 = bar_rect(st, view, row)
    yb = (y0 + y1) / 2 + S.focus_value_size * TIMELINE.text_metrics.mid_drop
    x = value_x(st, view, row)
    r = _put(ctx, f"focus:{row.id}", big, x, yb, S.focus_value_size, S.focus_value_font, acc, a)
    _put(ctx, f"focus_rest:{row.id}", rest, r[2], yb, S.focus_rest_size, S.focus_rest_font, acc, a)


def _draw_total(ctx: cairo.Context, view: "View", st: "StructureStage", t: float, e: dict, evs: list[dict]) -> None:
    """총지출 한 줄(D-1009 §1-1) — 머리 줄 오른쪽 끝에 "총지출 820.9조 · +12.8% · 2018~26 연평균 +6.8%"(화면 고정, 행 띠 밖)."""
    S = STRUCTURE  # noqa: N806
    a = layer_alpha([e], t, "total")
    if a <= 0.01:
        return
    tot, pct, avg = st.total_info()
    fa = focus_alpha(evs, t, TOTAL_ROW)   # 감독 판정 ②: 문장 동안 +12.8% = focus_value_size, 연평균 = focus_rest_size(accent), 금액은 그대로
    lerp = lambda u, v: u + (v - u) * fa  # noqa: E731
    mix = lambda c: tuple(lerp(p_, q_) for p_, q_ in zip(c, C["gold"]))  # noqa: E731
    parts = [(f"총지출 {fmt_amount(st, tot)}", S.head_size, S.head_font, C["white"]),
             (f" · {fmt_pct(pct)}", lerp(S.head_size, S.focus_value_size), S.focus_value_font if fa >= 0.5 else S.head_font, mix(C["green"]))]
    if avg is not None:
        parts.append((f" · {st.avg_span()} {S.avg_word} {fmt_pct(avg)}", lerp(S.head_size, S.focus_rest_size),
                      S.focus_rest_font if fa >= 0.5 else S.head_font, mix(C["muted"])))
    w = sum(tw(ctx, s_, sz, f) for s_, sz, f, _ in parts)
    x = view.vw - w
    for i, (s_, sz, f, col) in enumerate(parts):
        r = _put(ctx, f"total:{i}", s_, x, S.head_dy + S.head_size, sz, f, col, a)
        x = r[2]


def rows_band(view: "View") -> Rect:
    """행 띠(뷰포트 px) — 머리 줄 아래 ~ 출처 줄 위. 행은 이 안에만 그린다(확대해도 머리·출처와 겹침 0, D-1006)."""
    S, m = STRUCTURE, TIMELINE.text_metrics  # noqa: N806
    top = S.head_dy + S.head_size + S.head_size * (1 - m.ascent)
    bot = view.vh - S.source_dy - S.source_size * m.ascent
    return 0.0, top, view.vw, bot


def draw_structure(ctx: cairo.Context, R: "RenderCtx", view: "View", t: float, events: list[dict]) -> None:  # noqa: N803
    """구성 아일랜드 안 rank 층 전부 — 층 순서(LAYERS)대로. 행은 rows_band 안, 머리·출처 줄은 띠 밖(_draw_frame_text)."""
    DRAWN_TEXT.clear()
    DRAWN_STRINGS.clear()
    bars = [ce for ce in events if ce["type"] == "rank" and ce["layer"] == "bars" and ce["t0"] - 0.05 <= t <= ce["t1"] + 0.05]
    x0, y0, x1, y1 = rows_band(view)
    ctx.save()
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.clip()
    live = [ce for ce in events if ce["type"] == "rank" and ce["t0"] - 0.05 <= t <= ce["t1"] + 0.05]
    for layer in LAYERS:
        for ce in live:
            if ce["layer"] == layer and layer != "total":
                draw_rank(ctx, R, view, t, ce)
    ctx.restore()
    for ce in bars:
        _draw_frame_text(ctx, view, view.stage, t, ce)  # type: ignore[arg-type]
    for ce in live:   # 총지출 줄 = 머리 줄 오른쪽(행 띠 밖, D-1009)
        if ce["layer"] == "total":
            draw_rank(ctx, R, view, t, ce)


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

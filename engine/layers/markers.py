"""지점 마커 (v2.1.0, render3 `icon, draw_marker`). 차지한 영역은 R.reserved 에 올려 라벨이 피한다.

v5.2.0 back_and_forth D-0133 §1 — 차트 아일랜드 안 마커(`in_island`)만: 라벨 글자 상자가 상자 가장자리 − island.chart.label_flip_pad 를
넘으면 점 반대쪽에 붙이고(오른쪽 → 왼쪽), 그래도 넘치면 상자 안으로 클램프(`island_label`). 지도·시간축 무대 마커는 무변경(골든).
"""

from __future__ import annotations

import math

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.projection import View
from engine.style import C, ELEM, ISLAND, MOTION, SKIN, W_OUT, hexc, map_c, map_halo
from engine.timebase import ease_out, smooth, window
from engine.typography import text, tw
from rules import load_rules

MK = load_rules().layout_480p.marker   # v4.8.0 D-0101 §3 — 라벨·부제 글자(옛 리터럴 13·10.5)


def marker_label_alpha(box: tuple[float, float, float, float], zones: list) -> float:
    from engine.reserved import marker_label_alpha as f  # noqa: PLC0415 — 순환 회피

    return f(box, zones)


def icon(ctx: cairo.Context, kind: str, x: float, y: float, col: tuple, a: float) -> None:
    if kind == "boom":
        ctx.new_path()
        for k in range(10):
            ang = k * math.pi / 5 + 0.2
            r1, r2 = (9, 4) if k % 2 == 0 else (6, 3)
            ctx.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1)
            ctx.line_to(x + math.cos(ang + math.pi / 10) * r2, y + math.sin(ang + math.pi / 10) * r2)
        ctx.close_path()
        ctx.set_source_rgba(*C["amber"], a)
        ctx.fill()
    else:
        ctx.arc(x, y, 3.3, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6 * a)
        ctx.set_line_width(1)
        ctx.stroke()


_SIDE = {"right": (12, 4, "l"), "left": (-12, 4, "r"), "top": (0, -14, "c"), "bottom": (0, 22, "c")}


def marker_box(ctx: cairo.Context, e: dict, x: float, y: float, with_sub: bool = False) -> tuple[float, float, float, float]:
    """점·라벨이 차지하는 상자. 예약 영역(R.reserved)은 v3 그대로 라벨 폭만(골든 불변).
    with_sub=True 는 화면 밖 검사용 — 부제가 라벨보다 길면 그 폭까지(D-0049 쟁점 4)."""
    if map_skin(e):   # v7.4.0 4b-2 — skin 지도 마커: 점(번호 원)·알약 라벨이 그리는 자리 그대로
        return map_marker_box(ctx, e, x, y)
    side = e.get("side") or "right"
    anc = _SIDE[side][2]
    w = tw(ctx, e["label"], MK.label_size, "sansb") + 20
    if with_sub and e.get("sub"):
        w = max(w, tw(ctx, e["sub"], MK.sub_size, "sansm") + 20)
    if with_sub and anc == "c":   # v5.6.0 RENDER-AP-009 — 위·아래 라벨은 점 가운데 정렬로 그려진다(검사 상자도 그대로)
        dy = _SIDE[side][1]
        x0, x1 = _span(side, x, label_w(ctx, e), center_clamp(ctx, e, x))
        y0 = min(y - 16, y + dy - MK.label_size)
        y1 = max(y + 16, y + dy + (MK.sub_dy + MK.sub_size * 0.3 if e.get("sub") else MK.label_size * 0.3))
        return (min(x0 - 4, x - 14), y0, max(x1 + 4, x + 14), y1)
    return (x - 14 if anc != "r" else x - w, y - 16, x + w if anc != "r" else x + 14, y + 26)


_FLIP = {"right": "left", "left": "right"}


CENTER_PAD = 4.0   # v5.6.0 RENDER-AP-009 — 위·아래(가운데 정렬) 라벨이 화면 가장자리에서 잘리지 않게 안쪽으로 미는 여백(px)


def center_clamp(ctx: cairo.Context, e: dict, x: float) -> float:
    """위·아래 라벨(가운데 정렬)이 화면 밖으로 나가면 안쪽으로 미는 x 이동. 점은 사실 위치라 그대로, 글자만 민다(D-0033 원칙)."""
    side = e.get("side") or "right"
    if _SIDE[side][2] != "c":
        return 0.0
    x0, x1 = _span(side, x, label_w(ctx, e))
    if x0 < CENTER_PAD:
        return CENTER_PAD - x0
    if x1 > W_OUT - CENTER_PAD:
        return W_OUT - CENTER_PAD - x1
    return 0.0


def label_w(ctx: cairo.Context, e: dict) -> float:
    """라벨·부제 글자 폭(같은 기준점·같은 정렬로 그린다 — 넓은 쪽)."""
    w = tw(ctx, e["label"], MK.label_size, "sansb")
    return max(w, tw(ctx, e["sub"], MK.sub_size, "sansm")) if e.get("sub") else w


def _span(side: str, x: float, w: float, shift: float = 0.0) -> tuple[float, float]:
    dx, _, anc = _SIDE[side]
    x0 = x + dx + shift - (w if anc == "r" else w / 2 if anc == "c" else 0)
    return x0, x0 + w


def island_label(ctx: cairo.Context, e: dict, x: float, vw: float) -> tuple[str, float, str]:
    """아일랜드 마커 라벨 자리(D-0133 §1) → (side, x 이동, 처리 none|flip|clamp). vw = 상자 폭(뷰포트)."""
    pad = ISLAND.chart.label_flip_pad
    side = e.get("side") or "right"
    w = label_w(ctx, e)
    x0, x1 = _span(side, x, w)
    if x0 >= pad and x1 <= vw - pad:
        return side, 0.0, "none"
    how = "none"
    if side in _FLIP:
        f0, f1 = _span(_FLIP[side], x, w)
        if f0 >= pad and f1 <= vw - pad:
            return _FLIP[side], 0.0, "flip"
        if (x1 > vw - pad and side == "right") or (x0 < pad and side == "left"):
            side, x0, x1, how = _FLIP[side], f0, f1, "flip"
    lo, hi = pad, vw - pad - w
    shift = (max(lo, min(x0, hi)) if hi >= lo else lo) - x0   # 폭이 상자보다 넓으면 왼쪽 여백에 붙는다(넘친 오른쪽은 검사가 잡는다)
    return side, shift, "clamp" if abs(shift) > 1e-6 else how


def island_label_rect(ctx: cairo.Context, e: dict, x: float, y: float, vw: float) -> tuple[float, float, float, float, str]:
    """아일랜드 마커 라벨·부제 글자 상자(상자 좌표 x0, y0, x1, y1)와 처리 — checks island_label_clip·overlap 이 렌더와 같은 자리를 잰다."""
    side, shift, how = island_label(ctx, e, x, vw)
    x0, x1 = _span(side, x, label_w(ctx, e), shift)
    by = y + _SIDE[side][1]
    bot = by + MK.sub_dy + MK.sub_size * 0.25 if e.get("sub") else by + MK.label_size * 0.25
    return x0, by - MK.label_size, x1, bot, how


def marker_text_boxes(ctx: cairo.Context, e: dict, x: float, y: float) -> list[tuple[float, float, float, float]]:
    """라벨·부제 글자 줄 상자(그리기와 같은 기준점·정렬, 점·고리 제외) — v5.21.11 D-0192 경로 선 ↔ 마커 글자 교차 검사."""
    if map_skin(e):   # v7.4.0 4b-2 — skin 지도 마커: 글자 = 흰 알약 상자
        return [map_pill_rect(ctx, e, x, y)]
    side = e.get("side") or "right"
    dx, dy, anc = _SIDE[side]
    sx = x + dx + center_clamp(ctx, e, x)
    out = []
    for txt, size, font, oy in ((e.get("label"), MK.label_size, "sansb", 0.0), (e.get("sub"), MK.sub_size, "sansm", MK.sub_dy)):
        if not txt:
            continue
        w = tw(ctx, txt, size, font)
        x0 = sx - (w if anc == "r" else w / 2 if anc == "c" else 0)
        by = y + dy + oy
        out.append((x0, by - size * 0.86, x0 + w, by + size * 0.22))
    return out


def map_skin(e: dict) -> bool:
    """v7.4.0 4b-2 — skin 지도 마커인가: skin 켜짐 + 지도 앵커(lon·lat) + 아일랜드·값 핀 아님. 무대 없이 판정한다(상자 함수도 같은 답)."""
    return skin.active() and e.get("lat") is not None and not e.get("in_island") and e.get("pin_value") is None


def _pin_r(e: dict) -> float:
    """점(번호 원) 흰 고리 바깥 반지름."""
    M = SKIN.map_overlays.marker  # noqa: N806
    return M.num.r + M.num.ring_w if e.get("num") is not None else M.dot_r + M.ring_w


def map_pill_rect(ctx: cairo.Context, e: dict, x: float, y: float) -> tuple[float, float, float, float]:
    """skin 지도 마커 알약 라벨 상자 (x0, y0, x1, y1) — 이름(sansb) + 부제(같은 줄) + 좌우 pad. 자리 = side(점 고리 바깥 + gap),
    위·아래 알약은 점 가운데 정렬이고 화면 밖이면 안쪽으로 민다(점은 사실 위치라 그대로, D-0033)."""
    M = SKIN.map_overlays.marker  # noqa: N806
    w = tw(ctx, e["label"], M.name.size, M.name.font) + 2 * M.pill.pad_x
    if e.get("sub"):
        w += M.sub.gap + tw(ctx, e["sub"], M.sub.size, M.sub.font)
    h, d = M.pill.h, _pin_r(e) + M.gap
    side = e.get("side") or "right"
    if side == "right":
        x0, y0 = x + d, y - h / 2
    elif side == "left":
        x0, y0 = x - d - w, y - h / 2
    else:
        x0 = min(max(x - w / 2, CENTER_PAD), W_OUT - CENTER_PAD - w)
        y0 = y - d - h if side == "top" else y + d
    return (x0, y0, x0 + w, y0 + h)


def map_marker_box(ctx: cairo.Context, e: dict, x: float, y: float) -> tuple[float, float, float, float]:
    """skin 지도 마커 상자 = 알약 ∪ 점(번호 원)·맥동 고리 자리(종전 점 예약 ±14·16 과 큰 쪽)."""
    px0, py0, px1, py1 = map_pill_rect(ctx, e, x, y)
    r = _pin_r(e)
    rx, ry = max(r, 14.0), max(r, 16.0)
    return (min(px0, x - rx), min(py0, y - ry), max(px1, x + rx), max(py1, y + ry))


def _draw_map_marker(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, x: float, y: float, a: float) -> None:  # noqa: N803
    """v7.4.0 4b-2(UF-903·UF-906) — skin 지도 마커: 흰 고리 두른 점(강조 hl = accent.shape, 아니면 잉크 secondary, chip 그림자) 또는
    번호 원(accent.grad + 흰 고리 + 흰 display 숫자), 라벨 = 흰 알약(chip 그림자) 위 잉크 이름 + 잉크 secondary 부제. 테두리 글자 없음."""
    M = SKIN.map_overlays.marker  # noqa: N806
    lt = t - e["t0"]
    num = e.get("num")
    col = skin.ACCENT_SHAPE if (e.get("hl") or num is not None) else skin.INK2
    r = _pin_r(e)
    for k in range(2):
        f = ((lt * 0.5) + k / 2) % 1.0
        ctx.arc(x, y, r + M.pulse_span * ease_out(f), 0, 2 * math.pi)
        ctx.set_source_rgba(*col, M.pulse_alpha * (1 - f) * a)
        ctx.set_line_width(1.3)
        ctx.stroke()
    pa = a * ease_out(lt / MOTION["marker_icon_pop_sec"])
    if (e.get("icon") or "dot") == "boom":
        icon(ctx, "boom", x, y, col, pa)
    else:
        skin.soft_shadow(ctx, (x - r, y - r, 2 * r, 2 * r), r, getattr(SKIN.shadow, M.shadow), pa)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*skin.FILL, pa)
        ctx.fill()
        if num is None:
            ctx.arc(x, y, M.dot_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, pa)
            ctx.fill()
        else:
            N = M.num  # noqa: N806
            g0, g1 = (hexc(c) for c in SKIN.accent.grad)
            grad = cairo.LinearGradient(x, y - N.r, x, y + N.r)
            grad.add_color_stop_rgba(0, *g0, pa)
            grad.add_color_stop_rgba(1, *g1, pa)
            ctx.arc(x, y, N.r, 0, 2 * math.pi)
            ctx.set_source(grad)
            ctx.fill()
            text(ctx, str(num), x, y + N.size * N.baseline_k, N.size, N.font, skin.FILL, pa, 0, "c")
    la = a * smooth((lt - 0.2) / 0.4)
    box = map_marker_box(ctx, e, x, y)
    la *= marker_label_alpha(box, R.zones)   # 카드 뒤 라벨은 흐린다 — 점은 사실 위치라 그대로(D-0033)
    x0, y0, x1, y1 = map_pill_rect(ctx, e, x, y)
    if la > 0.01:
        skin.pill(ctx, (x0, y0, x1 - x0, y1 - y0), skin.FILL, la, M.pill.level)
        by = (y0 + y1) / 2
        tx = x0 + M.pill.pad_x
        tx += text(ctx, e["label"], tx, by + M.name.size * M.pill.baseline_k, M.name.size, M.name.font, skin.INK, la, 0, "l",
                   contrast="required")
        if e.get("sub"):
            text(ctx, e["sub"], tx + M.sub.gap, by + M.sub.size * M.pill.baseline_k, M.sub.size, M.sub.font, skin.INK2, la, 0, "l",
                 contrast="required")
    R.reserved.append(box)


def skin_marker(view: View, e: dict) -> bool:
    """v7.4.0 C0.0 3b — skin 무대의 아일랜드·스튜디오 마커인가(지도 마커 = 4단계, 종전 그리기)."""
    return skin.active() and (bool(e.get("in_island")) or e.get("pin_value") is not None
                              or getattr(view.stage, "name", None) in SKIN.stages)


def skin_pin(ctx: cairo.Context, x: float, y: float, lt: float, a: float, hl: bool, kind: str) -> None:
    """skin 핀 — 흰 고리 두른 점(강조 = accent.shape, 아니면 잉크 secondary). boom 아이콘은 종전 그대로."""
    M = SKIN.marker  # noqa: N806
    col = skin.ACCENT_SHAPE if hl else skin.INK2
    pa = a * ease_out(lt / MOTION["marker_icon_pop_sec"])
    if kind == "boom":
        icon(ctx, kind, x, y, col, pa)
        return
    ctx.arc(x, y, M.dot_r + M.ring_w, 0, 2 * math.pi)
    ctx.set_source_rgba(*skin.FILL, pa)
    ctx.fill()
    ctx.arc(x, y, M.dot_r, 0, 2 * math.pi)
    ctx.set_source_rgba(*col, pa)
    ctx.fill()


def skin_text(ctx: cairo.Context, lines: list[tuple[str, float, float, float, str, tuple]], anc: str, a: float) -> None:
    """skin 라벨 글자 — 잉크(테두리 없음) + 뒤 흰 번짐(skin.marker.glow). lines = (글자, x, 기준선 y, 크기, 글꼴, 색)."""
    G = SKIN.marker.glow  # noqa: N806
    xs = []
    for s_, x, y, size, font, _ in lines:
        w = tw(ctx, s_, size, font)
        x0 = x - (w if anc == "r" else w / 2 if anc == "c" else 0)
        xs.append((x0, y - size, x0 + w, y + size))
    rect = (min(b[0] for b in xs), min(b[1] for b in xs), max(b[2] for b in xs), max(b[3] for b in xs))

    def draw(c: cairo.Context) -> None:
        for s_, x, y, size, font, col in lines:
            text(c, s_, x, y, size, font, col, a, 0, anc, contrast="required")

    skin.glow(ctx, draw, rect, G.blur, G.gain, G.alpha * a)


def _draw_pin_label(ctx: cairo.Context, R: RenderCtx, view: View, lt: float, a: float, e: dict, x: float, y: float,  # noqa: N803
                    hk: dict) -> None:
    """값 레인 위 핀 라벨(D-0274 §1②, UF-143) — load_project 가 고른 단(pin_row)의 상자에 가운데 정렬, 점 → 상자 가장자리 리더선."""
    from engine.pin_labels import DOT_PX, pin_rect, plot_bounds  # noqa: PLC0415

    row = e.get("pin_row")
    if row is None:
        return
    S = load_rules().stage_timeline.series
    b = plot_bounds(ctx, view, view.stage, e["lane"], R.cache["series_range"][e["lane"]], e["pin_unit"])
    x0, y0, x1, y1 = pin_rect(ctx, e, x, y, row, b)
    la = a * smooth((lt - 0.2) / 0.4)
    edge = y1 if row > 0 else y0
    ctx.move_to(x, y - DOT_PX if row > 0 else y + DOT_PX)
    ctx.line_to(min(max(x, x0), x1), edge)
    ctx.set_source_rgba(*map_c(view.stage, "white"), S.pin_leader_alpha * la)
    ctx.set_line_width(S.pin_leader_w)
    ctx.stroke()
    cx = (x0 + x1) / 2
    by = y0 + MK.label_size
    if skin.active():   # v7.4.0 3b — 잉크 라벨 + 흰 번짐, 부제 잉크 secondary(강조색은 핀 점 하나)
        skin_text(ctx, [(e["label"], cx, by, MK.label_size, "sansb", skin.INK)]
                  + ([(e["sub"], cx, by + MK.sub_dy, MK.sub_size, "sansm", skin.INK2)] if e.get("sub") else []), "c", la)
        R.reserved.append((x0, y0, x1, y1))
        return
    text(ctx, e["label"], cx, by, MK.label_size, "sansb", map_c(view.stage, "white"), la, 3.2, "c", **hk, contrast="required")
    if e.get("sub"):
        text(ctx, e["sub"], cx, by + MK.sub_dy, MK.sub_size, "sansm", map_c(view.stage, "gold_text"), la, 3, "c", **hk, contrast="required")
    R.reserved.append((x0, y0, x1, y1))


def draw_marker(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], *ELEM["marker"])   # v7.4.0 UF-159 ×1.5
    if a <= 0.01:
        return
    x, y = view.to_screen(*e["world"])
    lt = t - e["t0"]
    ox, oy = getattr(view, "ox", 0.0), getattr(view, "oy", 0.0)   # v7.4.0 D-0257 — 시간축 틀 원점(지도·아일랜드 = 0)
    if x < ox - 80 or x > ox + view.vw + 80 or y < oy - 40 or y > oy + view.vh + 40:
        return
    if map_skin(e):   # v7.4.0 4b-2 — skin 지도 마커(점·번호 원 + 흰 알약 라벨)
        _draw_map_marker(ctx, R, t, e, x, y, a)
        return
    col = map_c(view.stage, "gold") if e.get("hl") else map_c(view.stage, "white")   # v5.18.0 D-0161 §3 — 지도 테마 보정
    if e.get("vline") and e.get("lane") is not None and hasattr(view.stage, "lane_screen"):   # v7.4.0 D-0309 §1-5 — 발표일 세로 점선
        top, bot = view.stage.lane_screen(view, view.stage.lane_index(e["lane"]))
        ctx.save()
        ctx.set_dash(list(MK.vline_dash))
        ctx.move_to(x, top)
        ctx.line_to(x, bot)
        ctx.set_source_rgba(*col, MK.vline_alpha * a)
        ctx.set_line_width(MK.vline_w)
        ctx.stroke()
        ctx.restore()
    halo = map_halo(view.stage)
    hk = {} if halo is None else {"halo_rgb": halo}
    sk = skin_marker(view, e)
    if sk:   # v7.4.0 3b — 퍼지는 고리 = 핀 색(강조 accent.shape · 아니면 잉크 secondary) × skin.marker.pulse_alpha
        col = skin.ACCENT_SHAPE if e.get("hl") else skin.INK2
    for k in range(2):
        f = ((lt * 0.5) + k / 2) % 1.0
        r = 4 + 20 * ease_out(f)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*col, (SKIN.marker.pulse_alpha if sk else 0.5) * (1 - f) * a)
        ctx.set_line_width(1.3)
        ctx.stroke()
    if sk:
        skin_pin(ctx, x, y, lt, a, bool(e.get("hl")), e.get("icon") or "dot")
    else:
        icon(ctx, e.get("icon") or "dot", x, y, col, a * ease_out(lt / MOTION["marker_icon_pop_sec"]))
    if e.get("pin_value") is not None:   # v7.4.0 D-0274 §1② — 값 레인 위 핀: 단 라벨 + 리더선(engine.pin_labels), 단 없으면 점만
        _draw_pin_label(ctx, R, view, lt, a, e, x, y, hk)
        return
    side, shift = e.get("side") or "right", 0.0
    if e.get("in_island"):   # v5.2.0 D-0133 §1 — 아일랜드 상자 밖으로 나가는 라벨은 반대쪽·클램프(상자 좌표, view.vw = 상자 폭)
        side, shift, _ = island_label(ctx, e, x, view.vw)
    else:
        shift = center_clamp(ctx, e, x)
    la = a * smooth((lt - 0.2) / 0.4)
    dx, dy, anc = _SIDE[side]
    box = marker_box(ctx, {**e, "side": side} if side != (e.get("side") or "right") else e, x + shift, y)
    la *= marker_label_alpha(box, R.zones)   # 카드 뒤 라벨은 흐린다 — 점은 사실 위치라 그대로(D-0033)
    if sk:   # v7.4.0 3b — 잉크 라벨(테두리 없음) + 흰 번짐, 부제 잉크 secondary
        skin_text(ctx, [(e["label"], x + dx + shift, y + dy, MK.label_size, "sansb", skin.INK)]
                  + ([(e["sub"], x + dx + shift, y + dy + MK.sub_dy, MK.sub_size, "sansm", skin.INK2)] if e.get("sub") else []), anc, la)
        R.reserved.append(box)
        return
    text(ctx, e["label"], x + dx + shift, y + dy, MK.label_size, "sansb", map_c(view.stage, "white"), la, 3.2, anc, **hk,
         contrast="required")
    if e.get("sub"):
        text(ctx, e["sub"], x + dx + shift, y + dy + MK.sub_dy, MK.sub_size, "sansm", map_c(view.stage, "gold_text"), la, 3, anc, **hk,
             contrast="required")
    R.reserved.append(box)

"""우상단 날짜 배지 — 모서리의 유일한 요소 (v2.1.0, render3 `draw_date`, 09 §4, C0 "모서리에는 날짜만")."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.style import C, DATE_BADGE, SKIN, W_OUT
from rules import load_rules
from engine.timebase import smooth
from engine.typography import ink_rgb, text, tw

if TYPE_CHECKING:
    from schemas.rules_models import SkinGlow

Box = tuple[float, float, float, float]
TRANSITION = load_rules().transition   # v7.4.0 D-0229 §2.2(UF-105)


def date_box() -> Box:
    """날짜 배지가 차지하는 화면 상자(x0, y0, x1, y1) — 가장 긴 날짜('YYYY. MM. DD')를 덮는 폭. 예약 영역 판정의 유일한 정의
    (미디어 배치 슬롯 후보·checks overlap 이 같이 쓴다, v3.6.0 NB23)."""
    B = DATE_BADGE  # noqa: N806
    return (W_OUT - B.x_right - B.size * 8, 0, W_OUT, B.underline_y + 2)


def draw_date(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    tb = R.tb
    sid = tb.cur_sentence(t)
    if sid is None or tb.in_fullcard(t):
        return
    d = tb.sent[sid].date
    prev = None
    t_ch = 0.0
    old: "str | None" = None   # v7.4.0 D-0229 §2.2 — bridge 문장에서 바뀐 날짜면 옛 날짜(교차 페이드)
    for s_ in tb.order:
        if tb.sent[s_].t0 - 0.3 > t:
            break
        if tb.sent[s_].date != prev:
            old = prev if getattr(tb.sent[s_], "role", None) == "bridge" else None
            prev = tb.sent[s_].date
            t_ch = tb.sent[s_].t0 - 0.3
    B = DATE_BADGE  # noqa: N806
    if old is not None and t - t_ch < TRANSITION.date_badge_xfade_sec:   # 시점 전환(UF-105) — 즉시 교체 대신 xfade, 옛 날짜는 제자리에서 사라진다
        x = smooth((t - t_ch) / TRANSITION.date_badge_xfade_sec)
        _date_text(ctx, old, 0.95 * (1 - x), B.y, SKIN.map_overlays.date_glow if _on_map(R) else None)
        k = 1.0
        a = 0.95 * x
    else:
        k = smooth((t - t_ch) / B.slide_sec)
        a = 0.95 * k
    g = SKIN.map_overlays.date_glow if _on_map(R) else None   # v7.4.0 4b-2 — 지도 위(지형·국기) 날짜 뒤 흰 번짐
    w = _date_text(ctx, d, a, B.y - (1 - k) * B.slide_px, g)
    if skin.active():   # 금색 밑줄 대신 글자 왼쪽 강조 점(밑줄 펼침 대신 함께 페이드)
        return
    ctx.set_source_rgba(*C["gold"], 0.9 * a)
    ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
    ctx.fill()


def _on_map(R: RenderCtx) -> bool:  # noqa: N803
    from engine.stage import skin_map  # noqa: PLC0415

    return skin_map(getattr(R, "stage", None))


def _date_text(ctx: cairo.Context, d: str, a: float, y: float, g: "SkinGlow | None" = None) -> float:
    """날짜 글자 — 종전: 흰 mono + 테두리. 디자인 시스템 무대(v7.4.0 C0.0·UF-906, D917): 작은 잉크 mono·자간·테두리 없음 + 왼쪽 강조 점(rules skin.date)."""
    B = DATE_BADGE  # noqa: N806
    txt = d.replace(".", ". ") if len(d) > 4 else d
    if not skin.active():
        return text(ctx, txt, W_OUT - B.x_right, y, B.size, B.font, (1, 1, 1), a, 3, "r")
    D = SKIN.date  # noqa: N806
    x_r = W_OUT - B.x_right
    out: list[float] = []

    def draw(c: cairo.Context) -> None:
        w_ = text(c, txt, x_r, y, D.size, B.font, ink_rgb(), a, 0, "r", spacing=D.track * D.size)
        out.append(w_)
        if a > 0.01:
            c.set_source_rgba(*skin.ACCENT_SHAPE, a)
            c.arc(x_r - w_ - D.dot_gap, y + D.dot_dy, D.dot_r, 0, math.tau)
            c.fill()

    if g is None or a <= 0.01:
        draw(ctx)
        return out[-1]
    # v7.4.0 4b-2 — skin 지도: 글자·점 뒤 흰 번짐(rules skin.map_overlays.date_glow). 상자 = 글자 폭(자간 포함) + 점
    w = tw(ctx, txt, D.size, B.font) + D.track * D.size * len(txt)
    skin.glow(ctx, draw, (x_r - w - D.dot_gap - D.dot_r, y - D.size, x_r, y + D.size / 3), g.blur, g.gain, g.alpha * a)
    return out[-1]

"""인물 발언 중앙 인용(quote) — v5.3.1 시안(사용자 제안 2026-10-02 — valdai-2026 한정, 마음에 들면 규약 승격).

사용자 제안 원문: "푸틴과 같은 인물이 이야기한 사항은 오른쪽 상단의 아일랜드 카드로 보여주기보다 지금 보여주는 인물 사진을 보여주면서
화면 중앙에 따옴표로 언급해 주면 좋지 않을까? 아래에 기사나 날짜 같은 건 작게 따옴표 글 하단에."

- 지도 위 균일 덮개(rules quote_center.scrim_* — 비네팅 아님, C0) → 가운데 초상(뱃지 렌더러 badge_at 재사용, 이름표 없음)
  → 세리프 인용문(여는·닫는 따옴표는 accent 색으로 코드가 그린다, 최대 quote_max_lines 줄) → 이름·직함 → 매체·날짜(가장 작게).
- 등장 = fade_sec 페이드 + rise_px 위로 떠오름. 줌 튐 없음.
- 글자가 quote_max_w·quote_max_lines 를 넘으면 렌더 전 오류(QuoteError — 자름·말줄임 없음, 15 P6). 수치는 전부 rules quote_center.
"""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, QUOTE as Q, W_OUT
from engine.timebase import ease_out, window
from engine.typography import text, tw, wrap


class QuoteError(ValueError):
    """인용문이 자리를 넘는다 — 조용히 자르지 않는다(15 P6). 연출이 문구를 줄인다."""


def quote_lines(ctx: cairo.Context, e: dict) -> list[str]:
    """인용문 줄(따옴표 자리 포함 폭으로 접는다). 넘치면 QuoteError."""
    room = Q.quote_max_w - 2 * tw(ctx, "“", Q.mark_size, "serifb")
    lines = wrap(ctx, e["text"], room, Q.quote_size, "serifb")
    if len(lines) > Q.quote_max_lines or any(tw(ctx, s, Q.quote_size, "serifb") > room for s in lines):
        raise QuoteError(f"[quote-overflow] {e['speaker']} {e['text']!r} — {len(lines)}줄 > {Q.quote_max_lines} 또는 폭 > {room:.0f}px, 문구를 줄인다")
    return lines


def quote_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], Q.fade_sec, Q.fade_sec)


def draw_quote(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    from engine.layers.badges import badge_at  # noqa: PLC0415 — badges → reserved 순환 회피

    a = quote_alpha(t, e)
    if a <= 0.01:
        return
    lines = quote_lines(ctx, e)
    ctx.save()
    ctx.rectangle(0, 0, W_OUT, 10_000)
    ctx.set_source_rgba(*Q.scrim_rgb, Q.scrim_alpha * a)
    ctx.fill()
    ctx.restore()
    dy = (1 - ease_out(min(1.0, (t - e["t0"]) / Q.fade_sec))) * Q.rise_px
    acc = C.get(e.get("accent") or "gold", C["gold"])
    cx = W_OUT / 2
    badge = dict(kind="person" if e.get("pid") else "flag", pid=e.get("pid"), flag=e["flag"], R=Q.portrait_R,
                 t0=e["t0"], label="", accent=e.get("accent") or "gold")
    badge_at(ctx, R, cx, Q.portrait_y + dy, badge, t, a)
    y = Q.quote_y + dy
    for k, s in enumerate(lines):
        yy = y + k * Q.quote_line_h
        text(ctx, s, cx, yy, Q.quote_size, "serifb", (1, 1, 1), a, 3, "c")
        w = tw(ctx, s, Q.quote_size, "serifb")
        if k == 0:
            text(ctx, "“", cx - w / 2 - 4, yy + Q.mark_size * 0.28, Q.mark_size, "serifb", acc, Q.mark_alpha * a, 0, "r")
        if k == len(lines) - 1:
            text(ctx, "”", cx + w / 2 + 4, yy + Q.mark_size * 0.28, Q.mark_size, "serifb", acc, Q.mark_alpha * a, 0, "l")
    yw = y + (len(lines) - 1) * Q.quote_line_h + Q.who_dy
    who = e["speaker"] + (f" · {e['role']}" if e.get("role") else "")
    text(ctx, who, cx, yw, Q.who_size, "sansb", (1, 1, 1), 0.92 * a, 2.6, "c")
    src = " · ".join(x for x in (e.get("src"), e.get("date")) if x)
    if src:
        text(ctx, src, cx, yw + Q.src_dy, Q.src_size, "mono", C["muted"], 0.9 * a, 2.4, "c")

"""사건 띠(chain) v2 "접히는 띠" — 지도 배경은 고정, 상단에 사건을 왼쪽부터 쌓되 지난 사건은 칩으로 접는다
(v5.2.0, 사용자 제안 2026-10-01, back_and_forth D-0135 — 시안).

- 지금 사건 = 펼친 카드(rules chain.card), 지난 사건 = 칩(rules chain.chip, 날짜 + 제목 한 줄). "쌓이되 작아진다".
- 새 사건이 오면(items[k].at) 직전 카드가 fold_sec 동안 칩으로 접히고(폭·높이·국기 원 smooth), 칩이 max_chips 를 넘으면
  가장 오래된 칩이 shift_sec 동안 왼쪽으로 밀려 흐려져 나간다. 새 카드는 접기·밀기가 끝난 뒤 아래에서 올라온다
  → 어느 순간에도 띠 폭 ≤ width_cap(checks chain 이 단언).
- 국기 원 = 얇은 시간 레일(rail_y) 위의 점, 카드·칩 좌상단 모서리(badge_at 재사용, 이름표 없음).
- 상자 = 아일랜드 공통 상자(engine.island.draw_frame — island.radius·fill_alpha·edge·shadow). 새 모양 없음.
- 패널 덮개 아래에 그린다(engine/render.py 순서). 뱃지 회피 영역 = 보이는 상자(engine.reserved.card_zones).
- 글자가 상자 폭을 넘으면 오류(`[chain-overflow]`, 말줄임표·자름 없음 — 15 P6). 수치는 전부 rules chain.
"""

from __future__ import annotations

from dataclasses import dataclass

import cairo

from engine.context import RenderCtx
from engine.style import C, CARD, CHAIN
from engine.timebase import ease_out, smooth, window
from engine.typography import rrect, text, tw

Box = tuple[float, float, float, float]
K, P = CHAIN.card, CHAIN.chip


class ChainError(ValueError):
    """사건 띠 글자가 상자 폭을 넘는다 — 조용히 자르지 않는다(15 P6). 연출이 문구를 줄인다."""


@dataclass(frozen=True)
class Slot:
    i: int          # item 번호
    x: float        # 상자 왼쪽(= 국기 원 중심 x)
    y: float        # 상자 위(= 레일 y + 등장 슬라이드)
    w: float
    h: float
    fold: float     # 0 = 펼친 카드, 1 = 칩
    a: float        # 등장·밀려남 알파
    appear: float   # 등장 시각(국기 팝인 기준)
    leaving: bool   # 왼쪽으로 밀려 나가는 중(칩 수에서 뺀다)


def check_text(ctx: cairo.Context, e: dict) -> list[str]:
    """글자 폭 검사 — 넘치는 줄마다 `[chain-overflow]` 한 줄(checks·렌더 공용). 카드와 칩 둘 다 본다."""
    out = []

    def fit(s: str, size: float, font: str, room: float, where: str) -> None:
        if s and tw(ctx, s, size, font) > room:
            out.append(f"[chain-overflow] {where} {s!r} 폭 {tw(ctx, s, size, font):.0f}px > {room:.0f}px — 문구를 줄인다")

    for it in e["items"]:
        fit(it["date"], K.date_size, "mono", K.w - CHAIN.flag_R - K.date_dx - K.pad_x, "카드 날짜")
        fit(it["title"], K.title_size, "sansb", K.w - K.pad_x * 2, "카드 제목")
        fit(it.get("line") or "", K.line_size, "sansm", K.w - K.pad_x * 2, "카드 부제")
        fit(it["date"], P.date_size, "mono", P.w - CHAIN.chip_flag_R - P.date_dx - P.pad_x, "칩 날짜")
        fit(it["title"], P.title_size, "sansb", P.w - P.pad_x * 2, "칩 제목")
    return out


def chain_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec)


def _appear(e: dict, k: int) -> float:
    """k 번째 사건 상자의 등장 시각 — 첫 사건은 at, 그 뒤는 직전 카드 접기·칩 밀기가 끝난 뒤."""
    at = e["items"][k]["at"]
    return at if k == 0 else at + max(CHAIN.fold_sec, CHAIN.shift_sec)


def layout(t: float, e: dict) -> list[Slot]:
    """보이는 상자들(왼쪽부터). 그리기·예약 영역·검사가 같이 쓴다."""
    items = e["items"]
    n = sum(1 for it in items if t >= it["at"])
    if n == 0:
        return []
    step_chip = P.w + CHAIN.gap
    off = sum(smooth((t - items[m]["at"]) / CHAIN.shift_sec) for m in range(CHAIN.max_chips + 1, n))
    out: list[Slot] = []
    x = CHAIN.x0 - off * step_chip
    for k in range(n):
        ap = _appear(e, k)
        if t < ap:
            break
        fold = smooth((t - items[k + 1]["at"]) / CHAIN.fold_sec) if k + 1 < n else 0.0
        w = K.w + (P.w - K.w) * fold
        h = K.h + (P.h - K.h) * fold
        gone = smooth(off - k) if off > k else 0.0
        a = smooth((t - ap) / CARD.fade_sec) * (1 - gone)
        y = CHAIN.rail_y + (1 - ease_out((t - ap) / CARD.fade_sec)) * CARD.slide_px / 2
        if a > 0.01:
            out.append(Slot(k, x, y, w, h, fold, a, ap, off > k))
        x += w + CHAIN.gap
    return out


def flag_r(s: Slot) -> float:
    return CHAIN.flag_R + (CHAIN.chip_flag_R - CHAIN.flag_R) * s.fold


def chain_boxes(t: float, e: dict) -> list[Box]:
    """보이는 상자의 제자리 상자(x0, y0, x1, y1) — 국기 원 포함. 뱃지 회피(engine.reserved)·검사용."""
    return [(s.x - flag_r(s), s.y - flag_r(s), s.x + s.w, s.y + s.h) for s in layout(t, e)]


def chain_width(t: float, e: dict) -> float:
    """띠 폭 = 보이는 상자 오른쪽 끝 − x0(밀려나는 칩은 x0 왼쪽이라 폭을 늘리지 않는다)."""
    sl = layout(t, e)
    return max((s.x + s.w for s in sl), default=CHAIN.x0) - CHAIN.x0


def chip_count(t: float, e: dict) -> int:
    """보이는 칩 수(접힘 절반 이상, 밀려 나가는 칩 제외)."""
    return sum(1 for s in layout(t, e) if s.fold >= 1 / 2 and not s.leaving)


def _flag(ctx: cairo.Context, R: RenderCtx, it: dict, s: Slot, t: float, a: float) -> None:  # noqa: N803
    """레일 위 국기 원(상자 좌상단 모서리) — 뱃지 그리기(badge_at)를 그대로 쓴다. 이름표 없음."""
    from engine.layers.badges import badge_at  # noqa: PLC0415 — badges → reserved → chain 순환 회피

    badge_at(ctx, R, s.x, s.y, dict(kind="flag", flag=it["flag"], R=flag_r(s), t0=s.appear, label="", accent=it.get("accent") or "gold"),
             t, a)


def draw_chain(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    from engine.island import draw_frame  # noqa: PLC0415 — island → style 순환 회피

    ea = chain_alpha(t, e)
    if ea <= 0.01:
        return
    bad = check_text(ctx, e)
    if bad:
        raise ChainError("\n".join(bad))
    sl = layout(t, e)
    if not sl:
        return
    # 레일 — 왼쪽 끝 ~ 마지막 국기 원
    ctx.move_to(CHAIN.x0, CHAIN.rail_y)
    ctx.line_to(sl[-1].x, CHAIN.rail_y)
    ctx.set_source_rgba(*C["muted"], CHAIN.rail_alpha * ea)
    ctx.set_line_width(CHAIN.rail_w)
    ctx.stroke()
    for s in sl:
        it = e["items"][s.i]
        a = ea * s.a
        acc = C[it.get("accent") or "gold"]
        draw_frame(ctx, (s.x, s.y, s.w, s.h), a)
        ca = a * (1 - smooth(s.fold * 2))                 # 카드 글자는 접기 앞 절반에 사라지고
        pa = a * smooth(s.fold * 2 - 1) * CHAIN.past_alpha   # 칩 글자는 뒤 절반에 나타난다
        if ca > 0.01:
            rrect(ctx, s.x + K.pad_x, s.y, s.w - K.pad_x * 2, K.accent_w, K.accent_w / 2)
            ctx.set_source_rgba(*acc, ca)
            ctx.fill()
            text(ctx, it["date"], s.x + flag_r(s) + K.date_dx, s.y + K.date_dy, K.date_size, "mono", acc, ca, 0, "l")
            text(ctx, it["title"], s.x + K.pad_x, s.y + K.title_dy, K.title_size, "sansb", (1, 1, 1), ca, 0, "l")
            if it.get("line"):
                text(ctx, it["line"], s.x + K.pad_x, s.y + K.line_dy, K.line_size, "sansm", C["muted"], ca, 0, "l")
        if pa > 0.01:
            text(ctx, it["date"], s.x + flag_r(s) + P.date_dx, s.y + P.date_dy, P.date_size, "mono", acc, pa, 0, "l")
            text(ctx, it["title"], s.x + P.pad_x, s.y + P.title_dy, P.title_size, "sansb", (1, 1, 1), pa, 0, "l")
        _flag(ctx, R, it, s, t, a * (1 - (1 - CHAIN.past_alpha) * s.fold))

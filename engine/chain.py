"""사건 띠(chain) — 지도 배경은 고정, 상단 가로줄에 사건 카드를 왼쪽부터 하나씩 더한다 (v5.2.0, 사용자 제안 2026-10-01, 시안).

- 카드 i 는 items[i].at 에 아래에서 살짝 올라오며(card.slide_px 재사용) 나타나 이벤트 끝까지 남는다.
- 지금 사건(가장 최근 카드) = 불투명·accent 윗선, 지난 사건 = rules chain.past_alpha. 강조는 다음 카드 등장과 함께 넘어간다.
- 카드 좌상단에 국기 원(rules chain.flag_R, 국기 레지스트리 flag11 — 뱃지와 같은 래스터).
- 보이는 카드가 max_visible 을 넘으면 shift_sec 동안 줄 전체를 왼쪽으로 밀고 가장 오래된 카드는 흐려져 나간다.
- 패널 덮개 아래·카드 층 아래에 그린다(engine/render.py 순서). 뱃지 회피 영역 = 보이는 카드 상자(engine.reserved.card_zones).
수치는 전부 rules chain(코드 리터럴 0 — 모서리 반경·윗선 두께는 카드 규칙과 같은 값).
"""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.style import C, CARD, CHAIN
from engine.timebase import ease_out, smooth, window
from engine.typography import rrect, text, tw

Box = tuple[float, float, float, float]


class ChainError(ValueError):
    """사건 띠 글자가 카드 폭을 넘는다 — 조용히 자르지 않는다(15 P6). 문구를 줄인다."""


def check_text(ctx: cairo.Context, e: dict) -> list[str]:
    """글자 폭 검사 — 넘치는 줄마다 `[chain-overflow]` 한 줄(checks·렌더 전 공용)."""
    room = CHAIN.w - 20
    out = []
    for it in e["items"]:
        for s, size, font in ((it["title"], CHAIN.title_size, "sansb"), (it.get("line") or "", CHAIN.line_size, "sansm"),
                              (it["date"], CHAIN.date_size, "mono")):
            lim = room - (CHAIN.flag_R + 8 if s == it["date"] else 0)
            if s and tw(ctx, s, size, font) > lim:
                out.append(f"[chain-overflow] {s!r} 폭 {tw(ctx, s, size, font):.0f}px > {lim:.0f}px — 문구를 줄인다")
    return out


def chain_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec)


def _shown(t: float, e: dict) -> list[int]:
    return [i for i, it in enumerate(e["items"]) if t >= it["at"]]


def slots(t: float, e: dict) -> list[tuple[int, float, float, float]]:
    """보이는 카드마다 (item 번호, x, y, 알파 배율) — 제자리 기준(슬라이드 포함). 그리기와 예약 영역이 같이 쓴다."""
    shown = _shown(t, e)
    if not shown:
        return []
    items = e["items"]
    step = CHAIN.w + CHAIN.gap
    # 밀기: n 번째 카드가 나타나는 순간부터 shift_sec 동안 (n - max_visible) 칸까지 왼쪽으로
    off = 0.0
    for n in range(CHAIN.max_visible, len(shown)):
        off += smooth((t - items[shown[n]]["at"]) / CHAIN.shift_sec)
    out = []
    for k, i in enumerate(shown):
        x = CHAIN.x0 + (k - off) * step
        f = ease_out((t - items[i]["at"]) / 0.55)
        y = CHAIN.y + (1 - f) * CARD.slide_px * 0.5
        gone = smooth(off - k) if off > k else 0.0          # 왼쪽으로 밀려나는 카드는 흐려져 나간다
        a = smooth((t - items[i]["at"]) / CARD.fade_sec) * (1 - gone)
        if a > 0.01:
            out.append((i, x, y, a))
    return out


def chain_boxes(t: float, e: dict) -> list[Box]:
    """보이는 카드의 제자리 상자(x0, y0, x1, y1) — 뱃지 회피(engine.reserved)·겹침 검사용."""
    return [(x - CHAIN.flag_R, y - CHAIN.flag_R, x + CHAIN.w, y + CHAIN.h) for _, x, y, _ in slots(t, e)]


def _flag(ctx: cairo.Context, R: RenderCtx, it: dict, x: float, y: float, t: float, a: float) -> None:  # noqa: N803
    """좌상단 국기 원 — 뱃지 그리기(badge_at: 그림자·팝인·국기 래스터)를 그대로 쓴다. 이름표 없음."""
    from engine.layers.badges import badge_at  # noqa: PLC0415 — badges → reserved → chain 순환 회피

    badge_at(ctx, R, x, y, dict(kind="flag", flag=it["flag"], R=CHAIN.flag_R, t0=it["at"], label="", accent=it.get("accent") or "gold"), t, a)


def draw_chain(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    ea = chain_alpha(t, e)
    if ea <= 0.01:
        return
    bad = check_text(ctx, e)
    if bad:
        raise ChainError("\n".join(bad))
    vis = slots(t, e)
    if not vis:
        return
    now = vis[-1][0]
    for i, x, y, a in vis:
        it = e["items"][i]
        cur = i == now
        # 강조 전환: 새 카드가 들어오는 동안 이전 카드는 past_alpha 로 내려간다
        nxt = e["items"][i + 1]["at"] if i + 1 < len(e["items"]) else math.inf
        dim = 1 - (1 - CHAIN.past_alpha) * smooth((t - nxt) / CARD.fade_sec)
        al = ea * a * (1 if cur else dim)        # 글자·윗선만 흐린다 — 바탕은 불투명 유지(지도 라벨이 비치지 않게)
        acc = C[it.get("accent") or "gold"]
        rrect(ctx, x, y, CHAIN.w, CHAIN.h, 5)
        ctx.set_source_rgba(0.05, 0.06, 0.09, 0.9 * ea * a)
        ctx.fill()
        ctx.set_source_rgba(*acc, al * (1 if cur else 0.6))
        ctx.rectangle(x + 5, y, CHAIN.w - 10, 2.5)
        ctx.fill()
        text(ctx, it["date"], x + CHAIN.flag_R + 8, y + 16, CHAIN.date_size, "mono", acc, al, 0, "l")
        text(ctx, it["title"], x + 10, y + 36, CHAIN.title_size, "sansb", (1, 1, 1), al, 0, "l")
        if it.get("line"):
            text(ctx, it["line"], x + 10, y + 54, CHAIN.line_size, "sansm", C["muted"], al, 0, "l")
        _flag(ctx, R, it, x, y, t, al)

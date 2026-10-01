"""겹침 카드(cascade) — 지도 배경은 고정, 사건 카드를 왼쪽부터 비스듬히 겹쳐 쌓는다
(v5.2.0, 사용자 제안·재구성 2026-10-01 — 시안. D-0135 "띠"를 대체).

어원: 라틴어 cadere(떨어지다) → 이탈리아어 cascata(층층 폭포) → 프랑스어 cascade. 화면 문법으로는 윈도의 '계단식 창 배열' —
앞 창은 온전히, 뒤 창은 제목줄만 보이게 비스듬히 겹친다.

- 지금 말하는 사건 = 맨 앞·rules cascade.front 크기·accent 윗선·부제까지.
- 다음 사건이 오면(items[k+1].at) 앞 카드는 focus_sec 동안 back_scale 로 물러나고(크기·글자 알파 smooth), 새 카드가 step 오른쪽에서
  위에 겹쳐 아래에서 올라온다. 뒤 카드는 다음 카드에 덮인 부분을 그리지 않는다(반투명 바탕끼리 비치지 않게 — 오른쪽 경계를 다음 카드 등장에 맞춰 당긴다).
  그래서 뒤 카드는 왼쪽 step 폭(국기 원·날짜)만 보인다. 제목·부제·윗선은 물러나며 사라진다(잘린 글자가 비치지 않게).
- 뒤 카드가 max_back 을 넘으면 가장 오래된 카드가 shift_sec 동안 왼쪽으로 밀려 흐려져 나간다.
- 상자 = 아일랜드 공통 상자(engine.island.draw_frame). 국기 원 = 카드 좌상단 모서리(badge_at 재사용, 이름표 없음).
- 패널 덮개 아래에 그린다(engine/render.py). 지명 라벨·뱃지는 보이는 카드 상자를 피한다(R.reserved·engine.reserved.card_zones).
- 글자가 앞 카드 폭, 또는 뒤 카드에서 보이는 날짜 자리를 넘으면 오류(`[cascade-overflow]`, 자름·말줄임 없음 — 15 P6). 수치는 전부 rules cascade.
"""

from __future__ import annotations

from dataclasses import dataclass

import cairo

from engine.context import RenderCtx
from engine.style import C, CARD, CASCADE, H_OUT
from engine.timebase import ease_out, smooth, window
from engine.typography import rrect, text, tw

Box = tuple[float, float, float, float]
F = CASCADE.front


class CascadeError(ValueError):
    """겹침 카드 글자가 자리를 넘는다 — 조용히 자르지 않는다(15 P6). 연출이 문구를 줄인다."""


@dataclass(frozen=True)
class Card:
    i: int            # item 번호
    x: float          # 카드 왼쪽(= 국기 원 중심 x)
    y: float
    scale: float      # 1 = 앞, back_scale = 뒤
    back: float       # 0 = 앞, 1 = 완전히 물러남
    a: float          # 등장·밀려남 알파
    clip_x1: float    # 이 x 오른쪽은 다음 카드가 덮는다(그리지 않음)
    appear: float
    leaving: bool

    @property
    def w(self) -> float:
        return F.w * self.scale

    @property
    def h(self) -> float:
        return F.h * self.scale

    @property
    def flag_r(self) -> float:
        return CASCADE.flag_R * self.scale


def check_text(ctx: cairo.Context, e: dict) -> list[str]:
    """글자 자리 검사 — 앞 카드 날짜·제목·부제, 뒤 카드에서 보이는 날짜(step 폭 안). 넘치면 `[cascade-overflow]` 한 줄씩."""
    out = []
    peek = CASCADE.step - (CASCADE.flag_R + F.date_dx + F.pad_x) * CASCADE.back_scale

    def fit(s: str, size: float, font: str, room: float, where: str) -> None:
        if s and tw(ctx, s, size, font) > room:
            out.append(f"[cascade-overflow] {where} {s!r} 폭 {tw(ctx, s, size, font):.0f}px > {room:.0f}px — 문구를 줄인다")

    for it in e["items"]:
        fit(it["date"], F.date_size, "mono", F.w - CASCADE.flag_R - F.date_dx - F.pad_x, "앞 카드 날짜")
        fit(it["title"], F.title_size, "sansb", F.w - F.pad_x * 2, "앞 카드 제목")
        fit(it.get("line") or "", F.line_size, "sansm", F.w - F.pad_x * 2, "앞 카드 부제")
        fit(it["date"], F.date_size * CASCADE.back_scale, "mono", peek, "뒤 카드 날짜(보이는 폭)")
    return out


def cascade_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec)


def layout(t: float, e: dict) -> list[Card]:
    """보이는 카드(뒤 → 앞 순서). 그리기·예약 영역·검사가 같이 쓴다."""
    items = e["items"]
    n = sum(1 for it in items if t >= it["at"])
    if n == 0:
        return []
    off = sum(smooth((t - items[m]["at"]) / CASCADE.shift_sec) for m in range(CASCADE.max_back + 1, n))
    xs, ys, alphas = [], [], []
    for k in range(n):
        ap = items[k]["at"]
        xs.append(CASCADE.x0 + (k - off) * CASCADE.step)
        ys.append(CASCADE.y + (1 - ease_out((t - ap) / CASCADE.focus_sec)) * CARD.slide_px / 2)   # 아래에서 올라온다(폭을 늘리지 않게)
        gone = smooth(off - k) if off > k else 0.0
        alphas.append(smooth((t - ap) / CARD.fade_sec) * (1 - gone))
    out: list[Card] = []
    for k in range(n):
        back = smooth((t - items[k + 1]["at"]) / CASCADE.focus_sec) if k + 1 < n else 0.0
        scale = 1 + (CASCADE.back_scale - 1) * back
        right = xs[k] + F.w * scale
        clip = right if k + 1 >= n else right + (xs[k + 1] - right) * alphas[k + 1]   # 다음 카드가 나타나는 만큼 경계를 당긴다
        if alphas[k] > 0.01:
            out.append(Card(k, xs[k], ys[k], scale, back, alphas[k], clip, items[k]["at"], off > k))
    return out


def cascade_boxes(t: float, e: dict) -> list[Box]:
    """보이는 카드 영역(x0, y0, x1, y1) — 국기 원 포함, 다음 카드에 덮인 부분 제외. 지명·뱃지 회피와 검사용."""
    return [(c.x - c.flag_r, c.y - c.flag_r, min(c.x + c.w, c.clip_x1), c.y + c.h) for c in layout(t, e)]


def cascade_width(t: float, e: dict) -> float:
    """겹침 카드 전체 폭 = 보이는 카드 오른쪽 끝 − x0(밀려 나가는 카드는 x0 왼쪽이라 폭을 늘리지 않는다)."""
    return max((min(c.x + c.w, c.clip_x1) for c in layout(t, e)), default=CASCADE.x0) - CASCADE.x0


def back_count(t: float, e: dict) -> int:
    """뒤로 물러난 카드 수(반 이상 물러남, 밀려 나가는 카드 제외)."""
    return sum(1 for c in layout(t, e) if c.back >= 1 / 2 and not c.leaving)


def draw_cascade(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    from engine.island import draw_frame  # noqa: PLC0415 — island → style 순환 회피
    from engine.layers.badges import badge_at  # noqa: PLC0415 — badges → reserved → cascade 순환 회피

    ea = cascade_alpha(t, e)
    if ea <= 0.01:
        return
    bad = check_text(ctx, e)
    if bad:
        raise CascadeError("\n".join(bad))
    for c in layout(t, e):
        it = e["items"][c.i]
        a = ea * c.a
        acc = C[it.get("accent") or "gold"]
        ta = a * (1 + (CASCADE.back_text_alpha - 1) * c.back)   # 글자·국기: 물러나면 흐리게
        fa = a * (1 - c.back)                                    # 윗선·제목·부제: 앞 카드에만(뒤 카드는 국기·날짜만 — 덮여 잘린 글자가 비치지 않게)
        ctx.save()
        ctx.rectangle(0, 0, c.clip_x1, H_OUT)
        ctx.clip()
        draw_frame(ctx, (c.x, c.y, c.w, c.h), a)
        ctx.translate(c.x, c.y)
        ctx.scale(c.scale, c.scale)
        if fa > 0.01:
            rrect(ctx, F.pad_x, 0, F.w - F.pad_x * 2, F.accent_w, F.accent_w / 2)
            ctx.set_source_rgba(*acc, fa)
            ctx.fill()
        text(ctx, it["date"], CASCADE.flag_R + F.date_dx, F.date_dy, F.date_size, "mono", acc, ta, 0, "l")
        if fa > 0.01:
            text(ctx, it["title"], F.pad_x, F.title_dy, F.title_size, "sansb", (1, 1, 1), fa, 0, "l")
        if it.get("line") and fa > 0.01:
            text(ctx, it["line"], F.pad_x, F.line_dy, F.line_size, "sansm", C["muted"], fa, 0, "l")
        ctx.restore()
        badge_at(ctx, R, c.x, c.y, dict(kind="flag", flag=it["flag"], R=c.flag_r, t0=c.appear, label="",
                                        accent=it.get("accent") or "gold"), t, ta)

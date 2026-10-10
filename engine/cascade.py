"""겹침 카드(cascade) — 지도 배경은 고정, 사건 카드를 왼쪽부터 비스듬히 겹쳐 쌓는다
(v5.2.0, 사용자 제안·재구성 2026-10-01 — D-0135 "띠"를 대체. v5.3.0 D-0139 채택, 사용자 결정 D116·판정 D117).

어원: 라틴어 cadere(떨어지다) → 이탈리아어 cascata(층층 폭포) → 프랑스어 cascade. 화면 문법으로는 윈도의 '계단식 창 배열' —
앞 창은 온전히, 뒤 창은 제목줄만 보이게 비스듬히 겹친다.

- v5.14.0 V2(back_and_forth D-0153 §4·D-0157, 사용자 결정 D148, 가이드 23 §6): 사건 k 의 논리 slot s = k − off, 좌상단
  x = x0 + dx·s, y = y0 + dy·s — 시간 순서대로 일정한 오른쪽 아래(좌상단 pivot 고정, 개별 Y slide·깊이 Y 없음).
- 지금 말하는 사건 = 맨 앞·rules cascade.front 크기·accent 윗선·부제까지. 다음 사건이 오면(items[k+1].at) 앞 카드는 focus_sec 동안
  back_scale·높이 (h − back_h_drop) 로 물러나고, 새 카드는 제자리에서 페이드로 나타난다.
- 가림: 뒤 카드의 상자(그림자·바탕·테두리)는 앞쪽 모든 카드의 실제 둥근 사각형(+ frame.occluder_pad)으로 차례로 지운다
  (`island.draw_frame(occluders=)`, 합집합). 그래서 뒤 카드는 왼쪽 dx 폭과 다음 카드 위로 드러난 윗띠(dy)가 끊김 없이 보인다
  (옛 v5.3.0 의 세로 전체 클립이 상자까지 잘라 하단선이 끊기던 문제 — 가이드 §6, phaseQ0 `cascade_asis_clip.png`).
- 글자는 따로: 다음 카드 왼쪽 끝까지(경계 back_fade_px 알파 그라데이션, D-0138). 물러나는 카드 글자는 focus_sec 앞 절반에 지우고
  새 카드 글자는 뒤 절반에 나타난다(밀기 있는 전환 = max(focus_sec, shift_sec), `text_sec`).
- 뒤 카드가 max_back 을 넘으면 off 가 shift_sec 동안 1 늘어 모든 카드가 같은 변위로 왼쪽 위로 가고, 가장 오래된 카드는 흐려져 나간다.
- 표면·글자색 = rules cascade.surface(앞/뒤 표면은 물러남으로 보간, 깊이마다 back_dim 어둡게). 국기 원 = 카드 좌상단 모서리(badge_at).
- 패널 덮개 아래에 그린다(engine/render.py). 지명 라벨·뱃지는 보이는 영역(`cascade_boxes` — 가림과 같은 계산의 보수적 사각형 분해)을 피한다.
- 글자가 앞 카드 폭, 또는 뒤 카드에서 보이는 날짜 자리를 넘으면 오류(`[cascade-overflow]`, 자름·말줄임 없음 — 15 P6). 수치는 전부 rules cascade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import cairo

from engine.context import RenderCtx
from engine.style import C, CARD, CASCADE, FONT, H_OUT
from engine.timebase import smooth, window
from engine.typography import rrect, text, tw

if TYPE_CHECKING:
    from engine.island import FrameStyle

Box = tuple[float, float, float, float]
F = CASCADE.front
FR = CASCADE.frame
SURF = CASCADE.surface
for _f in (F.date_font, F.title_font, F.line_font):
    if _f not in FONT:
        raise KeyError(f"rules cascade.front 글꼴 {_f!r} 는 engine.style.FONT 키가 아니다")


class CascadeError(ValueError):
    """겹침 카드 글자가 자리를 넘는다 — 조용히 자르지 않는다(15 P6). 연출이 문구를 줄인다."""


@dataclass(frozen=True)
class Card:
    i: int            # item 번호
    x: float          # 카드 왼쪽(= 국기 원 중심 x)
    y: float          # 카드 위 = y0 + dy·slot(V2 — 슬라이드·깊이 Y 없음)
    scale: float      # 1 = 앞, back_scale = 뒤
    back: float       # 0 = 앞, 1 = 완전히 물러남
    depth: float      # 앞에 쌓인 카드 수(smooth) — 어두움 back_dim 의 배수
    a: float          # 등장·밀려남 알파
    clip_x1: float    # 이 x 오른쪽은 다음 카드가 덮는다(그리지 않음)
    appear: float
    leaving: bool
    title_a: float    # 제목·날짜 글자 알파 배율(전환 순서: 물러나는 카드 = 앞 절반 지움 → 뒤 절반 뒤 카드 글자, 새 카드 = 뒤 절반)
    detail_a: float   # 부제·윗선 알파 배율(앞 카드에만)

    @property
    def w(self) -> float:
        return F.w * self.scale

    @property
    def h(self) -> float:
        return (F.h - CASCADE.back_h_drop * self.back) * self.scale

    @property
    def box(self) -> Box:
        """상자(x, y, 폭, 높이)."""
        return (self.x, self.y, self.w, self.h)

    @property
    def flag_r(self) -> float:
        return CASCADE.flag_R * self.scale


def check_text(ctx: cairo.Context, e: dict) -> list[str]:
    """글자 자리 검사 — 앞 카드 날짜·제목·부제, 뒤 카드에서 보이는 날짜(step 폭 안). 넘치면 `[cascade-overflow]` 한 줄씩."""
    out = []
    peek = CASCADE.dx - (CASCADE.flag_R + F.date_dx + F.pad_x) * CASCADE.back_scale

    def fit(s: str, size: float, font: str, room: float, where: str) -> None:
        if s and tw(ctx, s, size, font) > room:
            out.append(f"[cascade-overflow] {where} {s!r} 폭 {tw(ctx, s, size, font):.0f}px > {room:.0f}px — 문구를 줄인다")

    for it in e["items"]:
        fit(it["date"], F.date_size, F.date_font, F.w - CASCADE.flag_R - F.date_dx - F.pad_x, "앞 카드 날짜")
        fit(it["title"], F.title_size, F.title_font, F.w - F.pad_x * 2, "앞 카드 제목")
        fit(it.get("line") or "", F.line_size, F.line_font, F.w - F.pad_x * 2, "앞 카드 부제")
        fit(it["date"], F.date_size * CASCADE.back_scale, F.date_font, peek, "뒤 카드 날짜(보이는 폭)")
    return out


def cascade_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec)


def _half(p: float, second: bool) -> float:
    """전환 진행 p(0~1)의 앞 절반(사라짐) 또는 뒤 절반(나타남) 알파."""
    return smooth(p * 2 - 1) if second else 1 - smooth(p * 2)


def text_sec(k: int) -> float:
    """k 번째 사건이 앞에 서는 전환 길이 — 새 앞 카드 글자는 이 길이의 뒤 절반에 나타난다(v5.3.0 D-0139 §3, D-0137 §3).
    밀기 없는 전환 = focus_sec, 가장 오래된 뒤 카드가 밀려 나가는 전환(k ≥ max_back + 1) = max(focus_sec, shift_sec)."""
    return max(CASCADE.focus_sec, CASCADE.shift_sec) if k >= CASCADE.max_back + 1 else CASCADE.focus_sec


def layout(t: float, e: dict) -> list[Card]:
    """보이는 카드(뒤 → 앞 순서). 그리기·예약 영역·검사가 같이 쓴다."""
    items = e["items"]
    n = sum(1 for it in items if t >= it["at"])
    if n == 0:
        return []
    off = sum(smooth((t - items[m]["at"]) / CASCADE.shift_sec) for m in range(CASCADE.max_back + 1, n))
    prog = [min(1.0, max(0.0, (t - items[k]["at"]) / CASCADE.focus_sec)) for k in range(n)]   # k 번째 사건이 앞에 서는 전환 진행
    out: list[Card] = []
    for k in range(n):
        ap = items[k]["at"]
        x = CASCADE.x0 + (k - off) * CASCADE.dx          # V2 — 논리 slot 하나의 식(밀기 = 모든 카드 같은 변위)
        y = CASCADE.y0 + (k - off) * CASCADE.dy
        depth = sum(smooth(prog[m]) for m in range(k + 1, n))
        gone = smooth(off - k) if off > k else 0.0
        a = smooth((t - ap) / CARD.fade_sec) * (1 - gone)
        back = smooth(prog[k + 1]) if k + 1 < n else 0.0
        scale = 1 + (CASCADE.back_scale - 1) * back
        right = x + F.w * scale
        nx = CASCADE.x0 + (k + 1 - off) * CASCADE.dx
        clip = right if k + 1 >= n else right + (nx - right) * smooth(prog[k + 1] * 2)   # 다음 카드 전환 앞 절반에 경계를 다음 카드 왼쪽 끝까지 당긴다
        if k + 1 < n and prog[k + 1] < 1:      # 물러나는 중: 앞 절반 지움 → 뒤 절반 뒤 카드 글자
            title_a = _half(prog[k + 1], False) if prog[k + 1] < 1 / 2 else CASCADE.back_text_alpha * _half(prog[k + 1], True)
        elif k + 1 < n:
            title_a = CASCADE.back_text_alpha
        else:                                   # 맨 앞(새 카드): 전환 뒤 절반에 나타남. 첫 사건은 앞 카드가 없으니 바로
            title_a = _half(min(1.0, max(0.0, (t - ap) / text_sec(k))), True) if k > 0 else 1.0
        detail_a = (1 - smooth(prog[k + 1] * 2)) if k + 1 < n else title_a
        if a > 0.01:
            out.append(Card(k, x, y, scale, back, depth, a, clip, ap, off > k, title_a, detail_a))
    return out


def occluders(cards: list[Card], i: int) -> list[Card]:
    """cards[i] 를 가리는 카드 = 그 뒤에 그리는(앞쪽) 모든 카드."""
    return cards[i + 1:]


def visible_rects(c: Card, front: list[Card]) -> list[Box]:
    """카드 상자에서 앞쪽 카드(불투명에 가까운 것, a ≥ 0.99)를 뺀 보이는 영역 — 보수적 사각형 분해(x0, y0, x1, y1).
    가리는 상자는 모서리 반경만큼 안으로 줄여 잰다(둥근 모서리로 드러나는 조각까지 포함 — 덜 가리는 쪽으로 보수적)."""
    X0, Y0, X1, Y1 = c.x, c.y, c.x + c.w, c.y + c.h  # noqa: N806
    r = FR.radius
    occ = [(o.x + r, o.y + r, o.x + o.w - r, o.y + o.h - r) for o in front if o.a >= 0.99]
    occ = [(max(a, X0), max(b, Y0), min(cc, X1), min(d, Y1)) for a, b, cc, d in occ]
    occ = [q for q in occ if q[0] < q[2] and q[1] < q[3]]
    xs = sorted({X0, X1, *(v for q in occ for v in (q[0], q[2]))})
    ys = sorted({Y0, Y1, *(v for q in occ for v in (q[1], q[3]))})
    rows: list[tuple[float, float, list[tuple[float, float]]]] = []
    for ya, yb in zip(ys, ys[1:]):
        spans: list[tuple[float, float]] = []
        for xa, xb in zip(xs, xs[1:]):
            mx, my = (xa + xb) / 2, (ya + yb) / 2
            if any(q[0] <= mx <= q[2] and q[1] <= my <= q[3] for q in occ):
                continue
            if spans and spans[-1][1] == xa:
                spans[-1] = (spans[-1][0], xb)
            else:
                spans.append((xa, xb))
        if rows and rows[-1][2] == spans and rows[-1][1] == ya:
            rows[-1] = (rows[-1][0], yb, spans)
        else:
            rows.append((ya, yb, spans))
    return [(xa, ya, xb, yb) for ya, yb, spans in rows for xa, xb in spans]


def cascade_boxes(t: float, e: dict) -> list[Box]:
    """보이는 영역(x0, y0, x1, y1) — 카드마다 국기 원 상자 + 앞쪽 카드에 가려지지 않은 상자 조각(그리기 가림과 같은 기하).
    지명·뱃지 회피(R.reserved·reserved.card_zones)와 검사(checks cascade·chain)가 같이 쓴다."""
    cards = layout(t, e)
    out: list[Box] = []
    for i, c in enumerate(cards):
        out.append((c.x - c.flag_r, c.y - c.flag_r, c.x + c.flag_r, c.y + c.flag_r))
        out += visible_rects(c, occluders(cards, i))
    return out


def cascade_width(t: float, e: dict) -> float:
    """겹침 카드 전체 폭 = 보이는 영역 오른쪽 끝 − x0(밀려 나가는 카드는 x0 왼쪽이라 폭을 늘리지 않는다)."""
    return max((b[2] for b in cascade_boxes(t, e)), default=CASCADE.x0) - CASCADE.x0


def back_count(t: float, e: dict) -> int:
    """뒤로 물러난 카드 수(반 이상 물러남, 밀려 나가는 카드 제외)."""
    return sum(1 for c in layout(t, e) if c.back >= 1 / 2 and not c.leaving)


def frame_style(c: Card) -> "FrameStyle":
    """V2 상자 모양 — 표면 = 앞/뒤 보간(back) × 깊이 어두움(back_dim·depth), 테두리 = surface.edge."""
    from engine.island import FrameStyle  # noqa: PLC0415 — island → style 순환 회피

    dim = 1 - min(1.0, CASCADE.back_dim * c.depth)
    fill = tuple((f + (b - f) * c.back) * dim for f, b in zip(SURF.front, SURF.back))
    return FrameStyle(radius=FR.radius, edge_w=FR.edge_w, edge_rgb=tuple(SURF.edge), edge_alpha=1.0, fill_rgb=fill)  # type: ignore[arg-type]


def occluder_boxes(front: list[Card]) -> tuple:
    """앞쪽 카드의 실제 둥근 사각형(+ occluder_pad = 테두리 폭 절반) — 가림 알파 = 그 카드의 등장·밀려남 알파(전체 페이드 ea 는 제외)."""
    p = FR.occluder_pad
    return tuple(((o.x - p, o.y - p, o.w + 2 * p, o.h + 2 * p), FR.radius + p, o.a) for o in front)


def draw_cascade(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    from engine.island import draw_frame  # noqa: PLC0415 — island → style 순환 회피
    from engine.layers.badges import badge_at  # noqa: PLC0415 — badges → reserved → cascade 순환 회피

    ea = cascade_alpha(t, e)
    if ea <= 0.01:
        return
    bad = check_text(ctx, e)
    if bad:
        raise CascadeError("\n".join(bad))
    cards = layout(t, e)
    for i, c in enumerate(cards):
        it = e["items"][c.i]
        a = ea * c.a
        acc = C[it.get("accent") or "gold"]
        ta, fa = a * c.title_a, a * c.detail_a
        draw_frame(ctx, c.box, a, frame_style(c), occluder_boxes(occluders(cards, i)))   # 상자 = 앞 카드 실제 모양으로 가림(V2)
        ctx.save()
        ctx.rectangle(0, 0, c.clip_x1, H_OUT)    # 글자만 — 다음 카드 왼쪽 끝까지(상자 가림과 따로, 가이드 §6)
        ctx.clip()
        ctx.push_group()                         # 글자 — 덮이는 경계 back_fade_px 를 알파 그라데이션으로 가린다(자름 아님)
        ctx.translate(c.x, c.y)
        ctx.scale(c.scale, c.scale)
        if fa > 0.01:
            rrect(ctx, F.pad_x, 0, F.w - F.pad_x * 2, F.accent_w, F.accent_w / 2)
            ctx.set_source_rgba(*acc, fa)
            ctx.fill()
            if it.get("line"):
                text(ctx, it["line"], F.pad_x, F.line_dy, F.line_size, F.line_font, SURF.text_sub, fa, 0, "l")
        if ta > 0.01:
            text(ctx, it["date"], CASCADE.flag_R + F.date_dx, F.date_dy, F.date_size, F.date_font, acc, ta, 0, "l")
            text(ctx, it["title"], F.pad_x, F.title_dy, F.title_size, F.title_font, SURF.text, ta, 0, "l")
        glyphs = ctx.pop_group()
        if c.clip_x1 < c.x + c.w:
            fade = cairo.LinearGradient(c.clip_x1 - CASCADE.back_fade_px, 0, c.clip_x1, 0)
            fade.add_color_stop_rgba(0, 0, 0, 0, 1)
            fade.add_color_stop_rgba(1, 0, 0, 0, 0)
            ctx.set_source(glyphs)
            ctx.mask(fade)
        else:
            ctx.set_source(glyphs)
            ctx.paint()
        ctx.restore()
        badge_at(ctx, R, c.x, c.y, dict(kind="flag", flag=it["flag"], R=c.flag_r, t0=c.appear, label="",
                                        accent=it.get("accent") or "gold"), t, a * max(c.title_a, CASCADE.back_text_alpha))

"""versus 패널 skin 배치 셋 — axis·sheets·piles (v7.4.0 UF-912·UF-913 "세가지 다 적용해").

skin 무대(스튜디오·porcelain 지도)에서만 engine/panels/versus.draw 가 부른다. 판 흰 카드는 없다(base.make_panel_renderer 의 skin_backing):
- axis   — 가운데 세로 축, 거울 배치 큰 옆 제목, 항목이 t 순서대로 한 줄씩(바탕 없는 글씨 + 흰 번짐, UF-907)
- sheets — 살짝 기운 직각 흰 종이 두 장 + 가운데 VS 원(UF-908 직각, 알약·원만 둥글게)
- piles  — 논거 하나 = 직각 카드 한 장, 그쪽 더미에 내려앉아 쌓인다
두 쪽은 같은 무게(G4 — 옆 제목 같은 크기·같은 줄 간격). 지금 항목(t ≤ 지금 중 가장 늦은 것) 하나만 강조색 — 다음 항목이 들어오는 동안 옮겨 간다.
넘치면 VersusOverflowError(자름 없음, 15 P6). 수치 = rules skin.panel.versus.<layout>(코드 리터럴 0, 15 P3).
"""

from __future__ import annotations

import math
from collections.abc import Callable

import cairo

from engine import skin
from engine.panels.versus import VersusOverflowError
from engine.style import H_OUT, MOTION, PANEL, SKIN, W_OUT, Color
from engine.timebase import smooth
from engine.typography import text, tw, wrap

V = SKIN.panel.versus
INKS: dict[str, Color] = {"primary": skin.INK, "secondary": skin.INK2, "tertiary": skin.INK3}
WHITE: Color = (1.0, 1.0, 1.0)
Item = tuple[int, int, float, str]   # (쪽, 쪽 안 번호, t, 문구)


def _mix(c0: Color, c1: Color, k: float) -> Color:
    return tuple(a + (b - a) * k for a, b in zip(c0, c1))  # type: ignore[return-value]


def _order(e: dict) -> list[Item]:
    """두 쪽 항목을 t 순서로(같은 t 는 왼쪽 먼저 — 안정 정렬)."""
    out = [(si, ii, float(it["t"]), it["text"]) for si, sd in enumerate(e["sides"]) for ii, it in enumerate(sd["items"])]
    return sorted(out, key=lambda r: r[2])


def _appear(t: float, t_item: float) -> float:
    return smooth((t - t_item) / MOTION["panel_item_fast_in_sec"])


def _heat(order: list[Item], t: float) -> dict[tuple[int, int], tuple[float, float]]:
    """항목마다 (등장 알파, 강조 정도) — 강조 = 자기 등장 × (1 − 다음 항목 등장). 다 들어온 뒤엔 마지막으로 나타난 하나만 1."""
    ias = [_appear(t, r[2]) for r in order]
    out = {}
    for k, r in enumerate(order):
        nxt = ias[k + 1] if k + 1 < len(ias) else 0.0
        out[(r[0], r[1])] = (ias[k], ias[k] * (1 - nxt))
    return out


def _enter(t: float, e: dict) -> float:
    """머리(제목·종이·더미 머리)의 등장 진행 0→1 — 패널 페이드 시간(layout panel.fade_sec)에 맞춘 올라옴."""
    return smooth((t - e["t0"]) / PANEL.fade_sec)


def _rotate(ctx: cairo.Context, box: tuple[float, float, float, float], deg: float) -> None:
    x, y, w, h = box
    ctx.translate(x + w / 2, y + h / 2)
    ctx.rotate(deg * math.pi / 180)   # 도 → 라디안(180 = 반 바퀴, 각도 정의)
    ctx.translate(-(x + w / 2), -(y + h / 2))


def _balanced(ctx: cairo.Context, s: str, room: float, size: float, font: str) -> list[str]:
    """두 줄로 접히는 문구의 둘째 줄이 너무 짧으면(끝 낱말 하나만 남는 줄) 첫 줄 끝 낱말을 하나씩 내려 둘째 줄을 채운다 —
    둘째 줄 폭 ≥ 첫 줄 폭 × rules skin.panel.versus.tail_min 이 될 때까지. 읽는 흐름(앞에서부터 채움)은 지킨다. 그 밖은 wrap 그대로."""
    lines = wrap(ctx, s, room, size, font)
    if len(lines) != 2:   # 한 줄·세 줄 이상은 손대지 않는다(세 줄 이상은 호출부가 넘침으로 본다)
        return lines
    words = s.split(" ")
    k = len(lines[0].split(" "))
    while k > 1:
        head, tail = " ".join(words[:k]), " ".join(words[k:])
        if tw(ctx, tail, size, font) >= tw(ctx, head, size, font) * V.tail_min:
            return [head, tail]
        k -= 1
    return lines


def _fits(ctx: cairo.Context, s: str, room: float, size: float, font: str, max_lines: int | None, what: str) -> list[str]:
    lines = _balanced(ctx, s, room, size, font)
    if (max_lines is not None and len(lines) > max_lines) or any(tw(ctx, ln, size, font) > room for ln in lines):
        raise VersusOverflowError(f"[panel-overflow] versus {what} {s!r} — {len(lines)}줄(최대 {max_lines}) 또는 폭 > {room:.0f}px, 문구를 줄인다")
    return lines


def _card(ctx: cairo.Context, box: tuple[float, float, float, float], a: float, lift: float) -> None:
    """직각 흰 면 — card 그림자 + 지금 항목이면 lifted 그림자를 lift 만큼 더(들림이 부드럽게 옮겨 간다)."""
    if lift > 0:
        skin.soft_shadow(ctx, box, SKIN.surface.radius, SKIN.shadow.lifted, lift * a)
    skin.surface(ctx, box, a, "card")


def _glow(ctx: cairo.Context, draw: Callable[[cairo.Context], None], rect: tuple[float, float, float, float],
          blur: float, alpha: float) -> None:
    skin.glow(ctx, draw, rect, blur=blur, alpha=alpha)


# ───────────────────────────── axis
def _axis(ctx: cairo.Context, t: float, e: dict, a: float) -> None:
    X = V.axis  # noqa: N806
    cx = W_OUT / 2
    sides = e["sides"]
    room_h = cx - X.head.gap - X.head.x_margin
    size = X.head.size
    while any(tw(ctx, sd["title"], size, X.head.font) > room_h for sd in sides):
        size -= 1
        if size < X.head.min_size:
            raise VersusOverflowError(f"[panel-overflow] versus 옆 제목 {[sd['title'] for sd in sides]} — {X.head.min_size}px 로도 반쪽 폭 "
                                      f"{room_h:.0f}px 를 넘는다, 문구를 줄인다")
    order = _order(e)
    room_i = cx - X.item.gap - X.head.x_margin
    lines = [_fits(ctx, r[3], room_i, X.item.size, X.item.font, X.item.max_lines, "항목") for r in order]
    extra = [len(ls) - 1 for ls in lines]
    pitch = X.row.pitch
    while True:
        ys = [X.row.y0 + k * pitch + sum(extra[:k]) * X.item.line_gap for k in range(len(order))]
        last = ys[-1] + extra[-1] * X.item.line_gap
        if last <= X.row.max_y:
            break
        pitch -= 1
        if pitch < X.row.min_pitch:
            raise VersusOverflowError(f"[panel-overflow] versus 항목 {len(order)}개 — 줄 간격 {X.row.min_pitch}px 로도 "
                                      f"{X.row.max_y}px(자막 구역 위) 밖, 항목을 줄인다")
    heat = _heat(order, t)
    dy = X.rise * (1 - _enter(t, e))

    def block(c: cairo.Context) -> None:
        c.save()
        c.translate(0, dy)
        text(c, e["title"], cx, X.title.y, X.title.size, X.title.font, INKS[X.title.ink], a, 0, "c")
        c.new_path()
        c.rectangle(cx - X.line.w / 2, X.line.top, X.line.w, last + X.line.tail - X.line.top)
        c.set_source_rgba(*skin.INK, X.line.alpha * a)
        c.fill()
        for si, sd in enumerate(sides):
            sg = -1 if si == 0 else 1
            anchor = "r" if si == 0 else "l"
            text(c, sd["title"], cx + sg * X.head.gap, X.head.y, size, X.head.font, skin.INK, a, 0, anchor)
            text(c, sd["src"], cx + sg * X.head.gap, X.head.y + X.src.dy, X.src.size, X.src.font, skin.INK3, a, 0, anchor,
                 spacing=X.src.track * X.src.size)
        c.restore()
        for k, r in enumerate(order):
            ia, hot = heat[(r[0], r[1])]
            ia *= a
            if ia <= 0:
                continue
            sg = -1 if r[0] == 0 else 1
            y = ys[k]
            yd = y + X.dot.dy
            col = _mix(skin.INK2, skin.ACCENT_SHAPE, hot)
            c.new_path()
            c.move_to(cx + sg * X.tick.gap, yd)
            c.line_to(cx + sg * (X.tick.gap + X.tick.len), yd)
            c.set_source_rgba(*col, ia * (X.tick.alpha + (1 - X.tick.alpha) * hot))
            c.set_line_width(X.tick.w + (X.tick.w_hot - X.tick.w) * hot)
            c.stroke()
            c.new_path()
            c.arc(cx, yd, X.dot.r + (X.dot.r_hot - X.dot.r) * hot, 0, 2 * math.pi)
            c.set_source_rgba(*col, ia)
            c.fill()
            for j, ln in enumerate(lines[k]):
                text(c, ln, cx + sg * X.item.gap, y + j * X.item.line_gap, X.item.size, X.item.font, skin.INK, ia, 0,
                     "r" if r[0] == 0 else "l")

    rect = (X.head.x_margin, X.title.y - X.title.size, W_OUT - X.head.x_margin, last + X.item.size + dy)
    _glow(ctx, block, rect, X.glow.blur, X.glow.alpha)


# ───────────────────────────── sheets
def _sheets(ctx: cairo.Context, t: float, e: dict, a: float) -> None:
    S = V.sheets  # noqa: N806
    w, h, pad = S.sheet.w, S.sheet.h, S.sheet.pad
    inner = w - 2 * pad
    room = inner - S.item.dx
    limit = h - S.src.dy - S.src.clear
    lay: list[list[list[str]]] = []
    for sd in e["sides"]:
        if len(sd["items"]) > S.item.max:
            raise VersusOverflowError(f"[panel-overflow] versus sheets {sd['title']!r} 항목 {len(sd['items'])}개 > {S.item.max}, 항목을 줄인다")
        _fits(ctx, sd["title"], inner, S.head.size, S.head.font, 1, "옆 제목")
        lay.append([_fits(ctx, it["text"], room, S.item.size, S.item.font, S.item.max_lines, "항목") for it in sd["items"]])
    scale = 1.0
    for ls in lay:   # 두 장 같은 간격(같은 무게) — 더 긴 쪽에 맞춘다
        fixed = S.item.y0 + sum(len(x) - 1 for x in ls) * S.item.line_gap
        gaps = len(ls) * S.item.rule_dy + (len(ls) - 1) * S.item.next_dy
        if fixed + gaps > limit:
            scale = min(scale, (limit - fixed) / gaps)
    if scale < S.item.min_scale:
        raise VersusOverflowError(f"[panel-overflow] versus sheets 항목이 종이({h}px)에 들어가지 않는다 — 간격 {scale:.2f}배 < {S.item.min_scale}, 문구·항목을 줄인다")
    heat = _heat(_order(e), t)
    dy = S.rise * (1 - _enter(t, e))
    cx = W_OUT / 2
    _glow(ctx, lambda c: text(c, e["title"], cx, S.title.y + dy, S.title.size, S.title.font, skin.INK, a, 0, "c"),
          (cx - w, S.title.y - S.title.size + dy, cx + w, S.title.y + S.title.size / 2 + dy), S.glow.blur, S.glow.alpha)
    for si, (sd, place) in enumerate(zip(e["sides"], (S.left, S.right))):
        box = (place.x, place.y + dy, w, h)
        lift = min(1.0, sum(heat[(si, ii)][1] for ii in range(len(sd["items"]))))
        ctx.save()
        _rotate(ctx, box, place.rot)
        _card(ctx, box, a, lift)
        x0, y0 = box[0] + pad, box[1]
        text(ctx, sd["title"], x0, y0 + S.head.dy, S.head.size, S.head.font, skin.INK, a, 0, "l")
        ctx.new_path()
        ctx.rectangle(x0, y0 + S.head.rule_dy, inner, S.head.rule_w)
        ctx.set_source_rgba(*skin.INK, a)
        ctx.fill()
        yy = y0 + S.item.y0
        for ii, ls in enumerate(lay[si]):
            ia, hot = heat[(si, ii)]
            ia *= a
            text(ctx, f"{ii + 1:02d}", x0, yy, S.index.size, S.index.font, _mix(skin.INK3, skin.ACCENT_INK, hot), ia, 0, "l",
                 spacing=S.index.track * S.index.size)
            for j, ln in enumerate(ls):
                text(ctx, ln, x0 + S.item.dx, yy + j * S.item.line_gap, S.item.size, S.item.font, skin.INK, ia, 0, "l")
            yr = yy + (len(ls) - 1) * S.item.line_gap + S.item.rule_dy * scale
            ctx.new_path()
            ctx.rectangle(x0, yr - S.rule.w / 2, inner, S.rule.w)
            ctx.set_source_rgba(*skin.INK, S.rule.alpha * ia)
            ctx.fill()
            yy = yr + S.item.next_dy * scale
        text(ctx, sd["src"], x0, y0 + h - S.src.dy, S.src.size, S.src.font, skin.INK3, a, 0, "l", spacing=S.src.track * S.src.size)
        ctx.restore()
    B = S.vs  # noqa: N806
    skin.pill(ctx, (B.x - B.d / 2, B.y - B.d / 2 + dy, B.d, B.d), skin.INK, a, level=B.level)
    text(ctx, B.text, B.x, B.y + dy + B.size * B.baseline_k, B.size, B.font, WHITE, a, 0, "c", spacing=B.track * B.size)


# ───────────────────────────── piles
def _piles(ctx: cairo.Context, t: float, e: dict, a: float) -> None:
    P = V.piles  # noqa: N806
    Cd = P.card  # noqa: N806
    room = Cd.w - P.item.dx - P.item.pad_r
    lay: list[list[list[str]]] = []
    for sd in e["sides"]:
        n = len(sd["items"])
        if n > Cd.max:
            raise VersusOverflowError(f"[panel-overflow] versus piles {sd['title']!r} 카드 {n}장 > {Cd.max}, 항목을 줄인다")
        head_w = tw(ctx, sd["title"], P.head.size, P.head.font) + P.head.count_gap + tw(ctx, str(n), P.head.count_size, P.head.count_font)
        if head_w > P.rule.w:
            raise VersusOverflowError(f"[panel-overflow] versus piles 옆 제목 {sd['title']!r} — 폭 {head_w:.0f} > {P.rule.w}px, 문구를 줄인다")
        lay.append([_fits(ctx, it["text"], room, P.item.size, P.item.font, 2, "항목") for it in sd["items"]])
    most = max(len(ls) for ls in lay)
    pitch = Cd.pitch
    if most > 1:   # 두 더미 같은 간격(같은 무게) — 출처 위에 들어가게, 모자라면 겹쳐 쌓는다(min_pitch)
        pitch = min(pitch, (P.src.y - P.src.gap - Cd.h - Cd.y0) / (most - 1))
        if pitch < Cd.min_pitch:
            raise VersusOverflowError(f"[panel-overflow] versus piles 카드 {most}장 — 간격 {pitch:.0f} < {Cd.min_pitch}px, 항목을 줄인다")
    heat = _heat(_order(e), t)
    dy = P.rise * (1 - _enter(t, e))
    cx = W_OUT / 2
    H_ = P.head  # noqa: N806

    def head(c: cairo.Context) -> None:
        c.save()
        c.translate(0, dy)
        text(c, e["title"], cx, P.title.y, P.title.size, P.title.font, skin.INK, a, 0, "c")
        for si, sd in enumerate(e["sides"]):
            cnt = str(len(sd["items"]))
            tw_ = tw(c, sd["title"], H_.size, H_.font)
            if si == 0:
                text(c, sd["title"], H_.x_left, H_.y, H_.size, H_.font, skin.INK, a, 0, "l")
                text(c, cnt, H_.x_left + tw_ + H_.count_gap, H_.y, H_.count_size, H_.count_font, skin.INK3, a, 0, "l")
                rx = H_.x_left
                text(c, sd["src"], H_.x_left, P.src.y, P.src.size, P.src.font, skin.INK3, a, 0, "l", spacing=P.src.track * P.src.size)
            else:
                text(c, sd["title"], H_.x_right, H_.y, H_.size, H_.font, skin.INK, a, 0, "r")
                text(c, cnt, H_.x_right - tw_ - H_.count_gap, H_.y, H_.count_size, H_.count_font, skin.INK3, a, 0, "r")
                rx = H_.x_right - P.rule.w
                text(c, sd["src"], H_.x_right, P.src.y, P.src.size, P.src.font, skin.INK3, a, 0, "r", spacing=P.src.track * P.src.size)
            c.new_path()
            c.rectangle(rx, P.rule.y, P.rule.w, P.rule.h)
            c.set_source_rgba(*skin.INK, P.rule.alpha * a)
            c.fill()
        c.restore()

    _glow(ctx, head, (H_.x_left, P.title.y - P.title.size + dy, H_.x_right, P.src.y + P.src.size + dy), P.glow.blur, P.glow.alpha)
    for si, ls_side in enumerate(lay):
        sg = 1 if si == 0 else -1
        x_base = H_.x_left if si == 0 else H_.x_right - Cd.w
        for i, ls in enumerate(ls_side):
            raw, hot = heat[(si, i)]
            ia = raw * a
            if ia <= 0:
                continue
            box = (x_base + sg * i * Cd.shift, Cd.y0 + i * pitch - P.drop * (1 - raw) + dy, Cd.w, Cd.h)
            x, y = box[0], box[1]
            ctx.save()
            _rotate(ctx, box, sg * (Cd.rot0 + Cd.rot_step * i))
            _card(ctx, box, ia, hot)
            if hot > 0:
                ctx.new_path()
                ctx.rectangle(x, y, P.bar_w, Cd.h)
                ctx.set_source_rgba(*skin.ACCENT_SHAPE, hot * ia)
                ctx.fill()
            text(ctx, f"{i + 1:02d}", x + P.index.dx, y + P.index.dy, P.index.size, P.index.font, _mix(skin.INK3, skin.ACCENT_INK, hot),
                 ia, 0, "l", spacing=P.index.track * P.index.size)
            y1 = P.item.dy1 if len(ls) == 1 else P.item.dy2
            for j, ln in enumerate(ls):
                text(ctx, ln, x + P.item.dx, y + y1 + j * P.item.line_gap, P.item.size, P.item.font, skin.INK, ia, 0, "l")
            ctx.restore()


_DRAW = {"axis": _axis, "sheets": _sheets, "piles": _piles}


def draw(ctx: cairo.Context, t: float, e: dict, a: float, layout: str) -> None:
    """layout(axis·sheets·piles) 로 그린다 — 모르는 배치 = 오류(15 P10)."""
    if layout not in _DRAW:
        raise ValueError(f"versus layout {layout!r} — 등록된 배치 {sorted(_DRAW)} 밖")
    _DRAW[layout](ctx, t, e, a)


def overflow(e: dict, layout: str) -> list[str]:
    """렌더 전 넘침 판정(engine.checks.check_panel_overflow) — 렌더와 같은 함수를 버리는 면에 한 번 돌려 VersusOverflowError 를 문구로 돌려준다.
    마지막 시각(t1)·알파 1 = 모든 항목이 들어온 모습. 렌더 중에 처음 터지지 않게(연출이 렌더 전에 고친다)."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT))
    try:
        draw(ctx, float(e["t1"]), e, 1.0, layout)
    except VersusOverflowError as x:
        return [str(x)]
    return []

"""디자인 시스템 2b단계 — 인물·발언·기사 (v7.4.0 C0.0·UF-905·UF-907·UF-908, D917).

skin 무대(engine.skin.active)에서만 engine/quote.py·engine/layers/article.py 가 이 모듈로 그린다. 꺼지면 종전 그리기 그대로(바이트 동일).
- 발언(quote, pos center): 큰 인물 카드(직각 흰 카드 + 회색 타일에 곱하기로 얹은 초상 + 이름·직함·나라 칩) + 카드 없이 공간에 뜬 큰 글씨
  (여는 따옴표·줄·강조 막대·매체·날짜, 뒤에 흰 번짐 — 덮개·상자 없음, UF-907). 초상 없는 인용은 카드 없이 글씨만.
- 맞선 두 발언(pos upper·lower): 인물 알약(원형 초상 + 이름·직함) + 오른쪽 한두 줄 글씨 + 매체 줄.
- 기사(article): 직각 종이 카드(제호·날짜·두 줄 선·머리표·세리프 헤드라인·부제·꼬리) + 뒤에 겹친 종이 한 장. 프레스 사진은 카드 모서리에 걸친 타일.
글자가 자리를 넘으면 렌더 전 오류(QuoteError·ArticleOverflowError — 자름·말줄임 없음, 15 P6). 수치는 전부 rules skin.quote·person_card·person_pill·article(15 P3).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import cairo
from PIL import Image, ImageOps

from engine import skin, typography
from engine.assets import set_raster, surf_from_pil
from engine.context import RenderCtx
from engine.hud import date_box
from engine.layers.article import (DESCENT, SUB_Y, ArticleOverflowError, article_phase, article_text, press_credit_text,
                                   press_photo_credit_text, title_over)
from engine.media_registry import cached_registry
from engine.quote import QuoteError
from engine.style import ARTICLE, FONT, QUOTE, QUOTE_MAX_CHARS, SKIN, W_OUT, Color, hexc
from engine.timebase import ease_out
from engine.typography import text, tw, wrap

Box = tuple[float, float, float, float]    # x, y, 폭, 높이(설계 px)
Rect = tuple[float, float, float, float]   # x0, y0, x1, y1(설계 px)

Q, PC, PP, AR = SKIN.quote, SKIN.person_card, SKIN.person_pill, SKIN.article
WELL: Color = hexc(SKIN.surface.well)
TILE: tuple[Color, Color] = (hexc(PC.tile.grad[0]), hexc(PC.tile.grad[1]))
META = "media_meta"   # 매체·날짜·출처 메타 글자 역할(qa_checks.glyph_size_exempt)

_FONTS = (Q.font, Q.mark.font, Q.src.font, Q.src.date_font, PC.name.font, PC.role.font, PC.chip.font, PP.name.font, PP.role.font,
          AR.masthead.font, AR.date.font, AR.kicker.font, AR.headline.font, AR.sub.font, AR.footer.chip_font, AR.footer.host_font,
          AR.press.credit_font)
for _f in _FONTS:   # 없는 글꼴 키 = 시작 오류(P6·P10)
    if _f not in FONT:
        raise ValueError(f"skin 2b 글꼴 {_f!r} 가 engine.style.FONT 키가 아니다: {sorted(FONT)}")


# ------------------------------------------------------------------ 공용
def dots(d: str) -> str:
    """'2026.10.11'·'2026-10-31'·'2026. 10. 01' → '2026. 10. 11'(날짜 배지와 같은 '. ' 구분)."""
    return ". ".join(p.strip() for p in re.split(r"[.\-]", d) if p.strip())


def _tw(ctx: cairo.Context, s: str, size: float, name: str, track: float = 0.0) -> float:
    """text(spacing = track × size) 가 그리는 폭 — 한글 섞인 mono 는 자간 없이 그린다(typography.text 와 같은 규칙)."""
    if not track or (name in typography.MONO and typography.HANGUL.search(s)):
        return tw(ctx, s, size, name)
    return tw(ctx, s, size, name) + track * size * max(0, len(s) - 1)


def _ink(ctx: cairo.Context, s: str, size: float, name: str) -> tuple[float, float]:
    """기준선 기준 글자 잉크 (위, 아래) — 위는 음수."""
    typography.font(ctx, name, size)
    e = ctx.text_extents(s)
    return e.y_bearing, e.y_bearing + e.height


def _union(*rs: Optional[Rect]) -> Rect:
    v = [r for r in rs if r is not None]
    return min(r[0] for r in v), min(r[1] for r in v), max(r[2] for r in v), max(r[3] for r in v)


def _rect(b: Box) -> Rect:
    return b[0], b[1], b[0] + b[2], b[1] + b[3]


def _image(R: RenderCtx, key: str) -> Image.Image:  # noqa: N803
    R.assets.load_image(key)
    return R.assets.img[key]


def _cover_raster(R: RenderCtx, key: str, im: Image.Image, w: float, h: float) -> cairo.ImageSurface:  # noqa: N803
    """그림을 장치 px (w, h) × k 로 덮기 맞춤(가운데 자름) — 키·크기마다 한 번."""
    k = R.out.k
    size = (max(1, round(w * k)), max(1, round(h * k)))
    cache = R.cache.setdefault("skin_raster", {})
    if (key, size) not in cache:
        cache[(key, size)] = surf_from_pil(ImageOps.fit(im.convert("RGB"), size, Image.LANCZOS))
    return cache[(key, size)][0]


def _tile(ctx: cairo.Context, R: RenderCtx, e: dict, box: Box, cover: float, dy: float, a: float, circle: bool) -> None:  # noqa: N803
    """초상 타일 — 옅은 회색 대각 그라데이션 위에 흑백 초상을 곱하기로 얹는다(투명 → 흰색 먼저: 누끼 가장자리가 타일에 녹는다).
    초상 = 타일 덮기 × cover, 아래 맞춤 + dy, 타일로 자름. 콘티 판(badge_placeholder)은 초상 파일을 읽지 않는다(뱃지와 같은 규약).
    pid 없는 원형 타일 = 나라 국기(flag11, 덮기)."""
    x, y, w, h = box

    def path() -> None:
        ctx.new_path()
        if circle:
            ctx.arc(x + w / 2, y + h / 2, w / 2, 0, math.tau)
        else:
            ctx.rectangle(x, y, w, h)

    ctx.save()
    path()
    g = cairo.LinearGradient(x, y, x + w, y + h)
    g.add_color_stop_rgba(0, *TILE[0], a)
    g.add_color_stop_rgba(1, *TILE[1], a)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.clip()
    if R.cache.get("badge_placeholder") is None:
        if e.get("pid"):
            key = f"portrait:{e['pid']}"
            im = _image(R, key)
            sc = max(w / im.width, h / im.height) * cover
            dw, dh = im.width * sc, im.height * sc
            cache = R.cache.setdefault("skin_portrait", {})
            if key not in cache:   # 투명 → 흰색(곱하기에서 흰색 = 타일 색 그대로)
                cache[key] = Image.alpha_composite(Image.new("RGBA", im.size, "white"), im.convert("RGBA"))
            surf = _cover_raster(R, key, cache[key], dw, dh)
            set_raster(ctx, surf, R.out.k, x + w / 2 - dw / 2, y + h - dh + dy)
            ctx.set_operator(cairo.OPERATOR_MULTIPLY)
            ctx.paint_with_alpha(a)
        else:
            key = f"flag11:{e['flag']}"
            surf = _cover_raster(R, key, _image(R, key), w, h)
            set_raster(ctx, surf, R.out.k, x, y)
            ctx.paint_with_alpha(a)
    ctx.restore()


def _chip(ctx: cairo.Context, s: str, x: float, y: float, h: float, pad: float, size: float, name: str, track: float,
          baseline_k: float, a: float, role: Optional[str] = None) -> float:
    """well 알약 칩(높이 절반 반지름 — 알약만 둥글다, UF-908) + 글자(잉크 secondary). 폭을 돌려준다."""
    w = _tw(ctx, s, size, name, track) + 2 * pad
    skin.pill(ctx, (x, y, w, h), WELL, a)
    text(ctx, s, x + pad, y + h / 2 + size * baseline_k, size, name, skin.INK2, a, 0, "l", spacing=track * size, role=role)
    return w


# ------------------------------------------------------------------ 발언
@dataclass(frozen=True)
class QuoteLayout:
    pos: str
    card: Optional[Box]         # 인물 카드(center + pid)
    pill: Optional[Box]         # 인물 알약(upper·lower)
    x: float                    # 글자 왼쪽
    size: float
    lines: list[str]
    bases: list[float]
    name_size: float            # 카드·알약 이름 크기(카드는 넘치면 줄인 값)
    src_base: float
    src_size: float
    text_rect: Rect             # 글자 덩어리(따옴표·줄·막대·매체 줄, 번짐 여백 없음)
    box: Rect                   # 카드·알약 ∪ 글자 덩어리 — 예약 영역·checks subtitle_overlap


def _src_parts(e: dict) -> tuple[Optional[str], Optional[str]]:
    return (e["src"].upper() if e.get("src") else None), (dots(e["date"]) if e.get("date") else None)


def _src_width(ctx: cairo.Context, e: dict, size: float) -> float:
    src, date = _src_parts(e)
    w = _tw(ctx, src, size, Q.src.font, Q.src.track) if src else 0.0
    if date:
        w += (Q.src.gap if src else 0.0) + _tw(ctx, date, size, Q.src.date_font, Q.src.date_track)
    return w


def _fit_lines(ctx: cairo.Context, e: dict, room: float, tiers: list[tuple[float, int]]) -> tuple[float, list[str]]:
    for size, n in tiers:
        lines = wrap(ctx, e["text"], room, size, Q.font)
        if len(lines) <= n and all(tw(ctx, s, size, Q.font) <= room for s in lines):
            return size, lines
    size, n = tiers[-1]
    raise QuoteError(f"[quote-overflow] {e['speaker']} {e['text']!r} — {size:g}px {n}줄·폭 {room:.0f}px 를 넘는다(rules skin.quote), 문구를 줄인다")


def _card_name_size(ctx: cairo.Context, e: dict) -> float:
    """카드 이름 크기 — 칩 왼쪽까지 들어가게 step 씩 줄이고, min_size 밑이면 QuoteError(자름 없음). 직함도 같은 폭 안."""
    N, C = PC.name, PC.chip  # noqa: N806
    chip_w = _tw(ctx, e["flag"].upper(), C.size, C.font, C.track) + 2 * C.pad
    room = PC.box[2] - N.room - chip_w - N.chip_gap
    size = N.size
    while tw(ctx, e["speaker"], size, N.font) > room:
        size -= N.step
        if size < N.min_size:
            raise QuoteError(f"[quote-overflow] 인물 카드 이름 {e['speaker']!r} 이 {N.min_size:g}px 에도 폭 {room:.0f}px 를 넘는다(rules skin.person_card)")
    if e.get("role") and tw(ctx, e["role"], PC.role.size, PC.role.font) > room:
        raise QuoteError(f"[quote-overflow] 인물 카드 직함 {e['role']!r} 이 폭 {room:.0f}px 를 넘는다(rules skin.person_card)")
    return size


def _pill_box(ctx: cairo.Context, e: dict, pos: str) -> Box:
    """알약 — 폭은 rules person_pill.w, 이름·직함이 길면 그만큼 넓힌다(오른쪽 여백 = 높이 절반, 자름 없음)."""
    px, py = Q.pair.upper if pos == "upper" else Q.pair.lower
    need = max(tw(ctx, e["speaker"], PP.name.size, PP.name.font), tw(ctx, e["role"], PP.role.size, PP.role.font) if e.get("role") else 0.0)
    return px, py, max(PP.w, PP.name.dx + need + PP.h / 2), PP.h


def quote_layout(ctx: cairo.Context, e: dict) -> QuoteLayout:
    """skin 발언 배치(그리지 않음). 넘치면 QuoteError — 렌더 전 preflight(quote_lines)가 부른다."""
    pos = e.get("pos") or "center"
    card = pill = None
    name_size = PP.name.size
    if pos == "center":
        x = Q.text_x if e.get("pid") else Q.text_x_flag
        room = W_OUT - x - Q.right_margin
        size, lines = _fit_lines(ctx, e, room, [(s, len(b)) for s, b in Q.tiers])
        bases = list(Q.tiers[len(lines) - 1][1])
        if e.get("pid"):
            card = tuple(PC.box)
            name_size = _card_name_size(ctx, e)
        src_base, src_size = bases[-1] + Q.src.dy, Q.src.size
        mt, _ = _ink(ctx, "“", Q.mark.size, Q.mark.font)
        top = min(Q.mark.y + mt, bases[0] - size)
        left = x + min(Q.mark.dx, Q.bar.dx, Q.src.dx)
    else:
        pill = _pill_box(ctx, e, pos)
        x = pill[0] + pill[2] + Q.pair.gap
        room = W_OUT - x - Q.right_margin
        size, lines = _fit_lines(ctx, e, room, list(Q.pair.tiers))
        cy = pill[1] + pill[3] / 2
        b0 = cy - (len(lines) - 1) * Q.pair.line_h / 2 + size * Q.pair.baseline_k
        bases = [b0 + i * Q.pair.line_h for i in range(len(lines))]
        src_base, src_size = bases[-1] + Q.pair.src_dy, Q.pair.src_size
        top = bases[0] - size
        left = x + min(0.0, Q.src.dx)
    sw = _src_width(ctx, e, src_size)
    if x + Q.src.dx + sw > W_OUT - Q.right_margin:
        raise QuoteError(f"[quote-overflow] {e['speaker']} 매체·날짜 줄이 폭을 넘는다(rules skin.quote.src)")
    right = max([x + tw(ctx, s, size, Q.font) for s in lines] + [x + Q.src.dx + sw])
    _, desc = _ink(ctx, "Ag", src_size, Q.src.font)
    text_rect = (left, top, right, src_base + desc)
    shape = _rect(card) if card is not None else _rect(pill) if pill is not None else None
    return QuoteLayout(pos=pos, card=card, pill=pill, x=x, size=size, lines=lines, bases=bases, name_size=name_size,
                       src_base=src_base, src_size=src_size, text_rect=text_rect, box=_union(shape, text_rect))


def _draw_src(c: cairo.Context, e: dict, x: float, y: float, size: float, a: float) -> None:
    src, date = _src_parts(e)
    if src:
        x += text(c, src, x, y, size, Q.src.font, skin.INK2, a, 0, "l", spacing=Q.src.track * size, role=META) + Q.src.gap
    if date:
        text(c, date, x, y, size, Q.src.date_font, skin.INK3, a, 0, "l", spacing=Q.src.date_track * size, role=META)


def _quote_text(c: cairo.Context, e: dict, L: QuoteLayout, a: float) -> None:  # noqa: N803
    if L.pos == "center":
        text(c, "“", L.x + Q.mark.dx, Q.mark.y, Q.mark.size, Q.mark.font, skin.ACCENT_SHAPE, a, 0)
    for s, b in zip(L.lines, L.bases):
        text(c, s, L.x, b, L.size, Q.font, skin.INK, a, 0)
    if L.pos == "center":
        c.rectangle(L.x + Q.bar.dx, L.bases[-1] + Q.bar.dy, Q.bar.w, Q.bar.h)
        c.set_source_rgba(*skin.ACCENT_SHAPE, a)
        c.fill()
    _draw_src(c, e, L.x + Q.src.dx, L.src_base, L.src_size, a)


def _person_card(ctx: cairo.Context, R: RenderCtx, e: dict, L: QuoteLayout, a: float) -> None:  # noqa: N803
    x, y, w, h = L.card
    skin.surface(ctx, L.card, a, PC.level)
    T = PC.tile  # noqa: N806
    _tile(ctx, R, e, (x + T.inset, y + T.inset, w - 2 * T.inset, T.h), T.cover, T.dy, a, circle=False)
    text(ctx, e["speaker"], x + PC.name.dx, y + PC.name.dy, L.name_size, PC.name.font, skin.INK, a, 0)
    if e.get("role"):
        text(ctx, e["role"], x + PC.role.dx, y + PC.role.dy, PC.role.size, PC.role.font, skin.INK2, a, 0)
    C = PC.chip  # noqa: N806
    code = e["flag"].upper()
    cw = _tw(ctx, code, C.size, C.font, C.track) + 2 * C.pad
    _chip(ctx, code, x + w - C.right - cw, y + C.dy, C.h, C.pad, C.size, C.font, C.track, C.baseline_k, a)


def _person_pill(ctx: cairo.Context, R: RenderCtx, e: dict, L: QuoteLayout, a: float) -> None:  # noqa: N803
    x, y, w, h = L.pill
    skin.surface(ctx, L.pill, a, PP.level, radius=h / 2)
    P = PP.portrait  # noqa: N806
    _tile(ctx, R, e, (x + P.inset, y + (h - P.d) / 2, P.d, P.d), P.cover, P.dy, a, circle=True)
    text(ctx, e["speaker"], x + PP.name.dx, y + PP.name.dy, PP.name.size, PP.name.font, skin.INK, a, 0)
    if e.get("role"):
        text(ctx, e["role"], x + PP.role.dx, y + PP.role.dy, PP.role.size, PP.role.font, skin.INK2, a, 0)


def draw_quote(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    """덮개 없음(UF-907). 카드·알약과 글씨가 함께 quote_center.fade_sec 페이드 + rise_px 떠오름."""
    L = quote_layout(ctx, e)  # noqa: N806
    dy = (1 - ease_out(min(1.0, (t - e["t0"]) / QUOTE.fade_sec))) * QUOTE.rise_px
    ctx.save()
    ctx.translate(0, dy)
    if L.card is not None or L.pill is not None:   # 카드·알약은 한 물체로 페이드(곱하기 초상이 반투명 카드 밖 무대를 어둡게 하지 않게)
        ctx.push_group()
        (_person_card if L.card is not None else _person_pill)(ctx, R, e, L, 1.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    skin.glow(ctx, lambda c: _quote_text(c, e, L, a), L.text_rect, blur=Q.glow_blur, alpha=Q.glow_alpha * a)
    ctx.restore()


# ------------------------------------------------------------------ 기사
@dataclass(frozen=True)
class SkinArticleLayout:
    box: Box                    # 앞 종이 카드
    pub: str
    date: str
    headline: list[str]
    head_size: float
    head_base: list[float]
    sub: list[str]
    sub_base: list[float]
    translated: bool
    host: Optional[str]         # 레지스트리 url 의 호스트(대문자, www 뺌) — url 없으면 None
    credit: Optional[str]       # 프레스 사진 출처 줄(보도 인용 B 또는 공식 사진 A) — 없으면 None
    press: Optional[Box]        # 프레스 사진 타일
    rect: Rect                  # 카드 ∪ 프레스 타일·출처 줄 — 예약 영역·검사


def _host(mid: str) -> Optional[str]:
    url = getattr(cached_registry()[mid], "url", None)
    if not url:
        return None
    h = urlparse(url).netloc
    return (h[len("www."):] if h.startswith("www.") else h).upper() or None


def skin_article_layout(ctx: cairo.Context, e: dict) -> SkinArticleLayout:
    """종이 카드 배치(그리지 않음). 헤드라인·부제 줄 상한은 layout_480p.article_card 그대로, 넘치면 ArticleOverflowError(자름 없음)."""
    A, H, S = ARTICLE, AR.headline, AR.sub  # noqa: N806
    d = article_text(e)
    translated = not d["original"]
    if d["original"] and len(d["original"]) > QUOTE_MAX_CHARS:
        raise ArticleOverflowError(f"기사 {e['mid']}: 원문 헤드라인 {len(d['original'])}자 > 인용 상한 {QUOTE_MAX_CHARS}(verification.quote_max_chars)")
    head_src = d["headline"] if translated else (f"“{d['original']}”" if A.headline.quotes else d["original"])
    sub_src = d["sub"] if translated else d["headline"]
    x, w = AR.x, AR.w
    x0, x1 = x + AR.pad, x + w - AR.pad
    room = x1 - x0
    size, lh = H.size, H.line_h
    head = wrap(ctx, head_src, room, size, H.font)
    if len(head) > H.shrink_over and A.headline.max_lines > H.shrink_over:
        size, lh = H.small_size, H.small_line_h
        head = wrap(ctx, head_src, room, size, H.font)
    sub = wrap(ctx, sub_src, room - S.dx, S.size, S.font) if sub_src else []
    hb = [H.dy + i * lh for i in range(len(head))]   # 카드 위 끝 기준(높이를 정한 뒤 옮긴다)
    sb0 = hb[-1] + lh + S.gap + S.text_dy
    sb = [sb0 + i * S.line_h for i in range(len(sub))]
    bottom = (sb[-1] + S.size * DESCENT) if sb else hb[-1] + size * DESCENT
    need = bottom + AR.footer_gap + AR.footer.rule_dy   # 내용 + 빈 띠 없는 꼬리
    h = max(AR.min_h, need)
    over = [f"{what} {len(ls)}줄 > {mx}" for what, ls, mx in (("헤드라인", head, A.headline.max_lines), ("부제", sub, A.sub.max_lines))
            if len(ls) > mx]
    over += [f"줄 폭 > {room:.0f}px: {s!r}" for s in head if tw(ctx, s, size, H.font) > room]
    if not over and h > AR.max_h:
        over.append(f"카드 높이 {need:.0f} > {AR.max_h:g}")
    if over:
        raise ArticleOverflowError(f"기사 {e['mid']}({d['pub']}): {', '.join(over)} — 레지스트리 문구를 줄인다(rules skin.article·article_card)")
    top = date_box()[3]
    y = top + (SUB_Y - top - h) / 2   # 날짜 배지 아래 ~ 자막 구역 위 사이 가운데
    hb = [y + v for v in hb]
    sb = [y + v for v in sb]
    box = (x, y, w, h)
    credit = press_credit_text(e, d["pub"]) or press_photo_credit_text(e)
    P = AR.press  # noqa: N806
    press = (x + w - P.dx, y + h - P.dy, P.w, P.h) if e.get("press") else None
    cr = None
    if press is not None and credit:
        cw = tw(ctx, credit, P.credit_size, P.credit_font)
        cb = press[1] + press[3] + P.credit_dy
        cr = (press[0], press[1] + press[3], press[0] + cw, cb + P.credit_size * DESCENT)
        if cr[2] > W_OUT:
            raise ArticleOverflowError(f"기사 {e['mid']}: 프레스 사진 출처 줄이 화면 오른쪽을 넘는다 — {credit!r}(rules skin.article.press)")
    return SkinArticleLayout(box=box, pub=d["pub"], date=dots(d["date"]), headline=head, head_size=size, head_base=hb,
                             sub=sub, sub_base=sb, translated=translated, host=_host(e["mid"]), credit=credit if press else None,
                             press=press, rect=_union(_rect(box), _rect(press) if press else None, cr))


def _article_content(ctx: cairo.Context, L: SkinArticleLayout, a: float) -> None:  # noqa: N803
    x, y, w, h = L.box
    x0, x1 = x + AR.pad, x + w - AR.pad
    M, D, RL, K, H, S, F = AR.masthead, AR.date, AR.rule, AR.kicker, AR.headline, AR.sub, AR.footer  # noqa: N806
    text(ctx, L.pub, x0, y + M.dy, M.size, M.font, skin.INK, a, 0)
    text(ctx, L.date, x1, y + D.dy, D.size, D.font, skin.INK3, a, 0, "r", spacing=D.track * D.size, role=META)
    ctx.set_source_rgba(*skin.INK, a)
    ctx.rectangle(x0, y + RL.dy, x1 - x0, RL.h)
    ctx.fill()
    ctx.set_source_rgba(*skin.INK, RL.thin_alpha * a)
    ctx.rectangle(x0, y + RL.thin_dy, x1 - x0, RL.thin_h)
    ctx.fill()
    text(ctx, K.text, x0, y + K.dy, K.size, K.font, skin.ACCENT_INK, a, 0, "l", spacing=K.track * K.size, role=META)
    for s, b in zip(L.headline, L.head_base):
        text(ctx, s, x0, b, L.head_size, H.font, skin.INK, a, 0)
    if L.sub:
        top = L.sub_base[0] - S.text_dy + S.bar_dy
        ctx.set_source_rgba(*skin.ACCENT_SHAPE, a)
        ctx.rectangle(x0, top, S.bar_w, S.bar_h + (len(L.sub) - 1) * S.line_h)
        ctx.fill()
        for s, b in zip(L.sub, L.sub_base):
            text(ctx, s, x0 + S.dx, b, S.size, S.font, skin.INK, a, 0)
    fy = y + h - F.rule_dy
    ctx.new_path()
    ctx.move_to(x0, fy)
    ctx.line_to(x1, fy)
    ctx.set_source_rgba(*skin.INK, F.rule_alpha * a)
    ctx.set_line_width(F.rule_w)
    ctx.stroke()
    if L.translated:
        _chip(ctx, ARTICLE.source.translated_note, x0, y + h - F.chip_dy, F.chip_h, F.chip_pad, F.chip_size, F.chip_font, 0.0,
              F.chip_baseline_k, a, role=META)
    if L.host:
        text(ctx, L.host, x1, y + h - F.host_dy, F.host_size, F.host_font, skin.INK3, a, 0, "r", spacing=F.host_track * F.host_size, role=META)


def _press_tile(ctx: cairo.Context, R: RenderCtx, e: dict, L: SkinArticleLayout, a: float) -> None:  # noqa: N803
    P = AR.press  # noqa: N806
    bx, by, bw, bh = L.press
    skin.soft_shadow(ctx, L.press, 0, getattr(SKIN.shadow, P.level), a)
    m = R.assets.media_assets[e["press"]]
    key = f"media:{m.file}"
    surf = _cover_raster(R, key, _image(R, key), bw, bh)
    ctx.save()
    ctx.rectangle(bx, by, bw, bh)
    ctx.clip()
    set_raster(ctx, surf, R.out.k, bx, by)
    ctx.paint_with_alpha(a)
    ctx.restore()


def _press_credit(ctx: cairo.Context, L: SkinArticleLayout, a: float) -> None:  # noqa: N803
    """프레스 사진 출처 줄(press_credit_text·press_photo_credit_text 그대로 — checks press_credit 대조) — 타일 바로 아래, 흰 번짐."""
    P = AR.press  # noqa: N806
    bx, by, bw, bh = L.press
    if L.credit:
        base = by + bh + P.credit_dy
        rect = (bx, base - P.credit_size, bx + tw(ctx, L.credit, P.credit_size, P.credit_font), base + P.credit_size * DESCENT)

        def draw(c: cairo.Context) -> None:
            text(c, L.credit, bx, base, P.credit_size, P.credit_font, skin.INK3, a, 0, role=META)

        skin.glow(ctx, draw, rect, alpha=SKIN.subtitle.glow_alpha * a)


def draw_article(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    """종이 카드 — 카드·뒤 종이·프레스 타일 = article_phase 첫 알파(overlay_fade_sec 동안 rise_px 떠오름), 글자 = 두 번째 알파.
    제목 카드가 위에 뜨면(title_over) 카드 전체 알파 × ((1 − over) + over × title_sink.alpha) — 블러 없음."""
    pa, ta = article_phase(t, e)
    over = title_over(R, t)
    sink = (1 - over) + over * ARTICLE.title_sink.alpha
    ca, ta = pa * sink, ta * sink
    L = skin_article_layout(ctx, e)  # noqa: N806
    x, y, w, h = L.box
    B = AR.back  # noqa: N806
    rise = (1 - ease_out(min(1.0, (t - e["t0"]) / ARTICLE.overlay_fade_sec))) * AR.rise_px
    ctx.save()
    ctx.translate(0, rise)
    ctx.push_group()   # 종이 두 장·프레스 타일 = 한 물체로 페이드(앞 종이가 반투명일 때 뒤 종이 모서리가 비치지 않게)
    cx, cy = x + w / 2, y + h / 2
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(B.rot_deg * math.pi / 180)   # 도 → 라디안(180 = 반 바퀴, 각도 정의)
    ctx.translate(-cx, -cy)
    skin.surface(ctx, (x + B.dx, y + B.dy, w, h), 1.0, B.level, fill=hexc(B.fill))
    ctx.restore()
    skin.surface(ctx, L.box, 1.0, AR.level)
    if L.press is not None:
        _press_tile(ctx, R, e, L, 1.0)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(ca)
    if ta > 0:
        _article_content(ctx, L, ta)
    if L.credit and L.press is not None:
        _press_credit(ctx, L, ca)
    ctx.restore()


__all__ = ["QuoteLayout", "SkinArticleLayout", "dots", "draw_article", "draw_quote", "quote_layout", "skin_article_layout"]

"""기사 프레스 규약 v2 (v5.1.0, back_and_forth D-0121 §C·D-0126 Q5·Q6 A, 사용자 결정 D107).

옛 오른쪽·가운데 기사 카드(v4.8.0 D-0101 §2)를 대체한다(P2 — 옛 경로 삭제).
1. 프레스 사진 단독(press_lead_sec): 이벤트 `press` = 미디어 레지스트리 kind photo·rights_clear 공식 사진만(기사 자체 사진 금지).
   없으면 지금까지 그린 무대를 블러(article_card.press_fallback.blur_px)·dim 한 판(v5.2.0 D-0129 §A — 배경 사진 값과 분리) — 사진을 지어내지 않는다(G4-10·P6, provenance article.press none).
2. 덮개(theme overlay × overlay_alpha) + 글자 블록: 왼쪽 세로 선 · 세리프 헤드라인 · 산세리프 부제 · source 줄. 세로 가운데(자막 구역 위)·왼쪽 정렬.
   헤드라인 = 레지스트리 headline_original(원문 언어, 인용 부호) — 없으면 한국어 번역 headline(부호 없음) + source 줄 "헤드라인 번역"(Q6 A).
3. 퇴장 = 덮개·글자·사진 페이드(overlay_fade_sec).
글자·수치는 코드가 렌더한다(G4-10). 수치는 전부 `rules layout_480p.article_card`(코드 리터럴 0).
"""

from __future__ import annotations

from dataclasses import dataclass

import cairo
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from engine.assets import surf_from_pil
from engine.context import RenderCtx
from engine.credits import RightsError
from engine.media_registry import cached_registry
from engine.style import ARTICLE, QUOTE_MAX_CHARS, W_OUT
from engine.timebase import window
from engine.typography import text, wrap
from rules import load_rules

SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from   # 글자 블록은 자막 구역 위 공간의 세로 가운데
DESCENT = 0.25   # 글자 아래 끝 = 기준선 + 크기 × DESCENT(측정 근사 — 블록 높이·세로 선 끝)


class ArticleOverflowError(ValueError):
    """헤드라인·부제 줄 수 초과, 원문 인용 상한 초과(v5.1.0 D-0121 §C — 조용한 잘림 금지, 15 P6)."""


@dataclass(frozen=True)
class ArticleLayout:
    x: float                   # 세로 선 왼쪽
    text_x: float              # 글자 왼쪽
    top: float                 # 블록 위 끝
    headline: list[str]
    sub: list[str]
    source: str
    hl_base: list[float]       # 헤드라인 줄 기준선
    sub_base: list[float]
    source_base: float
    rule: tuple[float, float]  # 세로 선 (위, 아래)
    box: tuple[float, float, float, float]   # 블록 (x0, y0, x1, y1)
    translated: bool


def article_text(e: dict) -> dict:
    """기사 문구 — 레지스트리(kind article)에서만(D-0036). original = 원문 헤드라인(없으면 None)."""
    m = cached_registry()[e["mid"]]
    return dict(pub=m.caption, date=m.date, headline=m.headline, sub=m.sub, original=m.headline_original)


def source_date(iso: str) -> str:
    """'2026-09-24' → '2026.9.24'(참고 스크린샷 형식)."""
    y, m, d = iso.split("-")[:3]
    return f"{int(y)}.{int(m)}.{int(d)}"


def article_layout(ctx: cairo.Context, e: dict) -> ArticleLayout:
    """글자 블록 배치(그리지 않음). 줄 수·인용 상한 초과 = ArticleOverflowError(렌더 전 preflight 가 부른다)."""
    A = ARTICLE  # noqa: N806
    d = article_text(e)
    translated = not d["original"]
    if d["original"] and len(d["original"]) > QUOTE_MAX_CHARS:
        raise ArticleOverflowError(f"기사 {e['mid']}: 원문 헤드라인 {len(d['original'])}자 > 인용 상한 {QUOTE_MAX_CHARS}(verification.quote_max_chars)")
    head = d["headline"] if translated else (f"“{d['original']}”" if A.headline.quotes else d["original"])
    sub_src = d["sub"] if translated else d["headline"]
    x = W_OUT * A.x_left_ratio
    text_x = x + A.rule.w + A.rule.gap
    tw_max = W_OUT * A.max_w_ratio - A.rule.w - A.rule.gap
    hl = wrap(ctx, head, tw_max, A.headline.size, "serif")
    sub = wrap(ctx, sub_src, tw_max, A.sub.size, "sans") if sub_src else []
    over = [f"{what} {len(ls)}줄 > {mx}" for what, ls, mx in (("헤드라인", hl, A.headline.max_lines), ("부제", sub, A.sub.max_lines))
            if len(ls) > mx]
    if over:
        raise ArticleOverflowError(f"기사 {e['mid']}({d['pub']}): {', '.join(over)} — 레지스트리 문구를 줄인다(rules article_card)")
    src = A.source.format.replace("{publisher}", d["pub"]).replace("{date}", source_date(d["date"]))
    if translated:
        src += f" · {A.source.translated_note}"
    # 상대 기준선(위 = 0)
    hb = [A.headline.size + i * A.headline.gap for i in range(len(hl))]
    y = hb[-1] + A.headline.size * DESCENT
    rule = (0.0, y)
    sb = [y + A.sub.lead + A.sub.size + i * A.sub.gap for i in range(len(sub))]
    y = (sb[-1] + A.sub.size * DESCENT) if sb else y
    srcb = y + A.source.lead + A.source.size
    h = srcb + A.source.size * DESCENT
    top = (SUB_Y - h) / 2
    return ArticleLayout(x=x, text_x=text_x, top=top, headline=hl, sub=sub, source=src, hl_base=[top + v for v in hb],
                         sub_base=[top + v for v in sb], source_base=top + srcb, rule=(top + rule[0], top + rule[1]),
                         box=(x, top, x + W_OUT * A.max_w_ratio, top + h), translated=translated)


def article_box(ctx: cairo.Context, e: dict) -> tuple[float, float, float, float]:
    """글자 블록 제자리 상자(x0, y0, x1, y1) — 예약 영역·검사가 같이 쓴다."""
    return article_layout(ctx, e).box


def validate_press(e: dict, assets: dict | None = None):  # noqa: ANN201 — MediaAsset | None
    """프레스 사진 권리 게이트 — 없으면 None(블러 무대 폴백). 있으면 레지스트리 photo·rights_clear·파일(기사 자체 사진 금지 — 레지스트리 밖)."""
    pid = e.get("press")
    if not pid:
        return None
    reg = assets if assets is not None else cached_registry()
    if pid not in reg:
        raise RightsError(f"프레스 사진이 미디어 레지스트리에 없음: press={pid!r} (article {e.get('mid')}) — 권리 기록 있는 공식 사진만(C9)")
    a = reg[pid]
    if a.kind != "photo" or a.rights_status != "rights_clear" or not a.file:
        raise RightsError(f"프레스 사진 {pid}: kind {a.kind}·권리 {a.rights_status}·파일 {a.file!r} — photo·rights_clear·파일만(C9)")
    return a


def article_phase(t: float, e: dict) -> tuple[float, float]:
    """(사진·블러 판 알파, 덮개·글자 알파)."""
    A = ARTICLE  # noqa: N806
    lead = e["t0"] + A.press_lead_sec
    return (window(t, e["t0"], e["t1"], A.overlay_fade_sec, A.overlay_fade_sec),
            window(t, lead, e["t1"], A.overlay_fade_sec, A.overlay_fade_sec) if e["t1"] > lead else 0.0)


def _paint_device(ctx: cairo.Context, surf: cairo.ImageSurface, a: float) -> None:
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_press(ctx: cairo.Context, R: RenderCtx, e: dict, a: float) -> None:  # noqa: N803
    """프레스 사진(화면 덮기, 선명) 또는 블러 무대 폴백(지금 표면을 블러·dim)."""
    k = R.out.k
    tgt = ctx.get_target()
    W, H = tgt.get_width(), tgt.get_height()  # noqa: N806
    if e.get("press"):
        cache = R.cache.setdefault("press_surf", {})
        if e["press"] not in cache:
            m = R.assets.media_assets[e["press"]]
            R.assets.load_image(f"media:{m.file}")
            cache[e["press"]] = surf_from_pil(ImageOps.fit(R.assets.img[f"media:{m.file}"].convert("RGB"), (W, H)))
        _paint_device(ctx, cache[e["press"]][0], a)
        return
    tgt.flush()
    arr = np.ndarray((H, W, 4), np.uint8, buffer=tgt.get_data()).copy()
    im = Image.fromarray(arr[..., [2, 1, 0]])
    im = im.filter(ImageFilter.GaussianBlur(ARTICLE.press_fallback.blur_px * k))
    im = ImageEnhance.Brightness(im).enhance(1 - ARTICLE.press_fallback.dim)
    surf, _buf = surf_from_pil(im)
    _paint_device(ctx, surf, a)


def draw_article_text(ctx: cairo.Context, e: dict, a: float) -> None:
    """덮개 + 세로 선 + 헤드라인·부제·source 줄."""
    A = ARTICLE  # noqa: N806
    th = A.themes[e.get("theme") or A.theme_default]
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(*th.overlay, A.overlay_alpha * a)
    ctx.paint()
    ctx.restore()
    L = article_layout(ctx, e)  # noqa: N806
    ctx.set_source_rgba(*th.rule, a)
    ctx.rectangle(L.x, L.rule[0], A.rule.w, L.rule[1] - L.rule[0])
    ctx.fill()
    for ln, y in zip(L.headline, L.hl_base):
        text(ctx, ln, L.text_x, y, A.headline.size, "serif", th.ink, a, 0, "l")
    for ln, y in zip(L.sub, L.sub_base):
        text(ctx, ln, L.text_x, y, A.sub.size, "sans", th.ink, a, 0, "l")
    text(ctx, L.source, L.text_x, L.source_base, A.source.size, "sans", th.muted, a, 0, "l")


def draw_article(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    pa, ta = article_phase(t, e)
    if pa <= 0.01:
        return
    draw_press(ctx, R, e, pa)
    if ta > 0.01:
        draw_article_text(ctx, e, ta)


def article_usage(events: list[dict]) -> list[dict]:
    """provenance article[] — 매체·프레스 사진(없으면 none)·테마·헤드라인(원문|번역)."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    return [{"mid": e["mid"], "t0": round(e["t0"], 2), "press": e.get("press") or "none", "theme": e.get("theme") or ARTICLE.theme_default,
             "headline": "translated" if article_layout(ctx, e).translated else "original"} for e in events if e["type"] == "article"]


__all__ = ["ArticleLayout", "ArticleOverflowError", "article_box", "article_layout", "article_phase", "article_text", "article_usage",
           "draw_article", "draw_article_text", "draw_press", "source_date", "validate_press"]

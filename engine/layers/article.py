"""기사 프레스 규약 v2 (v5.1.0, back_and_forth D-0121 §C·D-0126 Q5·Q6 A, 사용자 결정 D107).

옛 오른쪽·가운데 기사 카드(v4.8.0 D-0101 §2)를 대체한다(P2 — 옛 경로 삭제).
1. 프레스 사진 단독(press_lead_sec): 이벤트 `press` = 미디어 레지스트리 kind photo·rights_clear 공식 사진만(기사 자체 사진 금지).
   없으면 지금까지 그린 무대를 블러(article_card.press_fallback.blur_px)·dim 한 판(v5.2.0 D-0129 §A — 배경 사진 값과 분리) — 사진을 지어내지 않는다(G4-10·P6, provenance article.press none).
2. 덮개(theme overlay × overlay_alpha) + 글자 블록: 왼쪽 세로 선 · 세리프 헤드라인 · 산세리프 부제 · source 줄. 세로 가운데(자막 구역 위)·왼쪽 정렬.
   헤드라인 = 레지스트리 headline_original(원문 언어, 인용 부호) — 없으면 한국어 번역 headline(부호 없음) + source 줄 "헤드라인 번역"(Q6 A).
3. 퇴장 = 덮개·글자·사진 페이드(overlay_fade_sec).
4. v5.21.0 D-0177(사용자 결정 D172) — 보도 인용(B): 인용한 기사에 실린 통신사 사진(레지스트리 photo·restricted·press_of = 이 기사·
   사용자 예외 press_quote)은 **그 기사 카드의 프레스 칸에서만** 쓴다. 카드 안 source 줄 아래 작은 줄 "사진: <통신사> via <매체>".
글자·수치는 코드가 렌더한다(G4-10). 수치는 전부 `rules layout_480p.article_card`(코드 리터럴 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    credit: Optional[str] = None           # v5.21.0 — 보도 인용(B) 사진 크레딧 줄(없으면 그리지 않는다)
    credit_base: Optional[float] = None


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
    credit = press_credit_text(e, d["pub"])
    if credit is not None and len(wrap(ctx, credit, tw_max, A.press_credit.size, "sans")) > 1:
        raise ArticleOverflowError(f"기사 {e['mid']}: 보도 인용 크레딧 줄이 한 줄을 넘는다 — {credit!r}(rules article_card.press_credit)")
    # 상대 기준선(위 = 0)
    hb = [A.headline.size + i * A.headline.gap for i in range(len(hl))]
    y = hb[-1] + A.headline.size * DESCENT
    rule = (0.0, y)
    sb = [y + A.sub.lead + A.sub.size + i * A.sub.gap for i in range(len(sub))]
    y = (sb[-1] + A.sub.size * DESCENT) if sb else y
    srcb = y + A.source.lead + A.source.size
    h = srcb + A.source.size * DESCENT
    crb = None
    if credit is not None:
        crb = h + A.press_credit.lead + A.press_credit.size
        h = crb + A.press_credit.size * DESCENT
    top = (SUB_Y - h) / 2
    return ArticleLayout(x=x, text_x=text_x, top=top, headline=hl, sub=sub, source=src, hl_base=[top + v for v in hb],
                         sub_base=[top + v for v in sb], source_base=top + srcb, rule=(top + rule[0], top + rule[1]),
                         box=(x, top, x + W_OUT * A.max_w_ratio, top + h), translated=translated,
                         credit=credit, credit_base=None if crb is None else top + crb)


def press_credit_text(e: dict, publisher: str) -> Optional[str]:
    """보도 인용(B) 사진이면 카드 안 크레딧 줄(rules article_card.press_credit.format), 아니면 None(A 공식 사진·블러 폴백은 줄 없음)."""
    pa = cached_registry().get(e.get("press") or "")
    if pa is None or getattr(pa, "press_of", None) is None:
        return None
    return ARTICLE.press_credit.format.replace("{agency}", pa.agency or "").replace("{publisher}", publisher)


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
    if getattr(a, "press_of", None) is not None:   # v5.21.0 D-0177 — 보도 인용(B): 그 사진이 실린 기사의 카드에서만, 범주 예외 press_quote
        from schemas.emblem_models import press_exception_ok  # noqa: PLC0415

        if a.press_of != e.get("mid"):
            raise RightsError(f"보도 인용 사진 {pid} 은 기사 {a.press_of} 의 카드에서만 쓴다(지금 article {e.get('mid')}) — 사용자 결정 D172")
        if a.kind != "photo" or not a.file or not press_exception_ok(a.user_exception):
            raise RightsError(f"보도 인용 사진 {pid}: kind {a.kind}·파일 {a.file!r}·예외 {a.user_exception!r} — photo·파일·press_quote 예외만(D-0177)")
        return a
    if a.kind != "photo" or a.rights_status != "rights_clear" or not a.file:
        raise RightsError(f"프레스 사진 {pid}: kind {a.kind}·권리 {a.rights_status}·파일 {a.file!r} — photo·rights_clear·파일만(C9)")
    return a


def article_full_span(e: dict) -> tuple[float, float]:
    """글자(덮개) 완전 불투명 구간 — article_phase 두 번째 알파가 1 인 구간(v5.21.10 D-0191 §1-2, 검사 card_exposure)."""
    A = ARTICLE  # noqa: N806
    return e["t0"] + A.press_lead_sec + A.overlay_fade_sec, e["t1"] - A.overlay_fade_sec


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


def fallback_gain(im: Image.Image) -> float:
    """블러 무대 밝기 배율 — 1 − dim, 단 결과 평균 밝기(Rec.709)가 press_fallback.max_luma 를 넘으면 그 상한에 맞춘다
    (v5.21.12 D-0193 — 지도 테마와 무관하게 같은 어두운 무대)."""
    F = ARTICLE.press_fallback  # noqa: N806
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    m = float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())
    g = 1 - F.dim
    return min(g, F.max_luma / m) if m * g > F.max_luma else g


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
    im = ImageEnhance.Brightness(im).enhance(fallback_gain(im))
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
    if L.credit is not None:
        text(ctx, L.credit, L.text_x, L.credit_base, A.press_credit.size, "sans", th.muted, a, 0, "l")


def draw_article(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    pa, ta = article_phase(t, e)
    if pa <= 0.01:
        return
    draw_press(ctx, R, e, pa)
    over = title_over(R, t)   # v6.0.2 D-0216 UF-98 — 제목 카드가 이 기사 위에 뜨면 기사 글자는 흐리게(블러·불투명도) 제목 뒤에 남는다
    sharp, soft = ta * (1.0 - over), ta * over * ARTICLE.title_sink.alpha
    if sharp > 0.01:
        draw_article_text(ctx, e, sharp)
    if soft > 0.01:
        _paint_device(ctx, _sunk_text(ctx, R, e), soft)


def _sunk_text(ctx: cairo.Context, R: RenderCtx, e: dict) -> cairo.ImageSurface:  # noqa: N803
    """기사 글자를 장치 해상도 표면에 그리고 title_sink.blur_px 로 블러(이벤트마다 한 번 — 글자는 이 구간에서 움직이지 않는다)."""
    cache = R.cache.setdefault("article_sunk", {})
    key = id(e)
    if key not in cache:
        tgt = ctx.get_target()
        W, H = tgt.get_width(), tgt.get_height()  # noqa: N806
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c2 = cairo.Context(surf)
        c2.set_matrix(ctx.get_matrix())
        draw_article_text(c2, e, 1.0)
        surf.flush()
        arr = np.ndarray((H, W, 4), np.uint8, buffer=surf.get_data()).copy()   # 미리 곱한 BGRA — 블러도 미리 곱한 채로(가장자리 색 번짐 없음)
        im = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(ARTICLE.title_sink.blur_px * R.out.k))
        buf = bytearray(np.asarray(im).tobytes())
        cache[key] = (cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H, W * 4), buf)
    return cache[key][0]


def title_over(R: RenderCtx, t: float) -> float:  # noqa: N803
    """기사 글자를 가라앉힐 정도 — 제목 카드가 나타나기 시작하면 0.7초(fullcards 페이드)에 걸쳐 1 까지, 그 뒤 카드 끝(+0.7초)까지 1 유지
    (제목이 사라지는 동안 기사 글자가 다시 떠오르지 않게). 제목 카드가 없으면 0."""
    tb = getattr(R, "tb", None)
    if tb is None:
        return 0.0
    return max([min(1.0, max(0.0, (t - c.t0) / 0.7)) for c in tb.plan.cards if c.kind == "title" and t <= c.t1 + 0.7] + [0.0])


def article_usage(events: list[dict]) -> list[dict]:
    """provenance article[] — 매체·프레스 사진(없으면 none)·테마·헤드라인(원문|번역)."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out = []
    for e in events:
        if e["type"] != "article":
            continue
        L = article_layout(ctx, e)  # noqa: N806
        row = {"mid": e["mid"], "t0": round(e["t0"], 2), "press": e.get("press") or "none", "theme": e.get("theme") or ARTICLE.theme_default,
               "headline": "translated" if L.translated else "original"}
        if L.credit is not None:   # v5.21.0 — 보도 인용(B) 사진을 쓴 카드에만(P5)
            row["press_quote"] = L.credit
        out.append(row)
    return out


__all__ = ["ArticleLayout", "ArticleOverflowError", "article_box", "article_layout", "article_phase", "article_text", "article_usage",
           "draw_article", "draw_article_text", "draw_press", "press_credit_text", "source_date", "validate_press"]

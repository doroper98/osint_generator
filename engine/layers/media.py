"""미디어 비트 — 사진·영상·기사 클리핑·컷아웃 (v2.5.5, render3 `media_frame … draw_cutout`, 14 §4).

권리 게이트(D-0036 작업 3): 이벤트는 `mid` 만 갖고, 파일·캡션·출처 줄·기사 문구는 미디어 레지스트리
(`assets/media/media_registry.json`)에서만 온다. `validate_media()` 가 렌더 전에 레지스트리 참조·종류·권리 상태를
확인하고 어기면 RightsError(C9, 15 P6). 이미지 키는 `media:<레지스트리 file>`(engine/assets.py).
"""

from __future__ import annotations

import math

import cairo
import numpy as np
from PIL import Image

from engine.assets import set_raster, surf_from_pil
from engine.context import RenderCtx
from engine.credits import RightsError
from engine.media_registry import cached_registry, credit_line, load_media_registry
from engine.projection import View
from engine.style import ARTICLE, CARD, C, FPS, W_OUT
from rules import load_rules
from engine.timebase import clamp01, ease_io, ease_out, smooth, window
from engine.typography import rrect, text, tw, wrap


SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from   # 자막 구역 위 — 기사 카드 가운데 자리의 세로 범위

EVENT_KIND: dict[str, str] = {"photo": "photo", "clip": "video", "cutout": "cutout", "article": "article"}   # 이벤트 → 레지스트리 kind


def validate_media(e: dict, assets: dict | None = None):  # noqa: ANN201 — schemas.media_models.MediaAsset
    """미디어 이벤트 하나의 권리 게이트. 통과하면 레지스트리 항목을 돌려준다. 어기면 RightsError(렌더 전)."""
    typ = e.get("type") or e.get("kind")
    where = f"{typ} t0={e.get('t0', '?')}"
    mid = e.get("mid")
    if not mid:
        raise RightsError(f"미디어 이벤트에 레지스트리 참조(mid)가 없다: {where} — 파일을 직접 가리킬 수 없다(C9)")
    reg = assets if assets is not None else load_media_registry()
    if mid not in reg:
        raise RightsError(f"미디어 레지스트리에 없음: mid={mid} ({where})")
    a = reg[mid]
    if EVENT_KIND.get(typ) != a.kind:
        raise RightsError(f"미디어 종류 불일치: 이벤트 {typ} ↔ 레지스트리 {mid}.kind={a.kind}")
    if a.rights_status != "rights_clear":
        raise RightsError(f"권리 미확인 미디어({a.rights_status}): {mid} — 렌더 금지(C9, <미검증> 라벨로 대신할 수 없다)")
    return a


def media_frame(ctx: cairo.Context, x: float, y: float, w: float, h: float, a: float) -> None:
    for d_, al in ((6, 0.10), (3, 0.18)):
        rrect(ctx, x - d_ + 2, y - d_ + 4, w + 2 * d_, h + 2 * d_, 4 + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()


def media_caption(ctx: cairo.Context, x: float, y: float, w: float, cap: str, credit: str, a: float) -> None:
    ctx.rectangle(x, y, w, 38)
    ctx.set_source_rgba(0.04, 0.05, 0.07, 0.9 * a)
    ctx.fill()
    text(ctx, cap, x + 10, y + 16, 10.5, "sansm", (1, 1, 1), a, 0, "l")
    text(ctx, credit, x + 10, y + 30, 7.8, "monom", C["muted"], a * 0.95, 0, "l", role="media_meta")


def caption_width(ctx: cairo.Context, cap: str, credit: str) -> float:
    """`media_caption` 글자가 실제로 차지하는 폭(왼쪽 여백 10 + 글자 + 오른쪽 여백 10). 바는 미디어 폭이지만 글자는 넘칠 수 있다 —
    패널 옆 슬롯(D-0050 NB9)이 출처 줄 잘림을 막으려고 이 폭까지 화면 안·장애물 밖을 요구한다."""
    return 20 + max(tw(ctx, cap, 10.5, "sansm"), tw(ctx, credit, 7.8, "monom"))


KEN_BURNS_MAX = 1.07   # 사진 켄 번스 끝 배율(v3 합격 값) — checks media_upscaled 도 이 값으로 필요한 폭을 잰다


def media_tag(ctx: cairo.Context, x: float, y: float, s_: str, a: float) -> None:
    w = tw(ctx, s_, 7.5, "mono") + 12
    rrect(ctx, x + 8, y + 8, w, 14, 2)
    ctx.set_source_rgba(0.02, 0.03, 0.05, 0.75 * a)
    ctx.fill()
    text(ctx, s_, x + 14, y + 18, 7.5, "mono", C["gold"], a, 0, "l", spacing=0.8, role="media_meta")


def draw_photo(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.5, 0.5)
    if a <= 0.01:
        return
    m = R.assets.media_assets[e["mid"]]
    lt = t - e["t0"]
    x, y, w = e["x"], e["y"] + (1 - ease_out(lt / 0.6)) * 12, e["w"]
    h = w * 0.625
    media_frame(ctx, x, y, w, h + 38, a)
    k = 1.0 + (KEN_BURNS_MAX - 1.0) * clamp01(lt / (e["t1"] - e["t0"]))  # Ken Burns
    fs, fw, fh = R.assets.raster(f"media:{m.file}", w * k, R.out.k)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    set_raster(ctx, fs, R.out.k, x - (fw - w) * 0.35, y - (fh - h) * 0.5)
    ctx.paint_with_alpha(a)
    ctx.restore()
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + 37)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    media_tag(ctx, x, y, "PHOTO", a)
    media_caption(ctx, x, y + h, w, m.caption, credit_line(m), a)


def draw_clip(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.35, 0.45)
    if a <= 0.01:
        return
    m = R.assets.media_assets[e["mid"]]
    R.assets.load_clip(m.file)
    fr = R.assets.clips[m.file]
    i = min(len(fr) - 1, max(0, int((t - e["t0"]) * FPS)))
    x, y, w = e["x"], e["y"], e["w"]
    h = w * fr.shape[1] / fr.shape[2]
    rgb = np.asarray(fr[i])
    OP = R.out  # noqa: N806 — 장치 해상도로 리샘플(원본이 더 작으면 checks media_upscaled 경고, D-0067 요건 3)
    size = (int(w), int(h)) if OP.k == 1 else (OP.px_i(w), OP.px_i(h))
    img = Image.fromarray(rgb).resize(size, Image.BILINEAR).convert("RGBA")
    surf, buf = surf_from_pil(img)
    R.cache["clip_buf"] = buf  # 표면이 칠해질 때까지 버퍼를 붙잡아 둔다
    media_frame(ctx, x, y, w, h + 38, a)
    set_raster(ctx, surf, OP.k, x, y)
    ctx.paint_with_alpha(a)
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + 37)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    media_tag(ctx, x, y, "VIDEO", a)
    media_caption(ctx, x, y + h, w, m.caption, credit_line(m), a)


class ArticleOverflowError(ValueError):
    """헤드라인·부제가 rules article_card 의 최대 줄 수를 넘는다(v4.8.0 D-0101 §2 — 조용한 잘림 금지, 15 P6)."""


def article_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], ARTICLE.fade_sec, ARTICLE.fade_sec)


def article_text(e: dict) -> dict:
    """기사 이벤트의 문구 — 레지스트리(kind article)에서(D-0036). pub=caption, date=file_note."""
    m = cached_registry()[e["mid"]]
    return dict(pub=m.caption, date=m.file_note, headline=m.headline, hl=m.hl, sub=m.sub, note=m.note)


def article_geom(ctx: cairo.Context, e: dict) -> tuple[float, float, float, float, list[str], list[str]]:
    """기사 카드 상자 (x, y, 폭, 높이, 헤드라인 줄, 부제 줄) — 슬라이드 전 제자리(RESERVED, D-0033).
    v4.8.0 D-0101 §2: 수치는 rules article_card, `align: center`(슬롯 center) = 무대 가운데. 줄 수 초과 = ArticleOverflowError."""
    A = ARTICLE  # noqa: N806
    e = {**e, **article_text(e)}
    w = A.w
    hl_lines = wrap(ctx, e["headline"], w - A.pad * 2, A.headline_size, "serifb")
    sub_lines = wrap(ctx, e["sub"], w - A.pad * 2, A.sub_size, "sans") if e["sub"] else []
    over = [f"{what} {len(ls)}줄 > {mx}" for what, ls, mx in (("헤드라인", hl_lines, A.headline_max_lines), ("부제", sub_lines, A.sub_max_lines))
            if len(ls) > mx]
    if over:
        raise ArticleOverflowError(f"기사 카드 {e['mid']}({e['pub']}): {', '.join(over)} — 레지스트리 문구를 줄인다(rules article_card)")
    last = A.body_top + (len(hl_lines) - 1) * A.headline_gap                       # 마지막 글자 줄 기준선
    if sub_lines:
        last += A.headline_gap + A.sub_lead + (len(sub_lines) - 1) * A.sub_gap
    h = last + A.foot_h
    if e.get("align") == "center":
        return (W_OUT - w) / 2, (SUB_Y - h) / 2, w, h, hl_lines, sub_lines
    return W_OUT - w - CARD.x_right_margin, A.y, w, h, hl_lines, sub_lines


def draw_article(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    A = ARTICLE  # noqa: N806
    a = article_alpha(t, e)
    if a <= 0.01:
        return
    e = {**e, **article_text(e)}
    lt = t - e["t0"]
    x0, y, w, h, hl_lines, sub_lines = article_geom(ctx, e)
    if e.get("align") == "center":        # 아래 지도·시간축을 dip 만큼 어둡게(D-0101 §2)
        ctx.set_source_rgba(0, 0, 0, A.center_dim * a)
        ctx.paint()
    x = x0 + (1 - ease_out(lt / A.slide_sec)) * CARD.slide_px
    for d_, al in A.shadow:
        rrect(ctx, x - d_ + A.shadow_dx, y - d_ + A.shadow_dy, w + d_ * 2, h + d_ * 2, A.radius + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()
    rrect(ctx, x, y, w, h, A.radius)
    ctx.set_source_rgba(*A.paper, a)
    ctx.fill()
    ink, grey = A.ink, A.grey
    text(ctx, e["pub"], x + A.pad, y + A.head_base, A.pub_size, "serifb", ink, a, 0, "l")
    text(ctx, e["date"], x + w - A.pad, y + A.head_base, A.date_size, "monom", grey, a, 0, "r", role="media_meta")
    ctx.set_source_rgba(*ink, A.rule_alpha * a)
    ctx.rectangle(x + A.pad, y + A.rule_y, w - A.pad * 2, A.rule_w)
    ctx.fill()
    yy = y + A.body_top
    hk = ease_io((lt - A.hl_delay_sec) / A.hl_sec)
    hs = A.headline_size
    for ln in hl_lines:
        if e.get("hl") and e["hl"] in ln and hk > 0:
            i = ln.index(e["hl"])
            hx = x + A.pad + tw(ctx, ln[:i], hs, "serifb")
            ww = tw(ctx, e["hl"], hs, "serifb")
            ctx.rectangle(hx - A.hl_pad, yy - hs * A.hl_rise, (ww + A.hl_pad * 2) * hk, hs * A.hl_h)
            ctx.set_source_rgba(*A.hl_rgba[:3], A.hl_rgba[3] * a)
            ctx.fill()
        text(ctx, ln, x + A.pad, yy, hs, "serifb", ink, a, 0, "l")
        yy += A.headline_gap
    yy += A.sub_lead
    for ln in sub_lines:
        text(ctx, ln, x + A.pad, yy, A.sub_size, "sans", grey, a, 0, "l")
        yy += A.sub_gap
    text(ctx, A.tag, x + A.pad, y + h - A.foot_inset, A.meta_size, "mono", grey, a, 0, "l", spacing=A.tag_spacing, role="media_meta")
    text(ctx, e["note"], x + w - A.pad, y + h - A.foot_inset, A.meta_size, "sans", grey, a, 0, "r", role="media_meta")


def draw_cutout(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.6, 0.5)
    if a <= 0.01:
        return
    lt = t - e["t0"]
    x, y = view.to_screen(*e["world"])
    x -= (1 - ease_out(lt / 1.2)) * 40
    y += math.sin(t * 1.3) * 2.2
    m = R.assets.media_assets[e["mid"]]
    fs, fw, fh = R.assets.raster(f"media:{m.file}", e["w"], R.out.k)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.04 + 0.015 * math.sin(t * 0.9))
    ctx.set_source_rgba(0, 0, 0, 0.25 * a)
    ctx.save()
    ctx.translate(6, 14)
    ctx.scale(1, 0.25)
    ctx.arc(0, 0, fw * 0.36, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    set_raster(ctx, fs, R.out.k, -fw / 2, -fh / 2)
    ctx.paint_with_alpha(a)
    ctx.restore()
    la = a * smooth((lt - 0.5) / 0.4)
    text(ctx, m.caption, x, y + fh / 2 + 16, 12, "sansb", (1, 1, 1), la, 3, "c")
    text(ctx, credit_line(m), x, y + fh / 2 + 30, 8.5, "monom", C["muted"], la, 2.4, "c", role="media_meta")
    R.reserved.append((x - fw / 2, y - fh / 2, x + fw / 2, y + fh / 2 + 34))

"""미디어 비트 — 사진·영상·기사 클리핑·컷아웃 (v2.1.0, render3 `media_frame … draw_cutout`).

이미지 키는 `media:<파일명>`(engine/assets.py). 출처 줄(credit)은 모델에서 필수다(07 §3, G4).
"""

from __future__ import annotations

import math

import cairo
import numpy as np
from PIL import Image

from engine.assets import surf_from_pil
from engine.context import RenderCtx
from engine.projection import View
from engine.style import C, FPS, W_OUT
from engine.timebase import clamp01, ease_io, ease_out, smooth, window
from engine.typography import rrect, text, tw, wrap


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
    text(ctx, credit, x + 10, y + 30, 7.8, "monom", C["muted"], a * 0.95, 0, "l")


def media_tag(ctx: cairo.Context, x: float, y: float, s_: str, a: float) -> None:
    w = tw(ctx, s_, 7.5, "mono") + 12
    rrect(ctx, x + 8, y + 8, w, 14, 2)
    ctx.set_source_rgba(0.02, 0.03, 0.05, 0.75 * a)
    ctx.fill()
    text(ctx, s_, x + 14, y + 18, 7.5, "mono", C["gold"], a, 0, "l", spacing=0.8)


def draw_photo(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.5, 0.5)
    if a <= 0.01:
        return
    lt = t - e["t0"]
    x, y, w = e["x"], e["y"] + (1 - ease_out(lt / 0.6)) * 12, e["w"]
    h = w * 0.625
    media_frame(ctx, x, y, w, h + 38, a)
    k = 1.0 + 0.07 * clamp01(lt / (e["t1"] - e["t0"]))  # Ken Burns
    fs = R.assets.scaled(f"media:{e['img']}", w * k)
    fw, fh = fs.get_width(), fs.get_height()
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.set_source_surface(fs, x - (fw - w) * 0.35, y - (fh - h) * 0.5)
    ctx.paint_with_alpha(a)
    ctx.restore()
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + 37)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    media_tag(ctx, x, y, "PHOTO", a)
    media_caption(ctx, x, y + h, w, e["caption"], e["credit"], a)


def draw_clip(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.35, 0.45)
    if a <= 0.01:
        return
    R.assets.load_clip(e["clip"])
    fr = R.assets.clips[e["clip"]]
    i = min(len(fr) - 1, max(0, int((t - e["t0"]) * FPS)))
    x, y, w = e["x"], e["y"], e["w"]
    h = w * fr.shape[1] / fr.shape[2]
    rgb = np.asarray(fr[i])
    img = Image.fromarray(rgb).resize((int(w), int(h)), Image.BILINEAR).convert("RGBA")
    surf, buf = surf_from_pil(img)
    R.cache["clip_buf"] = buf  # 표면이 칠해질 때까지 버퍼를 붙잡아 둔다
    media_frame(ctx, x, y, w, h + 38, a)
    ctx.set_source_surface(surf, x, y)
    ctx.paint_with_alpha(a)
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + 37)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    media_tag(ctx, x, y, "VIDEO", a)
    media_caption(ctx, x, y + h, w, e["caption"], e["credit"], a)


def draw_article(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.45, 0.45)
    if a <= 0.01:
        return
    lt = t - e["t0"]
    w = 300
    x = W_OUT - w - 24 + (1 - ease_out(lt / 0.55)) * 30
    y = 68
    hl_lines = wrap(ctx, e["headline"], w - 32, 13.5, "serifb")
    sub_lines = wrap(ctx, e["sub"], w - 32, 9.5, "sans")
    h = 44 + len(hl_lines) * 20 + 6 + len(sub_lines) * 14 + 24
    for d_, al in ((6, 0.12), (3, 0.2)):
        rrect(ctx, x - d_ + 2, y - d_ + 4, w + 2 * d_, h + 2 * d_, 3 + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()
    rrect(ctx, x, y, w, h, 3)
    ctx.set_source_rgba(0.95, 0.935, 0.905, a)
    ctx.fill()
    ink = (0.1, 0.105, 0.12)
    grey = (0.38, 0.39, 0.42)
    text(ctx, e["pub"], x + 16, y + 25, 12.5, "serifb", ink, a, 0, "l")
    text(ctx, e["date"], x + w - 16, y + 25, 8.5, "monom", grey, a, 0, "r")
    ctx.set_source_rgba(*ink, 0.35 * a)
    ctx.rectangle(x + 16, y + 33, w - 32, 0.8)
    ctx.fill()
    yy = y + 54
    hk = ease_io((lt - 0.8) / 0.7)
    for ln in hl_lines:
        if e.get("hl") and e["hl"] in ln and hk > 0:
            i = ln.index(e["hl"])
            x0 = x + 16 + tw(ctx, ln[:i], 13.5, "serifb")
            ww = tw(ctx, e["hl"], 13.5, "serifb")
            ctx.rectangle(x0 - 2, yy - 12, (ww + 4) * hk, 16)
            ctx.set_source_rgba(1.0, 0.8, 0.3, 0.55 * a)
            ctx.fill()
        text(ctx, ln, x + 16, yy, 13.5, "serifb", ink, a, 0, "l")
        yy += 20
    yy += 4
    for ln in sub_lines:
        text(ctx, ln, x + 16, yy, 9.5, "sans", grey, a, 0, "l")
        yy += 14
    text(ctx, "ARTICLE", x + 16, y + h - 11, 7.5, "mono", grey, a, 0, "l", spacing=0.8)
    text(ctx, e["note"], x + w - 16, y + h - 11, 7.8, "sans", grey, a, 0, "r")


def draw_cutout(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.6, 0.5)
    if a <= 0.01:
        return
    lt = t - e["t0"]
    x, y = view.xy(e["lon"], e["lat"])
    x -= (1 - ease_out(lt / 1.2)) * 40
    y += math.sin(t * 1.3) * 2.2
    fs = R.assets.scaled(f"media:{e['img']}", e["w"])
    fw, fh = fs.get_width(), fs.get_height()
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
    ctx.set_source_surface(fs, -fw / 2, -fh / 2)
    ctx.paint_with_alpha(a)
    ctx.restore()
    la = a * smooth((lt - 0.5) / 0.4)
    text(ctx, e["label"], x, y + fh / 2 + 16, 12, "sansb", (1, 1, 1), la, 3, "c")
    text(ctx, e["sub"], x, y + fh / 2 + 30, 8.5, "monom", C["muted"], la, 2.4, "c")
    R.reserved.append((x - fw / 2, y - fh / 2, x + fw / 2, y + fh / 2 + 34))

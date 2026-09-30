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
from engine.media_registry import credit_line, load_media_registry
from engine.projection import View
from engine.style import C, FPS
from rules import load_rules
from engine.timebase import clamp01, ease_out, smooth, window
from engine.typography import rrect, text, tw


MC = load_rules().layout_480p.media_caption   # v4.8.0 D-0101 §3 — 사진·영상 캡션 바·태그·컷아웃 캡션 글자(옛 리터럴)
BAR = load_rules().media_beats.caption_bar_px   # 캡션 바 높이(media_plan 상자 계산과 같은 값)

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
    ctx.rectangle(x, y, w, BAR)
    ctx.set_source_rgba(0.04, 0.05, 0.07, 0.9 * a)
    ctx.fill()
    text(ctx, cap, x + MC.pad_x, y + MC.caption_dy, MC.caption_size, "sansm", (1, 1, 1), a, 0, "l")
    text(ctx, credit, x + MC.pad_x, y + MC.credit_dy, MC.credit_size, "monom", C["muted"], a * 0.95, 0, "l", role="media_meta")


def caption_width(ctx: cairo.Context, cap: str, credit: str) -> float:
    """`media_caption` 글자가 실제로 차지하는 폭(왼쪽 여백 10 + 글자 + 오른쪽 여백 10). 바는 미디어 폭이지만 글자는 넘칠 수 있다 —
    패널 옆 슬롯(D-0050 NB9)이 출처 줄 잘림을 막으려고 이 폭까지 화면 안·장애물 밖을 요구한다."""
    return MC.pad_x * 2 + max(tw(ctx, cap, MC.caption_size, "sansm"), tw(ctx, credit, MC.credit_size, "monom"))


KEN_BURNS_MAX = 1.07   # 사진 켄 번스 끝 배율(v3 합격 값) — checks media_upscaled 도 이 값으로 필요한 폭을 잰다


def media_tag(ctx: cairo.Context, x: float, y: float, s_: str, a: float) -> None:
    w = tw(ctx, s_, MC.tag_size, "mono") + 12
    rrect(ctx, x + 8, y + 8, w, MC.tag_h, 2)
    ctx.set_source_rgba(0.02, 0.03, 0.05, 0.75 * a)
    ctx.fill()
    text(ctx, s_, x + 14, y + 8 + MC.tag_dy, MC.tag_size, "mono", C["gold"], a, 0, "l", spacing=0.8, role="media_meta")


def ken_burns_source(ctx: cairo.Context, src: cairo.ImageSurface, x: float, y: float, w: float, h: float, k: float) -> None:
    """사진을 설계 폭 w × k 로(연속 배율) 원천으로 건다 — 원본 해상도 표면 하나 + 패턴 행렬(v4.8.0 D-0104 D6, R-0119 S8).
    옛 방식(매 프레임 `raster(w × k)` = 3px 단위 폭으로 다시 리샘플)은 크기가 계단처럼 튀었다. 위치 기준(가로 0.35·세로 0.5)은 v3 그대로."""
    fw = w * k
    fh = fw * src.get_height() / src.get_width()
    ox, oy = x - (fw - w) * 0.35, y - (fh - h) * 0.5
    sc = src.get_width() / fw                       # 설계 1 단위당 원본 픽셀
    pat = cairo.SurfacePattern(src)
    pat.set_matrix(cairo.Matrix(xx=sc, yy=sc, x0=-ox * sc, y0=-oy * sc))
    pat.set_filter(cairo.FILTER_GOOD)
    ctx.set_source(pat)


def draw_photo(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.5, 0.5)
    if a <= 0.01:
        return
    m = R.assets.media_assets[e["mid"]]
    lt = t - e["t0"]
    x, y, w = e["x"], e["y"] + (1 - ease_out(lt / 0.6)) * 12, e["w"]
    h = w * 0.625
    media_frame(ctx, x, y, w, h + BAR, a)
    k = 1.0 + (KEN_BURNS_MAX - 1.0) * clamp01(lt / (e["t1"] - e["t0"]))  # Ken Burns
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ken_burns_source(ctx, R.assets.original(f"media:{m.file}"), x, y, w, h, k)
    ctx.paint_with_alpha(a)
    ctx.restore()
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + BAR - 1)
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
    media_frame(ctx, x, y, w, h + BAR, a)
    set_raster(ctx, surf, OP.k, x, y)
    ctx.paint_with_alpha(a)
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + BAR - 1)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    media_tag(ctx, x, y, "VIDEO", a)
    media_caption(ctx, x, y + h, w, m.caption, credit_line(m), a)


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
    text(ctx, m.caption, x, y + fh / 2 + MC.caption_dy, MC.cutout_caption_size, "sansb", (1, 1, 1), la, 3, "c")
    text(ctx, credit_line(m), x, y + fh / 2 + MC.credit_dy, MC.cutout_credit_size, "monom", C["muted"], la, 2.4, "c", role="media_meta")
    R.reserved.append((x - fw / 2, y - fh / 2, x + fw / 2, y + fh / 2 + MC.credit_dy + 4))

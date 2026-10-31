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
from engine.style import C, ELEM, FPS, MOTION
from rules import load_rules
from engine.timebase import clamp01, ease_out, smooth, window
from engine.typography import rrect, text, tw


MC = load_rules().layout_480p.media_caption   # v4.8.0 D-0101 §3 — 사진·영상 캡션 바·태그·컷아웃 캡션 글자(옛 리터럴)
BAR = load_rules().media_beats.caption_bar_px   # 캡션 바 높이(media_plan 상자 계산과 같은 값)

EVENT_KIND: dict[str, str] = {"photo": "photo", "clip": "video", "cutout": "cutout", "article": "article",
                              "inset": "inset"}   # 이벤트 → 레지스트리 kind. inset = flight.inset(v7.3.0 D-0206, 이벤트 타입 아님)


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
    if getattr(a, "press_of", None) is not None:   # v5.21.0 D-0177 — 보도 인용(B) 사진은 독립 비트·배경 금지(기사 카드 프레스 칸에서만)
        raise RightsError(f"기사 {a.press_of} 의 보도 인용 사진({a.agency})은 기사 카드 프레스 칸(article press)에서만 — 독립 사진·배경 금지(사용자 결정 D172)")
    if a.rights_status == "restricted" and a.kind == "video" and a.scope == "private_only":   # v7.4.0 사용자 결정 D264 — 비공개 시청 한정 클립
        return a                                                                                 # (provenance private_only_assets 에 남는다)
    if a.rights_status != "rights_clear":
        raise RightsError(f"권리 미확인 미디어({a.rights_status}): {mid} — 렌더 금지(C9, <미검증> 라벨로 대신할 수 없다)")
    return a


def media_frame(ctx: cairo.Context, x: float, y: float, w: float, h: float, a: float) -> None:
    for d_, al in ((6, 0.10), (3, 0.18)):
        rrect(ctx, x - d_ + 2, y - d_ + 4, w + 2 * d_, h + 2 * d_, 4 + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()


_MCTX = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))   # 글자 폭 재기 전용
ELLIPSIS = "…"


def _ellipsis(s: str, size: float, font: str, maxw: float) -> str:
    if tw(_MCTX, s, size, font) <= maxw:
        return s
    while s and tw(_MCTX, s.rstrip() + ELLIPSIS, size, font) > maxw:
        s = s[:-1]
    return s.rstrip() + ELLIPSIS


def _wrap(s: str, size: float, font: str, maxw: float) -> list[str]:
    """출처 줄 접기 — ' · ' 마디 단위로 채우고, 한 마디가 바보다 길면 빈칸 단위로. 한 낱말이 바보다 길면 그대로 둔다(검사가 잡는다)."""
    def fits(t: str) -> bool:
        return tw(_MCTX, t, size, font) <= maxw

    units: list[tuple[str, str]] = []   # (조각, 앞 구분자)
    for i, part in enumerate(s.split(" · ")):
        words = [part] if fits(part) else part.split(" ")
        units += [(wd, (" · " if i else "") if j == 0 else " ") for j, wd in enumerate(words)]
    lines: list[str] = []
    for wd, sep in units:
        if lines and fits(lines[-1] + sep + wd):
            lines[-1] += sep + wd
        else:
            lines.append(wd)
    return lines or [s]


def caption_layout(cap: str, credit: str, w: float) -> tuple[str, list[str], bool]:
    """(그릴 캡션 줄, 출처 줄들, 바 폭 안에 다 들어갔나) — v7.4.0 back_and_forth D-0333. 들어가면 옛 그림 그대로(한 줄씩)."""
    ov = MC.overflow
    maxw = w - 2 * MC.pad_x
    c = _ellipsis(cap, MC.caption_size, "sansm", maxw) if ov.caption == "ellipsis" else cap
    src = _wrap(credit, MC.credit_size, "monom", maxw) if ov.source == "wrap" else [credit]
    ok = (tw(_MCTX, c, MC.caption_size, "sansm") <= maxw and len(src) <= ov.source_max_lines
          and all(tw(_MCTX, ln, MC.credit_size, "monom") <= maxw for ln in src))
    return c, src, ok


def caption_bar_h(cap: str, credit: str, w: float) -> float:
    """캡션 바 높이 — 접힌 출처 줄마다 + rules media_caption.overflow.source_line_px(media_plan 상자 계산도 이 값)."""
    return BAR + (len(caption_layout(cap, credit, w)[1]) - 1) * MC.overflow.source_line_px


def media_caption(ctx: cairo.Context, x: float, y: float, w: float, cap: str, credit: str, a: float) -> None:
    c, src, _ = caption_layout(cap, credit, w)
    ctx.rectangle(x, y, w, BAR + (len(src) - 1) * MC.overflow.source_line_px)
    ctx.set_source_rgba(0.04, 0.05, 0.07, 0.9 * a)
    ctx.fill()
    text(ctx, c, x + MC.pad_x, y + MC.caption_dy, MC.caption_size, "sansm", (1, 1, 1), a, 0, "l")
    for i, ln in enumerate(src):
        text(ctx, ln, x + MC.pad_x, y + MC.credit_dy + i * MC.overflow.source_line_px, MC.credit_size, "monom", C["muted"], a * 0.95, 0, "l",
             role="media_meta")


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
    a = window(t, e["t0"], e["t1"], *ELEM["photo"])   # v7.4.0 UF-159 ×1.5
    if a <= 0.01:
        return
    m = R.assets.media_assets[e["mid"]]
    lt = t - e["t0"]
    x, y, w = e["x"], e["y"] + (1 - ease_out(lt / MOTION["photo_rise_sec"])) * 12, e["w"]
    h = w * 0.625
    bar = caption_bar_h(m.caption, credit_line(m), w)   # v7.4.0 D-0333 — 출처 줄 접힘만큼 바가 길다
    media_frame(ctx, x, y, w, h + bar, a)
    k = 1.0 + (KEN_BURNS_MAX - 1.0) * clamp01(lt / (e["t1"] - e["t0"]))  # Ken Burns
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ken_burns_source(ctx, R.assets.original(f"media:{m.file}"), x, y, w, h, k)
    ctx.paint_with_alpha(a)
    ctx.restore()
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + bar - 1)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    media_tag(ctx, x, y, "PHOTO", a)
    media_caption(ctx, x, y + h, w, m.caption, credit_line(m), a)


def draw_clip(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], *ELEM["clip"])
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
    bar = 0 if e.get("frame") else caption_bar_h(m.caption, credit_line(m), w)   # v7.4.0 D-0333 접힘 · v7.4.0 D-0274 §2① — 액자(clip_frame): 캡션 줄은 상자 안 위쪽 띠(아래는 자막 자리)
    media_frame(ctx, x, y, w, h + bar, a)
    set_raster(ctx, surf, OP.k, x, y)
    ctx.paint_with_alpha(a)
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + bar - 1)
    ctx.set_source_rgba(1, 1, 1, 0.22 * a)
    ctx.set_line_width(1)
    ctx.stroke()
    if e.get("frame"):
        media_caption(ctx, x, y, w, m.caption, credit_line(m), a)
        return
    media_tag(ctx, x, y, "VIDEO", a)
    media_caption(ctx, x, y + h, w, m.caption, credit_line(m), a)


def draw_cutout(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], *ELEM["cutout"])
    if a <= 0.01:
        return
    lt = t - e["t0"]
    x, y = view.to_screen(*e["world"])
    x -= (1 - ease_out(lt / MOTION["cutout_slide_sec"])) * 40
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


FL_INSET = load_rules().flight.inset   # v7.3.0 D-0206 — 위성 인셋 상자 토큰


def draw_inset(ctx: cairo.Context, R: RenderCtx, box: tuple[float, float, float, float], a: float, e: dict) -> None:  # noqa: N803
    """비행 이벤트의 위성 인셋(v7.3.0 D-0206, engine/layers/flight 가 부른다) — 레지스트리 kind inset 파일을 정사각 가운데 자름 →
    원형 클립(UF-103 "동그랗게", 사각 금지). 흔들림·회전 없음(위성 타일은 정지). 원 아래 가운데에 출처 줄(credit_formats.inset)."""
    from engine.layers.flight import circle_path  # noqa: PLC0415

    x, y, w, h = box
    m = R.assets.media_assets[e["inset"]["mid"]]
    fs, fw, fh = R.assets.raster(f"media:{m.file}", w, R.out.k)
    if fh < h:   # 가로로 긴 타일 → 높이를 지름에 맞춘다(정사각 가운데 자름)
        fs, fw, fh = R.assets.raster(f"media:{m.file}", w * h / fh, R.out.k)
    ctx.save()
    circle_path(ctx, box)
    ctx.clip()
    set_raster(ctx, fs, R.out.k, x + (w - fw) / 2, y + (h - fh) / 2)
    ctx.paint_with_alpha(a)
    ctx.restore()
    circle_path(ctx, box)
    ctx.set_source_rgba(1, 1, 1, FL_INSET.frame.alpha * a)
    ctx.set_line_width(FL_INSET.frame.width)
    ctx.stroke()
    text(ctx, credit_line(m), x + w / 2, y + h + FL_INSET.caption_dy, FL_INSET.caption_size, "monom", C["muted"], a, FL_INSET.caption_halo, "c",
         role="media_meta")

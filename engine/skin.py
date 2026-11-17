"""디자인 시스템 바탕 코어 — 흰 카드·부드러운 그림자·잉크 글자·흰 번짐 (v7.4.0 C0.0·UF-906, D917).

규칙 = `rules/video_rules.yaml skin`(코드 리터럴 0, 15 P3). `apply(무대 이름)` 이 영상마다 켜고 끈다 — rules skin.stages 의 주 무대면 켠다
(잉크 모드 typography.INK_MODE·팔레트는 engine.project 가 skin.palette 로). 꺼지면 종전 그리기 그대로(바이트 동일).
모서리는 skin.surface.radius(v7.4.0 UF-908·D918 — 0 = 직각), 알약 모양(칩·점)만 둥글다.

그리기 함수는 설계 px 상자를 받는다. 장치 배율은 컨텍스트 행렬에서 읽는다(전역 출력 프로파일을 보지 않는다).
번짐은 PIL GaussianBlur(시그마 = blur × sigma_k × 장치 배율) — 같은 입력 = 같은 바이트.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Callable

import cairo
import numpy as np
from PIL import Image, ImageFilter

from engine import typography
from engine.style import DATE_BADGE, FONT, SKIN, Color, hexc
from engine.typography import rrect

Box = tuple[float, float, float, float]   # x, y, 폭, 높이(설계 px)
Rect = tuple[float, float, float, float]  # x0, y0, x1, y1(설계 px)
ShadowLayers = list[tuple[float, float, float]]

for _f in (SKIN.subtitle.emphasis_font, DATE_BADGE.font):   # 없는 글꼴 키 = 시작 오류(P6·P10)
    if _f not in FONT:
        raise ValueError(f"skin 글꼴 {_f!r} 가 engine.style.FONT 키가 아니다: {sorted(FONT)}")

ACTIVE = False
INK: Color = hexc(SKIN.ink.primary)
INK2: Color = hexc(SKIN.ink.secondary)
INK3: Color = hexc(SKIN.ink.tertiary)
ACCENT_SHAPE: Color = hexc(SKIN.accent.shape)
ACCENT_INK: Color = hexc(SKIN.accent.ink)
HAIR: Color = hexc(SKIN.hairline.rgb)
FILL: Color = hexc(SKIN.surface.fill)


def apply(stage_name: str | None) -> bool:
    """영상마다 — 주 무대가 rules skin.stages 안이면 켠다. 끄면 잉크 모드도 끈다(한 프로세스 여러 영상)."""
    global ACTIVE
    ACTIVE = stage_name is not None and stage_name in SKIN.stages
    typography.INK_MODE = ACTIVE
    return ACTIVE


def active() -> bool:
    return ACTIVE


def device_scale(ctx: cairo.Context) -> float:
    """컨텍스트 행렬의 설계 → 장치 배율(회전 없음 전제 — 가로 축 길이)."""
    m = ctx.get_matrix()
    return math.hypot(m.xx, m.yx)


def box_path(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    """상자 경로 — r ≤ 0 이면 직각(UF-908·D918), 아니면 둥근 모서리(반경은 폭·높이 절반까지)."""
    if r <= 0:
        ctx.rectangle(x, y, w, h)
    else:
        rrect(ctx, x, y, w, h, min(r, w / 2, h / 2))


def _a8_from(a: np.ndarray) -> cairo.ImageSurface:
    h, w = a.shape
    out = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
    buf = np.ndarray((h, out.get_stride()), np.uint8, buffer=out.get_data())
    buf[:, :w] = a
    out.mark_dirty()
    return out


def _blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """8비트 알파 → 가우시안 번짐(PIL, 결정적)."""
    return np.asarray(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(sigma)))


@lru_cache(maxsize=256)
def _shadow_mask(w: float, h: float, r: float, blur: float, ks: float) -> tuple[cairo.ImageSurface, int]:
    """번진 상자 알파(A8, 장치 px)와 여백(장치 px)."""
    sigma = blur * SKIN.shadow.sigma_k * ks
    m = int(math.ceil(sigma * 3))
    sw, sh = int(math.ceil(w * ks)) + 2 * m, int(math.ceil(h * ks)) + 2 * m
    s = cairo.ImageSurface(cairo.FORMAT_A8, sw, sh)
    c = cairo.Context(s)
    c.translate(m, m)
    c.scale(ks, ks)
    box_path(c, 0, 0, w, h, r)
    c.set_source_rgba(0, 0, 0, 1)
    c.fill()
    s.flush()
    a = np.ndarray((sh, s.get_stride()), np.uint8, buffer=s.get_data())[:, :sw].copy()
    return _a8_from(_blur(a, sigma)), m


def soft_shadow(ctx: cairo.Context, box: Box, radius: float, layers: ShadowLayers, alpha: float = 1.0) -> None:
    """부드러운 그림자 — 겹마다 [아래로 dy, 번짐 blur, 알파](설계 px). 색 = rules skin.shadow.rgb."""
    x, y, w, h = box
    ks = device_scale(ctx)
    for dy, blur, al in layers:
        mask, m = _shadow_mask(round(w, 2), round(h, 2), radius, blur, round(ks, 6))
        ctx.save()
        ctx.translate(x, y + dy)
        ctx.scale(1 / ks, 1 / ks)
        ctx.set_source_rgba(*SKIN.shadow.rgb, al * alpha)
        ctx.mask_surface(mask, -m, -m)
        ctx.restore()


def surface(ctx: cairo.Context, box: Box, a: float = 1.0, level: str = "card", radius: float | None = None,
            fill: Color | None = None) -> None:
    """카드 면 — 그림자(skin.shadow.<level>) + 세로 그라데이션 면(fill → fill − fill_drop) + 가장자리 실선 + 안쪽 흰 선."""
    S = SKIN.surface  # noqa: N806
    r = S.radius if radius is None else radius
    f = FILL if fill is None else fill
    x, y, w, h = box
    soft_shadow(ctx, box, r, getattr(SKIN.shadow, level), a)
    box_path(ctx, x, y, w, h, r)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgba(0, *f, a)
    g.add_color_stop_rgba(1, *(max(0.0, c - S.fill_drop) for c in f), a)
    ctx.set_source(g)
    ctx.fill_preserve()
    lw = SKIN.hairline.w
    ctx.set_source_rgba(*HAIR, SKIN.hairline.alpha * a)
    ctx.set_line_width(lw)
    ctx.stroke()
    box_path(ctx, x + lw, y + lw, w - 2 * lw, h - 2 * lw, max(0.0, r - lw))
    ctx.set_source_rgba(1, 1, 1, S.inner_light_alpha * a)
    ctx.set_line_width(lw)
    ctx.stroke()


def glow(ctx: cairo.Context, draw: Callable[[cairo.Context], None], rect: Rect, blur: float | None = None,
         gain: float | None = None, alpha: float | None = None) -> None:
    """글자 뒤 부드러운 흰 번짐(테두리 아님) — draw(ctx) 가 글자를 그린다. rect(설계 px, x0·y0·x1·y1) 둘레만 임시 표면에 그려
    알파를 번지게 해(시그마 = blur × sigma_k × 배율) × gain(잘림) × alpha 흰색으로 칠한 뒤 실제 컨텍스트에 draw.
    blur·gain·alpha 를 주지 않으면 자막 값(rules skin.subtitle) — 다른 요소는 자기 rules 토큰을 넘긴다."""
    G = SKIN.subtitle  # noqa: N806
    g_blur = G.glow_blur if blur is None else blur
    g_gain = G.glow_gain if gain is None else gain
    g_alpha = G.glow_alpha if alpha is None else alpha
    ks = device_scale(ctx)
    sigma = g_blur * SKIN.shadow.sigma_k * ks
    m = int(math.ceil(g_blur * ks * 3))
    xs, ys = zip(*(ctx.user_to_device(px, py) for px in (rect[0], rect[2]) for py in (rect[1], rect[3])))
    dx0, dy0 = int(math.floor(min(xs))) - m, int(math.floor(min(ys))) - m
    dw, dh = int(math.ceil(max(xs))) + m - dx0, int(math.ceil(max(ys))) + m - dy0
    if dw > 0 and dh > 0:
        tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, dw, dh)
        tc = cairo.Context(tmp)
        xx, yx, xy_, yy, x0, y0 = tuple(ctx.get_matrix())
        tc.set_matrix(cairo.Matrix(xx, yx, xy_, yy, x0 - dx0, y0 - dy0))
        draw(tc)
        tmp.flush()
        a = np.ndarray((dh, tmp.get_stride() // 4, 4), np.uint8, buffer=tmp.get_data())[:, :dw, 3].copy()
        g = np.clip(_blur(a, sigma).astype(np.float32) * g_gain, 0, 255).astype(np.uint8)
        ctx.save()
        ctx.identity_matrix()
        ctx.set_source_rgba(1, 1, 1, g_alpha)
        ctx.mask_surface(_a8_from(g), dx0, dy0)
        ctx.restore()
    draw(ctx)


def pill(ctx: cairo.Context, box: Box, fill: Color, a: float = 1.0, level: str | None = None) -> None:
    """알약(높이 절반 반지름) 면 — 꼬리표·칩·인물 알약. level 을 주면 그 그림자(rules skin.shadow.<level>)를 깐다. 알약만 둥글다(UF-908)."""
    x, y, w, h = box
    r = h / 2
    if level is not None:
        soft_shadow(ctx, box, r, getattr(SKIN.shadow, level), a)
    rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*fill, a)
    ctx.fill()


__all__ = ["ACCENT_INK", "ACCENT_SHAPE", "INK", "INK2", "INK3", "SKIN", "active", "apply", "box_path", "device_scale", "glow",
           "pill", "soft_shadow", "surface"]

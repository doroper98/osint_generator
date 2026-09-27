"""르포 폰트 스택 텍스트 (v2.1.0, 19 부록 D `font, mixed_runs, text, tw, rrect, wrap`).

IBM Plex Mono 에는 한글이 없어 한글 구간은 IBM Plex Sans KR 로 런 분할한다(01 라운드 6).
GmarketSans woff→otf 변환본은 공백 글리프가 깨져 공백 폭을 크기 × display_space_advance 로 그린다(19 §3.13).
"""

from __future__ import annotations

import math
import re

import cairo

from engine.style import DISPLAY_SPACE, FONT

HANGUL = re.compile("[ᄀ-ᇿ㄰-㆏가-힣]")
MONO = ("mono", "monom")
DISP = ("disp", "dispm")


def font(ctx: cairo.Context, name: str, size: float) -> None:
    fam, b = FONT[name]
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if b else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def mixed_runs(s: str, name: str) -> list[list[str]]:
    fb = "sans" if name == "monom" else "sansm"
    runs: list[list[str]] = []
    for ch in s:
        f = fb if HANGUL.match(ch) else name
        if ch == " " and runs:
            f = runs[-1][1]
        if runs and runs[-1][1] == f:
            runs[-1][0] += ch
        else:
            runs.append([ch, f])
    return runs


def text(ctx: cairo.Context, s: str, x: float, y: float, size: float, name: str = "sansm",
         col: tuple = (1, 1, 1), a: float = 1.0, halo: float = 3.0, anchor: str = "l",
         spacing: float = 0.0, halo_a: float = 0.8) -> float:
    if a <= 0.01 or not s:
        return 0
    if name in MONO and HANGUL.search(s):
        runs = mixed_runs(s, name)
        w = sum(tw(ctx, r, size, f) for r, f in runs)
        if anchor == "c":
            x -= w / 2
        elif anchor == "r":
            x -= w
        for r, f in runs:
            x += text(ctx, r, x, y, size, f, col, a, halo, "l", 0.0, halo_a)
        return w
    font(ctx, name, size)
    disp = name in DISP and " " in s
    if disp and not spacing:
        spacing = 0.0001
    w = tw(ctx, s, size, name) + spacing * max(0, len(s) - 1)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    font(ctx, name, size)
    ctx.new_path()
    if spacing:
        xx = x
        for ch in s:
            if ch == " " and name in DISP:
                xx += size * DISPLAY_SPACE + spacing
                continue
            ctx.move_to(xx, y)
            ctx.text_path(ch)
            xx += ctx.text_extents(ch).x_advance + spacing
    else:
        ctx.move_to(x, y)
        ctx.text_path(s)
    if halo > 0:
        ctx.set_source_rgba(0.02, 0.03, 0.05, halo_a * a)
        ctx.set_line_width(halo)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*col[:3], a)
    ctx.fill()
    return w


def tw(ctx: cairo.Context, s: str, size: float, name: str) -> float:
    if name in MONO and HANGUL.search(s):
        return sum(tw(ctx, r, size, f) for r, f in mixed_runs(s, name))
    font(ctx, name, size)
    if name in DISP and " " in s:
        return sum(size * DISPLAY_SPACE if ch == " " else ctx.text_extents(ch).x_advance for ch in s)
    return ctx.text_extents(s).x_advance


def rrect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def wrap(ctx: cairo.Context, s: str, maxw: float, size: float, name: str) -> list[str]:
    font(ctx, name, size)
    words = s.split(" ")
    lines: list[str] = []
    cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if ctx.text_extents(t).x_advance > maxw and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines

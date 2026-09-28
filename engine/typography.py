"""르포 폰트 스택 텍스트 (v2.1.0, 19 부록 D `font, mixed_runs, text, tw, rrect, wrap`).

IBM Plex Mono 에는 한글이 없어 한글 구간은 IBM Plex Sans KR 로 런 분할한다(01 라운드 6).
GmarketSans woff→otf 변환본은 공백 글리프가 깨져 공백 폭을 크기 × display_space_advance 로 그린다(19 §3.13).
v3.6.0 NB16: 렌더 경로의 글꼴 선택(`font`)도 fontconfig 가 이름대로 찾았는지 확인한다 — 대체 글꼴로 조용히 그리지 않는다(15 P6).
v3.6.0 해상도(D-0067 요건 3): 글자 폭 **측정**(tw·wrap·자간 진행)은 늘 설계 480p 측정 컨텍스트(`_M`)에서 한다. 장치 배율(1080p)
컨텍스트에서 재면 힌팅이 장치 화소로 폭을 반올림해 줄바꿈·카드 폭·라벨 충돌이 480p 와 달라진다. 그리기만 장치 해상도.
"""

from __future__ import annotations

import math
import re
import subprocess
from functools import lru_cache

import cairo

from engine.style import DISPLAY_SPACE, FONT

HANGUL = re.compile("[ᄀ-ᇿ㄰-㆏가-힣]")
MONO = ("mono", "monom")
DISP = ("disp", "dispm")


class FontMissingError(RuntimeError):
    """프로젝트 글꼴이 설치되지 않아 fontconfig 가 다른 글꼴로 대체했다(D-0050 NB10 검사기, v3.6.0 NB16 렌더 경로)."""


@lru_cache(maxsize=None)
def fc_match(family: str) -> tuple[str, str]:
    """fontconfig 가 이 패밀리 이름으로 고른 (패밀리 목록, 파일 경로)."""
    out = subprocess.run(["fc-match", "-f", "%{family}\t%{file}", family], capture_output=True, text=True, check=True).stdout
    fams, _, path = out.partition("\t")
    return fams, path.strip()


def family_found(family: str) -> bool:
    return family in (f.strip() for f in fc_match(family)[0].split(","))


@lru_cache(maxsize=None)
def require_family(family: str) -> None:
    """이름대로 찾지 못하면 FontMissingError. 패밀리마다 한 번만 fc-match 를 부른다(성공만 캐시 — 실패는 매번 예외)."""
    if not family_found(family):
        raise FontMissingError(f"글꼴 {family!r} 없음(fontconfig 대체: {fc_match(family)[0].split(',')[0]!r})"
                               " — `python tools/fetch_data.py fonts` 먼저")


GLYPH_LOG: list[tuple[float, str | None, str]] | None = None   # 켜면(list) text() 가 (크기, 역할, 문자열) 을 남긴다 — checks glyph_size(v3.6.0 D-0069)
_M = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 1, 1))   # 설계 480p 측정 컨텍스트(항등 변환, 렌더 표면과 같은 형식)


def adv(s: str, size: float, name: str) -> float:
    """한 글꼴 구간의 전진 폭(설계 px) — 측정 컨텍스트에서."""
    font(_M, name, size)
    return _M.text_extents(s).x_advance


def font(ctx: cairo.Context, name: str, size: float) -> None:
    fam, b = FONT[name]
    require_family(fam)
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
         spacing: float = 0.0, halo_a: float = 0.8, role: str | None = None) -> float:
    """role = 글자 역할(규칙 qa_checks.glyph_size_exempt 의 이름). 없으면 최소 글자 검사 예외 대상이 아니다(기본 엄격, D-0069)."""
    if a <= 0.01 or not s:
        return 0
    if GLYPH_LOG is not None:
        GLYPH_LOG.append((size, role, s))
    if name in MONO and HANGUL.search(s):
        runs = mixed_runs(s, name)
        w = sum(tw(ctx, r, size, f) for r, f in runs)
        if anchor == "c":
            x -= w / 2
        elif anchor == "r":
            x -= w
        log, globals()["GLYPH_LOG"] = GLYPH_LOG, None   # 런 분할은 한 문자열로 이미 기록했다
        try:
            for r, f in runs:
                x += text(ctx, r, x, y, size, f, col, a, halo, "l", 0.0, halo_a)
        finally:
            globals()["GLYPH_LOG"] = log
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
            xx += adv(ch, size, name) + spacing
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
    if name in DISP and " " in s:
        return sum(size * DISPLAY_SPACE if ch == " " else adv(ch, size, name) for ch in s)
    return adv(s, size, name)


def rrect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def wrap(ctx: cairo.Context, s: str, maxw: float, size: float, name: str) -> list[str]:
    font(_M, name, size)
    words = s.split(" ")
    lines: list[str] = []
    cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if _M.text_extents(t).x_advance > maxw and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines

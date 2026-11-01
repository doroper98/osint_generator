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

from engine.style import DISPLAY_SPACE, FONT, GLYPH_FALLBACK, UNIT_FONT

HANGUL = re.compile("[ᄀ-ᇿ㄰-㆏가-힣]")
MONO = ("mono", "monom")
DISP = ("disp", "dispm")
UNIT_WEIGHT = {"sans": {"disp": "sansbb", "dispm": "sansb"}}   # unit_font 이름 → display 굵기별 같은 무게 글꼴(engine.style.FONT 키)


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


# v5.18.0 D-0161 §4 — 켜면(list) contrast= 를 준 text() 가 (종류, 장치 좌표 상자, 글자색, 알파, 문자열)을 남긴다 — checks map_contrast
CONTRAST_LOG: list[tuple[str, tuple[float, float, float, float], tuple, float, str]] | None = None
# v5.21.2 D-0186 §2-1 — 국소 대비 보정. (테마 label_contrast_fix, 문턱 map_contrast_text, 최소 알파 map_contrast_min_alpha) 를 렌더가 프레임마다 건다.
# contrast="required" 글자를 그린 직후 실제 바탕 대비가 문턱 미만이면 그 글자만 fix halo 로 다시 그린다. CONTRAST_FIXED = 이름 → 보정 전 최저 대비
CONTRAST_FIX: tuple | None = None
CONTRAST_FIXED: dict[str, float] = {}
CONTRAST_PENDING: list[tuple] = []   # 이번 프레임의 required 글자(장치 상자·행렬·검사 기록 항목·다시 그릴 인자) — flush_contrast_fix 가 비운다
_FIXING = False
GLYPH_LOG: list[tuple[float, str | None, str]] | None = None   # 켜면(list) text() 가 (크기, 역할, 문자열) 을 남긴다 — checks glyph_size(v3.6.0 D-0069)
FONT_LOG: set[str] | None = None   # 켜면(set) 실제로 글자를 그린 글꼴 이름(engine.style.FONT 키)을 모은다 — 카탈로그 판 라벨(v7.4.0 D-0251)
DISP_LATIN: list[str] | None = None   # v7.4.0 D-0229 §2.4(UF-111) — 켜면 display 글꼴로 그린 문자열 중 라틴 소문자가 남은 것(checks unit_glyph_font)
GLYPH_MISS: list[tuple[str, str, str]] | None = None   # v4.4.0 — 켜면 text() 가 **그 글꼴**에 없는 글자를 (글꼴 이름, 글자, 문자열)로 남긴다(checks glyphs)


@lru_cache(maxsize=None)
def font_cmap(name: str) -> frozenset[int]:
    """글꼴 이름(engine.style.FONT 키) → 그 파일의 cmap(fontTools). v4.4.0 — 글리프 검사를 '프로젝트 글꼴 중 하나'가 아니라
    실제로 그리는 글꼴 기준으로(카드 큰 숫자 글꼴에 없는 '−' 가 두부 상자로 나온 사고, fed_policy_2026 v1)."""
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    fam, _ = FONT[name]
    require_family(fam)
    f = TTFont(fc_match(fam)[1], fontNumber=0, lazy=True)
    return frozenset(f.getBestCmap() or {})
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


UNIT_TAIL = re.compile(r"\s*[A-Za-z][A-Za-z/]*$")   # v7.4.0 D-0229 §2.4 — 숫자 뒤 라틴 단위 꼬리(t·kb/d·mb/d·bbl). %·$ 는 display 글리프 그대로


def unit_split(s: str, name: str) -> "tuple[str, str, str] | None":
    """display 글꼴 문자열의 끝 라틴 단위를 떼어 (머리, 단위, 단위 글꼴) — 머리에 숫자가 있을 때만(제목 등 글자 문자열은 그대로).
    단위 글꼴 = rules fonts.unit_font 의 같은 굵기(disp → sansbb, dispm → sansb). unit_font 가 없으면 None(UF-111 십자형 t)."""
    uf = UNIT_FONT
    if uf is None or name not in DISP:
        return None
    m = UNIT_TAIL.search(s)
    if m is None or not re.search(r"\d", s[:m.start()]):
        return None
    return s[:m.start()], s[m.start():], UNIT_WEIGHT[uf][name]


def unit_face(unit: str, name: str = "disp") -> str:
    """따로 그리는 단위 글자(패널 unit 칸)의 글꼴 — 라틴 글자가 있으면 unit_font 같은 굵기, 아니면 display 그대로(v7.4.0 UF-111)."""
    return UNIT_WEIGHT[UNIT_FONT][name] if UNIT_FONT is not None and re.search("[A-Za-z]", unit) else name


def fallback_runs(s: str, name: str) -> "list[list[str]] | None":
    """v7.4.0 D-0250(UF-131) — rules fonts.glyph_fallback: 그 글꼴 cmap 에 없는 글자만 대체 글꼴 런으로. 대체가 필요 없으면 None."""
    fb = GLYPH_FALLBACK.get(name)
    if fb is None:
        return None
    cm = font_cmap(name)
    if all(ch.isspace() or ord(ch) in cm for ch in s):
        return None
    runs: list[list[str]] = []
    for ch in s:
        f = name if ch.isspace() or ord(ch) in cm else fb
        if runs and runs[-1][1] == f:
            runs[-1][0] += ch
        else:
            runs.append([ch, f])
    return runs


def drawn_missing(s: str, name: str) -> list[str]:
    """실제로 그리는 글꼴(대체 사슬 반영) 기준 없는 글자 — checks glyphs 의 전 문자열 대조(UF-131)."""
    runs = fallback_runs(s, name) or [[s, name]]
    return [ch for r, f in runs for ch in dict.fromkeys(r) if not ch.isspace() and ord(ch) not in font_cmap(f)]


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


HALO_RGB = (0.02, 0.03, 0.05)   # 글자 테두리 기본색(rules geo.themes.dark.map.halo 와 같음 — 지도 밖 글자는 테마와 무관)


def text(ctx: cairo.Context, s: str, x: float, y: float, size: float, name: str = "sansm",
         col: tuple = (1, 1, 1), a: float = 1.0, halo: float = 3.0, anchor: str = "l",
         spacing: float = 0.0, halo_a: float = 0.8, role: str | None = None,
         halo_rgb: tuple = HALO_RGB, contrast: str | None = None) -> float:
    """role = 글자 역할(규칙 qa_checks.glyph_size_exempt 의 이름). 없으면 최소 글자 검사 예외 대상이 아니다(기본 엄격, D-0069).
    halo_rgb = 글자 테두리 색(v5.13.0 D-0153 Q0-2 — 지도 지명만 테마 값을 넘긴다. 기본 = 종전 값)."""
    if a <= 0.01 or not s:
        return 0
    x_arg = x
    if GLYPH_LOG is not None:
        GLYPH_LOG.append((size, role, s))
    us = unit_split(s, name)
    if us is not None:   # v7.4.0 D-0229 §2.4(UF-111) — 숫자는 display, 단위 꼬리는 단위 글꼴(꼬리 있는 t)
        head, unit, uf = us
        w = tw(ctx, s, size, name)
        x -= w / 2 if anchor == "c" else w if anchor == "r" else 0
        log, globals()["GLYPH_LOG"] = GLYPH_LOG, None
        try:
            x += text(ctx, head, x, y, size, name, col, a, halo, "l", spacing, halo_a, halo_rgb=halo_rgb)
            text(ctx, unit, x, y, size, uf, col, a, halo, "l", 0.0, halo_a, halo_rgb=halo_rgb)
        finally:
            globals()["GLYPH_LOG"] = log
        return w
    fr = fallback_runs(s, name) if not (name in MONO and HANGUL.search(s)) else None
    if fr is not None:   # v7.4.0 D-0250(UF-131) — 없는 글자만 대체 글꼴(같은 굵기)
        w = sum(tw(ctx, r, size, f) for r, f in fr)
        x -= w / 2 if anchor == "c" else w if anchor == "r" else 0
        if GLYPH_MISS is not None:
            GLYPH_MISS.extend((name, ch, s[:40]) for ch in drawn_missing(s, name))
        log, globals()["GLYPH_LOG"] = GLYPH_LOG, None
        miss, globals()["GLYPH_MISS"] = GLYPH_MISS, None
        try:
            for r, f in fr:
                x += text(ctx, r, x, y, size, f, col, a, halo, "l", 0.0, halo_a, halo_rgb=halo_rgb)
        finally:
            globals()["GLYPH_LOG"], globals()["GLYPH_MISS"] = log, miss
        return w
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
                x += text(ctx, r, x, y, size, f, col, a, halo, "l", 0.0, halo_a, halo_rgb=halo_rgb)
        finally:
            globals()["GLYPH_LOG"] = log
        return w
    font(ctx, name, size)
    if DISP_LATIN is not None and name in DISP and re.search("[a-z]", s):
        DISP_LATIN.append(s)
    if GLYPH_MISS is not None:
        cm = font_cmap(name)
        GLYPH_MISS.extend((name, ch, s[:40]) for ch in dict.fromkeys(s) if not ch.isspace() and ord(ch) not in cm)
    disp = name in DISP and " " in s
    if disp and not spacing:
        spacing = 0.0001
    w = tw(ctx, s, size, name) + spacing * max(0, len(s) - 1)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    font(ctx, name, size)
    if FONT_LOG is not None:
        FONT_LOG.add(name)
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
        ctx.set_source_rgba(*halo_rgb, halo_a * a)
        ctx.set_line_width(halo)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*col[:3], a)
    ctx.fill()
    if contrast is not None and CONTRAST_LOG is not None:   # 지도 위 글자 대비 측정 대상(required | aux) — 설계 상자 → 장치 상자
        xs, ys = zip(*(ctx.user_to_device(px, py) for px in (x, x + w) for py in (y - size * 0.85, y + size * 0.25)))
        CONTRAST_LOG.append((contrast, (min(xs), min(ys), max(xs), max(ys)), tuple(col[:3]), a, s))
    if contrast == "required" and CONTRAST_FIX is not None and not _FIXING and a >= CONTRAST_FIX[2]:
        xs, ys = zip(*(ctx.user_to_device(px, py) for px in (x, x + w) for py in (y - size * 0.85, y + size * 0.25)))
        CONTRAST_PENDING.append(((min(xs), min(ys), max(xs), max(ys)), ctx.get_matrix(), CONTRAST_LOG[-1] if CONTRAST_LOG else None,
                                 (s, x_arg, y, size, name, col, a, anchor, spacing, halo_rgb)))
    return w


def flush_contrast_fix(ctx: cairo.Context) -> None:
    """v5.21.2 D-0186 §2-1 — 지도 층이 다 그려진 뒤(검사 스냅숏 직전) 미뤄 둔 required 글자를 실제 바탕에서 잰다(검사와 같은 식·같은 시점,
    engine.contrast). 문턱 미만인 글자만 fix halo 로 그 위에 다시 그리고, 보정 전 측정 항목은 검사 기록에서 뺀다(다시 그린 글자가 새로 기록).
    통과한 글자는 손대지 않는다(골든 바이트 무변화)."""
    global _FIXING
    from engine.contrast import surface_text_ratio  # noqa: PLC0415

    pend = list(CONTRAST_PENDING)
    CONTRAST_PENDING.clear()
    if CONTRAST_FIX is None or not pend:
        return
    fix, lim, _ = CONTRAST_FIX
    bad = []
    for box, mat, logged, args in pend:
        r = surface_text_ratio(ctx, box, args[5])
        if r is not None and r < lim:
            bad.append((r, mat, logged, args))
    if not bad:
        return
    m0 = ctx.get_matrix()
    _FIXING = True
    try:
        for r, mat, logged, (s, x, y, size, name, col, a, anchor, spacing, halo_rgb) in bad:
            if logged is not None and CONTRAST_LOG and logged in CONTRAST_LOG:
                CONTRAST_LOG.remove(logged)
            ctx.set_matrix(mat)
            text(ctx, s, x, y, size, name, col, a, fix.halo, anchor, spacing, fix.halo_a, halo_rgb=halo_rgb, contrast="required")
            CONTRAST_FIXED[s] = min(r, CONTRAST_FIXED.get(s, r))
    finally:
        _FIXING = False
        ctx.set_matrix(m0)


def tw(ctx: cairo.Context, s: str, size: float, name: str) -> float:
    us = unit_split(s, name)
    if us is not None:
        return tw(ctx, us[0], size, name) + tw(ctx, us[1], size, us[2])
    if not (name in MONO and HANGUL.search(s)) and (fr := fallback_runs(s, name)) is not None:   # v7.4.0 D-0250
        return sum(tw(ctx, r, size, f) for r, f in fr)
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

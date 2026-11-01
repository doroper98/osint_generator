"""병종 픽토그램 — 고대 부호 세트 병종을 한눈에 알리는 단색 벡터 글리프(v7.4.0 전쟁사 D-0605 ③, 사용자 UF-252).

그림은 전부 코드 경로(cairo)다. 남의 그림을 옮기지 않는다(권리 문제 없음, 참고 그림 조판 이식 금지 LLM-AP-022).
좌표 = 글리프 상자 [-1, 1] × [-1, 1](y 아래로). 크기·테두리는 호출자가 규칙 값(rules war_history.symbol_sets.glyph)으로 준다.
등록 = GLYPHS. 규칙 symbol_sets.<시대>.glyphs 의 값은 전부 여기 있어야 하고(P10), 여기 있는 것은 전부 갤러리 칸이 있다(시험이 강제).

- heavy_inf 중무장보병 = 큰 방패(가운데 돌기) 뒤 볏 달린 투구 + 세운 창
- light_inf 경무장보병 = 투창을 든 사람
- heavy_cav 중기병 = 말 + 기수 + 앞으로 겨눈 긴 창
- light_cav 경기병 = 말 + 기수 + 치켜든 짧은 투창
- skirmisher 투석·투창병 = 머리 위로 돌리는 투석끈(고리 + 돌)을 든 사람
- elephant 코끼리 = 몸통·머리·코·다리 윤곽
"""

from __future__ import annotations

import math
from typing import Callable

import cairo

Prim = tuple[str, Callable[[cairo.Context], None], float]   # (fill | stroke, 경로 함수, 선 두께[글리프 단위])


def _ellipse(ctx: cairo.Context, cx: float, cy: float, rx: float, ry: float) -> None:
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def _rrect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def _line(*pts: tuple[float, float]) -> Callable[[cairo.Context], None]:
    def f(ctx: cairo.Context) -> None:
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
    return f


def _person(x: float, top: float) -> list[Prim]:
    """서 있는 사람(머리 원 + 몸통 + 다리) — 경보병·투석병 공용."""
    return [("fill", lambda c: _ellipse(c, x, top + 0.17, 0.17, 0.17), 0),
            ("stroke", _line((x, top + 0.36), (x, top + 1.05)), 0.2),
            ("stroke", _line((x - 0.3, top + 1.6), (x, top + 1.05), (x + 0.3, top + 1.6)), 0.18)]


def _horse(lead: float) -> list[Prim]:
    """말(오른쪽을 본다) — 몸통 타원 + 목·머리 + 네 다리. lead = 앞다리 앞으로 뻗음."""
    def body(c: cairo.Context) -> None:
        _ellipse(c, -0.1, 0.25, 0.62, 0.27)

    def neck(c: cairo.Context) -> None:
        c.move_to(0.32, 0.12)
        c.line_to(0.62, -0.32)
        c.line_to(0.95, -0.2)
        c.line_to(0.9, -0.06)
        c.line_to(0.64, -0.1)
        c.line_to(0.52, 0.3)
        c.close_path()

    return [("fill", body, 0), ("fill", neck, 0),
            ("stroke", _line((0.38, 0.4), (0.42 + lead, 0.92)), 0.13),
            ("stroke", _line((0.2, 0.42), (0.2, 0.92)), 0.13),
            ("stroke", _line((-0.42, 0.42), (-0.5, 0.92)), 0.13),
            ("stroke", _line((-0.6, 0.38), (-0.72 - lead, 0.9)), 0.13),
            ("stroke", _line((-0.66, 0.12), (-0.95, 0.42)), 0.11)]   # 꼬리


def _rider() -> list[Prim]:
    return [("fill", lambda c: _ellipse(c, -0.08, -0.62, 0.14, 0.14), 0),
            ("stroke", _line((-0.08, -0.46), (-0.04, 0.02)), 0.18)]


def heavy_inf() -> list[Prim]:
    def helmet(c: cairo.Context) -> None:
        c.new_sub_path()
        c.arc(0.12, -0.5, 0.3, math.pi, 2 * math.pi)
        c.line_to(0.42, -0.38)
        c.line_to(-0.18, -0.38)
        c.close_path()

    return [("stroke", _line((0.62, 0.98), (0.62, -0.78)), 0.12),                                # 세운 창
            ("fill", _line((0.62, -1.0), (0.5, -0.74), (0.74, -0.74)), 0),
            ("fill", helmet, 0), ("fill", lambda c: _rrect(c, 0.02, -0.98, 0.2, 0.22, 0.06), 0),   # 투구 + 볏
            ("fill", lambda c: _rrect(c, -0.62, -0.28, 0.98, 1.26, 0.28), 0),                     # 큰 방패
            ("cut", lambda c: _ellipse(c, -0.13, 0.35, 0.15, 0.15), 0),                           # 방패 돌기(뚫어 보인다)
            ("cut_stroke", _line((-0.13, -0.12), (-0.13, 0.14)), 0.09), ("cut_stroke", _line((-0.13, 0.56), (-0.13, 0.8)), 0.09)]


def light_inf() -> list[Prim]:
    return [*_person(-0.15, -0.8), ("stroke", _line((-0.15, -0.2), (0.3, -0.45)), 0.15),
            ("stroke", _line((-0.2, 0.75), (0.75, -0.95)), 0.1),                                    # 투창
            ("fill", _line((0.75, -0.95), (0.6, -0.78), (0.82, -0.8)), 0)]


def heavy_cav() -> list[Prim]:
    return [*_horse(0.08), *_rider(), ("stroke", _line((-0.55, -0.22), (1.0, -0.5)), 0.1),               # 긴 창(앞으로)
            ("fill", lambda c: _ellipse(c, -0.32, -0.2, 0.17, 0.24), 0)]                                # 기수 방패


def light_cav() -> list[Prim]:
    return [*_horse(0.2), *_rider(), ("stroke", _line((-0.08, -0.3), (0.2, -0.7)), 0.13),
            ("stroke", _line((0.0, -0.4), (0.55, -0.98)), 0.09)]                                         # 치켜든 투창


def skirmisher() -> list[Prim]:
    def loop(c: cairo.Context) -> None:
        c.new_sub_path()
        c.arc(0.42, -0.62, 0.32, 0, 2 * math.pi)

    return [*_person(-0.2, -0.65), ("stroke", _line((-0.2, -0.1), (0.2, -0.42)), 0.15),
            ("stroke", loop, 0.08), ("fill", lambda c: _ellipse(c, 0.74, -0.62, 0.11, 0.11), 0)]


def elephant() -> list[Prim]:
    def body(c: cairo.Context) -> None:
        _ellipse(c, -0.15, 0.0, 0.66, 0.42)
        _ellipse(c, 0.52, -0.22, 0.3, 0.3)

    def trunk(c: cairo.Context) -> None:
        c.move_to(0.74, -0.12)
        c.curve_to(0.95, 0.2, 0.92, 0.55, 0.78, 0.7)

    return [("fill", body, 0), ("stroke", trunk, 0.14),
            ("fill", lambda c: _rrect(c, 0.2, 0.2, 0.2, 0.62, 0.06), 0),
            ("fill", lambda c: _rrect(c, -0.12, 0.25, 0.2, 0.57, 0.06), 0),
            ("fill", lambda c: _rrect(c, -0.5, 0.22, 0.2, 0.6, 0.06), 0),
            ("fill", lambda c: _rrect(c, -0.76, 0.12, 0.2, 0.7, 0.06), 0),
            ("cut", lambda c: _ellipse(c, 0.42, -0.3, 0.12, 0.17), 0),                                 # 귀 윤곽
            ("stroke", _line((0.5, 0.05), (0.72, 0.18)), 0.07)]                                          # 상아


GLYPHS: dict[str, Callable[[], list[Prim]]] = {
    "heavy_inf": heavy_inf, "light_inf": light_inf, "heavy_cav": heavy_cav,
    "light_cav": light_cav, "skirmisher": skirmisher, "elephant": elephant,
}


class GlyphError(KeyError):
    pass


def draw_glyph(ctx: cairo.Context, name: str, x: float, y: float, size: float, rgb: tuple, alpha: float,
               halo_rgb: tuple, halo_w: float, halo_a: float = 0.85) -> None:
    """(x, y) 가운데에 높이 size px 글리프. 바깥 테두리(halo) → 본색 순. cut = 본색 위를 테두리 색으로 뚫는다(방패 돌기·귀)."""
    if name not in GLYPHS:
        raise GlyphError(f"병종 글리프 없음: {name!r} — engine.glyphs.arms.GLYPHS {sorted(GLYPHS)}")
    prims = GLYPHS[name]()
    s = size / 2
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for kind, path, w in prims:   # 1) 테두리 — 본 모양을 halo_w px 만큼 두껍게
        if kind.startswith("cut"):
            continue
        ctx.new_path()
        path(ctx)
        ctx.set_source_rgba(*halo_rgb, halo_a * alpha)
        ctx.set_line_width(w + 2 * halo_w / s)
        ctx.stroke_preserve()
        if kind == "fill":
            ctx.fill()
        ctx.new_path()
    for kind, path, w in prims:   # 2) 본색
        ctx.new_path()
        path(ctx)
        ctx.set_source_rgba(*(halo_rgb if kind.startswith("cut") else rgb), alpha)
        if kind in ("fill", "cut"):
            ctx.fill()
        else:
            ctx.set_line_width(w)
            ctx.stroke()
    ctx.new_path()
    ctx.restore()

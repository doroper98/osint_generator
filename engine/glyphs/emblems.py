"""진영 휘장 재작도 — 유물에 근거한 당대 상징만(v7.4.0 전쟁사 D-0605 ②·D-0606 A, 사용자 UF-252).

휘장을 지어내지 않는다(D-0307 §3, C9). 도안마다 근거 유물이 `assets/emblems/registry.json` reconstructions 레코드에 있고
(basis·basis_title·basis_license·reconstruction: true), 화면에는 코드가 "…재현" 라벨을 붙인다.
여기 그림은 그 유물의 기호를 단순한 기하로 다시 그린 것이다(사진·남의 벡터를 옮기지 않는다).

- tanit 타니트 기호 = 원(머리) + 가로 막대(팔, 끝이 위로 굽음) + 삼각형(몸). 근거: 루브르 AO 5244 석회암 비석(기원전 3세기, PD 사진)
"""

from __future__ import annotations

from typing import Callable

import cairo

from engine.glyphs.arms import GlyphError, Prim, _ellipse, _line, draw_prims


def tanit() -> list[Prim]:
    def body(c: cairo.Context) -> None:
        c.move_to(0.0, -0.18)
        c.line_to(0.62, 0.98)
        c.line_to(-0.62, 0.98)
        c.close_path()

    return [("fill", body, 0),
            ("stroke", _line((-0.66, -0.42), (-0.66, -0.26), (0.66, -0.26), (0.66, -0.42)), 0.16),   # 팔(끝이 위로)
            ("fill", lambda c: _ellipse(c, 0, -0.68, 0.27, 0.27), 0)]                               # 머리 원반


EMBLEMS: dict[str, Callable[[], list[Prim]]] = {"tanit": tanit}


def draw_emblem(ctx: cairo.Context, name: str, x: float, y: float, size: float, rgb: tuple, alpha: float,
                halo_rgb: tuple, halo_w: float) -> None:
    if name not in EMBLEMS:
        raise GlyphError(f"휘장 재작도 없음: {name!r} — engine.glyphs.emblems.EMBLEMS {sorted(EMBLEMS)}")
    draw_prims(ctx, EMBLEMS[name](), x, y, size, rgb, alpha, halo_rgb, halo_w)

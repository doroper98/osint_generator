"""암전(dip) — 1초 검은 화면, 가운데서 카메라 cut (v2.1.0, render3 render_frame 의 dip 칠).
v7.4.0 R9(UF-902) — skin 영상(밝은 무대)의 dip 은 검정이 아니라 밝은 판(rules skin.fade_rgb)으로 갔다 돌아온다. 한가운데 알파 =
rules skin.dip.peak_alpha(그 순간 지도 ↔ 스튜디오 무대가 바뀐다). skin 이 꺼진 영상은 종전 그대로."""

from __future__ import annotations

import math

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.style import SKIN
from engine.timebase import clamp01


def draw_dip(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    d = math.sin(math.pi * clamp01((t - e["t0"]) / (e["t1"] - e["t0"])))
    if skin.active():
        ctx.set_source_rgba(*SKIN.fade_rgb, SKIN.dip.peak_alpha * d)
    else:
        ctx.set_source_rgba(0, 0, 0, 0.93 * d)
    ctx.paint()

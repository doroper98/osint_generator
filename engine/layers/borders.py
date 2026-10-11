"""국경·행정구역 선 (v2.1.0, render3 `path_rings, draw_borders`). LOD(`engine.stage.MERCATOR_LOD`): w<22 이면 fine, 행정구역은 w<24 에서 페이드 인.

v4.1.0: MercatorStage.render_base 가 부른다. 선은 무대가 미리 월드 좌표로 바꾼 고리(stage.bord·adm)다(D-0076 작업 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cairo
import numpy as np

from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.style import BORDER_GLOW as BG
from engine.timebase import smooth

if TYPE_CHECKING:
    from engine.stage import MercatorStage


_PACKS: dict[int, tuple] = {}


def _pack(items: list) -> tuple:
    """(uv, mn, mx) 목록의 묶음 — 상자 배열·크기·점 수·이어 붙인 점(v5.22.10 D-0201 결정 2). 무대 데이터는 고정이라 목록마다 한 번.
    목록 객체를 함께 보관해 id 재사용을 막는다."""
    pk = _PACKS.get(id(items))
    if pk is None or pk[0] is not items:
        mn = np.array([m for _, m, _ in items], dtype=float).reshape(-1, 2)
        mx = np.array([m for _, _, m in items], dtype=float).reshape(-1, 2)
        n = np.array([len(uv) for uv, _, _ in items])
        pk = (items, mn, mx, (mx - mn).max(axis=1) if len(items) else np.zeros(0), n,
              np.concatenate([uv for uv, _, _ in items]) if len(items) else np.zeros((0, 2)), np.concatenate([[0], np.cumsum(n)]))
        _PACKS[id(items)] = pk
    return pk


def _emit(ctx: cairo.Context, view: View, items: list, min_px: float, close: bool) -> int:
    """보이는 고리·선을 한꺼번에 화면 좌표로 바꿔 cairo 경로에 넣는다. 고르는 조건(view.visible·크기)·점·순서는 종전 한 개씩과 같다
    (같은 float64 비교·곱셈 — 골든 바이트 동일로 증명)."""
    if not items:
        return 0
    _, mn, mx, ext, _, uv, off = _pack(items)
    vis = ~((mx[:, 0] < view.x0) | (mn[:, 0] > view.x0 + view.w) | (mx[:, 1] < view.y1 - view.h) | (mn[:, 1] > view.y1))
    vis &= ~(ext * view.s < min_px)
    idx = np.flatnonzero(vis)
    if not len(idx):
        return 0
    pts = view.to_screen_arr(np.concatenate([uv[off[k]:off[k + 1]] for k in idx])).tolist()
    p = 0
    for k in idx:
        m = int(off[k + 1] - off[k])
        ctx.move_to(*pts[p])
        for x, y in pts[p + 1:p + m]:
            ctx.line_to(x, y)
        if close:
            ctx.close_path()
        p += m
    return len(idx)


def path_rings(ctx: cairo.Context, view: View, rings: list, min_px: float = 1.0) -> int:
    return _emit(ctx, view, rings, min_px, True)


def path_lines(ctx: cairo.Context, view: View, lines: list, min_px: float = 1.0) -> int:
    """열린 선(국경·해안 구간, v5.18.0) — path_rings 와 같되 닫지 않는다."""
    return _emit(ctx, view, lines, min_px, False)


def border_path(ctx: cairo.Context, stage: "MercatorStage", view: View, lod: str) -> None:
    """국경 경로 — 테마에 coast 가 있으면 공유 변만(v5.18.0 D-0161 §2), 없으면 종전처럼 모든 국가 고리."""
    ctx.new_path()
    if stage.theme.coast is not None:
        path_lines(ctx, view, stage.line_split(lod)["border"], 0.0)
        return
    for _k, rings in stage.bord[lod].items():
        path_rings(ctx, view, rings)


def draw_borders(ctx: cairo.Context, stage: "MercatorStage", view: View) -> None:
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    co = stage.theme.coast
    if co is not None:   # v5.18.0 D-0161 §2(가이드 23 §14) — 해안은 밝고 얇은 물빛 선, 국경 아래에 먼저
        ctx.new_path()
        path_lines(ctx, view, stage.line_split(lod)["coast"])
        ctx.set_source_rgba(*co.rgb, co.alpha if co.alpha is not None else 1.0)
        ctx.set_line_width(co.width)
        ctx.stroke()
    border_path(ctx, stage, view, lod)
    bo, ad_ = stage.theme.border, stage.theme.admin   # v5.13.0 D-0153 Q0-2 — 지도 테마 선 색·폭(rules geo.themes.<테마>.map)
    ba = LOD["border_alpha"]
    ctx.set_source_rgba(*bo.rgb, (ba["near"] if view.w < ba["below_w"] else ba["far"]) if bo.alpha is None else bo.alpha)
    ctx.set_line_width(bo.width)
    ctx.stroke()
    af = LOD["admin_lines_fade"]
    a = (af["alpha"] if ad_.alpha is None else ad_.alpha) * smooth((af["w"] - view.w) / af["span"])
    if a > 0.01:
        ctx.set_dash(ad_.dash)
        for _k, lst in stage.adm.items():
            ctx.new_path()
            for ad in lst:
                path_rings(ctx, view, ad["rings"], 2)
            ctx.set_source_rgba(*ad_.rgb, a)
            ctx.set_line_width(ad_.width)
            ctx.stroke()
        ctx.set_dash([])


def draw_border_glow(ctx: cairo.Context, stage: "MercatorStage", view: View, t: float) -> None:
    """v5.3.1 국경선 글로우(시안 — 사용자 제안 2026-10-02, valdai-2026 한정; 켜기 = direction stage_config.mercator.border_glow).
    국경선(draw_borders 와 같은 LOD 고리, 행정구역 선 제외) 위에 옅은 빛(rules border_glow.halo)을 상시 깔고, 짧은 빛 조각(run_seg_px)이
    run_period_px 간격으로 선을 따라 run_speed_px/초로 천천히 흐른다(cairo 대시 오프셋). 수치는 전부 rules border_glow."""
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    ctx.save()
    border_path(ctx, stage, view, lod)   # v5.18.0 — 해안을 분리한 테마는 국경(공유 변)에만 글로우
    path = ctx.copy_path()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    tg = stage.theme.border_glow   # v5.18.0 D-0161 §2 — 테마별 글로우 값(없으면 공통)
    rgb = tg.rgb if tg is not None and tg.rgb is not None else BG.rgb
    halo = tg.halo if tg is not None and tg.halo is not None else BG.halo
    run_layers = tg.run_layers if tg is not None and tg.run_layers is not None else BG.run_layers
    for w, a in halo:
        ctx.new_path()
        ctx.append_path(path)
        ctx.set_source_rgba(*rgb, a)
        ctx.set_line_width(w)
        ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_dash([BG.run_seg_px, BG.run_period_px - BG.run_seg_px], -BG.run_speed_px * t)
    for w, a in run_layers:
        ctx.new_path()
        ctx.append_path(path)
        ctx.set_source_rgba(*rgb, a)
        ctx.set_line_width(w)
        ctx.stroke()
    ctx.restore()

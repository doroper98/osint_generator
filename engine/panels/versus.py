"""패널 versus — 두 입장 병렬, 같은 무게 (v2.1.0, render3 `P_versus`, G4 양측 균형)."""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.panels.base import panel_title
from engine.style import C, MOTION, PANEL, W_OUT
from engine.timebase import smooth
from engine.typography import rrect, text, tw, wrap
from rules import load_rules

VS = load_rules().panels.versus   # v4.8.0 D-0101 §3 — 글자 크기(옛 리터럴)

AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
_COLS = (("teal", 60), ("amber", 450))  # 왼쪽·오른쪽 기둥의 색·x (v3 합격 값)
BOX_W = 344          # 기둥 상자 폭(v3 합격 값)
ITEM_X = 38          # 상자 왼쪽 → 항목 글자 시작


class VersusOverflowError(ValueError):
    """versus 항목 글자가 기둥 상자를 넘는다 — 조용히 자르지 않는다(15 P6). 연출이 문구를 줄인다."""


def item_lines(ctx: cairo.Context, s: str) -> list[str]:
    """v5.3.1(사용자 지적 2026-10-02 — "준비한다는 정보가 있다"의 '다'가 상자 밖으로 나감) — 상자 안 폭에 맞춰 접은 줄.
    한 줄에 들어가면 그대로(옛 출력과 같다). item_max_lines(rules panels.versus) 를 넘거나 한 낱말이 폭보다 길면 VersusOverflowError."""
    room = BOX_W - ITEM_X - VS.item_pad_r
    if tw(ctx, s, VS.item_size, "serifb") <= room:
        return [s]
    lines = wrap(ctx, s, room, VS.item_size, "serifb")
    if len(lines) > VS.item_max_lines or any(tw(ctx, ln, VS.item_size, "serifb") > room for ln in lines):
        raise VersusOverflowError(f"[panel-overflow] versus 항목 {s!r} — {len(lines)}줄 > {VS.item_max_lines} 또는 폭 > {room}px, 문구를 줄인다")
    return lines


def half_u(t: float, e: dict) -> float:
    """왼쪽 모음 진행(0 = 좌우 기둥, 1 = 왼쪽 위아래). half_left_from 이 없으면 0(v7.4.0 D-0629 §3)."""
    hf = e.get("half_left_from")
    if hf is None:
        return 0.0
    if VS.half_left is None:
        raise VersusOverflowError("[panel-overflow] versus half_left_from 을 썼는데 rules panels.versus.half_left 가 없다")
    return smooth((t - hf) / VS.half_left.move_sec)


def half_frame() -> tuple[float, float, float, float]:
    """왼쪽 모음 기둥 하나의 (x, 위 y, 폭, 높이) — 위 기둥 기준, 아래 기둥은 높이 + gap 아래."""
    hl = VS.half_left
    x, y, w = load_rules().placement.slots[hl.slot].box
    return float(x), float(y), float(w), (hl.bottom - y - hl.gap) / 2


def half_box() -> tuple[float, float, float, float]:
    """왼쪽 모음 패널 상자(설계 px) — 패널 제목 줄 ~ 아래 기둥 끝. [card-over-panel] 이 쓴다."""
    x, _, w, _ = half_frame()
    return x, PANEL.title_y - PANEL.title_size, x + w, VS.half_left.bottom


def _half_items(ctx: cairo.Context, side: dict) -> tuple[list[float], list[list[str]]]:
    """왼쪽 모음 기둥 안 항목 기준선(상자 위 기준)과 접힌 줄. 출처 줄 위를 넘으면 VersusOverflowError(P6)."""
    hl = VS.half_left
    _, _, _, h = half_frame()
    ys, lines, y = [], [], hl.item_dy0
    for it in side["items"]:
        ln = item_lines(ctx, it["text"])
        ys.append(y)
        lines.append(ln)
        y += hl.item_step + (len(ln) - 1) * VS.item_line_gap
    last = ys[-1] + (len(lines[-1]) - 1) * VS.item_line_gap
    if last + VS.item_size > h - hl.src_pad - VS.src_size:
        raise VersusOverflowError(f"[panel-overflow] versus 왼쪽 모음 기둥 {side['title']!r} 항목이 출처 줄과 겹친다 — 항목을 줄인다")
    return ys, lines


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    u = half_u(t, e)
    L = lambda p, q: p + (q - p) * u  # noqa: E731
    hx = hy = hw = hh = 0.0
    if e.get("half_left_from") is not None:
        hx, hy, hw, hh = half_frame()
    panel_title(ctx, a, e["title"], cx=L(W_OUT / 2, hx + hw / 2) if u > 0 else None)
    for i, ((cname, x0), side) in enumerate(zip(_COLS, e["sides"])):
        col = C[cname]
        items = side["items"]
        fa = a * smooth((t - items[0]["t"] + 0.6) / MOTION["panel_item_in_sec"])   # v7.4.0 UF-159 ×1.5
        if fa <= 0:
            continue
        hyi = hy + i * (hh + (VS.half_left.gap if VS.half_left else 0))
        if e.get("half_left_from") is not None:
            iys, ilines = _half_items(ctx, side)
        else:
            iys, ilines = [], []
        x, y, bw, bh = L(x0, hx), L(120, hyi), L(BOX_W, hw), L(262, hh)
        rrect(ctx, x, y, bw, bh, 6)
        ctx.set_source_rgba(0.07, 0.08, 0.12, 0.92 * fa)
        ctx.fill()
        ctx.set_source_rgba(*col, fa)
        ctx.rectangle(x, y, bw, 3)
        ctx.fill()
        text(ctx, side["title"], x + 22, y + L(36, VS.half_left.title_dy if VS.half_left else 36), VS.title_size, "sansb", col, fa, 0, "l")
        for j, it in enumerate(items):
            ia = a * smooth((t - it["t"]) / MOTION["panel_item_fast_in_sec"])
            iy = y + L(76 + j * 50, iys[j] if iys else 76 + j * 50)
            ctx.arc(x + 26, iy - 5, 3, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, ia)
            ctx.fill()
            for k, ln in enumerate(ilines[j] if ilines else item_lines(ctx, it["text"])):
                text(ctx, ln, x + ITEM_X, iy + k * VS.item_line_gap, VS.item_size, "serifb", (1, 1, 1), ia, 0, "l")
        text(ctx, side["src"], x + 22, y + L(246, bh - (VS.half_left.src_pad if VS.half_left else 16)), VS.src_size, "sans", C["muted"], fa, 0, "l")

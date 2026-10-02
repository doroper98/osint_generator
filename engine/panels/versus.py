"""패널 versus — 두 입장 병렬, 같은 무게 (v2.1.0, render3 `P_versus`, G4 양측 균형)."""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.panels.base import panel_title
from engine.style import C
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


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    panel_title(ctx, a, e["title"])
    for (cname, x), side in zip(_COLS, e["sides"]):
        col = C[cname]
        items = side["items"]
        fa = a * smooth((t - items[0]["t"] + 0.6) / 0.5)
        if fa <= 0:
            continue
        rrect(ctx, x, 120, BOX_W, 262, 6)
        ctx.set_source_rgba(0.07, 0.08, 0.12, 0.92 * fa)
        ctx.fill()
        ctx.set_source_rgba(*col, fa)
        ctx.rectangle(x, 120, BOX_W, 3)
        ctx.fill()
        text(ctx, side["title"], x + 22, 156, VS.title_size, "sansb", col, fa, 0, "l")
        for i, it in enumerate(items):
            ia = a * smooth((t - it["t"]) / 0.45)
            ctx.arc(x + 26, 196 + i * 50 - 5, 3, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, ia)
            ctx.fill()
            for k, ln in enumerate(item_lines(ctx, it["text"])):
                text(ctx, ln, x + ITEM_X, 196 + i * 50 + k * VS.item_line_gap, VS.item_size, "serifb", (1, 1, 1), ia, 0, "l")
        text(ctx, side["src"], x + 22, 366, VS.src_size, "sans", C["muted"], fa, 0, "l")

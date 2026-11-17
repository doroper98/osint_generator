"""패널 dots — 도트 매트릭스(비율·규모) (v2.5.0, v2 render2 `P_dots`, 08 §8). 수치는 `panels.charts.dots`."""

from __future__ import annotations

import math

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.panels import skin_panel
from engine.panels.base import chart
from engine.style import C
from engine.timebase import smooth
from engine.typography import text, tw, unit_face
from rules import load_rules

AXIS = "value"   # v4.3.0 D-0087 — 축 종류(값 축). 정직성 검사 적용 = rules qa_checks.chart_targets
D = load_rules().panels.charts.dots


def _labels_skin(ctx: cairo.Context, lt: float, e: dict, la: float, a: float) -> None:
    """skin — 큰 숫자·단위 = 디스플레이 강조 잉크, 캡션 잉크 primary, 설명 secondary, 가는 선, 메모 꼬리표 tertiary·값 잉크 primary."""
    big = skin.ACCENT_INK
    text(ctx, e["big"], D.big.x, D.big.y, D.big.size, "disp", big, la, 0, "l")
    if e["unit"]:
        ux = D.big.x + max(D.unit_dx, tw(ctx, e["big"], D.big.size, "disp") + D.unit_gap)
        text(ctx, e["unit"], ux, D.big.y, D.unit_size, unit_face(e["unit"]), big, la, 0, "l")
    text(ctx, e["caption"], D.caption.x, D.caption.y, D.caption.size, "sansb", skin.INK, la, 0, "l")
    text(ctx, e["detail"], D.detail.x, D.detail.y, D.detail.size, "sansm", skin.INK2, la, 0, "l")
    if e["note_value"]:
        lb = a * smooth((lt - D.note_sec) / D.label_fade_sec)
        rx, ry, rw, _ = D.rule
        skin_panel.hline(ctx, rx, rx + rw, ry, lb)
        n = D.note_label
        text(ctx, e["note_label"], n.x, n.y, n.size, "sansb", skin.INK3, lb, 0, "l", spacing=n.spacing)
        text(ctx, e["note_value"], D.note_value.x, D.note_value.y, D.note_value.size, "disp", skin.INK, lb, 0, "l")
        text(ctx, e["note_caption"], D.note_caption.x, D.note_caption.y, D.note_caption.size, "sansm", skin.INK2, lb, 0, "l")


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    sk = skin.active()   # v7.4.0 C0.0 3a — 회색 점 = 옅은 막대 회색, 강조 점·큰 숫자 = 강조색 하나, 글자 잉크 3단(테두리 없음)
    rows, cols = D.grid
    x0, y0 = D.origin
    acol = skin.ACCENT_SHAPE if sk else C[e.get("accent") or "ru"]   # v7.4.0 D-0229 §2.6 — 강조 색 토큰
    n = e.get("total") or rows * cols
    few = n <= D.few.max_total and e.get("total") is not None   # v7.4.0 — "N 중 M": 한 줄 큰 점, 강조점 = 앞 highlight 개
    sp = min(D.few.spacing, (D.few.x1 - D.few.x0) / max(1, n - 1)) if few else D.spacing
    rad = D.few.radius if few else D.radius
    step = D.fill_step_sec * (rows * cols / n if few else 1)
    for i in range(n):
        r_, c_ = divmod(i, cols)
        f = smooth((lt - D.fill_start_sec - i * step) / D.fill_sec)
        if f <= 0:
            continue
        x, y = (D.few.x0 + i * sp, D.few.y) if few else (x0 + c_ * D.spacing, y0 + r_ * D.spacing)
        acc = i < e["highlight"]
        if acc:
            p = D.pulse_base + D.pulse_amp * math.sin(t * D.pulse_rate)
            g = cairo.RadialGradient(x, y, 0, x, y, D.pulse_r)
            g.add_color_stop_rgba(0, *acol, D.pulse_alpha * p * a)
            g.add_color_stop_rgba(1, *acol, 0)
            ctx.set_source(g)
            ctx.arc(x, y, D.pulse_r, 0, 2 * math.pi)
            ctx.fill()
        ctx.arc(x, y, rad * f, 0, 2 * math.pi)
        ctx.set_source_rgba(*(acol if acc else (skin_panel.BAR if sk else D.base_rgb)), a)
        ctx.fill()
    la = a * smooth((lt - D.label_sec) / D.label_fade_sec)
    if sk:
        _labels_skin(ctx, lt, e, la, a)
        return
    text(ctx, e["big"], D.big.x, D.big.y, D.big.size, "disp", acol, la, D.big.halo, "l")
    if e["unit"]:
        ux = D.big.x + max(D.unit_dx, tw(ctx, e["big"], D.big.size, "disp") + D.unit_gap)   # v5.3.1 — '45%' 겹침(사용자 시청 2026-10-02)
        text(ctx, e["unit"], ux, D.big.y, D.unit_size, unit_face(e["unit"]), acol, la, D.big.halo, "l")
    text(ctx, e["caption"], D.caption.x, D.caption.y, D.caption.size, "sansb", C["white"], la, D.caption.halo, "l")
    text(ctx, e["detail"], D.detail.x, D.detail.y, D.detail.size, "sansm", C["muted"], la, D.detail.halo, "l")
    if e["note_value"]:
        lb = a * smooth((lt - D.note_sec) / D.label_fade_sec)
        rx, ry, rw, ralpha = D.rule
        ctx.set_source_rgba(*C["white"], ralpha * lb)
        ctx.rectangle(rx, ry, rw, 1)
        ctx.fill()
        n = D.note_label
        text(ctx, e["note_label"], n.x, n.y, n.size, "sansb", C["gold"], lb, n.halo, "l", spacing=n.spacing)
        text(ctx, e["note_value"], D.note_value.x, D.note_value.y, D.note_value.size, "disp", C["white"], lb, 0, "l")
        text(ctx, e["note_caption"], D.note_caption.x, D.note_caption.y, D.note_caption.size, "sansm", C["muted"], lb, 0, "l")

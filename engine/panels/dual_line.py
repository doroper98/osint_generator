"""패널 dual_line — 두 계열 추세 (v2.5.0, v2 render2 `P_dual`, 08 §8). 수치는 `panels.charts.dual_line`."""

from __future__ import annotations

import math
from decimal import Decimal

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.layers.routes import glow_line
from engine.panels.base import chart
from engine.style import C
from engine.timebase import clamp01, ease_io
from engine.typography import text
from rules import load_rules

AXIS = "value"   # v4.3.0 D-0087 — 축 종류(값 축). 정직성 검사 적용 = rules qa_checks.chart_targets
L = load_rules().panels.charts.dual_line


def _fmt(v: float, prefix: str, decimals: int) -> str:
    return f"{prefix}{v:.{decimals}f}"


def step_decimals(step: float) -> int:
    """v5.3.1 — 세로축 눈금 소수 자릿수 = 눈금 간격이 필요로 하는 만큼(0.4 → 1). 옛 코드는 0 고정이라 소수 간격 축이
    "$6 · $6 · $6" 처럼 같은 값으로 찍혔다(사용자 확인 2026-10-02, 정직성). 정수 간격은 0(옛 출력 그대로)."""
    return max(0, -Decimal(str(step)).normalize().as_tuple().exponent)


class DuplicateTickError(ValueError):
    """세로축 눈금 글자가 겹친다(값이 다른 눈금이 같은 글자) — 정직성 결함(UF-57, "$6·$6·$6")."""


def tick_labels(e: dict) -> list[tuple[float, str]]:
    """세로축 눈금 (값, 글자). 서로 다른 눈금이 같은 글자면 DuplicateTickError — 렌더 전 오류(v5.22.4 UF-57, P6)."""
    lo, hi, step = e["y_min"], e["y_max"], e["y_step"]
    out = [(lo + k * step, _fmt(lo + k * step, e["y_prefix"], step_decimals(step))) for k in range(round((hi - lo) / step) + 1)]
    labels = [s for _, s in out]
    if len(set(labels)) != len(labels):
        raise DuplicateTickError(f"dual_line 세로축 눈금 글자 중복 {labels} — y_step·자릿수를 고친다(UF-57)")
    return out


def present_runs(vals: list) -> list[list[int]]:
    """값이 이어진 구간(인덱스 목록, 점 2개 이상) — 빈 값(None)에서 끊는다(v7.3.0 D232 U4, 보간 금지)."""
    runs: list[list[int]] = [[]]
    for i, v in enumerate(vals):
        if v is None:
            runs.append([])
        else:
            runs[-1].append(i)
    return [r for r in runs if len(r) >= 2]


def gap_pairs(vals: list) -> list[tuple[int, int]]:
    """v7.4.0 D-0247(UF-128) — 보간할 빈 구간: 실측 두 점 (i, j) 사이에 빈 값(None)이 하나 이상(j - i > 1). 양 끝 바깥은 없다(외삽 금지)."""
    idx = [i for i, v in enumerate(vals) if v is not None]
    return [(i, j) for i, j in zip(idx, idx[1:]) if j - i > 1]


def interpolated_idx(e: dict) -> list[list[int]]:
    """계열마다 보간으로 채운 인덱스(provenance panels[].interpolated_idx, P5). gap_policy break 면 빈 목록."""
    if L.gap_policy != "interpolate":
        return [[] for _ in e["series"]]
    return [[k for i, j in gap_pairs(ser["values"]) for k in range(i + 1, j)] for ser in e["series"]]


def gap_subtitle(e: dict) -> str | None:
    """출처 줄 + 보간 표기(rules gap_note) — 보간 구간이 있을 때만 코드가 붙인다(연출이 손으로 쓰지 않는다)."""
    sub = e.get("subtitle")
    if L.gap_policy != "interpolate" or not L.gap_note or not any(interpolated_idx(e)):
        return sub
    return f"{sub} · {L.gap_note}" if sub else L.gap_note


def record_errors(e: dict) -> list[str]:
    """v7.3.0 D232 U4 — record 를 단 계열의 값은 데이터 레코드와 같아야 한다(20 §5.1 데이터에서 직접): 값 있는 점 = 레코드 값(순서대로),
    빈 점(null) 수 = 그 사이 레코드 빈 달, open_idx = 레코드 cited.open. 어기면 렌더 전 오류(P6)."""
    from data.series import SeriesError, load_series  # noqa: PLC0415

    errs: list[str] = []
    for ser in e["series"]:
        if not ser.get("record"):
            continue
        try:
            rec = load_series(ser["record"])
        except SeriesError as ex:
            errs.append(str(ex))
            continue
        got = [v for v in ser["values"] if v is not None]
        want = [v for _, v in rec.values]
        if got != want:
            errs.append(f"dual_line 계열 {ser['label']!r} 값 {got} ≠ 레코드 {rec.series_id} {want} (값은 레코드에서만, 20 §5.1)")
        opens = [k for k, (d, _) in enumerate(rec.values) if (c := rec.citation(d)) is not None and c.open]
        idx = [i for i, v in enumerate(ser["values"]) if v is not None]
        if sorted(idx.index(i) for i in ser.get("open_idx", []) if i in idx) != opens:
            errs.append(f"dual_line 계열 {ser['label']!r} open_idx ≠ 레코드 {rec.series_id} cited.open")
    return errs


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    X0, X1 = L.x  # noqa: N806
    Y0, Y1 = L.y  # noqa: N806
    lo, hi = e["y_min"], e["y_max"]

    def fy(v: float) -> float:
        return Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)

    for v, lab in tick_labels(e):
        ctx.set_source_rgba(*C["white"], L.grid_alpha * a)
        ctx.rectangle(X0, fy(v), X1 - X0, 1)
        ctx.fill()
        text(ctx, lab, X0 + L.tick_dx, fy(v) + L.tick_dy, L.tick_size, "sansm", C["muted"], a, 0, "r")
    n = len(e["x_labels"])
    xs = [X0 + L.x_pad + (X1 - X0 - 2 * L.x_pad) * i / (n - 1) for i in range(n)]
    for x, s_ in zip(xs, e["x_labels"]):
        if e.get("x_label_rotate"):   # v5.3.1 — 45도: 글자 끝이 눈금 아래에 오도록 오른쪽 정렬로 기울인다
            ctx.save()
            ctx.translate(x + L.x_label_rot_dx, Y1 + L.x_label_rot_dy)
            ctx.rotate(-L.x_label_rot_rad)   # 화면 글자 회전(지도 투영 아님)
            text(ctx, s_, 0, 0, L.x_label_size, "sansm", C["muted"], a, 0, "r")
            ctx.restore()
        else:
            text(ctx, s_, x, Y1 + L.x_label_dy, L.x_label_size, "sansm", C["muted"], a, 0, "c")
    for si, ser in enumerate(e["series"]):
        col = C[ser["col"]]
        prog = ease_io((lt - L.draw_start_sec - si * L.draw_step_sec) / L.draw_sec)
        if prog <= 0:
            continue
        reach = X0 + L.x_pad + (X1 - X0 - 2 * L.x_pad) * prog   # 그려진 끝 x(왼쪽 → 오른쪽)
        vals = ser["values"]
        if L.gap_policy == "interpolate":   # v7.4.0 D-0247(UF-128) — 빈 달은 실측 두 점 사이 점선(연하게·점·값 라벨 없음)
            ist = L.interpolated_style
            for i, j in gap_pairs(vals):
                seg = [(xs[i] + (xs[j] - xs[i]) * u, fy(vals[i]) + (fy(vals[j]) - fy(vals[i])) * u) for u in np.linspace(0, 1, L.samples)]
                sub = [q for q in seg if q[0] <= reach]
                if len(sub) >= 2:
                    glow_line(ctx, np.array(sub), col, a * ist.alpha, L.line_width, dash=list(ist.dash))
        for run in present_runs(vals):   # 실측 구간(실선) — 빈 달 자리는 위 점선이 잇는다(break 정책이면 끊긴다)
            pts = [(xs[i], fy(vals[i])) for i in run]
            dense = []
            for i in range(len(pts) - 1):
                for s in np.linspace(0, 1, L.samples, endpoint=False):
                    dense.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * s, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * s))
            dense.append(pts[-1])
            sub = [q for q in dense if q[0] <= reach]
            if len(sub) >= 2:
                glow_line(ctx, np.array(sub), col, a, L.line_width)
        last = None
        for i, v in enumerate(vals):
            if v is None or xs[i] > reach:
                continue
            p = (xs[i], fy(v))
            last = p
            ctx.arc(p[0], p[1], L.point_r, 0, 2 * math.pi)
            if i in ser.get("open_idx", []):   # 상·하한 표기 값("4 미만") = 빈 점(테두리만)
                ctx.set_source_rgba(*col, a)
                ctx.set_line_width(L.line_width)
                ctx.stroke()
            else:
                ctx.set_source_rgba(*col, a)
                ctx.fill()
            dy = L.value_dy_above if si == 0 else L.value_dy_below
            text(ctx, _fmt(v, "", ser["decimals"]), p[0], p[1] + dy, L.value_size, "sansb", col, a, L.value_halo, "c")
        if last is not None:
            text(ctx, ser["label"], X1 + L.name_dx, last[1] + L.name_dy, L.name_size, "sansb", col,
                 a * clamp01(prog * 3 - 2), L.value_halo, "l")

"""시리즈 레이어 `series` — 데이터 레코드에서 직접 그린 계단선·꺾은선 (v4.3.0, docs/handoff/20 §5.1·§6, back_and_forth D-0084 작업 4·D-0086).

`{type: series, lane, series_id, style: step|line, grow, col}` — 값은 `data/series/<series_id>` 레코드에서만 온다(연출이 숫자를 주지 않는다).
- 세로: 레인 띠 안, 레인의 값 범위(`lane_range` — 그 레인 모든 series 의 [min(0, 최소), 최대]). 0 기준선과 범위 끝 값 라벨을 그린다.
- grow: 카메라와 함께 왼쪽→오른쪽으로 자란다(등장 문법 05). 앞끝 = (화면 왼쪽 + 화면 폭 × playhead)의 누적 최대 —
  되돌아가도 줄지 않는다. 등장 직후 grow_in_sec 동안 화면 왼쪽에서 앞끝까지 쓸어 나간다(`load_project` 가 프레임별로 미리 계산).
- 값 라벨은 드러난 마지막 점 하나(단위 포함). 레인 아래쪽에 출처·기준 시점 줄(20 §5.1 "YYYY년 M월 기준").
- 빈 달(레코드 missing, D-0086): 선을 끊고 그 자리에 "자료 없음" 표시. 보간 선분 없음.
수치·색은 `rules stage_timeline.series`·`missing_mark`(코드 리터럴 0).
"""

from __future__ import annotations

import math
from datetime import date
from typing import TYPE_CHECKING

import cairo

from data.series import load_series
from engine.style import C, FPS, TIMELINE, W_OUT
from engine.timebase import ease_out, window
from engine.typography import text

if TYPE_CHECKING:
    from engine.context import RenderCtx
    from engine.projection import View
    from engine.stage_timeline import TimelineStage

MONTHS = 12
AXIS = "value"   # D-0087 — 값 축(정직성 검사 4개 전부, rules qa_checks.chart_targets)


def lane_range(events: list[dict], lane: str) -> tuple[float, float]:
    """레인 값 범위 — 그 레인의 모든 series 값의 [min(0, 최소), 최대](0 기준선을 늘 포함, 20 §5.3)."""
    vs = [v for e in events if e["type"] == "series" and e["lane"] == lane for _, v in load_series(e["series_id"]).values]
    lo, hi = min(0.0, min(vs)), max(vs)
    if hi <= lo:
        hi = lo + 1
    return lo, hi


def value_y(stage: "TimelineStage", lane: str, rng: tuple[float, float], v: float) -> float:
    lo_y, hi_y = stage.lane_y(lane)
    S = TIMELINE.series  # noqa: N806
    b, t = lo_y + S.lane_pad_bottom, hi_y - S.lane_pad_top
    return b + (v - rng[0]) / (rng[1] - rng[0]) * (t - b)


def segments(values: list[tuple[date, float]]) -> list[list[tuple[date, float]]]:
    """빈 달(한 달보다 긴 간격)에서 끊은 연속 구간들 — 보간하지 않는다(D-0086)."""
    out: list[list[tuple[date, float]]] = [[values[0]]]
    for a, b in zip(values, values[1:]):
        if (b[0].year * MONTHS + b[0].month) - (a[0].year * MONTHS + a[0].month) != 1:
            out.append([])
        out[-1].append(b)
    return out


def fmt_value(v: float, unit: str) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".") + unit


def source_line(e: dict) -> str:
    r = load_series(e["series_id"])
    return f"{r.source} · {r.as_of_label()}"


def draw_series(ctx: cairo.Context, R: "RenderCtx", view: "View", t: float, e: dict) -> None:  # noqa: N803
    S = TIMELINE.series  # noqa: N806
    a = window(t, e["t0"], e["t1"], S.fade_sec, S.fade_sec)
    if a <= S.min_alpha:
        return
    stage: "TimelineStage" = view.stage  # type: ignore[assignment]
    rec = load_series(e["series_id"])
    rng = R.cache["series_range"][e["lane"]]
    front = math.inf
    if e["grow"]:
        fr = R.cache["series_front"][e["key"]]   # 프레임별 앞끝(월드 x) — load_project 가 카메라 경로로 미리 계산
        front = float(fr[min(len(fr) - 1, max(0, int(t * FPS)))])
    col = C[e["col"]]
    fx = view.to_screen(front, 0.0)[0] if front != math.inf else float(W_OUT)
    ctx.save()
    ctx.rectangle(0, 0, max(0.0, fx), TIMELINE.area_bottom + TIMELINE.series.clip_below_px)
    ctx.clip()
    last: tuple[float, float, float] | None = None
    for seg in segments(rec.values):
        pts = [(stage.x_of(d), value_y(stage, e["lane"], rng, v), v) for d, v in seg]
        if e["style"] == "step":   # 값은 그 달 첫날부터 다음 달 첫날까지 유지(월평균)
            nxt = stage.x_of(_next_month(seg[-1][0]))
            st: list[tuple[float, float, float]] = []
            for i, p in enumerate(pts):
                if i:
                    st.append((p[0], pts[i - 1][1], pts[i - 1][2]))
                st.append(p)
            pts = st + [(nxt, pts[-1][1], pts[-1][2])]
        ctx.new_path()
        for i, (x, y, _) in enumerate(pts):
            sx, sy = view.to_screen(x, y)
            (ctx.move_to if i == 0 else ctx.line_to)(sx, sy)
        ctx.set_source_rgba(*col, a)
        ctx.set_line_width(S.line_w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
        for x, y, v in pts:
            if x <= front:
                last = (x, y, v)
    ctx.restore()
    _draw_missing(ctx, view, stage, rec, e, front, a)
    if last is not None:
        sx, sy = view.to_screen(last[0], last[1])
        if S.value_min_x <= sx <= W_OUT:
            ctx.arc(sx, sy, S.tip_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, a)
            ctx.fill()
            text(ctx, fmt_value(last[2], rec.unit), sx + S.value_dx, sy + S.value_dy, S.value_size, S.value_font, col, a,
                 S.value_halo, "l")
    _draw_axis(ctx, view, stage, e, rng, rec.unit, a)
    _draw_source(ctx, view, stage, e, a)


def _next_month(d: date) -> date:
    return date(d.year + d.month // MONTHS, d.month % MONTHS + 1, 1)


def _draw_missing(ctx: cairo.Context, view: "View", stage: "TimelineStage", rec: object, e: dict, front: float, a: float) -> None:
    """빈 달 자리 표시(D-0086 보정 1) — 짧은 점선 + "자료 없음"."""
    M = TIMELINE.missing_mark  # noqa: N806
    lo_y, hi_y = stage.lane_y(e["lane"])
    for d in rec.missing_dates():  # type: ignore[attr-defined]
        x = stage.x_of(d) + (stage.x_of(_next_month(d)) - stage.x_of(d)) / 2
        if x > front:
            continue
        sx, top = view.to_screen(x, hi_y)
        _, bot = view.to_screen(x, lo_y)
        if not 0 <= sx <= W_OUT:
            continue
        ctx.set_dash(M.dash)
        ctx.move_to(sx, top + M.inset_px)
        ctx.line_to(sx, bot - M.inset_px)
        ctx.set_source_rgba(*C[M.color], M.alpha * a)
        ctx.set_line_width(M.line_w)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, M.label, sx, bot - M.inset_px + M.label_dy, M.label_size, M.label_font, C[M.color], M.alpha * a, M.label_halo, "c")


def _draw_axis(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float], unit: str, a: float) -> None:
    """0 기준선과 범위 끝 값(단위 포함) — 레인 오른쪽 끝에 고정. 레인의 첫 series 만 그린다(겹침 방지)."""
    if not e["axis"]:
        return
    S = TIMELINE.series  # noqa: N806
    for v in (rng[0], rng[1]):
        _, sy = view.to_screen(0.0, value_y(stage, e["lane"], rng, v))
        ctx.move_to(0, sy)
        ctx.line_to(W_OUT, sy)
        ctx.set_source_rgba(*C["white"], (S.zero_alpha if v == 0 else S.grid_alpha) * a)
        ctx.set_line_width(S.grid_w)
        ctx.stroke()
        text(ctx, fmt_value(v, unit), W_OUT - S.axis_label_margin_px, sy + S.axis_label_dy, S.axis_label_size, S.axis_label_font,
             C["muted"], a, S.axis_label_halo, "r")


def _draw_source(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, a: float) -> None:
    """출처·기준 시점 줄(20 §5.1·§5.3) — 레인 아래쪽, 왼쪽 고정. 같은 레인의 n 번째 series 는 한 줄씩 위."""
    L = TIMELINE.lane_label  # noqa: N806
    S = TIMELINE.series  # noqa: N806
    _, bot = stage.lane_screen(view, stage.lane_index(e["lane"]))
    text(ctx, source_line(e), L.x, bot - S.source_dy - S.source_step * e["slot"], S.source_size, S.source_font,
         C["muted"], a, S.source_halo, "l")


__all__ = ["draw_series", "fmt_value", "lane_range", "segments", "source_line", "value_y"]

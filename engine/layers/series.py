"""시리즈 레이어 `series` — 데이터 레코드에서 직접 그린 계단선·꺾은선 (v4.3.0, docs/handoff/20 §5.1·§6, back_and_forth D-0084 작업 4·D-0086).

`{type: series, lane, series_id, style: step|line, grow, col}` — 값은 `data/series/<series_id>` 레코드에서만 온다(연출이 숫자를 주지 않는다).
- 세로: 레인 띠 안, 레인의 값 범위(`lane_range` — 그 레인 모든 series 의 [min(0, 최소), 최대]). 0 기준선과 범위 끝 값 라벨을 그린다.
- grow: 카메라와 함께 왼쪽→오른쪽으로 자란다(등장 문법 05). 앞끝 = (화면 왼쪽 + 화면 폭 × playhead)의 누적 최대 —
  되돌아가도 줄지 않는다. 등장 직후 grow_in_sec 동안 화면 왼쪽에서 앞끝까지 쓸어 나간다(`load_project` 가 프레임별로 미리 계산).
- 값 라벨은 드러난 마지막 점 하나(단위 포함). 레인 아래쪽에 출처·기준 시점 줄(20 §5.1 "YYYY년 M월 기준").
- 빈 달(레코드 missing, D-0086): 선을 끊고 그 자리에 "자료 없음" 표시. 보간 선분 없음.
- band(v4.4.0 D-0090 작업 2): 두 레코드(series_id = 아래 끝, upper_id = 위 끝) 사이를 계단 띠로 칠한다(목표 범위).
  값 라벨은 "아래–위단위", 두 레코드의 날짜는 같아야 한다(다르면 렌더 전 오류). 토큰 `rules stage_timeline.band`.
수치·색은 `rules stage_timeline.series`·`band`·`missing_mark`(코드 리터럴 0).
"""

from __future__ import annotations

import math
from datetime import date
from typing import TYPE_CHECKING

import cairo

from data.series import load_series
from engine.style import C, FPS, TIMELINE, W_OUT
from engine.timebase import ease_out, window
from engine.typography import text, tw

if TYPE_CHECKING:
    from engine.context import RenderCtx
    from engine.projection import View
    from engine.stage_timeline import TimelineStage

MONTHS = 12
AXIS = "value"   # D-0087 — 값 축(정직성 검사 4개 전부, rules qa_checks.chart_targets)


def record_ids(e: dict) -> list[str]:
    """이벤트가 읽는 레코드 id — band 면 아래 끝·위 끝 두 개(v4.4.0)."""
    return [e["series_id"]] + ([e["upper_id"]] if e.get("upper_id") else [])


def band_pairs(e: dict) -> list[tuple[date, float, float]]:
    """band 의 (달, 아래, 위). 두 레코드의 날짜가 다르면 ValueError(보간 금지, D-0086), 위 < 아래 도 오류."""
    lo, hi = load_series(e["series_id"]), load_series(e["upper_id"])
    if [d for d, _ in lo.values] != [d for d, _ in hi.values]:
        raise ValueError(f"band {lo.series_id}·{hi.series_id}: 두 레코드의 날짜가 다르다 — 같은 달끼리만 띠를 칠한다")
    out = [(d, a, b) for (d, a), (_, b) in zip(lo.values, hi.values)]
    bad = [d for d, a, b in out if b < a]
    if bad:
        raise ValueError(f"band {lo.series_id}·{hi.series_id}: 위 끝 < 아래 끝 {bad[:3]}")
    return out


def regimes(values: list[tuple[date, float]], months: int) -> list[str]:
    """달마다 색 의미 키(v4.4.0 D-0091 ②) — 마지막 변화(앞 달과 다름)가 months 달 안이면 그 방향(hike 오름·cut 내림), 아니면 hold.
    첫 달·변화 기록 없음 = hold. 빈 달(끊김)은 앞뒤 값을 비교하지 않는다(보간 금지 — 끊긴 뒤 첫 달은 새로 시작)."""
    out: list[str] = []
    last: tuple[int, str] | None = None
    for i, (d, v) in enumerate(values):
        k = d.year * MONTHS + d.month
        if i:
            pd, pv = values[i - 1]
            if k - (pd.year * MONTHS + pd.month) == 1 and v != pv:
                last = (k, "hike" if v > pv else "cut")
        out.append(last[1] if last is not None and k - last[0] < months else "hold")
    return out


def month_colors(e: dict, R: object) -> dict[date, tuple[float, float, float]] | None:  # noqa: N803
    """color_by change 면 {달: RGB}(장르 프로필 color_semantics hike·cut·hold — 없으면 오류, P6). fixed 면 None."""
    if e.get("color_by", "fixed") != "change":
        return None
    from engine.primitives import semantic_rgba  # noqa: PLC0415
    from genres.load import load_genre  # noqa: PLC0415

    sem = load_genre(R.cache["genre"]["name"]).color_semantics  # type: ignore[attr-defined]
    missing = [k for k in ("hike", "cut", "hold") if k not in sem]
    if missing:
        raise ValueError(f"series color_by change: 장르 프로필 color_semantics 에 {missing} 가 없다")
    rgb = {k: semantic_rgba(sem[k])[:3] for k in ("hike", "cut", "hold")}
    vals = load_series(e["series_id"]).values
    return {d: rgb[r] for (d, _), r in zip(vals, regimes(vals, TIMELINE.series.change_regime_months))}


def lane_range(events: list[dict], lane: str) -> tuple[float, float]:
    """레인 값 범위 — 그 레인의 모든 series 값의 [min(0, 최소), 최대](0 기준선을 늘 포함, 20 §5.3)."""
    vs = [v for e in events if e["type"] == "series" and e["lane"] == lane for sid in record_ids(e) for _, v in load_series(sid).values]
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
    recs = [load_series(s) for s in record_ids(e)]
    srcs = list(dict.fromkeys(f"{r.source} · {r.as_of_label()}" for r in recs))
    return " / ".join(srcs)


def value_text(e: dict, v: float, unit: str, hi: float | None = None) -> str:
    """끝점 값 라벨 — band 는 "아래–위단위"(rules stage_timeline.band.sep)."""
    if hi is None:
        return fmt_value(v, unit)
    return fmt_value(v, "") + TIMELINE.band.sep + fmt_value(hi, unit)


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
    mcol = month_colors(e, R)   # v4.4.0 D-0091 ② — None 이면 한 색(기존 그대로)
    fx = view.to_screen(front, 0.0)[0] if front != math.inf else float(W_OUT)
    ctx.save()
    ctx.rectangle(0, 0, max(0.0, fx), TIMELINE.area_bottom + TIMELINE.series.clip_below_px)
    ctx.clip()
    last: tuple[float, float, float] | None = None
    last_hi: float | None = None
    if e["style"] == "band":
        last, last_hi = _draw_band(ctx, view, stage, e, rng, col, a, front, mcol)
    for seg in ([] if e["style"] == "band" or mcol is None else segments(rec.values)):   # 달마다 색(change)
        _draw_pieces(ctx, view, stage, e, rng, seg, mcol, a)
        for d, v in seg:
            x = stage.x_of(d)
            if x <= front:
                last = (x, value_y(stage, e["lane"], rng, v), v)
    for seg in ([] if e["style"] == "band" or mcol is not None else segments(rec.values)):
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
            tip = col if mcol is None else mcol[_month_of(stage, last[0], rec)]
            ctx.arc(sx, sy, S.tip_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*tip, a)
            ctx.fill()
            s = value_text(e, last[2], rec.unit, last_hi)
            lw = tw(ctx, s, S.value_size, S.value_font)
            x0 = sx + S.value_dx if sx + S.value_dx + lw <= W_OUT - S.axis_zone_px else sx - S.value_dx - lw   # 오른쪽 축 값 자리를 비킨다
            box = (x0, sy + S.value_dy - S.value_size, x0 + lw, sy + S.value_dy)
            if not _hits(box, _lane_name_box(ctx, view, stage, e["lane"])):   # 레인 이름을 덮지 않는다(끝점은 그대로)
                text(ctx, s, box[0], sy + S.value_dy, S.value_size, S.value_font, tip, a, S.value_halo, "l")
    _draw_axis(ctx, view, stage, e, rng, rec.unit, a)
    _draw_source(ctx, view, stage, e, a)


def _month_of(stage: "TimelineStage", x: float, rec: object) -> date:
    """월드 x(그 달 첫날) → 레코드의 달."""
    return min((d for d, _ in rec.values), key=lambda d: abs(stage.x_of(d) - x))  # type: ignore[attr-defined]


def _draw_pieces(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
                 seg: list[tuple[date, float]], mcol: dict, a: float) -> None:
    """color_by change 의 선(v4.4.0 D-0091 ②) — 달마다 조각(step = 앞 달 값에서 오르내리는 세로 + 그 달 가로, line = 앞 점→이 점)."""
    S = TIMELINE.series  # noqa: N806
    ctx.set_line_width(S.line_w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i, (d, v) in enumerate(seg):
        y = value_y(stage, e["lane"], rng, v)
        x0 = stage.x_of(d)
        pts: list[tuple[float, float]] = []
        if e["style"] == "step":
            if i:
                pts.append((x0, value_y(stage, e["lane"], rng, seg[i - 1][1])))
            pts += [(x0, y), (stage.x_of(_next_month(d)), y)]
        elif i:
            pd, pv = seg[i - 1]
            pts = [(stage.x_of(pd), value_y(stage, e["lane"], rng, pv)), (x0, y)]
        if len(pts) < 2:
            continue
        ctx.new_path()
        for j, (x, yy) in enumerate(pts):
            sx, sy = view.to_screen(x, yy)
            (ctx.move_to if j == 0 else ctx.line_to)(sx, sy)
        ctx.set_source_rgba(*mcol[d], a)
        ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)


def _draw_band(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
               col: tuple[float, float, float], a: float, front: float,
               mcol: dict | None = None) -> tuple[tuple[float, float, float] | None, float | None]:
    """목표 범위 띠(v4.4.0 D-0090 작업 2) — 달마다 [그 달 첫날, 다음 달 첫날) 계단. 위·아래 끝 선 + 반투명 칠.
    돌려주는 값 = 드러난 마지막 달 (x, 아래 y, 아래 값), 위 값 — 끝점 라벨용. 이 함수가 부르는 쪽의 clip 안에서 그린다."""
    B = TIMELINE.band  # noqa: N806
    rows = band_pairs(e)
    last: tuple[float, float, float] | None = None
    last_hi: float | None = None
    for seg in segments([(d, i) for i, (d, _, _) in enumerate(rows)]):   # 빈 달에서 끊는다(보간 금지)
        lo_pts: list[tuple[float, float]] = []
        hi_pts: list[tuple[float, float]] = []
        for d, i in seg:
            _, lo, hi = rows[int(i)]
            x0, x1 = stage.x_of(d), stage.x_of(_next_month(d))
            ylo, yhi = value_y(stage, e["lane"], rng, lo), value_y(stage, e["lane"], rng, hi)
            lo_pts += [(x0, ylo), (x1, ylo)]
            hi_pts += [(x0, yhi), (x1, yhi)]
            if x0 <= front:
                last, last_hi = (x0, ylo, lo), hi
            if mcol is not None:   # v4.4.0 D-0091 ② — 달마다 색(아래 끝 레코드의 변화)
                s0, t0 = view.to_screen(x0, yhi)
                s1, t1 = view.to_screen(x1, ylo)
                ctx.rectangle(s0, t0, s1 - s0, t1 - t0)
                ctx.set_source_rgba(*mcol[d], B.fill_alpha * a)
                ctx.fill()
                for yy in (yhi, ylo):
                    ctx.move_to(s0, view.to_screen(x0, yy)[1])
                    ctx.line_to(s1, view.to_screen(x1, yy)[1])
                ctx.set_source_rgba(*mcol[d], B.edge_alpha * a)
                ctx.set_line_width(B.edge_w)
                ctx.stroke()
        if mcol is not None:
            continue
        ctx.new_path()
        for i, (x, y) in enumerate(hi_pts + lo_pts[::-1]):
            sx, sy = view.to_screen(x, y)
            (ctx.move_to if i == 0 else ctx.line_to)(sx, sy)
        ctx.close_path()
        ctx.set_source_rgba(*col, B.fill_alpha * a)
        ctx.fill()
        for pts in (hi_pts, lo_pts):
            ctx.new_path()
            for i, (x, y) in enumerate(pts):
                sx, sy = view.to_screen(x, y)
                (ctx.move_to if i == 0 else ctx.line_to)(sx, sy)
            ctx.set_source_rgba(*col, B.edge_alpha * a)
            ctx.set_line_width(B.edge_w)
            ctx.stroke()
    return last, last_hi


def lane_name(ln: object) -> str:
    """레인 이름표 — 이름 + (단위). 무대(draw_labels)와 레이어가 같은 문자열을 쓴다."""
    return ln.label if not ln.unit else f"{ln.label} ({ln.unit})"  # type: ignore[attr-defined]


def _lane_name_box(ctx: cairo.Context, view: "View", stage: "TimelineStage", lane: str) -> tuple[float, float, float, float]:
    L = TIMELINE.lane_label  # noqa: N806
    i = stage.lane_index(lane)
    top, _ = stage.lane_screen(view, i)
    return (L.x, top + L.dy - L.size, L.x + tw(ctx, lane_name(stage.lanes[i]), L.size, L.font), top + L.dy + L.size / 2)


def _hits(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


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


__all__ = ["band_pairs", "month_colors", "regimes", "draw_series", "fmt_value", "lane_range", "record_ids", "segments", "source_line", "value_text", "value_y"]

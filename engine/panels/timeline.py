"""패널 timeline — 날짜 축 위 사건 (v2.5.0, render3 `P_timeline`, 08 §5·§11-3). 사건·기간·표시 시각은 이벤트 필드(D25).

기하·타이밍은 `rules/video_rules.yaml panels.timeline`(v3 합격 값). 사건의 층(`side`, 축 위 −/아래 +, 절댓값 = 층)은
데이터에 있으면 그대로 쓴다(연출 = LLM+사용자, P8). 없으면 `assign_sides()` 가 라벨 폭을 실측해 겹치지 않는 층을 고른다.
"""

from __future__ import annotations

import math
from datetime import date

import cairo

from engine.context import RenderCtx
from engine.panels.base import panel_title
from engine.style import C
from engine.timebase import ease_io, ease_out, smooth
from engine.typography import text, tw
from rules import load_rules

AXIS = "date"   # v4.3.0 D-0087 — 축 종류(날짜 축만(값 축 없음)). 정직성 검사 적용 = rules qa_checks.chart_targets
TL = load_rules().panels.timeline


def _d(s: str) -> date:
    return date(*map(int, s.split("-")))


def _months(start: date, end: date) -> list[date]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(date(y, m, 1))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _fx(e: dict):  # noqa: ANN202
    x0, x1 = TL.x
    d0, d1 = _d(e["start"]), _d(e["end"])
    return lambda s: x0 + (_d(s) - d0).days / (d1 - d0).days * (x1 - x0)


def _date_text(d: str) -> str:
    dd = _d(d)
    return f"{dd.month}.{dd.day}"


def _box(ctx: cairo.Context, ev: dict, x: float) -> tuple[float, float]:
    """사건 라벨 상자의 가로 범위(날짜·라벨 중 넓은 쪽)."""
    w = max(tw(ctx, _date_text(ev["date"]), TL.date.size, "mono"), tw(ctx, ev["label"], TL.label.size, "sansb"))
    return x - w / 2, x + w / 2


def _band_obstacle(e: dict, ctx: cairo.Context) -> list[tuple[float, tuple[float, float], float]]:
    """기간 띠 라벨(축 아래 band_label_dy)은 아래쪽 1층보다 안쪽 — 아래로 가는 줄기가 뚫지 않게 장애물로 둔다.
    층 값 1/2 는 '아래쪽, 1층보다 안쪽' 이라는 뜻이다(같은 층 비교에는 걸리지 않는다)."""
    band = e.get("band")
    if not band:
        return []
    fx = _fx(e)
    cx = (fx(band["start"]) + fx(band["end"])) / 2
    w = tw(ctx, band["label"], TL.band_label.size, "sansm")
    return [(1 / 2, (cx - w / 2, cx + w / 2), cx)]


def _layer_pairs(e: dict, ctx: cairo.Context, sides: list[int]) -> list[tuple[int, tuple[float, float], float]]:
    fx = _fx(e)
    return [(s, _box(ctx, ev, fx(ev["date"])), fx(ev["date"])) for ev, s in zip(e["events"], sides)]


def _free(placed: list[tuple[int, tuple[float, float], float]], side: int, box: tuple[float, float], x: float) -> bool:
    g = TL.label_gap_px
    for s, (a0, a1), _ in placed:
        if s == side and box[0] < a1 + g and a0 < box[1] + g:
            return False                                   # 같은 층 라벨 겹침
        if s * side > 0 and abs(s) < abs(side) and a0 - g <= x <= a1 + g:
            return False                                   # 줄기가 안쪽 층 라벨을 뚫고 지나감
    return True


def assign_sides(e: dict, ctx: cairo.Context) -> tuple[list[int], list[str]]:
    """층 배정 — 데이터의 side 는 그대로, 비어 있는 사건만 날짜 순으로 가장 안쪽의 빈 층(직전 사건 반대쪽 먼저).
    빈 층이 없으면 가장 바깥 층에 두고 경고한다(조용히 겹치지 않는다, P6). 결과는 결정적이다."""
    fx = _fx(e)
    order = sorted(range(len(e["events"])), key=lambda i: (e["events"][i]["date"], i))
    sides: list[int | None] = [ev.get("side") for ev in e["events"]]
    placed = _band_obstacle(e, ctx) + [(s, _box(ctx, ev, fx(ev["date"])), fx(ev["date"]))
                                       for ev, s in zip(e["events"], sides) if s is not None]
    warns: list[str] = []
    prev = 1   # 첫 사건은 위(−)부터 — v3 연표와 같은 시작
    for i in order:
        ev = e["events"][i]
        if sides[i] is not None:
            prev = sides[i]
            continue
        x = fx(ev["date"])
        box = _box(ctx, ev, x)
        first = -1 if prev > 0 else 1
        cands = [sg * lv for lv in range(1, len(TL.layer_px) + 1) for sg in (first, -first)]
        pick = next((c for c in cands if _free(placed, c, box, x)), None)
        if pick is None:
            pick = cands[-1]
            warns.append(f"[timeline-no-free-layer] '{e['title']}' {ev['date']} {ev['label']} — 빈 층 없음, 층 {pick}")
        sides[i] = pick
        placed.append((pick, box, x))
        prev = pick
    return [int(s) for s in sides], warns


def lint(e: dict) -> list[str]:
    """겹침 경고 — 자동 배정 실패, 또는 데이터가 준 층끼리 라벨이 겹칠 때(오류 아님)."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    sides, warns = assign_sides(e, ctx)
    pairs = _layer_pairs(e, ctx, sides)
    band = _band_obstacle(e, ctx)
    for j, (s, box, x) in enumerate(pairs):
        if not _free(band + pairs[:j], s, box, x):
            ev = e["events"][j]
            warns.append(f"[timeline-overlap] '{e['title']}' {ev['date']} {ev['label']} 층 {s} 라벨이 앞 사건과 겹친다")
    return warns


def occupied(ctx: cairo.Context, e: dict, t_until: float) -> list[tuple[float, float, float, float]]:
    """화면에서 이 연표가 차지하는 상자들(x0, y0, x1, y1) — `t_until` 까지 등장한 사건만. 패널 옆 미디어 슬롯
    (`placement.slots.*.beside_panel`, D-0050 NB9)이 이 상자를 피한다. 좌표는 `draw` 와 같은 식(글자 기준선 − 크기 ~ + 헤일로)."""
    X0, X1 = TL.x  # noqa: N806
    Y = TL.y  # noqa: N806
    out = [(X0, Y - TL.tick_h, X1, Y + TL.month_dy + TL.month.size / 3)]          # 축·눈금·월 라벨 띠
    band = e.get("band")
    if band:
        fx = _fx(e)
        cx = (fx(band["start"]) + fx(band["end"])) / 2
        w = tw(ctx, band["label"], TL.band_label.size, "sansm")
        by = Y + TL.band_label_dy
        out.append((cx - w / 2, by - TL.band_label.size, cx + w / 2, by + TL.band_label.size / 3))
    fx = _fx(e)
    sides = assign_sides(e, ctx)[0]
    for ev, side in zip(e["events"], sides):
        if ev["t"] > t_until:
            continue
        x = fx(ev["date"])
        x0, x1 = _box(ctx, ev, x)
        L = TL.layer_px[abs(side) - 1]  # noqa: N806
        yy = Y - L if side < 0 else Y + L
        ty = yy + (TL.date_dy_above if side < 0 else TL.date_dy_below)
        ly = ty + (TL.label_dy_above if side < 0 else TL.label_dy_below)
        top = min(Y, ty - TL.date.size - TL.date.halo)
        bot = max(Y, ly + TL.label.size / 3 + TL.label.halo)
        out.append((x0 - TL.label.halo, top, x1 + TL.label.halo, bot))
    return out


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    panel_title(ctx, a, e["title"], e.get("subtitle"))
    X0, X1 = TL.x  # noqa: N806
    Y = TL.y  # noqa: N806
    fx = _fx(e)
    key = f"timeline_sides:{e['title']}:{e['t0']}"
    if key not in R.cache:
        R.cache[key] = assign_sides(e, ctx)[0]
    sides = R.cache[key]

    k = ease_io(lt / TL.axis_draw_sec)
    ctx.set_source_rgba(*C["white"], TL.axis_alpha * a)
    ctx.set_line_width(TL.axis_width)
    ctx.move_to(X0, Y)
    ctx.line_to(X0 + (X1 - X0) * k, Y)
    ctx.stroke()
    for md in _months(_d(e["start"]), _d(e["end"])):
        x = fx(md.isoformat())
        if x <= X0 + (X1 - X0) * k:
            ctx.rectangle(x, Y - TL.tick_h / 2, TL.tick_w, TL.tick_h)
            ctx.set_source_rgba(*C["white"], TL.axis_alpha * a)
            ctx.fill()
            text(ctx, f"{md.month}월", x + TL.month_dx, Y + TL.month_dy, TL.month.size, "sansm", C["muted"],
                 a * TL.month_alpha, TL.month.halo, "l")
    band = e.get("band")
    if band:
        ca = a * smooth((t - band["t_show"]) / TL.band_fade_sec)
        if ca > 0:
            x0, x1 = fx(band["start"]), fx(band["end"])
            ctx.rectangle(x0, Y - TL.band_h / 2, x1 - x0, TL.band_h)
            ctx.set_source_rgba(*C[band["col"]], TL.band_alpha * ca)
            ctx.fill()
            text(ctx, band["label"], (x0 + x1) / 2, Y + TL.band_label_dy, TL.band_label.size, "sansm", C[band["col"]], ca,
                 TL.band_label.halo, "c")
    cur = None
    for ev, side in zip(e["events"], sides):
        f = smooth((t - ev["t"]) / TL.event_fade_sec)
        if f <= 0:
            continue
        d = ev["date"]
        cur = d
        x = fx(d)
        c_ = C[ev["col"]]
        al = a * f * (TL.dim_alpha if ev.get("dim") else 1)
        L = TL.layer_px[abs(side) - 1]  # noqa: N806
        yy = Y - L if side < 0 else Y + L
        ctx.set_source_rgba(*c_, al * TL.stem_alpha)
        ctx.set_line_width(TL.stem_width)
        ctx.move_to(x, Y)
        ctx.line_to(x, Y + (yy - Y) * ease_out(f))
        ctx.stroke()
        ctx.arc(x, Y, TL.dot_r, 0, 2 * math.pi)
        ctx.set_source_rgba(*c_, al)
        ctx.fill()
        ty = yy + (TL.date_dy_above if side < 0 else TL.date_dy_below)
        text(ctx, _date_text(d), x, ty, TL.date.size, "mono", c_, al, TL.date.halo, "c")
        text(ctx, ev["label"], x, ty + (TL.label_dy_above if side < 0 else TL.label_dy_below), TL.label.size, "sansb",
             C["white"], al, TL.label.halo, "c")
    if cur:
        x = fx(cur)
        ctx.set_source_rgba(*C["gold"], TL.cursor_alpha * a)
        ctx.set_line_width(TL.cursor_width)
        ctx.set_dash(TL.cursor_dash)
        ctx.move_to(x, TL.cursor_y[0])
        ctx.line_to(x, TL.cursor_y[1])
        ctx.stroke()
        ctx.set_dash([])

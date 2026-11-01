"""값 레인 위 사건 핀 라벨 배치 (v7.4.0, back_and_forth D-0274 §1②·D-0276, 사용자 의견 UF-143 "차트에 글씨가 너무 겹치네").

핀 점(engine.project.pins_on_series — 월드 y = 그 날짜 계열 값) 위·아래로 라벨 상자를 단(row)으로 쌓는다. 단 = +1·+2(선 위)·−1·−2(선 아래),
rules stage_timeline.series.pin_label_rows 만큼. 상자는 점 가운데 정렬, 플롯 안으로 x 클램프, 점 → 상자 가장자리 리더선.
배치(`assign_pin_rows`)·렌더(`draw_pin_label`)·검사(`pin_conflicts` — [island-pin-collision]·[pin-label-collision])가 같은 상자 함수를 쓴다.
장애물 = 같은 순간 다른 핀 라벨·점, 그 레인 계열 선·띠·전망 점, 축 값 라벨, 끝값 라벨, 플롯 경계. 자리가 없으면 점만(pin_row None).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Callable, Optional

import cairo

from engine.style import FPS, ISLAND, TIMELINE
from engine.typography import tw
from rules import load_rules

MK = load_rules().layout_480p.marker
Box = tuple[float, float, float, float]
DOT_PX = 7.0          # 핀 점(맥동 고리 안쪽 점 + 테두리) 반폭 — 라벨이 다른 핀의 점을 덮으면 겹침(D-0267)
GAP_PX = 6.0          # 라벨끼리 가로 최소 간격(맞닿은 라벨 "인하워시" 금지, D-0267)
TOL_PX = 2.0          # 세로 경계 접촉(≤ 2px)은 겹침이 아니다
LINE_STEP_PX = 2      # 계열 선·띠 교차 표본 간격(가로 px)
LEAD_SEC = 0.6        # 핀이 나타난 뒤 라벨이 다 보인 시각(draw_marker 라벨 페이드 0.2+0.4초)
ASSIGN_STEP_SEC = 0.25   # 단 고르기 표본 간격 — 이동 숏 중 전망 점 열을 스치는 순간을 놓치지 않게(econ 115초)


def rows() -> list[int]:
    n = TIMELINE.series.pin_label_rows
    return list(range(1, n + 1)) + [-r for r in range(1, n + 1)]   # 선 위 먼저, 그다음 선 아래(D-0276)


def _lines(e: dict) -> list[tuple[str, float, str]]:
    out = [(e["label"], MK.label_size, "sansb")]
    if e.get("sub"):
        out.append((e["sub"], MK.sub_size, "sansm"))
    return out


def block(ctx: cairo.Context, e: dict) -> tuple[float, float]:
    """라벨 상자 (폭, 높이) — 첫 줄 글자 위 끝 ~ 마지막 줄 기준선 아래 0.25 글자."""
    w = max(tw(ctx, s, size, font) for s, size, font in _lines(e))
    h = MK.label_size + (MK.sub_dy + MK.sub_size * 0.25 if e.get("sub") else MK.label_size * 0.25)
    return w, h


def pin_rect(ctx: cairo.Context, e: dict, x: float, y: float, row: int, bounds: Box) -> Box:
    """단 row 의 라벨 상자(화면 좌표). bounds = 플롯 (왼, 위, 오른, 아래) — x 만 클램프(세로 밖은 검사가 잡는다)."""
    S = TIMELINE.series  # noqa: N806
    w, h = block(ctx, e)
    pitch = h + (S.pin_label_row_gap_px - MK.label_size)   # 한 줄 라벨 단 간격(13 + 3)의 여백을 두 줄 라벨에도
    k = abs(row) - 1
    if row > 0:
        y1 = y - S.pin_label_first_dy_px - k * pitch
        y0 = y1 - h
    else:
        y0 = y + S.pin_label_first_dy_px + k * pitch
        y1 = y0 + h
    x0 = min(max(x - w / 2, bounds[0]), bounds[2] - w)
    return x0, y0, x0 + w, y1


def plot_bounds(ctx: cairo.Context, view: object, stage: object, lane: str, rng: tuple[float, float], unit: str) -> Box:
    from engine.layers.series import plot_right  # noqa: PLC0415

    pad = ISLAND.chart.label_flip_pad
    top, bot = stage.lane_screen(view, stage.lane_index(lane))  # type: ignore[attr-defined]
    return view.ox + pad, top, plot_right(ctx, view, stage, lane, rng, unit) - pad, bot  # type: ignore[attr-defined]


def _ov(a: Box, b: Box) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > -GAP_PX and min(a[3], b[3]) - max(a[1], b[1]) > TOL_PX


def dot_box(x: float, y: float) -> Box:
    return x - DOT_PX, y - DOT_PX, x + DOT_PX, y + DOT_PX


def series_hit(box: Box, view: object, stage: object, evs: list[dict], rng: tuple[float, float], t: float,
               fronts: dict) -> Optional[str]:
    """라벨 상자가 그 순간 보이는 계열 선·띠·전망 점과 겹치면 그 계열 id. 선은 굵기 절반, 띠는 아래~위 구간."""
    from data.series import load_series  # noqa: PLC0415
    from engine.layers.series import band_pairs, projection_dots, value_y  # noqa: PLC0415

    lane = evs[0]["lane"] if evs else None
    half = TIMELINE.series.line_w / 2
    for e in evs:
        if not e["t0"] <= t <= e["t1"]:
            continue
        if e["style"] == "projection":
            rec = load_series(e["series_id"])
            for _, _, x, pts, _ in projection_dots(stage, e, rec, rng):
                sx, _ = view.to_screen(x, 0.0)  # type: ignore[attr-defined]
                for dx, wy in pts:
                    _, sy = view.to_screen(x, wy)  # type: ignore[attr-defined]
                    if _ov(box, dot_box(sx + dx, sy)):
                        return e["series_id"]
            continue
        fr = fronts.get(e.get("key"))
        front = float(fr[min(len(fr) - 1, max(0, int(t * FPS)))]) if fr is not None and e.get("grow") else float("inf")
        pairs = band_pairs(e) if e["style"] == "band" else None
        vals = None if pairs is not None else load_series(e["series_id"]).values
        for sx in range(int(box[0]), int(box[2]) + 1, LINE_STEP_PX):
            wx = view.x0 + (sx - view.ox) / view.s  # type: ignore[attr-defined]
            if wx > front:
                break
            d = stage.cfg.start + timedelta(days=stage.date_of(wx))  # type: ignore[attr-defined]
            if pairs is not None:
                pr = [(lo, hi) for dd, lo, hi in pairs if dd <= d]
                if not pr:
                    continue
                y_hi = view.to_screen(wx, value_y(stage, lane, rng, pr[-1][1]))[1]  # type: ignore[attr-defined]
                y_lo = view.to_screen(wx, value_y(stage, lane, rng, pr[-1][0]))[1]  # type: ignore[attr-defined]
                lo, hi = y_hi - half, y_lo + half
            else:
                vv = [v for dd, v in vals if dd <= d]
                if not vv:
                    continue
                sy = view.to_screen(wx, value_y(stage, lane, rng, vv[-1]))[1]  # type: ignore[attr-defined]
                lo, hi = sy - half, sy + half
            if min(box[3], hi) - max(box[1], lo) > 0:
                return e["series_id"]
    return None


def static_boxes(ctx: cairo.Context, view: object, stage: object, lane: str, rng: tuple[float, float], unit: str,
                 ends: list[Box], source_e: Optional[dict] = None) -> list[tuple[str, Box]]:
    """축 값 라벨 상자 + 끝값 라벨 상자 + 레인 출처 줄 상자(이름 붙여)."""
    from engine.layers.series import axis_label_boxes, source_line_boxes  # noqa: PLC0415

    S = TIMELINE.series  # noqa: N806
    out = [("축 값 라벨", b) for b in axis_label_boxes(ctx, view, stage, lane, rng, unit)] + [("끝값 라벨", b) for b in ends]
    if source_e is not None:
        out += [("출처 줄", (x, by - S.source_size, x + tw(ctx, ln, S.source_size, S.source_font), by + S.source_size * 0.25))
                for ln, x, by in source_line_boxes(ctx, view, stage, source_e)]
    return out


def conflicts(ctx: cairo.Context, rect: Box, bounds: Box, others: list[tuple[str, Box]], line_hit: Callable[[Box], Optional[str]]) -> list[str]:
    """라벨 상자 하나의 교차 목록 — 플롯 세로 밖, 다른 상자(핀 라벨·점·축 값·끝값), 계열 선·띠."""
    out = []
    if rect[1] < bounds[1] - TOL_PX or rect[3] > bounds[3] + TOL_PX:
        out.append("플롯 밖")
    out += [name for name, b in others if _ov(rect, b)]
    if (s := line_hit(rect)) is not None:
        out.append(f"계열 {s}")
    return out


def end_boxes(ctx: cairo.Context, view: object, stage: object, evs: list[dict], rng: tuple[float, float], unit: str, t: float,
              fronts: dict) -> list[Box]:
    """그 순간 끝값 라벨 상자(series.draw_series 와 같은 자리 — 세로 분산 전 기준선)."""
    from data.series import load_series  # noqa: PLC0415
    from engine.layers.series import band_pairs, plot_right, value_text, value_y  # noqa: PLC0415

    S = TIMELINE.series  # noqa: N806
    out: list[Box] = []
    pr = plot_right(ctx, view, stage, evs[0]["lane"], rng, unit) if evs else 0.0
    for e in evs:
        if not e["t0"] <= t <= e["t1"] or e["style"] == "projection" or (e["style"] == "band" and e.get("lane_n", 1) > 1):
            continue
        fr = fronts.get(e.get("key"))
        front = float(fr[min(len(fr) - 1, max(0, int(t * FPS)))]) if fr is not None and e.get("grow") else float("inf")
        front = min(front, view.x0 + (pr - view.ox) / view.s)  # type: ignore[attr-defined]  # series.draw_series 와 같은 끝(예약 열 왼쪽)
        if e["style"] == "band":
            pts = [(stage.x_of(d), lo, hi) for d, lo, hi in band_pairs(e)]  # type: ignore[attr-defined]
            pts = [p for p in pts if p[0] <= front]
            if not pts:
                continue
            x, v, hi = pts[-1]
        else:
            pts2 = [(stage.x_of(d), v) for d, v in load_series(e["series_id"]).values]  # type: ignore[attr-defined]
            pts2 = [p for p in pts2 if p[0] <= front]
            if not pts2:
                continue
            (x, v), hi = pts2[-1], None
        sx, sy = view.to_screen(x, value_y(stage, e["lane"], rng, v))  # type: ignore[attr-defined]
        if not view.ox + S.value_min_x <= sx <= pr:  # type: ignore[attr-defined]
            continue
        s = value_text(e, v, unit, hi)
        lw = tw(ctx, s, S.value_size, S.value_font)
        x0 = sx + S.value_dx if sx + S.value_dx + lw <= view.right - S.axis_zone_px else sx - S.value_dx - lw  # type: ignore[attr-defined]
        by = sy + S.value_dy
        out.append((x0, by - S.value_size, x0 + lw, by))
    return out


class PinScene:
    """핀 배치·검사 입력 — 시간축 무대 하나(주 무대 틀 또는 차트 아일랜드)의 계열·범위·단위·grow 앞끝과 시각 → 뷰."""

    def __init__(self, stage: object, events: list[dict], ranges: dict, fronts: dict, view_at: Callable[[float], object]) -> None:
        from data.series import load_series  # noqa: PLC0415

        self.stage, self.ranges, self.fronts, self.view_at = stage, ranges, fronts, view_at
        self.ser: dict[str, list[dict]] = {}
        for e in events:
            if e["type"] == "series":
                self.ser.setdefault(e["lane"], []).append(e)
        self.units = {lane: load_series(evs[0]["series_id"]).unit for lane, evs in self.ser.items()}
        self.pins = sorted((e for e in events if e["type"] == "marker" and e.get("label") and e.get("pin_value") is not None),
                           key=lambda e: e["t0"])
        self.ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def frame(self, t: float, rows_of: Callable[[dict], Optional[int]]) -> list[tuple[dict, Optional[Box], Box, list[str]]]:
        """시각 t 에 보이는 핀마다 (핀, 라벨 상자 또는 None, 점 상자, 교차 목록)."""
        v = self.view_at(t)
        if v is None:
            return []
        live = [p for p in self.pins if p["t0"] <= t <= p["t1"]]
        geo = []
        for p in live:
            x, y = v.to_screen(*p["world"])  # type: ignore[attr-defined]
            if x < v.ox - 80 or x > v.ox + v.vw + 80:  # type: ignore[attr-defined]
                continue   # 렌더러도 그리지 않는다
            lane = p["lane"]
            b = plot_bounds(self.ctx, v, self.stage, lane, self.ranges[lane], self.units[lane])
            r = rows_of(p)
            geo.append((p, None if r is None else pin_rect(self.ctx, p, x, y, r, b), dot_box(x, y), b))
        out = []
        for i, (p, rect, dot, b) in enumerate(geo):
            if rect is None:
                out.append((p, None, dot, []))
                continue
            lane = p["lane"]
            evs = self.ser[lane]
            others = [(f"핀 {q['label']!r} 점", qd) for j, (q, _, qd, _) in enumerate(geo) if j != i]
            others += [(f"핀 {q['label']!r} 라벨", qr) for j, (q, qr, _, _) in enumerate(geo) if j != i and qr is not None]
            ends = end_boxes(self.ctx, v, self.stage, evs, self.ranges[lane], self.units[lane], t, self.fronts)
            src = next((s for s in evs if not s.get("slot", 0) and s["t0"] <= t <= s["t1"]), None)   # 레인당 출처 한 줄(D-0256)
            others += static_boxes(self.ctx, v, self.stage, lane, self.ranges[lane], self.units[lane], ends, src)
            hit = conflicts(self.ctx, rect, b, others,
                            lambda r_: series_hit(r_, v, self.stage, evs, self.ranges[lane], t, self.fronts))
            out.append((p, rect, dot, hit))
        return out


def assign_pin_rows(scene: PinScene) -> list[str]:
    """핀 순서대로(t0) 단을 고른다 — 앞서 놓인 핀과 장애물에 교차 0 인 첫 단(선 위 1·2 → 아래 1·2). 표본 시각 = 나타난 뒤 LEAD_SEC 부터
    끝 직전까지 ASSIGN_STEP_SEC 간격. 넷 다 막히면 pin_row None(점만). 라벨을 못 단 핀 목록을 돌려준다(provenance pin_labels.dropped)."""
    placed: set[int] = set()
    dropped: list[str] = []
    for e in scene.pins:
        t_a, t_b = min(e["t1"], e["t0"] + LEAD_SEC), max(e["t0"], e["t1"] - 0.05)   # 카메라가 움직이는 동안 자리가 바뀐다 — 수명 전체를 표본
        ts = sorted({t_a, t_b, *(t_a + k * ASSIGN_STEP_SEC for k in range(int((t_b - t_a) / ASSIGN_STEP_SEC) + 1))})
        e["pin_row"] = None
        for r in rows():
            def rows_of(p: dict, r: int = r) -> Optional[int]:
                return r if p is e else (p.get("pin_row") if id(p) in placed else None)
            ok = all(not hit for t in ts for p, rect, _, hit in scene.frame(t, rows_of) if p is e)
            ok = ok and all(not (p is not e and rect is not None and _ov(rect, dot_box(*scene.view_at(t).to_screen(*e["world"]))))  # type: ignore[attr-defined]
                            for t in ts if scene.view_at(t) is not None for p, rect, _, _ in scene.frame(t, rows_of))
            if ok:
                e["pin_row"] = r
                break
        if e["pin_row"] is None:
            dropped.append(e["label"])
        placed.add(id(e))
    return dropped


STEP_FRAMES = 2   # 검사 표본 간격(프레임) — engine.island.LABEL_STEP_FRAMES 와 같은 값


def pin_label_check(scene: PinScene) -> list[dict]:
    """표본 프레임마다 렌더와 같은 자리로 핀 라벨 교차를 잰다 → [{a: 핀 라벨, b: 교차 대상, t0, t1}](연속 표본은 한 구간).
    라벨이 보이는(draw_marker 라벨 알파 > 0.01) 프레임만. 점만 남은 핀(pin_row None)은 라벨이 없다 — 그 점을 덮는 다른 핀 라벨은 센다."""
    from engine.timebase import smooth, window  # noqa: PLC0415

    rows_out: list[dict] = []
    if not scene.pins:
        return rows_out
    f0 = int(min(p["t0"] for p in scene.pins) * FPS)
    f1 = int(max(p["t1"] for p in scene.pins) * FPS)
    for f in range(-(-f0 // STEP_FRAMES) * STEP_FRAMES, f1 + 1, STEP_FRAMES):
        t = f / FPS
        for p, rect, _, hit in scene.frame(t, lambda q: q.get("pin_row")):
            la = window(t, p["t0"], p["t1"], 0.35, 0.5) * smooth((t - p["t0"] - 0.2) / 0.4)
            if rect is None or la <= 0.01:
                continue
            for h in hit:
                prev = next((r for r in reversed(rows_out) if r["a"] == p["label"] and r["b"] == h), None)
                if prev is not None and t - prev["t1"] <= STEP_FRAMES / FPS + 0.011:
                    prev["t1"] = round(t, 2)
                else:
                    rows_out.append({"a": p["label"], "b": h, "t0": round(t, 2), "t1": round(t, 2)})
    return rows_out

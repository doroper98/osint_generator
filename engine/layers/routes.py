"""항로·유조선·봉쇄선 (v2.1.0, render3 `catmull, route_uv(→ engine.stage.attach_world), glow_line, tanker, draw_route, draw_tanker_loop, draw_barrier`)."""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.projection import View
from engine.style import H_OUT, W_OUT, C, map_c, map_halo
from engine.timebase import ease_io, ease_out, smooth, window
from engine.typography import text, tw
from rules import load_rules

DECLARED_SAMPLES = 12   # 꼭짓점 사이 곡선 표본 수(catmull n) — 굴절 항로의 꺾임점 = bend_index × 이 값(v7.4.0)
RL = load_rules().layout_480p.route_label   # v4.8.0 D-0101 §3 — 항로·봉쇄선 라벨 글자(옛 리터럴 11.5·12.5)


def catmull(pts: list, n: int = 10) -> np.ndarray:
    P_ = [pts[0]] + list(pts) + [pts[-1]]  # noqa: N806
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = map(np.array, P_[i - 1:i + 3])
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(np.array(P_[-2]))
    return np.array(out)


def glow_line(ctx: cairo.Context, S_: np.ndarray, col: tuple, a: float, w: float, dash: list | None = None,  # noqa: N803
              casing=None) -> None:  # noqa: ANN001 — RouteCasing | None(v5.18.0 D-0161 §2, 테마 지도만)
    ctx.new_path()
    ctx.move_to(*S_[0])
    for x, y in S_[1:]:
        ctx.line_to(x, y)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash:
        ctx.set_dash(dash)
    if casing is not None:   # 선 아래 밝은 테두리 — 배경이 어두운 바다여도 선이 떨어져 보이게(가이드 23 §7 도형 3:1)
        ctx.set_source_rgba(*casing.rgb, casing.alpha * a)
        ctx.set_line_width(w + 2 * casing.width_add)
        ctx.stroke_preserve()
    for wd, al in ((w * 4.5, 0.08), (w * 2.2, 0.22), (w, 0.95)):
        ctx.set_source_rgba(*col, al * a)
        ctx.set_line_width(wd)
        ctx.stroke_preserve()
    ctx.new_path()
    ctx.set_dash([])


def tanker(ctx: cairo.Context, x: float, y: float, ang: float, a: float, sc: float = 1.0) -> None:
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(sc, sc)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 15)
    g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.45 * a)
    g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 15, 0, 2 * math.pi)
    ctx.fill()
    ctx.new_path()
    ctx.move_to(9, 0)
    ctx.line_to(5, -3)
    ctx.line_to(-8, -3)
    ctx.line_to(-8, 3)
    ctx.line_to(5, 3)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill_preserve()
    ctx.set_source_rgba(0, 0, 0, 0.5 * a)
    ctx.set_line_width(0.6)
    ctx.stroke()
    ctx.rectangle(-7, -2, 3, 4)
    ctx.set_source_rgba(0.2, 0.25, 0.3, a)
    ctx.fill()
    ctx.restore()


def log_shape(ctx: cairo.Context, pts: "np.ndarray", col: tuple, a: float, name: str, step: int = 6) -> None:
    """경로 선 대비 표본(v5.18.0 D-0161 §4) — 다 나타난 선(a ≥ 0.95)의 꼭짓점 몇 개를 장치 좌표·법선으로 남긴다(checks map_contrast)."""
    from engine import typography  # noqa: PLC0415

    if typography.CONTRAST_LOG is None or a < 0.95 or len(pts) < 3:
        return
    for i in range(1, len(pts) - 1, step):
        (x0, y0), (x1, y1) = ctx.user_to_device(*pts[i - 1]), ctx.user_to_device(*pts[i + 1])
        px, py = ctx.user_to_device(*pts[i])
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1.0
        typography.CONTRAST_LOG.append(("shape", (px, py, -dy / n, dx / n), tuple(col[:3]), a, name))


def draw_route(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.35, 0.6)
    if a <= 0.01:
        return
    if "curve" not in e:
        e["curve"] = catmull(e["world_pts"], DECLARED_SAMPLES)   # 경로 꼭짓점의 월드 좌표(engine.stage.attach_world) → 곡선
    S_ = view.to_screen_arr(e["curve"])  # noqa: N806
    prog = ease_io((t - e["t0"]) / e["grow"]) if e["grow"] > 0.05 else 1
    n = max(2, int(len(S_) * prog))
    sub = S_[:n]
    col = map_c(view.stage, e["col"])   # v5.18.0 D-0161 §3
    casing = getattr(getattr(view.stage, "theme", None), "route_casing", None)   # 테마 없는 무대(시간축·아일랜드) = 테두리 없음
    dec = e.get("declared")
    if dec:   # v7.4.0 D-0229 §2.5(UF-112) — 굴절 항로: 꺾임점까지 신고(muted 점선), 뒤는 실제(col 실선)
        kb = dec["bend_index"] * DECLARED_SAMPLES + 1
        mu = map_c(view.stage, "muted")
        glow_line(ctx, sub[:kb], mu, a, 1.9, dash=[5, 4], casing=casing)
        if n > kb:
            glow_line(ctx, sub[kb - 1:], col, a * (0.75 if e.get("glow_only") else 1), 1.9, casing=casing)
        if n >= kb:
            bx, by = S_[kb - 1]
            text(ctx, dec["label"], bx + 7, by - 7, RL.route_size, "sansm", mu, a * smooth((n - kb) / DECLARED_SAMPLES + 0.5), 3, "l",
                 **({} if map_halo(view.stage) is None else {"halo_rgb": map_halo(view.stage)}), contrast="required")
    else:
        glow_line(ctx, sub, col, a * (0.75 if e.get("glow_only") else 1), 1.9, dash=[5, 4] if e.get("dashed") else None,
                  casing=casing)
    log_shape(ctx, sub, col, a, e.get("label") or e.get("col", "route"))   # v5.18.0 D-0161 §4 — 도형 대비 측정 표본
    if e.get("ship") and len(sub) > 1:
        (x0, y0), (x1, y1) = sub[-2], sub[-1]
        tanker(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a)
    if e.get("dashed") and prog >= 0.98:
        (x0, y0), (x1, y1) = sub[-2], sub[-1]
        ang = math.atan2(y1 - y0, x1 - x0)
        ctx.new_path()
        ctx.move_to(x1 + math.cos(ang) * 3, y1 + math.sin(ang) * 3)
        for s_ in (2.5, -2.5):
            ctx.line_to(x1 - math.cos(ang + s_ / 6) * 9, y1 - math.sin(ang + s_ / 6) * 9)
        ctx.close_path()
        ctx.set_source_rgba(*col, a)
        ctx.fill()
    if e.get("label") and prog >= 0.99:
        la = a * smooth((t - e["t0"] - e["grow"]) / 0.4)
        pend = R.cache.get("route_labels_pending")
        if pend is None or e.get("in_island"):   # 아일랜드 안(상자 좌표)·지연 목록 없는 호출 = 그 자리에서(옛 동작)
            draw_route_label(ctx, view, e, S_, col, la, place_route_label(ctx, view.stage, e["label"], S_, [], [S_]))
        else:
            pend.append((e, S_, col, la))   # v5.21.11 — 마커·뱃지가 자리를 잡은 뒤 flush_route_labels 가 자리를 고른다


# ---------------------------------------------------------------- v5.21.11 경로 라벨 자리(D-0191 §1-3·D-0192)
Box = tuple[float, float, float, float]


def label_style(stage):  # noqa: ANN001, ANN201 — RouteLabelTheme | None
    th = getattr(stage, "theme", None)
    return getattr(th, "route_label", None) if th is not None else None


def label_extent(ctx: cairo.Context, stage, label: str) -> tuple[float, float]:  # noqa: ANN001
    """(글자 폭, 색 표시 포함 전체 폭)."""
    w = tw(ctx, label, RL.route_size, "sansb")
    st = label_style(stage)
    extra = st.mark_w + st.mark_gap if st is not None and st.style == "ink" and st.mark_w > 0 else 0.0
    return w, w + extra


def _box(cx: float, by: float, W: float) -> Box:  # noqa: N803
    return (cx - W / 2, by - RL.route_size, cx + W / 2, by + RL.route_size * 0.3)


def segs_cross_box(pts: "np.ndarray", box: Box, pad: float = 0.0) -> bool:
    """꺾은선이 상자(pad 만큼 넓힌)를 지나가나 — Liang–Barsky 선분 자르기."""
    if len(pts) < 2:
        return False
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    P0, P1 = pts[:-1], pts[1:]  # noqa: N806
    d = P1 - P0
    lo = np.zeros(len(d))
    hi = np.ones(len(d))
    ok = np.ones(len(d), bool)
    for p_, q_ in ((-d[:, 0], P0[:, 0] - x0), (d[:, 0], x1 - P0[:, 0]), (-d[:, 1], P0[:, 1] - y0), (d[:, 1], y1 - P0[:, 1])):
        par = np.abs(p_) < 1e-12
        ok &= ~(par & (q_ < 0))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(par, 0.0, q_ / np.where(par, 1.0, p_))
        lo = np.where(~par & (p_ < 0), np.maximum(lo, r), lo)
        hi = np.where(~par & (p_ > 0), np.minimum(hi, r), hi)
    return bool(np.any(ok & (lo <= hi)))


def _overlap(a: Box, b: Box) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def label_candidates(S_: "np.ndarray", W: float) -> list[tuple[float, float]]:  # noqa: N803
    """(가운데 x, 기준선 y) 후보 — 0 = 옛 자리(가운데 점 위 legacy_dy), 그 뒤 place_fracs 마다 선의 양쪽 수직 방향."""
    x, y = S_[len(S_) // 2]
    out = [(float(x), float(y - RL.legacy_dy))]
    h = RL.route_size * 1.3
    for f in RL.place_fracs:
        i = min(len(S_) - 2, max(1, int(round(f * (len(S_) - 1)))))
        (ax, ay), (bx, by_), (px, py) = S_[i - 1], S_[i + 1], S_[i]
        tx, ty = bx - ax, by_ - ay
        n = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / n, tx / n
        reach = RL.line_gap + abs(nx) * W / 2 + abs(ny) * h / 2   # 상자 가운데 ↔ 선 거리 = 간격 + 상자 반폭의 법선 성분
        for sg in ((-1.0, 1.0) if ny > 0 else (1.0, -1.0)):   # 위쪽(화면 y 감소) 먼저 — 라벨은 선 위가 읽기 자연스럽다
            cx, cy = px + sg * nx * reach, py + sg * ny * reach
            out.append((float(cx), float(cy + RL.route_size * 0.35)))   # 상자 세로 가운데 → 기준선
    return out


def place_route_label(ctx: cairo.Context, stage, label: str, S_: "np.ndarray", obstacles: list[Box],  # noqa: ANN001, N803
                      lines: list["np.ndarray"]) -> tuple[float, float, Box, bool]:
    """경로 라벨 자리 → (가운데 x, 기준선 y, 상자, 통과). 통과 = 어떤 경로 선도 상자를 지나지 않고, 장애물(마커·뱃지·겹침 카드·해역 이름)과
    겹치지 않고, 화면 안. 후보 0 이 통과하면 옛 자리 그대로. 통과 후보가 없으면 걸림이 가장 적은 후보(검사가 hard 로 잡는다).
    렌더(flush_route_labels)와 검사(route_label_cross·overlap)가 같은 함수다."""
    return pick_route_label(ctx, stage, label, S_, obstacles, lines)[1]


def _bad(b: Box, obstacles: list[Box], lines: list["np.ndarray"]) -> int:
    pad = RL.screen_pad
    bad = sum(segs_cross_box(L_, b, RL.line_clear_px) for L_ in lines) * 2 + sum(_overlap(b, o) for o in obstacles)
    return bad + (0 if (b[0] >= pad and b[2] <= W_OUT - pad and b[1] >= pad and b[3] <= H_OUT - RL.bottom_pad) else 1)


def pick_route_label(ctx: cairo.Context, stage, label: str, S_: "np.ndarray", obstacles: list[Box],  # noqa: ANN001, N803
                     lines: list["np.ndarray"]) -> tuple[int, tuple[float, float, Box, bool]]:
    """place_route_label + 고른 후보 번호 k(v5.22.7 D209 — 나타나는 순간 고른 k 를 수명 내내 쓴다, `route_label_slots`)."""
    _, W = label_extent(ctx, stage, label)  # noqa: N806
    best: tuple[int, int, float, float, Box] | None = None
    for k, (cx, by) in enumerate(label_candidates(S_, W)):
        b = _box(cx, by, W)
        bad = _bad(b, obstacles, lines)
        if bad == 0:
            return k, (cx, by, b, True)
        if best is None or bad < best[0]:
            best = (bad, k, cx, by, b)
    assert best is not None
    return best[1], (best[2], best[3], best[4], False)


def slot_route_label(ctx: cairo.Context, stage, label: str, S_: "np.ndarray", k: int, obstacles: list[Box],  # noqa: ANN001, N803
                     lines: list["np.ndarray"]) -> tuple[float, float, Box, bool]:
    """고정 후보 k 의 지금 자리(카메라를 따라 선과 함께 움직인다) → (가운데 x, 기준선 y, 상자, 통과). 통과 = 지금 장애물·선과 안 겹침."""
    _, W = label_extent(ctx, stage, label)  # noqa: N806
    cx, by = label_candidates(S_, W)[k]
    b = _box(cx, by, W)
    return cx, by, b, _bad(b, obstacles, lines) == 0


def draw_route_label(ctx: cairo.Context, view: View, e: dict, S_: "np.ndarray", col: tuple, la: float,  # noqa: N803
                     placed: tuple[float, float, Box, bool]) -> None:
    """dark(color) = 경로 색 글자(종전). light(ink) = 테마 글자 톤 + 테마 halo, 경로 색은 글자 앞 짧은 막대(D-0191 §1-3)."""
    cx, by, b, _ = placed
    st = label_style(view.stage)
    if st is None or st.style == "color":
        text(ctx, e["label"], cx, by, RL.route_size, "sansb", col, la, 3, "c", contrast="required")
        return
    x0 = b[0]
    if st.mark_w > 0:
        my = by - RL.route_size * 0.35
        ctx.save()
        ctx.rectangle(x0, my - st.mark_h / 2, st.mark_w, st.mark_h)
        ctx.set_source_rgba(*col, la)
        ctx.fill()
        ctx.restore()
        x0 += st.mark_w + st.mark_gap
    halo = map_halo(view.stage)
    text(ctx, e["label"], x0, by, RL.route_size, "sansb", map_c(view.stage, "white"), la, st.halo or 3, "l",
         **({} if halo is None else {"halo_rgb": halo}), contrast="required")


def route_lines(view: View, events: list[dict], t: float) -> list["np.ndarray"]:
    """지금 화면에 그려진 경로 선(자라는 중이면 자란 부분) — 라벨 교차 판정 대상(자기 선·남의 선)."""
    out = []
    for e in events:
        if e["type"] != "route" or e.get("in_island") or not e["t0"] <= t <= e["t1"] or window(t, e["t0"], e["t1"], 0.35, 0.6) <= 0.01:
            continue
        S_ = view.to_screen_arr(e["curve"] if "curve" in e else catmull(e["world_pts"], 12))  # noqa: N806
        prog = ease_io((t - e["t0"]) / e["grow"]) if e["grow"] > 0.05 else 1
        out.append(S_[:max(2, int(len(S_) * prog))])
    return out


def label_obstacles(ctx: cairo.Context, view: View, events: list[dict], t: float, reserved: list[Box], tb: object = None,
                    foreground: bool = True) -> list[Box]:
    """경로 라벨이 피할 상자 — 예약 상자(뱃지·마커 라벨·겹침 카드) + 마커 부제까지의 글자 상자 + 해역 이름 + 그 순간 자막 줄(line_gap 여유).
    렌더·검사 공용."""
    from engine.layers.labels import sea_labels  # noqa: PLC0415
    from engine.layers.markers import marker_box  # noqa: PLC0415
    from engine.subtitles import subtitle_boxes  # noqa: PLC0415

    out = list(reserved)
    if tb is not None:
        g = RL.line_gap
        out += [(a - g, b - g, c + g, d + g) for a, b, c, d in subtitle_boxes(ctx, tb, t)]
    for e in events:
        if e["type"] == "marker" and e.get("label") and not e.get("in_island") and e["t0"] <= t <= e["t1"]:
            x, y = view.to_screen(*e["world"])
            if -80 <= x <= W_OUT + 80 and -40 <= y <= H_OUT + 40:
                out.append(marker_box(ctx, e, x, y, with_sub=True))
    if hasattr(view.stage, "seas"):
        out += [b for *_, b in sea_labels(ctx, view.stage, view)]
    if foreground:   # v5.22.7 D209 — 자리 고르는 순간에만 전경 층을 피한다. 나중에 나타난 전경 층은 흐림(label_fade)
        out += foreground_boxes(ctx, events, t)
    return out


def foreground_boxes(ctx: cairo.Context, events: list[dict], t: float) -> list[Box]:
    """v5.22.6 D208 — 지도 위 전경 층 상자: 인용(초상·국기 뱃지 ~ 매체 줄)·카드·게시물·도형·겹침 카드(card_zones 와 같은 문턱).
    기사 카드는 화면 전체 덮개라 넣지 않는다(지도 이름표가 비킬 자리가 없다). 렌더·검사(route_label_overlap·label_collision) 공용."""
    from engine.quote import quote_alpha, quote_box  # noqa: PLC0415
    from engine.reserved import RES, card_zones  # noqa: PLC0415

    return [b for b, _ in foreground_zones(ctx, events, t)]


def foreground_zones(ctx: cairo.Context, events: list[dict], t: float) -> list[tuple[Box, float]]:
    """foreground_boxes 의 (상자, 그 순간 불투명도) — 이름표 흐림(label_fade)이 쓴다."""
    from engine.quote import quote_alpha, quote_box  # noqa: PLC0415
    from engine.reserved import RES, card_zones  # noqa: PLC0415

    out = [(z.box, z.a) for z in card_zones(ctx, events, t)]
    out += [(quote_box(ctx, e), qa) for e in events if e["type"] == "quote" and (qa := quote_alpha(t, e)) > RES.min_zone_alpha]
    return out


def slot_fade(fades: dict, e: dict, t: float) -> float:
    """v5.22.7 D210 — 수명 전체에서 안 겹치는 자리가 없던 이름표: 겹치는 구간(route_label_slots 가 정한 [시작, 끝])에서 그 자리 그대로 흐린다.
    구간 가장자리 RL 고정 0.25초로 나고 든다(튀지 않게)."""
    return 1.0 - max([window(t, a, b, 0.25, 0.25) for a, b in fades.get(id(e), [])] + [0.0])


def label_fade(ctx: cairo.Context, events: list[dict], t: float, b: Box) -> float:
    """v5.22.7 D209 — 이름표 상자를 덮는 전경 층이 있으면 그 불투명도만큼 그 자리에서 흐린다(자리를 옮기지 않는다)."""
    return 1.0 - max([a for fb, a in foreground_zones(ctx, events, t) if _overlap(b, fb)] + [0.0])


class LabelCapture(Exception):
    """route_label_slots 가 나타나는 순간 프레임의 렌더 예약 상자를 받으려고 render_frame 을 flush 에서 멈춘다(오류 아님)."""


def flush_route_labels(ctx: cairo.Context, R: RenderCtx, view: View, events: list[dict], t: float) -> None:  # noqa: N803
    """지연된 경로 라벨을 그린다 — 자리는 나타나는 순간 고른 후보(R.cache route_label_slots = engine.checks.route_label_slots, v5.22.7 D209)
    그대로, 나중에 나타난 전경 층에 가리면 흐린다. 그린 상자는 R.reserved 에 올려 배경 지명(나라·도시)이 피한다."""
    cap = R.cache.get("route_label_capture")
    if cap is not None:   # route_label_slots 의 붙잡기 — 이 프레임 렌더 예약 상자만 받고 나머지 그리기는 멈춘다
        cap["reserved"] = list(R.reserved)
        R.cache["route_labels_pending"] = None
        raise LabelCapture
    pend = R.cache.get("route_labels_pending") or []
    R.cache["route_labels_pending"] = None
    if not pend:
        return
    slots = R.cache.get("route_label_slots") or {}
    for e, S_, col, la in pend:  # noqa: N806
        k = slots.get(id(e))
        if k is None:   # 프레임 격자에서 한 번도 보이지 않은 이름표(나타나는 순간이 없다) — 보이면 오류(조용한 대체 금지, P6)
            if la > 0.01:
                raise RuntimeError(f"경로 이름표 {e['label']!r} t={t:.3f} 고정 자리 없음(route_label_slots) — 이름표 수명이 한 프레임보다 짧다")
            continue
        placed = slot_route_label(ctx, view.stage, e["label"], S_, k, [], [])
        fade = label_fade(ctx, events, t, placed[2]) * slot_fade(R.cache.get("route_label_fades") or {}, e, t)
        draw_route_label(ctx, view, e, S_, col, la * fade, placed)
        R.reserved.append(placed[2])


def draw_tanker_loop(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.6, 0.6)
    if "curve" not in e:
        e["curve"] = catmull(e["world_pts"], 12)   # 경로 꼭짓점의 월드 좌표(engine.stage.attach_world) → 곡선
    S_ = view.to_screen_arr(e["curve"])  # noqa: N806
    for k in range(3):
        f = ((t - e["t0"]) / 26.0 + k / 3) % 1.0
        i = int(f * (len(S_) - 2))
        (x0, y0), (x1, y1) = S_[i], S_[i + 1]
        tanker(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a * 0.95, 0.85)


def draw_barrier(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], 0.4, 0.5)
    k = ease_out((t - e["t0"]) / 0.8)
    x0, y0 = view.to_screen(*e["world_p0"])
    x1, y1 = view.to_screen(*e["world_p1"])
    xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    glow_line(ctx, np.array([[x0, y0], [xe, ye]]), map_c(view.stage, "ru"), a, 3.2)
    if k > 0.95:
        text(ctx, e["label"], (x0 + x1) / 2 - 12, (y0 + y1) / 2 + 4, RL.barrier_size, "sansb", map_c(view.stage, "ru"), a, 3, "r")

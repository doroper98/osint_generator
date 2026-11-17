"""비행 이벤트 — 출발 발광 · 점선 꼬리선 · 아이콘 · 착탄 링 · 위성 인셋 (v7.3.0, back_and_forth D-0206 §4).

개략 표현이다(사용자 결정 D232 U3-a): 비행 시간은 거리와 무관하게 `rules flight.dur_sec`, 출발 위치는 점·라벨 없는 발광,
꼬리선은 점선. 착탄 링은 `effects.draw_boom` 을 그대로 부른다(새 링 모양 금지 — v3 합격 문법).
수치는 전부 `rules/video_rules.yaml flight` 에서 읽는다(tests/anti_inertia/test_no_magic_numbers).
"""

from __future__ import annotations

import math
from typing import Callable, Optional

import cairo

from engine.context import RenderCtx
from engine.layers.effects import draw_boom
from engine.layers.media import draw_inset
from engine.projection import View
from engine.style import FPS, W_OUT, map_c
from engine.timebase import ease_out, smooth, window
from rules import load_rules

_R = load_rules()
F = _R.flight

Pt = tuple[float, float]


def hit_time(e: dict) -> float:
    """착탄 시각 = t0 + dur_sec(코드 계산, P8)."""
    return e["t0"] + F.dur_sec


def bezier(s: Pt, c: Pt, e: Pt, u: float) -> Pt:
    v = 1 - u
    return (v * v * s[0] + 2 * v * u * c[0] + u * u * e[0], v * v * s[1] + 2 * v * u * c[1] + u * u * e[1])


def control(s: Pt, e: Pt) -> Pt:
    """2차 베지어 제어점 — 중점 + 법선 × 화면 거리 × bulge_ratio."""
    dx, dy = e[0] - s[0], e[1] - s[1]   # 법선(−dy, dx)/d × d × bulge_ratio
    return ((s[0] + e[0]) / 2 - dy * F.bulge_ratio, (s[1] + e[1]) / 2 + dx * F.bulge_ratio)


def _scale(kind: str, size: float) -> float:
    """윤곽 좌표 → 설계 px 배율. 긴 변(x·y 중 큰 폭)을 size 로(전익기는 날개폭). 기존 세 종류는 y 폭이 긴 변이라 값이 같다."""
    return size / (max(max(abs(p[0]), abs(p[1])) for p in F.icon.shapes[kind]) * 2)


def _outline(ctx: cairo.Context, kind: str, sc: float) -> None:
    pts = F.icon.shapes[kind]
    ctx.move_to(pts[0][0] * sc, pts[0][1] * sc)
    for p in pts[1:]:
        ctx.line_to(p[0] * sc, p[1] * sc)
    ctx.close_path()


def _icon(ctx: cairo.Context, kind: str, rgb: tuple) -> None:
    I = F.icon  # noqa: N806
    sc = _scale(kind, I.size_px[kind])
    _outline(ctx, kind, sc)
    ctx.set_source_rgba(0, 0, 0, I.halo_alpha)
    ctx.set_line_width(I.halo)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*rgb[:3], 1)
    ctx.fill()
    for a, b in I.body_lines.get(kind, []):
        ctx.move_to(a[0] * sc, a[1] * sc)
        ctx.line_to(b[0] * sc, b[1] * sc)
    if I.body_lines.get(kind):
        ctx.set_source_rgba(0, 0, 0, I.body_line.alpha)
        ctx.set_line_width(I.body_line.width)
        ctx.stroke()


def heading(s: Pt, c: Pt, e: Pt, u: float) -> float:
    """u 에서 기체 회전각(머리 = −y 가 진행 방향) — 아이콘과 같은 계산."""
    x, y = bezier(s, c, e, u)
    x2, y2 = bezier(s, c, e, min(1.0, u + F.heading_du))
    return math.atan2(y2 - y, x2 - x) + math.pi / 2


def model_size(kind: str) -> float:
    """look model 크기 — rules flight.model.size_px, 없는 종류는 icon.size_px."""
    return F.model.size_px.get(kind, F.icon.size_px[kind])


def formation_offsets(e: dict) -> list[Pt]:
    """선두 기준 오프셋(옆 = 오른쪽 +, 뒤 = +, 설계 px) — 선두 (0, 0) 포함 count 개. 간격 = rules flight.formation × 기체 크기.
    vee: 순번 k(1, 1, 2, 2, …)마다 오른쪽·왼쪽 번갈아. line: 일렬 종대. echelon: 오른쪽으로 비스듬히."""
    n = e.get("count", 1)
    if n == 1:
        return [(0.0, 0.0)]
    size = model_size(e["kind"]) if e.get("look", "glyph") == "model" else F.icon.size_px[e["kind"]]
    sl = getattr(F.formation, e["formation"])
    out: list[Pt] = [(0.0, 0.0)]
    for i in range(1, n):
        if e["formation"] == "vee":
            k, side = (i + 1) // 2, (1 if i % 2 else -1)
        else:
            k, side = i, 1
        out.append((side * k * sl.lateral * size, k * sl.back * size))
    return out


def _place(s: Pt, c: Pt, e: Pt, u: float, off: Pt) -> tuple[float, float, float]:
    """편대 한 대의 화면 자리·회전각 — 선두(베지어 u)에서 선두 좌표계 오프셋을 돌려 더한다(굳은 한 덩어리)."""
    x, y = bezier(s, c, e, u)
    a = heading(s, c, e, u)
    ca, sa = math.cos(a), math.sin(a)
    return x + off[0] * ca - off[1] * sa, y + off[0] * sa + off[1] * ca, a


def _path_len(s: Pt, c: Pt, e: Pt) -> float:
    pts = [bezier(s, c, e, i / F.samples) for i in range(F.samples + 1)]
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _model_body(ctx: cairo.Context, kind: str, glyph_rgb: tuple, look: str, angle: float) -> None:
    """기체 한 대(이미 그 자리로 옮기고 돌린 좌표계). glyph = 옛 아이콘, model = 회색 두 면 음영 + 가는 테두리 + 세부선."""
    if look != "model":
        _icon(ctx, kind, glyph_rgb)
        return
    M = F.model  # noqa: N806
    sz = model_size(kind)
    sc = _scale(kind, sz)
    # 빛은 그림자 반대쪽(왼쪽 위)에서 — 화면에서 빛을 향한 날개 쪽(+x 또는 −x)이 밝은 면
    lit = 1 if -(math.cos(angle) * M.shadow.offset[0] + math.sin(angle) * M.shadow.offset[1]) >= 0 else -1
    _outline(ctx, kind, sc)
    ctx.set_source_rgb(*(min(1.0, v * (1 - M.shade)) for v in M.body_rgb))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ctx.rectangle(0, -sz, lit * sz, sz * 2)
    ctx.set_source_rgb(*(min(1.0, v * (1 + M.shade)) for v in M.body_rgb))
    ctx.fill()
    ctx.restore()
    _outline(ctx, kind, sc)
    for a, b in M.lines.get(kind, []):
        ctx.move_to(a[0] * sc, a[1] * sc)
        ctx.line_to(b[0] * sc, b[1] * sc)
    ctx.set_source_rgba(*M.edge.rgb, M.edge.alpha)
    ctx.set_line_width(M.edge.width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def _draw_models(ctx: cairo.Context, e: dict, s: Pt, c: Pt, end: Pt, p: float, rgb: tuple) -> None:
    """v7.4.0 UF-900 R7a — 편대(count)·모델 모양(look). 순서: 그림자 전부(지면) → 비행운 전부 → 몸체 전부.
    그림자·비행운은 look model 만. 착탄 링·인셋은 선두 표적 그대로(draw_flight)."""
    M = F.model  # noqa: N806
    look = e.get("look", "glyph")
    kind = e["kind"]
    offs = formation_offsets(e)
    places = [_place(s, c, end, p, o) for o in offs]
    if look == "model":
        sc = _scale(kind, model_size(kind))
        sh = M.shadow
        for x, y, a in places:
            ctx.save()
            ctx.translate(x + sh.offset[0], y + sh.offset[1])
            ctx.rotate(a)
            _outline(ctx, kind, sc)
            ctx.set_source_rgba(*sh.rgb, sh.alpha)
            ctx.fill_preserve()
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            for w, al in sh.soft:
                ctx.set_source_rgba(*sh.rgb, al)
                ctx.set_line_width(w)
                ctx.stroke_preserve()
            ctx.new_path()
            ctx.restore()
        CT = M.contrail  # noqa: N806
        u0 = max(0.0, p - CT.length_px / max(_path_len(s, c, end), CT.length_px))
        if u0 < p:
            for o in offs:
                trail = [_place(s, c, end, u0 + (p - u0) * i / CT.samples, o)[:2] for i in range(CT.samples + 1)]
                g = cairo.LinearGradient(*trail[0], *trail[-1])
                g.add_color_stop_rgba(0, *CT.rgb, 0)
                g.add_color_stop_rgba(1, *CT.rgb, CT.alpha)
                ctx.move_to(*trail[0])
                for q in trail[1:]:
                    ctx.line_to(*q)
                ctx.set_source(g)
                ctx.set_line_width(CT.width)
                ctx.set_line_cap(cairo.LINE_CAP_BUTT)
                ctx.stroke()
    for x, y, a in places:
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(a)
        _model_body(ctx, kind, rgb, look, a)
        ctx.restore()


def inset_safe() -> tuple[float, float, float, float]:
    """v7.4.0 D-0240 §2 — 인셋 원+출처 줄이 들어가야 하는 안전 영역(x0, y0, x1, y1): 날짜 배지 아래·자막 띠 위·좌우 여백."""
    m = F.inset.safe_margin_px
    db = _R.hud.date_badge
    return m, db.underline_y + 2 + m, W_OUT - m, _R.layout_480p.reserved_zones.subtitle.y_from - m


def inset_fits(box: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = inset_safe()
    x, y, w, h = box
    return x >= x0 and y >= y0 and x + w <= x1 and y + h + F.inset.caption_dy + F.inset.caption_size <= y1


Box = tuple[float, float, float, float]


def inset_clear(side: str, x: float, y: float, obstacles: "list[Box] | None" = None) -> bool:
    """그 자리가 안전 영역 안이고 장애물(표적 표지 라벨 상자, D-0305 ①)과 겹치지 않는가 — 원 + 출처 줄 상자로 잰다."""
    b = _inset_box_at(side, x, y)
    if not inset_fits(b):
        return False
    r = (b[0], b[1], b[0] + b[2], b[1] + b[3] + F.inset.caption_dy + F.inset.caption_size)
    return not any(r[0] < o[2] and o[0] < r[2] and r[1] < o[3] and o[1] < r[3] for o in obstacles or ())


def first_fit_side(e: dict, x: float, y: float, skip: Optional[str] = None, obstacles: "list[Box] | None" = None) -> str:
    """연출 side → 안 맞으면 rules flight.inset.side_order 첫 적합(skip 제외, 장애물 피함). 어느 자리도 안 맞으면 연출 side([inset-clipped])."""
    side = (e.get("inset") or {}).get("side", "up")
    for s in [side, *F.inset.side_order]:
        if s != skip and inset_clear(s, x, y, obstacles):
            return s
    return side


MOVE_PEAK = 3 / 2        # smooth(3u² − 2u³) 보간의 최고 속도 = 평균 속도 × 3/2(u = 1/2 에서 미분 최댓값)


def move_frames(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> int:
    """자리 옮김 보간 프레임 수 — rules flight.inset.move_sec 이 하한, 최고 속도가 jump_px_max × move_headroom 을 넘지 않게 거리에 맞춰 늘린다."""
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    return max(1, round(F.inset.move_sec * FPS), math.ceil(MOVE_PEAK * d / (F.inset.jump_px_max * F.inset.move_headroom)))


def build_inset_track(e: dict, frames: list[tuple[int, float, float, "list[Box]"]]) -> None:
    """인셋 자리 궤적(v7.4.0 back_and_forth D-0300·D-0305, UF-146). frames = 인셋이 보이는 프레임의 (번호, 표적 화면 x, y, 장애물 상자).
    ① 예측(flight.inset.predict_keyframes): 연출 side → side_order 순으로, 인셋 생애의 **모든 프레임** 구도에서 안전 영역·표적 라벨에 맞는
       자리를 찾으면 처음부터 그 자리로 고정(옮김 0) ② 없으면 등장 때 자리를 정하고(sticky) 벗어날 때만 다음 적합 자리로 보간 이동.
    e["inset_track"] = {"side", "moves": [(시작 프레임, 옛 자리, 새 자리, 보간 프레임 수)], "basis": predicted|sticky} — 렌더·검사가 같은 궤적."""
    if not frames or not F.inset.sticky_side:
        return
    side0 = (e.get("inset") or {}).get("side", "up")
    if F.inset.predict_keyframes:
        for s in dict.fromkeys([side0, *F.inset.side_order]):
            if all(inset_clear(s, x, y, obs) for _, x, y, obs in frames):
                e["inset_track"] = {"side": s, "moves": [], "basis": "predicted"}
                return
    f0, x0, y0, o0 = frames[0]
    first = cur = first_fit_side(e, x0, y0, obstacles=o0)
    moves: list[tuple[int, str, str, int]] = []
    for f, x, y, obs in frames[1:]:
        if moves and f - moves[-1][0] < moves[-1][3]:   # 옮기는 중에는 다시 고르지 않는다
            continue
        if not inset_clear(cur, x, y, obs):
            nxt = first_fit_side(e, x, y, skip=cur, obstacles=obs)
            if nxt != cur and inset_clear(nxt, x, y, obs):
                moves.append((f, cur, nxt, move_frames(_inset_box_at(cur, x, y), _inset_box_at(nxt, x, y))))
                cur = nxt
    e["inset_track"] = {"side": first, "moves": moves, "basis": "sticky"}


def inset_box(e: dict, x: float, y: float, t: Optional[float] = None) -> tuple[float, float, float, float]:
    """표적 화면 점(x, y) 기준 인셋 원의 바깥 정사각(x0, y0, 지름, 지름) — side 방향으로 gap_px 떨어진 자리(UF-103 원형).
    궤적(inset_track, D-0300)이 있고 t 를 주면 그 시각의 자리(옮기는 중이면 두 자리 사이 보간). 없으면 v7.4.0 D-0240 §2 첫 적합 자리."""
    tr = e.get("inset_track")
    if tr is None or t is None:
        return _inset_box_at(first_fit_side(e, x, y), x, y)
    f = round(t * FPS)
    side, prev = tr["side"], None
    for fs, a, b, mf in tr["moves"]:
        if fs <= f:
            side, prev = b, (fs, a, mf)
    if prev is None or f - prev[0] >= prev[2]:
        return _inset_box_at(side, x, y)
    u = smooth((f - prev[0]) / prev[2])
    a, b = _inset_box_at(prev[1], x, y), _inset_box_at(side, x, y)
    return tuple(p + (q - p) * u for p, q in zip(a, b))  # type: ignore[return-value]


def _inset_box_at(side: str, x: float, y: float) -> tuple[float, float, float, float]:
    I = F.inset  # noqa: N806
    d = I.w_px
    if "_" in side:   # v7.4.0 — 대각(가까운 모서리가 표적에서 gap_px)
        v, h = side.split("_")
        g = I.gap_px / math.sqrt(2)
        return (x - g - d if h == "left" else x + g), (y - g - d if v == "up" else y + g), d, d
    if side == "up":
        return x - d / 2, y - I.gap_px - d, d, d
    if side == "down":
        return x - d / 2, y + I.gap_px, d, d
    if side == "left":
        return x - I.gap_px - d, y - d / 2, d, d
    return x + I.gap_px, y - d / 2, d, d


def circle_path(ctx: cairo.Context, box: tuple[float, float, float, float]) -> None:
    """인셋 원(UF-103) — 상자에 내접."""
    x, y, w, h = box
    ctx.new_path()
    ctx.arc(x + w / 2, y + h / 2, min(w, h) / 2, 0, 2 * math.pi)


def inset_alpha(t: float, e: dict) -> float:
    th = hit_time(e)
    end = (e.get("inset") or {}).get("hold_until")   # v7.4.0 D-0229 §2.7 — 명시·같은 장소 유지
    stop = min(max(th + F.inset.hold_sec + F.impact_sec, end or 0.0), e.get("t1", math.inf))   # v7.4.0 D-0300 — 이벤트 끝 전에 페이드가 끝난다(컷에 잘리지 않게)
    return window(t, th - F.inset.lead_sec, stop, *F.inset.fade)


InsetDrawer = Callable[[cairo.Context, RenderCtx, tuple[float, float, float, float], float, dict], None]


def draw_flight(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict,  # noqa: N803
                inset_drawer: Optional[InsetDrawer] = None) -> None:
    t0 = e["t0"]
    th = hit_time(e)
    rgb = map_c(view.stage, e.get("col", "amber"))
    s = view.to_screen(*e["world_origin"])
    end = view.to_screen(*e["world"])
    c = control(s, end)
    fade = window(t, e["t0"] - F.origin.pulse_sec, e["t1"], 0, F.trail.fade_sec)
    # 1) 출발 발광(점·라벨 없음)
    O = F.origin  # noqa: N806
    if t0 - O.pulse_sec <= t <= t0 + O.out_sec:
        a = window(t, t0 - O.pulse_sec, t0 + O.out_sec, O.fade_in_sec, O.out_sec)
        br = 1 - O.breath + O.breath * math.sin((t - t0) * 2 * math.pi / O.pulse_sec)
        g = cairo.RadialGradient(s[0], s[1], 0, s[0], s[1], O.r_px)
        g.add_color_stop_rgba(0, *rgb[:3], O.alpha * a * br)
        g.add_color_stop_rgba(1, *rgb[:3], 0)
        ctx.set_source(g)
        ctx.arc(s[0], s[1], O.r_px, 0, 2 * math.pi)
        ctx.fill()
    # 2) 꼬리선(점선 = 개략) — 출발 후 자라고 착탄 뒤 fade_sec 에 사라진다
    p = ease_out((t - t0) / F.dur_sec) if t >= t0 else 0.0
    T = F.trail  # noqa: N806
    ta = T.alpha * fade * (1.0 if t < th else max(0.0, 1 - (t - th) / T.fade_sec))
    if p > 0 and ta > 0:
        ctx.move_to(*s)
        for i in range(1, F.samples + 1):
            ctx.line_to(*bezier(s, c, end, p * i / F.samples))
        ctx.set_dash(list(T.dash))
        ctx.set_line_width(T.width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*rgb[:3], ta)
        ctx.stroke()
        ctx.set_dash([])
    # 3) 아이콘(진행 방향으로 회전). v7.4.0 UF-900 R7a — look model·편대는 _draw_models(glyph 1대 = 옛 경로 그대로)
    if 0 < p < 1:
        if e.get("look", "glyph") == "model" or e.get("count", 1) > 1:
            _draw_models(ctx, e, s, c, end, p, rgb)
        else:
            x, y = bezier(s, c, end, p)
            x2, y2 = bezier(s, c, end, min(1.0, p + F.heading_du))
            ctx.save()
            ctx.translate(x, y)
            ctx.rotate(math.atan2(y2 - y, x2 - x) + math.pi / 2)
            _icon(ctx, e["kind"], rgb)
            ctx.restore()
    # 4) 착탄 링 = boom 과 같은 링(새 모양 금지)
    if e.get("impact", True) and th <= t <= th + F.impact_sec:
        draw_boom(ctx, R, view, t, {"t0": th, "t1": th + F.impact_sec, "world": e["world"]})
    # 5) 위성 인셋
    if e.get("inset"):
        ia = inset_alpha(t, e)
        if ia > 0:
            box = inset_box(e, *end, t)
            (inset_drawer or draw_inset)(ctx, R, box, ia, e)
            R.reserved.append((box[0], box[1], box[0] + box[2], box[1] + box[3] + F.inset.caption_dy))

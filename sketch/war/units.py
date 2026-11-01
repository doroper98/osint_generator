"""시대 부호 세트 부대 — 키프레임으로 움직이는 블록·쐐기·점열(v7.4.0 전쟁사 W3, back_and_forth D-0600 §5).

부호 이름은 rules war_history.symbol_sets(세트 판정은 schemas.war_history.symbol_set_mixed). 화면 수치는 rules sketch.war.unit.
위치·모양은 spec 키프레임(중심·정면 방위·정면 폭·종심 km). 키 사이는 smooth 로 옮긴다 — 한 번에 튀지 않는다.
모양은 지표 위 실제 크기(geodesy.dest)로 그린 뒤, 작전 지도 축척에서 너무 작으면 화면 최소 크기까지 키운다(개략).
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.glyphs.arms import draw_glyph
from engine.glyphs.emblems import draw_emblem
from engine.projection import View
from engine.stage import ym
from engine.style import C
from engine.timebase import clamp01, smooth
from engine.typography import text, tw
from rules import load_rules
from sketch.campaign.units import unit_symbol
from sketch.common.draw import SK, WHITE
from sketch.common.geodesy import dest
from sketch.war.spec import UnitKey, WarSpec, WarUnit

U, F = SK.war.unit, SK.fade
WS = load_rules().war_history.symbol_sets   # 모양·글리프·입체·대열 격자(D-0605 ①③)
EMB = load_rules().war_history.faction_badge.emblem   # 진영 휘장 크기·자리(D-0606 A)
APP6 = {"app6_inf": "inf", "app6_arm": "arm", "app6_cav": "cav"}
BLACK = (0.0, 0.0, 0.0)
RIGHT_ANGLE = 90


def key_at(u: WarUnit, t: float) -> UnitKey:
    """시각 t 의 부대 상태 — 앞뒤 키 사이 smooth 보간(첫 키 전 = 첫 키, 마지막 키 뒤 = 마지막 키)."""
    ks = u.keys
    if t <= ks[0].t:
        return ks[0]
    for a, b in zip(ks, ks[1:]):
        if t < b.t:
            k = smooth(clamp01((t - a.t) / (b.t - a.t)))
            dh = (b.heading - a.heading + 180) % 360 - 180
            return UnitKey(t=t, lon=a.lon + (b.lon - a.lon) * k, lat=a.lat + (b.lat - a.lat) * k, heading=a.heading + dh * k,
                           length_km=a.length_km + (b.length_km - a.length_km) * k, depth_km=a.depth_km + (b.depth_km - a.depth_km) * k)
    return ks[-1]


def _corners(view: View, k: UnitKey) -> np.ndarray:
    """정면 폭 × 종심 사각형 네 꼭짓점(화면 px) — 정면 = heading 방향."""
    side = k.heading + RIGHT_ANGLE
    pts = []
    for s_lat, s_dep in ((-1, -1), (1, -1), (1, 1), (-1, 1)):   # 뒤-왼, 뒤-오른, 앞-오른, 앞-왼
        lon, lat = dest(k.lon, k.lat, side if s_lat > 0 else side + 180, k.length_km / 2)
        lon, lat = dest(lon, lat, k.heading if s_dep > 0 else k.heading + 180, k.depth_km / 2)
        pts.append(view.to_screen(lon, ym(lat)))
    return np.array(pts)


def _grow(pts: np.ndarray, heading_px: np.ndarray) -> np.ndarray:
    """화면 최소 크기(rules sketch.war.unit.min_px)까지 중심 기준으로 키운다 — 작전 지도 축척에서도 블록이 보이게."""
    c = pts.mean(axis=0)
    along = heading_px / (np.linalg.norm(heading_px) or 1)
    lateral = np.array([-along[1], along[0]])
    rel = pts - c
    L = np.abs(rel @ lateral).max() * 2
    D = np.abs(rel @ along).max() * 2
    sl = U.min_px[0] / L if 0 < L < U.min_px[0] else 1
    sd = U.min_px[1] / D if 0 < D < U.min_px[1] else 1
    return c + np.outer(rel @ lateral * sl, lateral) + np.outer(rel @ along * sd, along)


class WarUnitLayer:
    def __init__(self, spec: WarSpec, emblems: "dict[str, str] | None" = None) -> None:
        self.spec = spec
        self.emblems = emblems or {}   # 진영 id → 휘장 재작도 글리프(engine.glyphs.emblems) — 블록 위 작게(D-0606 A)
        self.drawn: dict[str, int] = {}

    def draw(self, ctx: cairo.Context, view: View, t: float, res: list) -> None:
        for u in self.spec.units:
            t_in = u.keys[0].t
            a = smooth((t - t_in) / U.in_sec)
            if u.t_out is not None:
                a *= 1 - smooth((t - u.t_out) / U.in_sec)
            if a <= F.min_alpha:
                continue
            k = key_at(u, t)
            col = C[self.spec.factions[u.faction].token]
            x, y = view.to_screen(k.lon, ym(k.lat))
            fx, fy = view.to_screen(*(lambda p: (p[0], ym(p[1])))(dest(k.lon, k.lat, k.heading, k.depth_km)))
            hv = np.array([fx - x, fy - y])
            shape = WS.shape_of(u.symbol)
            if shape == "app6":
                unit_symbol(ctx, x, y, col, "", APP6[u.symbol], a, U.app6_scale)
            else:
                self._ancient(ctx, view, k, shape, col, a, hv)
            glyph = WS.glyph_of(u.symbol)
            if glyph:
                G = WS.glyph  # noqa: N806
                draw_glyph(ctx, glyph, x, y + G.dy, G.size_px, WHITE, G.alpha * a, G.halo_rgb, G.halo_px)
                self.drawn[f"glyph:{glyph}"] = self.drawn.get(f"glyph:{glyph}", 0) + 1
            em = self.emblems.get(u.faction)
            if em and shape != "app6":   # 진영 휘장 — 픽토그램 오른쪽 위 작게(rules faction_badge.emblem.block_*)
                EB = EMB  # noqa: N806
                draw_emblem(ctx, em, x + EB.block_dx, y + WS.glyph.dy + EB.block_dy, EB.block_px, WHITE, EB.alpha * a,
                            WS.glyph.halo_rgb, EB.halo_px)
                self.drawn[f"emblem_block:{em}"] = self.drawn.get(f"emblem_block:{em}", 0) + 1
            if u.name:
                N = U.name
                text(ctx, u.name, x, y + N.dy, N.size, N.font, WHITE, a, N.halo, "c")
            if a > F.min_alpha:   # 부대 상자(이름 포함) — SK-C2 겹침·SK-W6 카드 덮임 입력
                half = max(U.min_px[0], tw(ctx, u.name, U.name.size, U.name.font) if u.name else 0) / 2
                res.append((x - half, y - U.name.dy, x + half, y + U.name.dy))
            self.drawn[f"unit:{u.symbol}"] = self.drawn.get(f"unit:{u.symbol}", 0) + 1

    def _ancient(self, ctx: cairo.Context, view: View, k: UnitKey, shape: str, col: tuple, a: float, hv: np.ndarray) -> None:
        pts = _grow(_corners(view, k), hv)
        along = hv / (np.linalg.norm(hv) or 1)
        lateral = np.array([-along[1], along[0]])
        rel = pts - pts.mean(axis=0)
        L, D = np.abs(rel @ lateral).max() * 2, np.abs(rel @ along).max() * 2   # noqa: N806 — 화면 정면 폭·종심
        Dp = WS.depth  # noqa: N806
        th = max(Dp.side_min_px, Dp.side_ratio * min(L, D))
        off = np.array([0.5, 1.0]) * th   # 단면 = 아래·오른쪽(빛 = 왼쪽 위)
        if shape in ("dots", "big_dots"):   # 투석·투창병 · 코끼리 — 정면 선을 따라 점열(점마다 그림자)
            p0, p1 = (pts[0] + pts[3]) / 2, (pts[1] + pts[2]) / 2
            n = max(2, int(np.linalg.norm(p1 - p0) / U.dot_gap_px))
            r = U.dot_r * (2 if shape == "big_dots" else 1)
            qs = [p0 + (p1 - p0) * i / n for i in range(n + 1)]
            for colr, alpha, sh in ((BLACK, Dp.shadow_alpha, np.array(Dp.shadow_px) * r / U.dot_r / 2), (col, 1.0, np.zeros(2))):
                for q in qs:
                    ctx.new_sub_path()
                    ctx.arc(q[0] + sh[0], q[1] + sh[1], r, 0, 2 * math.pi)
                ctx.set_source_rgba(*colr, alpha * a)
                ctx.fill()
            return
        if shape == "wedge":   # 쐐기 — 뒤쪽 두 꼭짓점 + 정면 가운데
            tip = (pts[2] + pts[3]) / 2
            poly = np.array([pts[0], pts[1], pts[1] + (tip - pts[1]) * U.wedge_ratio, tip])
        elif shape == "triangle":
            poly = np.array([pts[0], pts[1], (pts[2] + pts[3]) / 2])
        else:
            poly = pts
        c = poly.mean(axis=0)
        edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]

        def outward(p: np.ndarray, q: np.ndarray) -> np.ndarray:
            e = q - p
            nrm = np.array([e[1], -e[0]])
            return nrm if nrm @ ((p + q) / 2 - c) > 0 else -nrm

        def path(pp: np.ndarray) -> None:
            ctx.move_to(*pp[0])
            for q in pp[1:]:
                ctx.line_to(*q)
            ctx.close_path()

        path(poly + off + np.array(Dp.shadow_px))   # 바닥 그림자
        ctx.set_source_rgba(*BLACK, Dp.shadow_alpha * a)
        ctx.fill()
        side = tuple(v * Dp.side_dark for v in col)
        for p, q in edges:   # 보이는 단면(바깥 법선이 단면 방향과 같은 변)
            if outward(p, q) @ off > 0:
                path(np.array([p, q, q + off, p + off]))
                ctx.set_source_rgba(*side, a)
                ctx.fill()
        path(poly)   # 윗면
        ctx.set_source_rgba(*col, Dp.top_alpha * a)
        ctx.fill()
        RG = WS.rank_grid  # noqa: N806
        if shape in RG.shapes:   # 대열 격자 — 고정 간격(병력 비례 아님)
            ctx.save()
            path(poly)
            ctx.clip()
            ax, span, other = (along, D, L) if shape == "block" else (lateral, L, D)   # 보병 = 정면과 나란한 줄, 기병 = 진행 방향 줄
            perp = np.array([-ax[1], ax[0]])
            n = min(RG.max_lines, int(span * (1 - 2 * RG.inset) / RG.gap_px))
            for i in range(n):
                f = (i + 0.5) / n - 0.5 if n > 0 else 0
                m = c + ax * f * span * (1 - 2 * RG.inset)
                ctx.move_to(*(m - perp * other / 2 * (1 - RG.inset)))
                ctx.line_to(*(m + perp * other / 2 * (1 - RG.inset)))
            ctx.set_line_width(RG.w)
            ctx.set_source_rgba(*side, RG.alpha * a)
            ctx.stroke()
            ctx.restore()
        path(poly)   # 윤곽 = 어두운 단면색
        ctx.set_line_width(U.edge_w)
        ctx.set_source_rgba(*side, U.edge_alpha * a)
        ctx.stroke()
        for p, q in edges:   # 위 모서리(빛을 받는 변) 밝은 선
            if outward(p, q) @ off < 0:
                ctx.move_to(*p)
                ctx.line_to(*q)
        ctx.set_line_width(Dp.rim_w)
        ctx.set_source_rgba(*WHITE, Dp.rim_alpha * a)
        ctx.stroke()

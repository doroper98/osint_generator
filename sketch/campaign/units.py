"""부대 부호(나토식 단순화) — 사각 틀(국가 색) + 병종(보병 X, 기갑 타원) + 위에 제대 표시, 아래 부대 이름.
원본: 4d9dc65 `uranus_sketch.unit_symbol`·`draw_units`. 수치 = rules sketch.campaign.symbol·echelon·unit_name.
"""

from __future__ import annotations

import math

import cairo

from engine.projection import View
from engine.stage import ym
from engine.style import C, H_OUT, W_OUT
from engine.timebase import clamp01, ease_out, smooth
from engine.typography import text, tw
from sketch.campaign.fronts import ramps
from sketch.campaign.spec import CampaignSpec
from sketch.common.draw import SK, WHITE

CA, F = SK.campaign, SK.fade
INFANTRY = "inf"


def unit_symbol(ctx: cairo.Context, x: float, y: float, col: tuple, ech: str, arm: str, a: float, scale: float = 1) -> None:
    Sy, E = CA.symbol, CA.echelon
    w, h = Sy.w * scale, Sy.h * scale
    x0, y0 = x - w / 2, y - h / 2
    ctx.rectangle(x0, y0, w, h)
    ctx.set_source_rgba(*col, Sy.fill_alpha * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*WHITE, Sy.edge_alpha * a)
    ctx.set_line_width(Sy.edge_w)
    ctx.stroke()
    ctx.set_source_rgba(*WHITE, Sy.edge_alpha * a)
    ctx.set_line_width(Sy.mark_w)
    if arm == INFANTRY:
        ctx.move_to(x0, y0)
        ctx.line_to(x0 + w, y0 + h)
        ctx.move_to(x0 + w, y0)
        ctx.line_to(x0, y0 + h)
        ctx.stroke()
    else:   # 기갑(기병도 같은 타원 — 검토본에 기병 부대 기호 없음)
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(w * Sy.armor_rx, h * Sy.armor_ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.stroke()
    text(ctx, ech, x, y0 + E.dy, E.size, E.font, WHITE, a, E.halo, "c", role="echelon")


class UnitLayer:
    def __init__(self, spec: CampaignSpec) -> None:
        self.spec = spec
        self.drawn: dict[str, int] = {}

    def name_color(self, nation: str) -> tuple:
        n = self.spec.nations[nation]
        return tuple(CA.light_name_rgb) if n.light_name else C[n.color]

    def draw(self, ctx: cairo.Context, view: View, t: float, res: list) -> None:
        N, m = CA.unit_name, CA.offscreen_px
        pad, top, bottom = CA.unit_box
        for u in self.spec.units:
            a = smooth((t - u.t) / CA.unit_in) * ramps(u.fade, t)
            if a <= F.min_alpha:
                continue
            x, y = view.to_screen(u.lon, ym(u.lat))
            if not (-m < x < W_OUT + m and -m < y < H_OUT + m):
                continue
            pop = 1 + CA.symbol.pop * (1 - ease_out(clamp01((t - u.t) / CA.symbol.pop_sec)))
            unit_symbol(ctx, x, y, C[self.spec.nations[u.nation].color], u.echelon, u.arm, a, pop)
            text(ctx, u.name, x, y + N.dy, N.size, N.font, self.name_color(u.nation), a, N.halo, "c")
            wd = max(tw(ctx, u.name, N.size, N.font), CA.symbol.w)
            res.append((x - wd / 2 - pad, y - top, x + wd / 2 + pad, y + bottom))
            self.drawn[f"unit:{u.echelon}"] = self.drawn.get(f"unit:{u.echelon}", 0) + 1

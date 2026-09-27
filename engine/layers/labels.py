"""라벨 LOD — 해역·국가·도(道)·도시 + 충돌 회피 (v2.1.0, render3 `draw_labels`, 04 §6·§7).

확대하면 정보가 늘어난다(00 §4-4). 마커·뱃지·컷아웃이 이번 프레임에 차지한 영역(R.reserved)은 피한다.
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.projection import View
from engine.style import H_OUT, SEA_LABEL, W_OUT
from engine.typography import text, tw


def draw_labels(ctx: cairo.Context, R: RenderCtx, view: View, t: float, la: float) -> None:  # noqa: N803
    A = R.assets  # noqa: N806
    lab = A.labels
    placed = list(R.reserved)

    def free(x: float, y: float, w: float, h: float) -> bool:
        for (a, b, c, d) in placed:
            if x < c and x + w > a and y < d and y + h > b:
                return False
        return True

    # seas
    for s in lab.seas:
        if not (s.wmin <= view.w <= s.wmax):
            continue
        x, y = view.xy(s.lon, s.lat)
        if -40 < x < W_OUT + 40 and 0 < y < H_OUT:
            text(ctx, s.name, x, y, 11 if view.w > 30 else 12, "serif", SEA_LABEL, 0.62 * la, 0, "c", spacing=2.2)
    # countries
    thr = 2 if view.w > 60 else 4 if view.w > 30 else 6 if view.w > 12 else 9
    for k, m in A.geo["meta"].items():
        if m["lx"] is None or (m.get("rank") or 9) > thr:
            continue
        if k in lab.hide_country_label_below_w and view.w < lab.hide_country_label_below_w[k]:
            continue
        x, y = view.xy(m["lx"], m["ly"])
        if not (30 < x < W_OUT - 30 and 60 < y < H_OUT - 70):
            continue
        nm = lab.ko.get(k, m["ko"])
        size = 12 if view.w > 30 else 13
        w = tw(ctx, nm, size, "sansm") + 1.8 * len(nm)
        if not free(x - w / 2, y - 12, w, 16):
            continue
        text(ctx, nm, x, y, size, "sansm", (0.9, 0.92, 0.96), 0.55 * la, 2.2, "c", spacing=1.8)
        placed.append((x - w / 2, y - 12, x + w / 2, y + 4))
    # admin-1 names (close zoom)
    if view.w < 8.5:
        for k in lab.province_countries:
            for ad in A.adm.get(k, []):
                if ad["lx"] is None:
                    continue
                x, y = view.xy(ad["lx"], ad["ly"])
                if 20 < x < W_OUT - 20 and 60 < y < H_OUT - 70:
                    w = tw(ctx, ad["name"], 9.5, "sans")
                    if free(x - w / 2, y - 9, w, 12):
                        text(ctx, ad["name"], x, y, 9.5, "sans", (0.78, 0.82, 0.88), 0.42 * la, 1.8, "c")
                        placed.append((x - w / 2, y - 9, x + w / 2, y + 3))
    # cities
    rk = 1 if view.w > 60 else 2 if view.w > 25 else 4 if view.w > 12 else 6 if view.w > 5 else 8
    xs = (A.plc_lon - view.u0) * view.s
    ys = (view.v1 - A.plc_v) * view.s
    m = (xs > 12) & (xs < W_OUT - 12) & (ys > 58) & (ys < H_OUT - 72) & ((A.plc_rank <= rk) | (A.plc_cap & (A.plc_rank <= rk + 2)))
    idx = np.where(m)[0]
    idx = idx[np.lexsort((-A.plc_pop[idx], A.plc_rank[idx]))][:40]
    n = 0
    for i in idx:
        x, y = xs[i], ys[i]
        nm = A.plc[i]["ko"]
        cap = A.plc_cap[i]
        size = 11.5 if cap else 10.5
        w = tw(ctx, nm, size, "sansb" if cap else "sansm")
        if not free(x - 3, y - 8, w + 10, 13):
            continue
        ctx.arc(x, y, 2.4 if cap else 1.9, 0, 2 * math.pi)
        ctx.set_source_rgba(0.95, 0.96, 0.98, 0.9 * la)
        ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6 * la)
        ctx.set_line_width(0.8)
        ctx.stroke()
        text(ctx, nm, x + 5, y + 4, size, "sansb" if cap else "sansm", (0.93, 0.94, 0.97), 0.82 * la, 2.6, "l")
        placed.append((x - 3, y - 8, x + w + 7, y + 5))
        n += 1
        if n >= 18:
            break

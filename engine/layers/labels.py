"""라벨 LOD — 해역·국가·도(道)·도시 + 충돌 회피 (v2.1.0, render3 `draw_labels`, 04 §6·§7).

확대하면 정보가 늘어난다(00 §4-4). 마커·뱃지·컷아웃이 이번 프레임에 차지한 영역(reserved)은 피한다.
v4.1.0: MercatorStage.draw_labels 가 부른다. 라벨 기준점은 무대가 미리 월드 좌표로 바꿔 둔 값, LOD 문턱은 `MERCATOR_LOD`(D-0076 작업 2).
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from typing import TYPE_CHECKING

from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.stage import by_w
from engine.style import H_OUT, W_OUT, hexc
from engine.typography import text, tw
from rules import load_rules

QA = load_rules().qa_checks

if TYPE_CHECKING:
    from engine.stage import MercatorStage


class LabelBox(tuple):
    """그린 지명 상자 (x0, y0, x1, y1) + 이름·종류(v5.3.0 D-0139 §3 — checks cascade 가 깔림·회피 지명을 이름으로 기록). 튜플 그대로 쓴다."""

    name: str
    kind: str


def _lb(box: tuple, name: str, kind: str) -> LabelBox:
    b = LabelBox(box)
    b.name, b.kind = name, kind
    return b


def _fix_contrast(ctx: cairo.Context, stage: "MercatorStage", nm: str, x: float, y: float, w: float, size: float, fnt: str,
                  th, a: float, hr: tuple) -> None:  # noqa: ANN001 — schemas.rules_models.MapTheme
    """v5.21.2 D-0186 §2-1 — 국소 대비 보정. 방금 그린 지명의 실제 바탕 대비(검사와 같은 식, engine.contrast)가
    qa_checks.map_contrast_text 미만이면 그 글자만 테마 label_contrast_fix halo 로 다시 그린다. 검사가 재지 않는 알파(< min_alpha)는 건드리지 않는다.
    통과한 글자는 그대로라 골든 컷 바이트가 바뀌지 않는다. 보정한 글자는 stage.label_contrast_fixed(이름 → 보정 전 최저 대비)에 남는다."""
    from engine import typography as ty  # noqa: PLC0415
    from engine.contrast import surface_text_ratio  # noqa: PLC0415

    fix = getattr(th, "label_contrast_fix", None)
    if fix is None or a < QA.map_contrast_min_alpha:
        return
    xs, ys = zip(*(ctx.user_to_device(px, py) for px in (x, x + w) for py in (y - size * 0.85, y + size * 0.25)))
    r = surface_text_ratio(ctx, (min(xs), min(ys), max(xs), max(ys)), th.city_label)
    if r is None or r >= QA.map_contrast_text:
        return
    if ty.CONTRAST_LOG:   # 보정 전 측정 항목은 지우고, 다시 그린 글자가 새로 기록된다
        ty.CONTRAST_LOG.pop()
    text(ctx, nm, x, y, size, fnt, th.city_label, a, fix.halo, "l", halo_a=fix.halo_a, halo_rgb=hr, contrast="required")
    fixed = stage.__dict__.setdefault("label_contrast_fixed", {})
    fixed[nm] = min(r, fixed.get(nm, r))


def draw_labels(ctx: cairo.Context, stage: "MercatorStage", view: View, reserved: list, la: float) -> list:
    A = stage.assets  # noqa: N806
    lab = A.labels
    th = stage.theme   # v5.13.0 D-0153 Q0-2 — 지명 색·글자 테두리(rules geo.themes.<테마>.map)
    hr = tuple(th.halo)
    placed = list(reserved)
    drawn: list = []   # v5.2.0 — 그린 지명 상자(해역 포함). 겹침 카드 깔림 검사(checks chain)가 읽는다. 그리기는 그대로

    def free(x: float, y: float, w: float, h: float) -> bool:
        for (a, b, c, d) in placed:
            if x < c and x + w > a and y < d and y + h > b:
                return False
        return True

    # seas
    for s, sw in stage.seas:
        if not (s.wmin <= view.w <= s.wmax):
            continue
        x, y = view.to_screen(*sw)
        if -40 < x < W_OUT + 40 and 0 < y < H_OUT:
            text(ctx, s.name, x, y, 11 if view.w > 30 else 12, "serif", hexc(th.sea_label), 0.62 * la, 0, "c", spacing=2.2, contrast="aux")
            sw_ = tw(ctx, s.name, 11 if view.w > 30 else 12, "serif") + 2.2 * len(s.name)
            drawn.append(_lb((x - sw_ / 2, y - 11, x + sw_ / 2, y + 3), s.name, "sea"))
    # countries
    thr = by_w(view.w, LOD["country_rank_max"])
    for k, m, mw in stage.countries:
        if mw is None or (m.get("rank") or 9) > thr:
            continue
        if k in lab.hide_country_label_below_w and view.w < lab.hide_country_label_below_w[k]:
            continue
        x, y = view.to_screen(*mw)
        if not (30 < x < W_OUT - 30 and 60 < y < H_OUT - 70):
            continue
        nm = lab.ko.get(k, m["ko"])
        size = 12 if view.w > 30 else 13
        w = tw(ctx, nm, size, "sansm") + 1.8 * len(nm)
        if not free(x - w / 2, y - 12, w, 16):
            continue
        text(ctx, nm, x, y, size, "sansm", th.country_label, 0.55 * la, 2.2, "c", spacing=1.8, halo_rgb=hr, contrast="aux")
        placed.append((x - w / 2, y - 12, x + w / 2, y + 4))
        drawn.append(_lb(placed[-1], nm, "country"))
    # admin-1 names (close zoom)
    if view.w < LOD["admin_names_below_w"]:
        for k in lab.province_countries:
            for ad in stage.adm.get(k, []):
                if ad["xy"] is None:
                    continue
                x, y = view.to_screen(*ad["xy"])
                if 20 < x < W_OUT - 20 and 60 < y < H_OUT - 70:
                    w = tw(ctx, ad["name"], 9.5, "sans")
                    if free(x - w / 2, y - 9, w, 12):
                        text(ctx, ad["name"], x, y, 9.5, "sans", th.admin_label, 0.42 * la, 1.8, "c", halo_rgb=hr, contrast="aux")
                        placed.append((x - w / 2, y - 9, x + w / 2, y + 3))
                        drawn.append(_lb(placed[-1], ad["name"], "admin"))
    # cities
    rk = by_w(view.w, LOD["city_rank_max"])
    xs = (stage.plc_x - view.x0) * view.s
    ys = (view.y1 - stage.plc_y) * view.s
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
        ctx.set_source_rgba(*th.city_dot.fill, 0.9 * la)
        ctx.fill_preserve()
        ctx.set_source_rgba(*th.city_dot.edge, th.city_dot.edge_alpha * la)
        ctx.set_line_width(0.8)
        ctx.stroke()
        text(ctx, nm, x + 5, y + 4, size, "sansb" if cap else "sansm", th.city_label, 0.82 * la, 2.6, "l", halo_rgb=hr, contrast="required")
        _fix_contrast(ctx, stage, nm, x + 5, y + 4, w, size, "sansb" if cap else "sansm", th, 0.82 * la, hr)
        placed.append((x - 3, y - 8, x + w + 7, y + 5))
        drawn.append(_lb(placed[-1], nm, "city"))
        n += 1
        if n >= LOD["city_labels_max"]:
            break
    return drawn

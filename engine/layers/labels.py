"""라벨 LOD — 해역·국가·도(道)·도시 + 충돌 회피 (v2.1.0, render3 `draw_labels`, 04 §6·§7).

확대하면 정보가 늘어난다(00 §4-4). 마커·뱃지·컷아웃이 이번 프레임에 차지한 영역(reserved)은 피한다.
v4.1.0: MercatorStage.draw_labels 가 부른다. 라벨 기준점은 무대가 미리 월드 좌표로 바꿔 둔 값, LOD 문턱은 `MERCATOR_LOD`(D-0076 작업 2).
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from typing import TYPE_CHECKING, Callable

from engine import skin
from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.stage import by_w, skin_map
from engine.style import H_OUT, SKIN, W_OUT, hexc
from engine.typography import text, tw
from rules import load_rules

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


def sea_labels(ctx: cairo.Context, stage: "MercatorStage", view: View) -> list[tuple[str, float, float, float, tuple]]:
    """지금 보이는 해역 이름(이름, x, y, 크기, 상자). 해역 이름은 다른 글자를 피하지 않는다 — 경로 라벨이 이 상자를 피한다(v5.21.11 D-0192)."""
    out = []
    on = skin_map(stage)   # v7.4.0 4b — skin 지도: 기울임 없는 sans, 작게(rules skin.map.sea_label)
    T = SKIN.map.sea_label  # noqa: N806
    for s, sw in stage.seas:
        if not (s.wmin <= view.w <= s.wmax):
            continue
        x, y = view.to_screen(*sw)
        if -40 < x < W_OUT + 40 and 0 < y < H_OUT:
            if on:
                size = T.size if view.w > 30 else (T.size_near or T.size)
                sw_ = tw(ctx, s.name, size, T.font) + T.track * len(s.name)
                out.append((s.name, x, y, size, (x - sw_ / 2, y - size, x + sw_ / 2, y + size / 3)))
                continue
            size = 11 if view.w > 30 else 12
            sw_ = tw(ctx, s.name, size, "serif") + 2.2 * len(s.name)
            out.append((s.name, x, y, size, (x - sw_ / 2, y - 11, x + sw_ / 2, y + 3)))
    return out


def _ink(name: str | None, default: tuple) -> tuple:
    return default if name is None else hexc(getattr(SKIN.ink, name))


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

    on = skin_map(stage)   # v7.4.0 4b — skin 지도 지명(rules skin.map): 잉크 3단·밝은 테마 halo·국기 채운 나라는 흰 알약
    SM = SKIN.map  # noqa: N806
    # seas
    for name, x, y, size, box in sea_labels(ctx, stage, view):
        if on:
            T = SM.sea_label  # noqa: N806
            text(ctx, name, x, y, size, T.font, _ink(T.ink, hexc(th.sea_label)), T.alpha * la, T.halo, "c", spacing=T.track,
                 halo_a=T.halo_a, halo_rgb=hr, contrast="aux")
        else:
            text(ctx, name, x, y, size, "serif", hexc(th.sea_label), 0.62 * la, 0, "c", spacing=2.2, contrast="aux")
        drawn.append(_lb(box, name, "sea"))
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
        if on:
            fa = stage.flag_codes.get(k, 0.0)
            anc = _flag_anchor(ctx, view, k, nm) if fa > 0 else None
            if fa > 0 and anc is None:   # v7.4.0 4b-2 — 나라 위·아래 어디에도 자리가 없으면 이름을 국기 위에 얹지 않는다
                continue
            box = _skin_country(ctx, nm, x, y, view.w, la, fa, hr, free, anc)
            if box is None:
                continue
            placed.append(box)
            drawn.append(_lb(placed[-1], nm, "country"))
            continue
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
                        if on:
                            T = SM.admin_label  # noqa: N806
                            text(ctx, ad["name"], x, y, T.size, T.font, _ink(T.ink, th.admin_label), T.alpha * la, T.halo, "c",
                                 spacing=T.track, halo_a=T.halo_a, halo_rgb=hr, contrast="aux")
                        else:
                            text(ctx, ad["name"], x, y, 9.5, "sans", th.admin_label, 0.42 * la, 1.8, "c", halo_rgb=hr, contrast="aux")
                        placed.append((x - w / 2, y - 9, x + w / 2, y + 3))
                        drawn.append(_lb(placed[-1], ad["name"], "admin"))
    # cities
    rk = by_w(view.w, LOD["city_rank_max"])
    xs = (stage.plc_x - view.x0) * view.s
    ys = (view.y1 - stage.plc_y) * view.s
    flags = _flag_paths(ctx, view, stage) if on else []   # v7.4.0 4b-2 — 국기로 채운 나라(알파, 화면 경로)
    cand = (A.plc_rank <= rk) | (A.plc_cap & (A.plc_rank <= rk + 2))
    cr = load_rules().labels   # v7.4.0 D-0229 §2.1(UF-106) — 수도 상시 표기(폭 LOD 무관, 화면당 상한은 그대로)
    if cr.capital_always and (cr.capital_always_max_w is None or view.w <= cr.capital_always_max_w):
        cand = cand | A.plc_cap0   # 나라 수도만(1급 행정 중심 제외)
    m = (xs > 12) & (xs < W_OUT - 12) & (ys > 58) & (ys < H_OUT - 72) & cand
    idx = np.where(m)[0]
    idx = idx[np.lexsort((-A.plc_pop[idx], A.plc_rank[idx]))][:40]
    n = 0
    for i in idx:
        x, y = xs[i], ys[i]
        nm = A.plc[i]["ko"]
        cap = A.plc_cap[i]
        if on:
            fk = _flag_fade(ctx, flags, x, y, reserved)
            if fk <= 0.01:
                continue
            box = _skin_city(ctx, nm, x, y, bool(cap), la * fk, hr, free)
            if box is None:
                continue
            placed.append(box)
            drawn.append(_lb(placed[-1], nm, "city"))
            n += 1
            if n >= LOD["city_labels_max"]:
                break
            continue
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
        placed.append((x - 3, y - 8, x + w + 7, y + 5))
        drawn.append(_lb(placed[-1], nm, "city"))
        n += 1
        if n >= LOD["city_labels_max"]:
            break
    return drawn


def _flag_anchor(ctx: cairo.Context, view: View, code: str, nm: str) -> tuple[float, float] | None:
    """v7.4.0 4b-2 — 국기로 채운 나라 이름 알약 가운데(x, y − flag_label.dy): 나라 외곽 상자 아래 끝 + gap, 가로 = 상자 가운데(화면 좌우
    margin_x 안으로 민다). 국기 문장(紋章) 위를 덮지 않게 나라 밖에 둔다 — 아래 끝이 H − bottom(자막 위)을 넘으면 상자 위 끝 − gap,
    그것도 top 위로 나가면 None(이름 없음, 국기 위로 끌어올리지 않는다). rules skin.map_overlays.flag_label_below."""
    from engine.layers.flag_fill import world_box  # noqa: PLC0415 — flag_fill → labels 순환 회피

    F, B = SKIN.map.flag_label, SKIN.map_overlays.flag_label_below  # noqa: N806
    wx0, wy0, wx1, wy1 = world_box(view, [code])
    sx0, sy0 = view.to_screen(wx0, wy1)
    sx1, sy1 = view.to_screen(wx1, wy0)
    pw = tw(ctx, nm, F.size, F.font) + F.track * len(nm) + 2 * F.pad_x
    cx = min(max((sx0 + sx1) / 2, B.margin_x + pw / 2), W_OUT - B.margin_x - pw / 2)
    cy = sy1 + B.gap + F.h / 2
    if cy + F.h / 2 > H_OUT - B.bottom:
        cy = sy0 - B.gap - F.h / 2
        if cy - F.h / 2 < B.top:
            return None
    return cx, cy - F.dy


def _flag_paths(ctx: cairo.Context, view: View, stage: "MercatorStage") -> list[tuple[float, cairo.Path]]:
    """v7.4.0 4b-2 — 이 프레임 국기로 채운 나라의 (국기 알파, 화면 경로) — 그 안 도시 이름은 국기와 함께 사라진다."""
    from engine.layers.flag_fill import _path  # noqa: PLC0415

    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    out = []
    for code, fa in stage.flag_codes.items():
        if fa <= 0:
            continue
        ctx.save()
        if _path(ctx, view, lod, [code]):
            out.append((fa, ctx.copy_path()))
        ctx.new_path()
        ctx.restore()
    return out


def _flag_fade(ctx: cairo.Context, flags: list[tuple[float, cairo.Path]], x: float, y: float, reserved: list) -> float:
    """도시 이름 알파 배율 — 국기로 채운 나라 안이면 1 − 국기 알파(국기가 보이는 동안 숨김). 보이는 마커가 가리키는 자리(예약 상자 안)는 그대로."""
    k = 1.0
    for fa, path in flags:
        ctx.save()
        ctx.new_path()
        ctx.append_path(path)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        inside = ctx.in_fill(x, y)
        ctx.new_path()
        ctx.restore()
        if inside:
            k = min(k, 1.0 - fa)
    if k < 1.0 and any(a <= x <= c and b <= y <= d for (a, b, c, d) in reserved):
        return 1.0
    return k


def _skin_country(ctx: cairo.Context, nm: str, x: float, y: float, vw: float, la: float, fa: float, hr: tuple,
                  free: "Callable[[float, float, float, float], bool]", anchor: tuple[float, float] | None = None) -> tuple | None:
    """v7.4.0 4b — skin 지도 나라 이름: 보조 잉크·넓은 자간·밝은 halo. 국기로 채운 나라(fa > 0) = 흰 알약 위 잉크(skin.pill + 그림자 겹).
    v7.4.0 4b-2 — 알약 자리 = anchor(나라 외곽 상자 아래, `_flag_anchor`). 사라지는 옛 글자는 지명점 그대로."""
    T = SKIN.map.country_label  # noqa: N806
    if fa > 0:
        F = SKIN.map.flag_label  # noqa: N806
        ax, ay = anchor if anchor is not None else (x, y)
        w = tw(ctx, nm, F.size, F.font) + F.track * len(nm)
        pw = w + 2 * F.pad_x
        bx = (ax - pw / 2, ay + F.dy - F.h / 2, pw, F.h)
        if not free(bx[0], bx[1], bx[2], bx[3]):
            return None
        skin.pill(ctx, bx, skin.FILL, la * fa, F.shadow)
        text(ctx, nm, ax, ay + F.dy + F.text_dy, F.size, F.font, _ink(F.ink, skin.INK), la * fa, 0, "c", spacing=F.track, contrast="aux")
        if fa < 1:   # 국기가 나타나는 동안 — 알약 밖 글자가 사라진다
            text(ctx, nm, x, y, T.size if vw > 30 else (T.size_near or T.size), T.font, _ink(T.ink, skin.INK2), T.alpha * la * (1 - fa),
                 T.halo, "c", spacing=T.track, halo_a=T.halo_a, halo_rgb=hr, contrast="aux")
        return (bx[0], bx[1], bx[0] + bx[2], bx[1] + bx[3])
    size = T.size if vw > 30 else (T.size_near or T.size)
    w = tw(ctx, nm, size, T.font) + T.track * len(nm)
    if not free(x - w / 2, y - size, w, size * 4 / 3):
        return None
    text(ctx, nm, x, y, size, T.font, _ink(T.ink, skin.INK2), T.alpha * la, T.halo, "c", spacing=T.track, halo_a=T.halo_a,
         halo_rgb=hr, contrast="aux")
    return (x - w / 2, y - size, x + w / 2, y + size / 3)


def _skin_city(ctx: cairo.Context, nm: str, x: float, y: float, cap: bool, la: float, hr: tuple,
               free: "Callable[[float, float, float, float], bool]") -> tuple | None:
    """v7.4.0 4b — skin 지도 도시: 잉크 점 + 흰 고리, 굵지 않은 잉크 글자(sansm) + 밝은 halo. 수도는 한 단 크게."""
    T, D = SKIN.map.city_label, SKIN.map.city_dot  # noqa: N806
    size = T.size_cap if cap else T.size
    w = tw(ctx, nm, size, T.font)
    if not free(x - D.r_cap, y - size * 3 / 4, w + T.dx + D.r_cap * 2, size * 5 / 4):
        return None
    ink = _ink(T.ink, skin.INK)
    ctx.new_path()
    ctx.arc(x, y, D.r_cap if cap else D.r, 0, 2 * math.pi)
    ctx.set_source_rgba(*ink, la)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hr, D.ring_alpha * la)
    ctx.set_line_width(D.ring_w)
    ctx.stroke()
    text(ctx, nm, x + T.dx, y + T.dy, size, T.font, ink, T.alpha * la, T.halo, "l", halo_a=T.halo_a, halo_rgb=hr, contrast="required")
    return (x - D.r_cap, y - size * 3 / 4, x + T.dx + w + D.r_cap, y + size / 2)

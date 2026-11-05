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
from engine.style import H_OUT, W_OUT, hexc, map_c
from engine.typography import text, tw
from rules import load_rules

LR = load_rules().labels   # 모듈 로드 때 한 번(load_rules 는 매번 YAML 을 다시 읽는다 — 프레임·숏 일정 표본마다 부르면 느리다)

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
    for s, sw in stage.seas:
        if not (s.wmin <= view.w <= s.wmax):
            continue
        x, y = view.to_screen(*sw)
        if -40 < x < W_OUT + 40 and 0 < y < H_OUT:
            size = 11 if view.w > 30 else 12
            sw_ = tw(ctx, s.name, size, "serif") + 2.2 * len(s.name)
            out.append((s.name, x, y, size, (x - sw_ / 2, y - 11, x + sw_ / 2, y + 3)))
    return out


class Cand:
    """지명 후보 하나 — id(종류:이름), test 상자(x, y, w, h — free 판정), placed 상자(예약에 올리는 것), 그리기 함수.
    v7.4.0 D-0311(UF-175) — 프레임별 선택(옛)과 숏 단위 일정(새)이 같은 후보 목록을 쓴다."""

    __slots__ = ("id", "kind", "test", "placed", "draw", "blocks", "name")

    def __init__(self, cid: str, kind: str, test: "tuple | None", placed: tuple, draw: object, blocks: bool = True, name: str = "") -> None:
        self.id, self.kind, self.test, self.placed, self.draw, self.blocks, self.name = cid, kind, test, placed, draw, blocks, name


def label_candidates(ctx: cairo.Context, stage: "MercatorStage", view: View, lod_w: "float | None" = None) -> list[Cand]:
    """이 뷰에서 그릴 수 있는 지명 후보(그리기 차례대로). lod_w = LOD 판정에 쓸 폭(기본 view.w — 숏 일정의 이력 LOD 는 더 좁은 폭을 준다).
    자리·크기·글꼴·색은 v7.3·D-0303 값 그대로(골든 동작 = 이 목록을 차례로 free 판정)."""
    A = stage.assets  # noqa: N806
    lab = A.labels
    th = stage.theme   # v5.13.0 D-0153 Q0-2 — 지명 색·글자 테두리(rules geo.themes.<테마>.map)
    hr = tuple(th.halo)
    lw = view.w if lod_w is None else lod_w
    out: list[Cand] = []
    # seas — 다른 글자를 피하지 않고 막지도 않는다(경로 라벨이 이 상자를 피한다)
    for s, sw in stage.seas:
        if not (s.wmin <= lw <= s.wmax):
            continue
        x, y = view.to_screen(*sw)
        if -40 < x < W_OUT + 40 and 0 < y < H_OUT:
            size = 11 if view.w > 30 else 12
            sw_ = tw(ctx, s.name, size, "serif") + 2.2 * len(s.name)
            box = (x - sw_ / 2, y - 11, x + sw_ / 2, y + 3)

            def d(la: float, nm: str = s.name, x: float = x, y: float = y, size: float = size) -> None:
                text(ctx, nm, x, y, size, "serif", hexc(th.sea_label), 0.62 * la, 0, "c", spacing=2.2, contrast="aux")
            out.append(Cand("sea:" + s.name, "sea", None, box, d, blocks=False, name=s.name))
    # countries
    thr = by_w(lw, LOD["country_rank_max"])
    for k, m, mw in stage.countries:
        if mw is None or (m.get("rank") or 9) > thr:
            continue
        if k in lab.hide_country_label_below_w and lw < lab.hide_country_label_below_w[k]:
            continue
        x, y = view.to_screen(*mw)
        if not (30 < x < W_OUT - 30 and 60 < y < H_OUT - 70):
            continue
        nm = lab.ko.get(k, m["ko"])
        size = 12 if view.w > 30 else 13
        w = tw(ctx, nm, size, "sansm") + 1.8 * len(nm)

        def d(la: float, nm: str = nm, x: float = x, y: float = y, size: float = size) -> None:
            text(ctx, nm, x, y, size, "sansm", th.country_label, 0.55 * la, 2.2, "c", spacing=1.8, halo_rgb=hr, contrast="aux")
        out.append(Cand("country:" + k, "country", (x - w / 2, y - 12, w, 16), (x - w / 2, y - 12, x + w / 2, y + 4), d, name=nm))
    # admin-1 names — v7.4.0 D-0303 §1(UF-167·168): 모드(rules labels.admin1_modes, direction stage_config.mercator.admin1_labels)
    md = getattr(stage, "admin1_mode", None)
    if md is None:   # 모드 규칙이 없는 옛 규칙 파일 — v7.3 리터럴과 같은 값
        md_below, md_size, md_font, md_alpha, md_halo, md_halo_a, mc = LOD["admin_names_below_w"], 9.5, "sans", 0.42, 1.8, 0.8, None
    else:
        md_below, md_size, md_font, md_alpha, md_halo, md_halo_a, mc = md.below_w, md.size, md.font, md.alpha, md.halo, md.halo_a, md.cities
    md_col = map_c(stage, "white") if md is not None and md.color == "ink" else th.admin_label   # v7.4.0 D-0305 — prominent 주 이름 잉크
    if lw < md_below:
        for k in lab.province_countries:
            for ad in stage.adm.get(k, []):
                if ad["xy"] is None:
                    continue
                x, y = view.to_screen(*ad["xy"])
                if 20 < x < W_OUT - 20 and 60 < y < H_OUT - 70:
                    w = tw(ctx, ad["name"], md_size, md_font)
                    top, hh = round(md_size * 0.95), round(md_size * 1.26)   # subtle 9.5px → 9·12(v7.3 상자 그대로)

                    def d(la: float, nm: str = ad["name"], x: float = x, y: float = y) -> None:
                        text(ctx, nm, x, y, md_size, md_font, md_col, md_alpha * la, md_halo, "c", 0.0, md_halo_a, halo_rgb=hr, contrast="aux")
                    out.append(Cand(f"admin:{k}:{ad['name']}", "admin", (x - w / 2, y - top, w, hh), (x - w / 2, y - top, x + w / 2, y - top + hh), d, name=ad["name"]))
    # cities
    rk = by_w(lw, LOD["city_rank_max"])
    xs = (stage.plc_x - view.x0) * view.s
    ys = (view.y1 - stage.plc_y) * view.s
    cand = (A.plc_rank <= rk) | (A.plc_cap & (A.plc_rank <= rk + 2))
    cr = LR   # v7.4.0 D-0229 §2.1(UF-106) — 수도 상시 표기(폭 LOD 무관, 화면당 상한은 그대로)
    if cr.capital_always and (cr.capital_always_max_w is None or lw <= cr.capital_always_max_w):
        cand = cand | A.plc_cap0   # 나라 수도만(1급 행정 중심 제외)
    if mc is not None:   # v7.4.0 D-0303 §1 — prominent: 초점 나라 밖 도시 제외, 넓은 화면에선 수도(주도·나라 수도)만
        if not mc.foreign:
            miss = [k for k in lab.province_countries if k not in lab.iso3]
            if miss or not lab.province_countries:   # 초점 나라를 모르고 도시를 조용히 다 지우지 않는다(P6)
                raise ValueError(f"labels.yaml province_countries {lab.province_countries} 의 iso3 가 없다 {miss} — admin1 prominent cities.foreign false")
            iso3 = {lab.iso3[k] for k in lab.province_countries}
            cand = cand & np.isin(A.plc_iso, list(iso3))
        if lw > mc.capitals_only_above_w:
            cand = cand & A.plc_cap
    m = (xs > 12) & (xs < W_OUT - 12) & (ys > 58) & (ys < H_OUT - 72) & cand
    idx = np.where(m)[0]
    idx = idx[np.lexsort((-A.plc_pop[idx], A.plc_rank[idx]))][:40]
    for i in idx:
        x, y = float(xs[i]), float(ys[i])
        nm = A.plc[i]["ko"]
        cap = bool(A.plc_cap[i])
        size = (11.5 if cap else 10.5) if mc is None else mc.size
        halo = 2.6 if mc is None else mc.halo
        w = tw(ctx, nm, size, "sansb" if cap else "sansm")

        def d(la: float, nm: str = nm, x: float = x, y: float = y, cap: bool = cap, size: float = size, halo: float = halo) -> None:
            ctx.arc(x, y, 2.4 if cap else 1.9, 0, 2 * math.pi)
            ctx.set_source_rgba(*th.city_dot.fill, 0.9 * la)
            ctx.fill_preserve()
            ctx.set_source_rgba(*th.city_dot.edge, th.city_dot.edge_alpha * la)
            ctx.set_line_width(0.8)
            ctx.stroke()
            text(ctx, nm, x + 5, y + 4, size, "sansb" if cap else "sansm", th.city_label, (0.82 if mc is None else mc.alpha) * la, halo, "l", halo_rgb=hr, contrast="required")
        out.append(Cand(f"city:{i}", "city", (x - 3, y - 8, w + 10, 13), (x - 3, y - 8, x + w + 7, y + 5), d, name=nm))
    return out


def city_cap(stage: "MercatorStage") -> int:
    md = getattr(stage, "admin1_mode", None)
    return LOD["city_labels_max"] if md is None or md.cities is None else md.cities.max_per_frame


def _hit(r: tuple, boxes: list) -> bool:
    x, y, w, h = r
    return any(x < c and x + w > a and y < dd and y + h > b for (a, b, c, dd) in boxes)


def select_greedy(cands: list[Cand], reserved: list, cmax: int) -> list[Cand]:
    """프레임 하나의 선택(옛 동작 그대로) — 차례대로 free 판정, 도시는 화면당 cmax."""
    placed = list(reserved)
    out: list[Cand] = []
    n = 0
    for c in cands:
        if c.kind == "city" and n >= cmax:
            continue
        if c.test is not None and _hit(c.test, placed):
            continue
        out.append(c)
        if c.blocks:
            placed.append(c.placed)
        if c.kind == "city":
            n += 1
    return out


def draw_labels(ctx: cairo.Context, stage: "MercatorStage", view: View, reserved: list, la: float, t: "float | None" = None) -> list:
    """지명 그리기. t 와 숏 단위 일정(stage.label_plan, v7.4.0 D-0311 UF-175)이 있으면 일정대로(있고 없음·페이드),
    없으면 프레임 하나의 선택(검사·아일랜드 등 시각이 없는 호출)."""
    plan = getattr(stage, "label_plan", None)
    drawn: list = []
    if plan is None or t is None:
        for c in select_greedy(label_candidates(ctx, stage, view), reserved, city_cap(stage)):
            c.draw(la)
            drawn.append(_lb(c.placed, c.name, c.kind))
        return drawn
    S = LR.stability  # noqa: N806
    act = plan.active(t)
    if not act:
        return drawn
    for c in label_candidates(ctx, stage, view, lod_w=view.w / S.lod_hysteresis):
        a = act.get(c.id)
        if a is None:
            continue
        c.draw(la * a)
        drawn.append(_lb(c.placed, c.name, c.kind))
    return drawn

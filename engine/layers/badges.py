"""원형 뱃지 — 인물·국기·휘장 (v2.1.0, render3 `flag_wave, badge_at, draw_badge`).

이미지 키: 인물 `portrait:<pid>`, 국기 `flag43:<cc>`·`flag11:<cc>`, 휘장 `emblem:<id>` (engine/assets.py).

v4.8.0 back_and_forth D-0101 §1(사용자 결정 D89) — 인물 뱃지 적응 크기. 연출이 R 를 주지 않은 인물 뱃지는 코드가
같은 무대에서 보이는 인물 뱃지 수 n(t) 로 R 를 정한다(`assign_person_sizes`, 15 P8). 크기·이름표 글자는 `rules layout_480p.badge`.
"""

from __future__ import annotations

import math

import cairo

from engine.assets import set_raster
from engine.context import RenderCtx
from engine.projection import View
from engine.style import BADGE, BADGE_BG, C
from engine.timebase import ease_back, smooth, window
from engine.typography import rrect, text, tw


def flag_wave(ctx: cairo.Context, R: RenderCtx, key: str, cx: float, cy: float, wdt: float, a: float,  # noqa: N803
              t: float) -> None:
    k_ = R.out.k
    fs, fw, fh = R.assets.raster(key, wdt, k_)
    n = 14
    for i in range(n):
        dy = math.sin(t * 2.6 + i * 0.5) * wdt * 0.032
        ctx.save()
        ctx.rectangle(cx - fw / 2 + fw * i / n, cy - fh / 2 + dy - 1, fw / n + 1, fh + 2)
        ctx.clip()
        set_raster(ctx, fs, k_, cx - fw / 2, cy - fh / 2 + dy)
        ctx.paint_with_alpha(a)
        ctx.set_source_rgba(0, 0, 0, 0.16 * (0.5 + 0.5 * math.sin(t * 2.6 + i * 0.5 + 1.2)) * a)
        ctx.paint()
        ctx.restore()


def resolve_kind(R: RenderCtx, e: dict) -> tuple[str, str | None]:  # noqa: N803
    """휘장 뱃지의 권리 결정 적용(D5): flag_fallback 이면 ("flag", 대체 국기). 그 밖에는 (kind, 국기)."""
    if e["kind"] == "emblem":
        fb = R.assets.emblem_flag(e["img"])
        if fb is not None:
            return "flag", fb
    return e["kind"], e.get("flag")


def image_keys(e: dict, R: RenderCtx | None = None) -> list[str]:  # noqa: N803
    """뱃지 하나가 쓰는 이미지 키(렌더 전 자산 점검용)."""
    if e["kind"] == "emblem" and R is not None:
        kind, fb = resolve_kind(R, e)
        if kind == "flag":
            return [f"flag11:{fb}"]
    if e["kind"] == "person":
        return [f"portrait:{e['pid']}", f"flag43:{e['flag']}"]
    if e["kind"] == "flag":
        return [f"flag11:{e['flag']}"]
    return [f"emblem:{e['img']}"]


def _target_R(n: int) -> float:  # noqa: N802
    """보이는 인물 뱃지 수 → 목표 R. n ≤ 1 = solo, 2 = group 큰 값, ≥ 3 = group 작은 값."""
    lo, hi = BADGE.R_person_group
    return BADGE.R_person_solo if n <= 1 else hi if n == 2 else lo


def _pool(e: dict) -> str:
    return "panel" if e.get("over_panel") else "stage"


def assign_person_sizes(events: list[dict]) -> None:
    """R 없는 인물 뱃지마다 크기 일정 `R_sched` = {base, steps: [[c, dR], …]} 를 단다(제자리). 결정적 — 이벤트 시각만 쓴다.
    센다 = 같은 풀(지도·시간축 무대 / 패널 위)의 인물 뱃지가 팝인을 끝낸 뒤 ~ 페이드 아웃 시작 전. 뱃지 자신은 뜨는 순간부터 센다."""
    people = [e for e in events if e["type"] == "badge" and e["kind"] == "person"]
    for e in people:
        if e.get("R") is not None:
            continue
        pool = [b for b in people if _pool(b) == _pool(e)]
        spans = [(e["t0"] if b is e else b["t0"] + BADGE.popin_sec, b["t1"] - BADGE.fade_out_sec) for b in pool]

        def n_at(s: float, spans: list[tuple[float, float]] = spans) -> int:
            return sum(1 for a, z in spans if a <= s < z)

        cuts = sorted({c for sp in spans for c in sp if e["t0"] < c < e["t1"]})
        prev = _target_R(n_at(e["t0"]))
        steps: list[list[float]] = []
        for c in cuts:
            cur = _target_R(n_at(c))
            if cur != prev:
                steps.append([c, cur - prev])
            prev = cur
        e["R_sched"] = {"base": _target_R(n_at(e["t0"])), "steps": steps}


def badge_R(e: dict, t: float | None = None) -> float:  # noqa: N802
    """뱃지 반지름. 연출 R 이 있으면 그 값. 적응 인물 뱃지는 시각 t 의 값(t 없음 = 구간 최대, 상자 계산의 보수값).
    국기·휘장에 R 이 없으면 `badge.R_other`."""
    if e.get("R") is not None:
        return float(e["R"])
    sch = e.get("R_sched")
    if sch is None:
        return BADGE.R_other if e["kind"] != "person" else _target_R(1)
    if t is None:
        vals, acc = [sch["base"]], sch["base"]
        for _, d in sch["steps"]:
            acc += d
            vals.append(acc)
        return max(vals)
    return sch["base"] + sum(d * smooth((t - c) / BADGE.resize_sec) for c, d in sch["steps"])


def label_sizes(e: dict, Rr: float) -> tuple[float, float]:  # noqa: N803
    """이름표 (이름, 역할) 글자 크기. 적응 인물 뱃지는 R 에 따라 group ↔ solo 보간, 그 밖은 group(아래)·side(오른쪽)."""
    base = BADGE.label_side if e.get("side") == "right" else BADGE.label_group
    if e["kind"] != "person" or e.get("R") is not None:
        return base
    hi = BADGE.R_person_group[1]
    f = min(1.0, max(0.0, (Rr - hi) / (BADGE.R_person_solo - hi)))
    return tuple(g + (s_ - g) * f for g, s_ in zip(base, BADGE.label_solo))  # type: ignore[return-value]


def badge_at(ctx: cairo.Context, R: RenderCtx, x: float, y: float, e: dict, t: float, a: float) -> None:  # noqa: N803
    Rr = badge_R(e, t)  # noqa: N806
    lt = t - e["t0"]
    k = ease_back(lt / BADGE.popin_sec)
    if k <= 0.01:
        return
    acc = C.get(e.get("accent") or "gold", C["gold"])
    kind, flag = resolve_kind(R, e)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(k, k)
    for r_, al in ((Rr + 7, 0.1), (Rr + 4, 0.18)):
        ctx.arc(1.5, 3, r_, 0, 2 * math.pi)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()
    ctx.save()
    ctx.arc(0, 0, Rr, 0, 2 * math.pi)
    ctx.clip()
    ctx.set_source_rgba(*BADGE_BG, a)
    ctx.paint()
    if e["kind"] == "person":
        flag_wave(ctx, R, f"flag43:{e['flag']}", Rr * 0.25, -Rr * 0.05, Rr * 2.3, 0.92 * a, t)
    elif kind == "flag":
        fs, fw, fh = R.assets.raster(f"flag11:{flag}", Rr * 2.1, R.out.k)
        set_raster(ctx, fs, R.out.k, -fw / 2, -fh / 2)
        ctx.paint_with_alpha(a)
    elif kind == "emblem":
        ctx.set_source_rgba(0.96, 0.96, 0.97, a)
        ctx.paint()
        fs, fw, fh = R.assets.raster(f"emblem:{e['img']}", Rr * 1.96, R.out.k)
        set_raster(ctx, fs, R.out.k, -fw / 2, -fh / 2)
        ctx.paint_with_alpha(a)
    ctx.restore()
    if e["kind"] == "person":
        ps, pw, ph = R.assets.raster(f"portrait:{e['pid']}", Rr * 1.72, R.out.k)
        ctx.save()
        ctx.arc(0, 0, Rr, 0, 2 * math.pi)
        ctx.rectangle(-Rr * 0.66, -Rr * 2.4, Rr * 1.32, Rr * 2.4)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        ctx.clip()
        set_raster(ctx, ps, R.out.k, -pw / 2, Rr - ph + Rr * 0.02)
        ctx.paint_with_alpha(a)
        ctx.restore()
    ctx.new_path()
    ctx.arc(0, 0, Rr, 0, 2 * math.pi)
    ctx.set_source_rgba(0.03, 0.04, 0.06, a)
    ctx.set_line_width(3.2)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*acc, 0.92 * a)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.restore()
    la = a * smooth((lt - 0.3) / 0.35)
    if e.get("label") and la > 0.01:
        LB = BADGE.label_box  # noqa: N806
        ls, rs = label_sizes(e, Rr)
        if e.get("side") == "right":
            text(ctx, e["label"], x + Rr * k + LB.side_dx, y + LB.side_dy, ls, "sansb", (1, 1, 1), la, 3, "l")
            if e.get("role"):
                text(ctx, e["role"], x + Rr * k + LB.side_dx, y + LB.side_role_dy * ls / BADGE.label_side[0], rs, "sansm", acc, la, 2.6, "l")
        else:
            w = tw(ctx, e["label"], ls, "sansb")
            box_h = ls + LB.pad_y
            top = y + Rr * k + LB.gap
            rrect(ctx, x - w / 2 - LB.pad_x, top, w + LB.pad_x * 2, box_h, 3)
            ctx.set_source_rgba(0.03, 0.04, 0.06, 0.84 * la)
            ctx.fill()
            base = top + box_h - LB.inset
            text(ctx, e["label"], x, base, ls, "sansb", (1, 1, 1), la, 0, "c")
            if e.get("role"):
                text(ctx, e["role"], x, base + rs + LB.role_gap, rs, "sansm", acc, la, 2.6, "c")
    R.reserved.append((x - Rr - 10, y - Rr * BADGE.reserve_top_factor, x + Rr + 10, y + Rr + BADGE.reserve_bottom_px))


def badge_box(ctx: cairo.Context, e: dict, x: float, y: float, t: float | None = None) -> tuple[float, float, float, float]:
    """지도 뱃지가 차지하는 상자(원·그림자·인물 머리·이름표·역할) — 카드 RESERVED 회피용(D-0033).
    t = 시각(적응 인물 뱃지의 그 순간 R). None 이면 구간 최대 R(보수값 — 카메라 구도·framing)."""
    Rr = badge_R(e, t)  # noqa: N806
    LB = BADGE.label_box  # noqa: N806
    top = y - Rr * BADGE.reserve_top_factor if e["kind"] == "person" else y - Rr - 7
    x0, x1, y1 = x - Rr - 7, x + Rr + 7, y + Rr + 7
    if e.get("label"):
        ls, rs = label_sizes(e, Rr)
        if e.get("side") == "right":
            w = max(tw(ctx, e["label"], ls, "sansb"), tw(ctx, e.get("role") or "", rs, "sansm"))
            x1 = max(x1, x + Rr + LB.side_dx + w)
        else:
            w = max(tw(ctx, e["label"], ls, "sansb") + LB.pad_x * 2, tw(ctx, e.get("role") or "", rs, "sansm"))
            x0, x1 = min(x0, x - w / 2), max(x1, x + w / 2)
            box_bottom = LB.gap + ls + LB.pad_y
            role_bottom = box_bottom - LB.inset + rs + LB.role_gap + LB.role_pad
            y1 = y + Rr + (role_bottom if e.get("role") else box_bottom)
    return x0, top, x1, y1


def draw_badge(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    from engine.reserved import avoid_badge  # noqa: PLC0415 — reserved 가 cards·media 를 import(순환 회피)

    a = window(t, e["t0"], e["t1"], BADGE.fade_in_sec, BADGE.fade_out_sec)
    if a <= 0.01:
        return
    x, y = view.to_screen(*e["world"])
    dx, dy, ka, _ = avoid_badge(badge_box(ctx, e, x, y, t), R.zones)   # 카드가 떠 있는 동안만(D-0033)
    badge_at(ctx, R, x + dx, y + dy, e, t, a * ka)

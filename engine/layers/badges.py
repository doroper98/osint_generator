"""원형 뱃지 — 인물·국기·휘장 (v2.1.0, render3 `flag_wave, badge_at, draw_badge`).

이미지 키: 인물 `portrait:<pid>`, 국기 `flag43:<cc>`·`flag11:<cc>`, 휘장 `emblem:<id>` (engine/assets.py).
"""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.projection import View
from engine.style import BADGE, BADGE_BG, C
from engine.timebase import ease_back, smooth, window
from engine.typography import rrect, text, tw


def flag_wave(ctx: cairo.Context, R: RenderCtx, key: str, cx: float, cy: float, wdt: float, a: float,  # noqa: N803
              t: float) -> None:
    fs = R.assets.scaled(key, wdt)
    fh, fw = fs.get_height(), fs.get_width()
    n = 14
    for i in range(n):
        dy = math.sin(t * 2.6 + i * 0.5) * wdt * 0.032
        ctx.save()
        ctx.rectangle(cx - fw / 2 + fw * i / n, cy - fh / 2 + dy - 1, fw / n + 1, fh + 2)
        ctx.clip()
        ctx.set_source_surface(fs, cx - fw / 2, cy - fh / 2 + dy)
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


def badge_at(ctx: cairo.Context, R: RenderCtx, x: float, y: float, e: dict, t: float, a: float) -> None:  # noqa: N803
    Rr = e.get("R") or 30  # noqa: N806
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
        fs = R.assets.scaled(f"flag11:{flag}", Rr * 2.1)
        ctx.set_source_surface(fs, -fs.get_width() / 2, -fs.get_height() / 2)
        ctx.paint_with_alpha(a)
    elif kind == "emblem":
        ctx.set_source_rgba(0.96, 0.96, 0.97, a)
        ctx.paint()
        fs = R.assets.scaled(f"emblem:{e['img']}", Rr * 1.96)
        ctx.set_source_surface(fs, -fs.get_width() / 2, -fs.get_height() / 2)
        ctx.paint_with_alpha(a)
    ctx.restore()
    if e["kind"] == "person":
        ps = R.assets.scaled(f"portrait:{e['pid']}", Rr * 1.72)
        pw, ph = ps.get_width(), ps.get_height()
        ctx.save()
        ctx.arc(0, 0, Rr, 0, 2 * math.pi)
        ctx.rectangle(-Rr * 0.66, -Rr * 2.4, Rr * 1.32, Rr * 2.4)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        ctx.clip()
        ctx.set_source_surface(ps, -pw / 2, Rr - ph + Rr * 0.02)
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
        if e.get("side") == "right":
            text(ctx, e["label"], x + Rr * k + 10, y + 1, 13, "sansb", (1, 1, 1), la, 3, "l")
            if e.get("role"):
                text(ctx, e["role"], x + Rr * k + 10, y + 17, 10, "sansm", acc, la, 2.6, "l")
        else:
            w = tw(ctx, e["label"], 12, "sansb")
            rrect(ctx, x - w / 2 - 8, y + Rr * k + 5, w + 16, 20, 3)
            ctx.set_source_rgba(0.03, 0.04, 0.06, 0.84 * la)
            ctx.fill()
            text(ctx, e["label"], x, y + Rr * k + 19.5, 12, "sansb", (1, 1, 1), la, 0, "c")
            if e.get("role"):
                text(ctx, e["role"], x, y + Rr * k + 38, 10, "sansm", acc, la, 2.6, "c")
    R.reserved.append((x - Rr - 10, y - Rr * BADGE.reserve_top_factor, x + Rr + 10, y + Rr + BADGE.reserve_bottom_px))


def badge_box(ctx: cairo.Context, e: dict, x: float, y: float) -> tuple[float, float, float, float]:
    """지도 뱃지가 차지하는 상자(원·그림자·인물 머리·이름표·역할) — 카드 RESERVED 회피용(D-0033)."""
    Rr = e.get("R") or 30  # noqa: N806
    top = y - Rr * BADGE.reserve_top_factor if e["kind"] == "person" else y - Rr - 7
    x0, x1, y1 = x - Rr - 7, x + Rr + 7, y + Rr + 7
    if e.get("label"):
        if e.get("side") == "right":
            w = max(tw(ctx, e["label"], 13, "sansb"), tw(ctx, e.get("role") or "", 10, "sansm"))
            x1 = max(x1, x + Rr + 10 + w)
        else:
            w = max(tw(ctx, e["label"], 12, "sansb") + 16, tw(ctx, e.get("role") or "", 10, "sansm"))
            x0, x1 = min(x0, x - w / 2), max(x1, x + w / 2)
            y1 = y + Rr + (42 if e.get("role") else 25)
    return x0, top, x1, y1


def draw_badge(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    from engine.reserved import avoid_badge  # noqa: PLC0415 — reserved 가 cards·media 를 import(순환 회피)

    a = window(t, e["t0"], e["t1"], 0.01, 0.45)
    if a <= 0.01:
        return
    x, y = view.xy(e["lon"], e["lat"])
    dx, dy, ka, _ = avoid_badge(badge_box(ctx, e, x, y), R.zones)   # 카드가 떠 있는 동안만(D-0033)
    badge_at(ctx, R, x + dx, y + dy, e, t, a * ka)

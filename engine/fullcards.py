"""전면 카드 — 타이틀·엔딩 (v2.1.0, render3 `draw_endcard, draw_fullcards`, 09 §6)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.credits import credit_sections
from engine.style import END_CARD, TITLE_CARD, C, H_OUT, W_OUT
from engine.timebase import ease_io, ease_out, smooth, window
from engine.typography import text

ENDCARD_NOTE = "수치와 인용은 제작 시점의 공개 보도에 근거합니다"


def draw_endcard(ctx: cairo.Context, R: RenderCtx, t: float, c: object, a: float) -> None:  # noqa: N803
    lt = t - c.t0  # type: ignore[attr-defined]
    plan = R.tb.plan
    E = END_CARD  # noqa: N806
    bg = 0.94 * a
    if E.hold_black_after and t > c.t1 - 0.7:  # type: ignore[attr-defined]  # 사라질 때 글자만 빠지고 배경은 검정으로(지도가 다시 드러나지 않게)
        bg = 0.94 + 0.06 * min(1.0, (t - (c.t1 - 0.7)) / 0.7)  # type: ignore[attr-defined]
    ctx.set_source_rgba(0.018, 0.022, 0.032, bg)
    ctx.paint()
    if a <= 0.01:
        return
    k = ease_out((lt - 0.1) / 0.9)
    text(ctx, "SOURCES  &  CREDITS", 64, 84 - (1 - k) * 6, 8.5, "mono", C["gold"], a * k, 0, "l", spacing=2.4, role="end_card")
    text(ctx, "자료 및 출처", 64, 110 - (1 - k) * 6, 17, "serif", (0.96, 0.95, 0.93), a * k, 0, "l", spacing=1.0, role="end_card")
    ctx.set_source_rgba(*C["gold"], 0.9 * a * k)
    ctx.rectangle(64, 122, 36 * k, 1.1)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.08 * a * k)
    ctx.rectangle(64, 140, W_OUT - 128, 0.8)
    ctx.fill()
    cols = [(64, 158), (456, 158)]
    cr = R.credits
    if cr is None:
        raise RuntimeError("엔딩 카드에 크레딧 데이터가 없다(projects/<p>/credits.yaml)")
    secs = credit_sections(cr, R.assets.rights, R.assets.media, R.cache.get("credit_refs"), R.cache.get("cited_sources"),
                           R.cache.get("series_records"))
    place = [s.column for s in cr.sections]
    # 1) 자리 계산(그리지 않음) — 넘치는지 보고 롤 오프셋을 정한다(잘림 금지, P6)
    rows: list[tuple] = []
    yy = [158, 158]
    n = 0
    for si, (sec, items) in enumerate(secs):
        ci = place[si]
        x = cols[ci][0]
        y = yy[ci]
        rows.append(("sec", x, y, sec, si, 0))
        y += 15
        for m, lic in items:
            rows.append(("item", x, y, (m, lic), si, n))
            n += 1
            y += 23 if lic else 14
        yy[ci] = y + 10
    over = max(yy) - 10 - E.scroll_bottom
    off = 0.0
    if over > 0:
        span = c.t1 - c.t0 - E.scroll_hold_in_sec - E.scroll_hold_out_sec  # type: ignore[attr-defined]
        off = over * ease_io((lt - E.scroll_hold_in_sec) / max(span, 0.1))
        ctx.save()
        ctx.rectangle(0, E.scroll_top, W_OUT, E.scroll_bottom - E.scroll_top + E.license_size)
        ctx.clip()

    def edge(y: float) -> float:
        if over <= 0:
            return 1.0
        return max(0.0, min(1.0, (y - E.scroll_top) / E.scroll_fade_px, (E.scroll_bottom + E.license_size - y) / E.scroll_fade_px))

    # 2) 그리기
    for kind, x, y, v, si, k in rows:
        y -= off
        if kind == "sec":
            sa = a * smooth((lt - 0.5 - si * 0.18) / 0.6) * edge(y)
            text(ctx, v, x, y, 8.5, "sansb", C["gold"], sa * 0.9, 0, "l", spacing=1.4, role="end_card")
            continue
        m, lic = v
        ia = a * smooth((lt - 0.6 - si * 0.18 - k * 0.03) / 0.6)
        text(ctx, m, x, y, END_CARD.item_size, "sans", (0.86, 0.87, 0.9), ia * edge(y), 0, "l", role="end_card")
        if lic:
            text(ctx, lic, x, y + 11, END_CARD.license_size, "monom", C["muted"], ia * 0.9 * edge(y + 11), 0, "l", role="end_card")
    if over > 0:
        ctx.restore()
    fa = a * smooth((lt - 1.6) / 0.8)
    ctx.set_source_rgba(1, 1, 1, 0.08 * fa)
    ctx.rectangle(64, H_OUT - 44, W_OUT - 128, 0.8)
    ctx.fill()
    text(ctx, plan.date.replace(".", ". ") + " 기준", 64, H_OUT - 26, 7.8, "monom", C["muted"], fa, 0, "l", spacing=0.6, role="end_card")
    text(ctx, ENDCARD_NOTE, W_OUT - 64, H_OUT - 26, 7.8, "sans", C["muted"], fa, 0, "r", role="end_card")


def draw_fullcards(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    plan = R.tb.plan
    for c in plan.cards:
        hold = c.kind == "end" and END_CARD.hold_black_after
        if not (c.t0 - 0.1 <= t <= c.t1 + 0.1) and not (hold and t > c.t1):
            continue
        a = window(t, c.t0, c.t1, 0.7, 0.7)
        lt = t - c.t0
        if c.kind == "title":
            g = cairo.LinearGradient(0, 0, 0, H_OUT)
            for st, al in ((0, 0.86), (0.5, 0.7), (1, 0.92)):
                g.add_color_stop_rgba(st, 0.01, 0.015, 0.03, al * a)
            ctx.set_source(g)
            ctx.paint()
            k = ease_out(lt / 1.0)
            text(ctx, plan.title, W_OUT / 2, 232 - (1 - k) * 10, TITLE_CARD.title_size, "disp", (1, 1, 1),
                 a * smooth((lt - 0.1) / 0.6), 0, "c")
            ctx.set_source_rgba(*C["gold"], 0.95 * a)
            lw = TITLE_CARD.rule_w * ease_io((lt - 0.5) / 0.9)
            ctx.rectangle(W_OUT / 2 - lw / 2, 254, lw, 1.6)
            ctx.fill()
            text(ctx, plan.subtitle, W_OUT / 2, 290, TITLE_CARD.subtitle_size, "serifb", (0.92, 0.9, 0.88),
                 a * smooth((lt - 0.8) / 0.6), 0, "c")
            text(ctx, plan.date.replace(".", ". "), W_OUT / 2, 322, 12, "mono", C["gold"], a * smooth((lt - 1.1) / 0.6), 0, "c")
        else:
            draw_endcard(ctx, R, t, c, a)

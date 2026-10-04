"""패널 precedent — 연도 카드 나열 (v2.1.0, render3 `P_precedent`)."""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.badges import badge_at
from engine.panels.base import panel_title
from engine.style import C
from engine.timebase import smooth
from engine.typography import rrect, text
from rules import load_rules

PR = load_rules().panels.precedent   # v4.8.0 D-0101 §3 — 글자 크기(옛 리터럴)


CARD_W = 172        # 카드 폭(v3 합격 값)
TEXT_X = 16         # 카드 왼쪽 → 글자 시작
TEXT_PAD_R = 10     # v5.6.0 RENDER-AP-013 — 글자 오른쪽 여백(이보다 길면 panel_overflow hard)


def overflow(ctx: cairo.Context, e: dict) -> list[str]:
    """v5.6.0(RENDER-AP-013 — 1701 카드 둘째 줄 '단절'이 카드 밖으로 나감) — 카드 폭을 넘는 글자. 조용히 자르지 않는다(15 P6)."""
    from engine.typography import tw  # noqa: PLC0415

    room = CARD_W - TEXT_X - TEXT_PAD_R
    out: list[str] = []
    for cd in e["cards"]:
        items = [(cd["year"], PR.year_size, "disp"), (cd["title"], PR.title_size, "sansb")]
        items += [(s_, PR.line_size, "sansm") for s_ in cd["lines"]]
        if cd.get("person"):
            items.append((cd["person"]["caption"], PR.caption_size, "sansb"))
        out += [f"[panel-overflow] precedent {cd['year']} 카드 {s_!r} — 폭 {tw(ctx, s_, size, font):.0f}px > {room}px, 문구를 줄인다"
                for s_, size, font in items if tw(ctx, s_, size, font) > room]
    return out


AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    panel_title(ctx, a, e["title"], e.get("subtitle"))
    for i, cd in enumerate(e["cards"]):
        t0 = cd["t0"]
        f = smooth((t - t0) / 0.5)
        if f <= 0:
            continue
        x = 58 + i * 190
        y = 150 - (1 - f) * 16
        ca = a * f
        col = C["gold"] if cd.get("hl") else C["teal"]
        rrect(ctx, x, y, CARD_W, 212, 6)
        ctx.set_source_rgba(0.07, 0.08, 0.12, 0.92 * ca)
        ctx.fill()
        ctx.set_source_rgba(*col, ca)
        ctx.rectangle(x, y, CARD_W, 3)
        ctx.fill()
        text(ctx, cd["year"], x + 16, y + 42, PR.year_size, "disp", col, ca, 0, "l")
        text(ctx, cd["title"], x + 16, y + 68, PR.title_size, "sansb", (1, 1, 1), ca, 0, "l")
        for j, s_ in enumerate(cd["lines"]):
            text(ctx, s_, x + 16, y + 96 + j * 20, PR.line_size, "sansm", C["muted"], ca, 0, "l")
        pp = cd.get("person")
        if pp:
            badge_at(ctx, R, x + 136, y + 172, dict(kind="person", pid=pp["pid"], flag=pp["flag"], R=24, t0=t0 + 0.3,
                                                    label="", accent="teal"), t, a)
            text(ctx, pp["caption"], x + 16, y + 196, PR.caption_size, "sansb", C["teal"], ca * smooth((t - t0 - 0.6) / 0.4), 0, "l")

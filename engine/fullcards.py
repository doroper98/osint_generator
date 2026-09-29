"""전면 카드 — 타이틀·엔딩 (v2.1.0, render3 `draw_endcard, draw_fullcards`, 09 §6).

v4.5.0(D85, back_and_forth D-0096): 엔딩 카드 맨 마지막 줄에 검증 안내 한 줄(`rules layout_480p.end_card.notice_unverified`).
v4.5.0(back_and_forth D-0098 §2): 크레딧 배치는 `endcard_layout` 한 곳에서 계산한다. 두 열의 마지막 기준선이
하단 구분선(H−44) − `end_card.bottom_margin` 을 넘으면 `EndCardOverflowError`(조용한 넘침 금지, 15 P6) — checks offscreen 도 같은 함수로 본다.
v4.7.0(back_and_forth D-0106 1-C, dmz_mine 브랜치 롤): 넘치면 목록이 위로 흐른다(롤). 롤 속도가 `end_card.scroll_max_px_per_sec` 를
넘을 때만 `EndCardOverflowError`. 상한 안 롤은 checks warning `[endcard-roll]`·provenance `end_card` 기록.
"""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.credits import credit_sections
from engine.style import END_CARD, TITLE_CARD, C, H_OUT, W_OUT
from engine.timebase import ease_io, ease_out, smooth, window
from engine.typography import text

ENDCARD_NOTE = "수치와 인용은 제작 시점의 공개 보도에 근거합니다"
NOTICE = END_CARD.notice_unverified
COLS_X = (64, 456)      # 크레딧 두 열의 왼쪽 x
TOP_Y = 158             # 크레딧 첫 절 제목 기준선
RULE_Y = H_OUT - 44     # 하단 구분선(날짜·안내 줄 위)


class EndCardOverflowError(RuntimeError):
    """크레딧이 하단 구분선 − bottom_margin 을 넘는다 — 글자가 화면 아래로 사라지는 권리 표기 결함(C9)."""


# (절 순번, 열, x, 절 제목 y, [(항목 문구, 라이선스, 항목 y)])
Placed = tuple[int, int, float, float, list[tuple[str, str, float]]]


def endcard_layout(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int]) -> tuple[list[Placed], list[float]]:
    """절 배치와 열마다 마지막 기준선(글자를 그린 마지막 y — 라이선스 줄이 있으면 그 줄). 빈 열은 TOP_Y 이전(0)."""
    yy = [float(TOP_Y), float(TOP_Y)]
    last = [0.0, 0.0]
    out: list[Placed] = []
    for si, (_sec, items) in enumerate(secs):
        ci = place[si]
        y = yy[ci]
        head, y = y, y + 15
        last[ci] = head
        rows = []
        for m, lic in items:
            rows.append((m, lic, y))
            last[ci] = y + 11 if lic else y
            y += 23 if lic else 14
        out.append((si, ci, COLS_X[ci], head, rows))
        yy[ci] = y + 10
    return out, last


def endcard_roll(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int]) -> tuple[float, float]:
    """(롤 거리 px, 롤 속도 px/s). 두 열 마지막 기준선이 한도(H−44 − bottom_margin) 안이면 (0, 0) — 롤 없음.
    넘치면 마지막 줄이 아래 페이드 구역 위(scroll_bottom − scroll_fade_px)에 멈출 만큼 흐른다(D-0106 1-C)."""
    E = END_CARD  # noqa: N806
    _, last = endcard_layout(secs, place)
    if max(last) <= RULE_Y - E.bottom_margin:
        return 0.0, 0.0
    dist = max(last) - (E.scroll_bottom - E.scroll_fade_px)
    return dist, dist / (E.dur_sec - E.scroll_hold_in_sec - E.scroll_hold_out_sec)


def endcard_overflow(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int]) -> list[str]:
    """롤 속도가 상한을 넘으면 그 사실 한 줄(읽을 수 없는 롤 = 넘침). 롤 없음·상한 안 롤 = []."""
    dist, v = endcard_roll(secs, place)
    mx = END_CARD.scroll_max_px_per_sec
    return [f"[endcard-overflow] 크레딧 롤 속도 {v:.1f} px/s > 상한 {mx:g}(롤 거리 {dist:.0f}px) — credits.yaml 절을 줄인다"] if v > mx else []


def endcard_roll_note(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int]) -> list[str]:
    """상한 안 롤 — checks warning(검수자가 보게). 롤 없음·상한 초과(오류 쪽) = []."""
    dist, v = endcard_roll(secs, place)
    return [f"[endcard-roll] 크레딧이 넘쳐 롤 {dist:.0f}px · {v:.1f} px/s(상한 {END_CARD.scroll_max_px_per_sec:g})"] \
        if 0 < v <= END_CARD.scroll_max_px_per_sec else []


def project_credit_sections(R: RenderCtx) -> list[tuple[str, list[tuple[str, str]]]]:  # noqa: N803
    """이번 렌더의 엔딩 카드 절 — draw_endcard 와 checks 가 같은 입력으로 본다."""
    if R.credits is None:
        raise RuntimeError("엔딩 카드에 크레딧 데이터가 없다(projects/<p>/credits.yaml)")
    return credit_sections(R.credits, R.assets.rights, R.assets.media, R.cache.get("credit_refs"), R.cache.get("cited_sources"),
                           R.cache.get("series_records"))


def unverified_notice(R: RenderCtx) -> str | None:  # noqa: N803
    """엔딩 카드 마지막 줄(v4.5.0 사용자 결정 D85, C9) — 이 영상에 들어간 문장 중 검증 라벨이 붙은 문장 수 n.
    n = 0 이면 None(줄 없음). 라벨 표는 `R.cache["sentence_labels"]`(claims status → 규칙 표, engine.project)."""
    labels = R.cache.get("sentence_labels") or {}
    n = sum(1 for sid in R.tb.order if labels.get(sid))
    return NOTICE.template.replace("{n}", str(n)) if n else None


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
    secs = project_credit_sections(R)
    place = [s.column for s in R.credits.sections]  # type: ignore[union-attr]
    over = endcard_overflow(secs, place)
    if over:
        raise EndCardOverflowError("; ".join(over))
    dist, _v = endcard_roll(secs, place)   # D-0106 1-C — 넘치면 롤(잘림 금지, P6)
    off = 0.0
    if dist > 0:
        span = c.t1 - c.t0 - E.scroll_hold_in_sec - E.scroll_hold_out_sec  # type: ignore[attr-defined]
        off = dist * ease_io((lt - E.scroll_hold_in_sec) / span)
        ctx.save()
        ctx.rectangle(0, E.scroll_top, W_OUT, E.scroll_bottom - E.scroll_top + E.license_size)
        ctx.clip()

    def edge(y: float) -> float:
        if dist <= 0:
            return 1.0
        return max(0.0, min(1.0, (y - E.scroll_top) / E.scroll_fade_px, (E.scroll_bottom + E.license_size - y) / E.scroll_fade_px))

    n = 0
    for si, _ci, x, head, rows in endcard_layout(secs, place)[0]:
        sa = a * smooth((lt - 0.5 - si * 0.18) / 0.6)
        text(ctx, secs[si][0], x, head - off, 8.5, "sansb", C["gold"], sa * 0.9 * edge(head - off), 0, "l", spacing=1.4, role="end_card")
        for m, lic, y in rows:
            ia = a * smooth((lt - 0.6 - si * 0.18 - n * 0.03) / 0.6)
            n += 1
            y -= off
            text(ctx, m, x, y, END_CARD.item_size, "sans", (0.86, 0.87, 0.9), ia * edge(y), 0, "l", role="end_card")
            if lic:
                text(ctx, lic, x, y + 11, END_CARD.license_size, "monom", C["muted"], ia * 0.9 * edge(y + 11), 0, "l", role="end_card")
    if dist > 0:
        ctx.restore()
    fa = a * smooth((lt - 1.6) / 0.8)
    ctx.set_source_rgba(1, 1, 1, 0.08 * fa)
    ctx.rectangle(64, RULE_Y, W_OUT - 128, 0.8)
    ctx.fill()
    text(ctx, plan.date.replace(".", ". ") + " 기준", 64, H_OUT - 26, 7.8, "monom", C["muted"], fa, 0, "l", spacing=0.6, role="end_card")
    text(ctx, ENDCARD_NOTE, W_OUT - 64, H_OUT - 26, 7.8, "sans", C["muted"], fa, 0, "r", role="end_card")
    notice = unverified_notice(R)
    if notice:   # 맨 마지막 줄, 가장 작은 글씨 — 본문(자막·패널·카드)에는 검증 라벨을 그리지 않는다
        text(ctx, notice, 64, H_OUT - 26 + NOTICE.dy, NOTICE.size, "sans", C["muted"], fa, 0, "l", role="end_card")


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

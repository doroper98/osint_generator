"""전면 카드 — 타이틀·엔딩 (v2.1.0, render3 `draw_endcard, draw_fullcards`, 09 §6).

v4.5.0(D85, back_and_forth D-0096): 엔딩 카드 맨 마지막 줄에 검증 안내 한 줄(`rules layout_480p.end_card.notice_unverified`).
v4.5.0(back_and_forth D-0098 §2): 크레딧 배치는 `endcard_layout` 한 곳에서 계산한다. 두 열의 마지막 기준선이
하단 구분선(H−44) − `end_card.bottom_margin` 을 넘으면 `EndCardOverflowError`(조용한 넘침 금지, 15 P6) — checks offscreen 도 같은 함수로 본다.
v4.7.0(back_and_forth D-0106 1-C, dmz_mine 브랜치 롤): 넘치면 목록이 위로 흐른다(롤). 롤 속도가 `end_card.scroll_max_px_per_sec` 를
넘을 때만 `EndCardOverflowError`. 상한 안 롤은 checks warning `[endcard-roll]`·provenance `end_card` 기록.
v5.1.0(back_and_forth D-0124, 사용자 결정 D109): 오른쪽 아래 구석 버전 도장 `v{VERSION}`(`end_card.version_stamp`) — 렌더 시점 VERSION 파일,
롤에 고정(클립·스크롤 밖), 안내 줄과 겹치면 dy 만큼 위로. 화면 밖이면 `[endcard-overflow]`.
"""

from __future__ import annotations

from pathlib import Path

import cairo

from engine.context import RenderCtx
from engine.credits import credit_sections
from engine.style import C, ELEM, END_CARD, H_OUT, MOTION, TITLE_CARD, W_OUT
from engine.timebase import ease_io, ease_out, smooth, window
from engine.typography import _M, adv, text, wrap

ENDCARD_NOTE = "수치와 인용은 제작 시점의 공개 보도에 근거합니다"
NOTICE = END_CARD.notice_unverified
INVEST = END_CARD.notice_invest      # v7.4.0 D-0278 §4.3
TPL = END_CARD.template_line         # v7.4.0 UF-147
STAMP = END_CARD.version_stamp
VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
COLS_X = (64, 456)      # 크레딧 두 열의 왼쪽 x
TOP_Y = 158             # 크레딧 첫 절 제목 기준선
RULE_Y = H_OUT - 44     # 하단 구분선(날짜·안내 줄 위)
COL_W = (COLS_X[1] - COLS_X[0] - 16, W_OUT - 64 - COLS_X[1])   # v7.4.0 — 열마다 글자 폭 한도(옆 열과 16px 띄움)
ITEM_LINE = 12          # v7.4.0 — 줄바꿈한 크레딧 항목의 줄 간격
LICENSE_LINE = 10       # v7.4.0 — 줄바꿈한 라이선스 줄의 줄 간격(license_size 7.8 기준, 항목 줄 간격보다 좁게)
NOTICE_DY = 4           # v7.4.0 — 표기 전용 줄 기준선 = 하단 구분선 − 이 값(구분선 바로 위)
NOTICE_H = 12           # v7.4.0 — 표기 전용 줄이 있으면 크레딧 열 아래 한도를 이만큼 올린다(겹침 방지)


class EndCardOverflowError(RuntimeError):
    """크레딧이 하단 구분선 − bottom_margin 을 넘는다 — 글자가 화면 아래로 사라지는 권리 표기 결함(C9)."""


# (절 순번, 열, x, 절 제목 y, [(항목 문구, 라이선스, 항목 y)])
Placed = tuple[int, int, float, float, list[tuple[str, str, float]]]


class TitleOverflowError(ValueError):
    """타이틀 카드 제목이 title_min_size 로 줄여도 화면 폭(max_w_ratio)을 넘는다 — 원고 제목을 줄인다(조용한 잘림 금지, 15 P6, v5.21.3)."""


def title_fit_size(ctx: cairo.Context, title: str) -> float:
    """제목 글자 크기 — 폭이 W × max_w_ratio 안이면 title_size 그대로(종전 바이트), 넘을 때만 비례로 줄인다."""
    from engine.typography import tw  # noqa: PLC0415

    size = TITLE_CARD.title_size
    room = W_OUT * TITLE_CARD.max_w_ratio
    w = tw(ctx, title, size, "disp")
    if w <= room:
        return size
    fit = size * room / w
    while fit >= TITLE_CARD.title_min_size and tw(ctx, title, fit, "disp") > room:   # 글자 폭은 크기에 정확히 비례하지 않는다(힌팅) — 0.5px 씩
        fit -= 0.5
    if fit < TITLE_CARD.title_min_size:
        raise TitleOverflowError(f"타이틀 제목 {title!r} 폭 {w:.0f}px — {TITLE_CARD.title_min_size:g}px 로 줄여도 {room:.0f}px 를 넘는다. "
                                 "원고 title 을 줄인다(rules layout_480p.title_card)")
    return fit


def item_lines(m: str, ci: int) -> list[str]:
    """크레딧 항목 글자를 열 폭(COL_W) 안으로 줄바꿈(v7.4.0 D-0229 §2.10 — 긴 항목이 옆 열에 붙던 것). 폭 안이면 한 줄 그대로."""
    if adv(m, END_CARD.item_size, "sans") <= COL_W[ci]:
        return [m]
    return wrap(_M, m, COL_W[ci], END_CARD.item_size, "sans")


def license_lines(lic: str, ci: int) -> list[str]:
    """라이선스 줄도 열 폭 안으로 줄바꿈(v7.4.0 — 인물 사진 auto: people 의 긴 권리 문구가 화면 오른쪽 밖으로 나가던 것). 폭 안이면 한 줄."""
    if adv(lic, END_CARD.license_size, "monom") <= COL_W[ci]:
        return [lic]
    return wrap(_M, lic, COL_W[ci], END_CARD.license_size, "monom")


def endcard_layout(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int]) -> tuple[list[Placed], list[float]]:
    """절 배치와 열마다 마지막 기준선(글자를 그린 마지막 y — 라이선스 줄이 있으면 그 줄). 빈 열은 TOP_Y 이전(0).
    v7.4.0: 열 폭을 넘는 항목은 줄을 바꾼다(줄마다 ITEM_LINE px 아래) — rows 의 m 은 줄바꿈 문자로 이은 글자."""
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
            ls = item_lines(m, ci)
            lls = license_lines(lic, ci) if lic else []
            rows.append(("\n".join(ls), "\n".join(lls), y))
            y += ITEM_LINE * (len(ls) - 1)
            extra = LICENSE_LINE * max(0, len(lls) - 1)
            last[ci] = y + 11 + extra if lic else y
            y += (23 + extra) if lic else 14
        out.append((si, ci, COLS_X[ci], head, rows))
        yy[ci] = y + 10
    return out, last


def endcard_roll(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int], reserve: float = 0.0) -> tuple[float, float]:
    """(롤 거리 px, 롤 속도 px/s). 두 열 마지막 기준선이 한도(H−44 − bottom_margin) 안이면 (0, 0) — 롤 없음.
    넘치면 마지막 줄이 아래 페이드 구역 위(scroll_bottom − scroll_fade_px)에 멈출 만큼 흐른다(D-0106 1-C)."""
    E = END_CARD  # noqa: N806
    _, last = endcard_layout(secs, place)
    if max(last) <= RULE_Y - E.bottom_margin - reserve:   # reserve = 표기 전용 줄 높이(v7.4.0, notice_reserve)
        return 0.0, 0.0
    dist = max(last) - (E.scroll_bottom - E.scroll_fade_px - reserve)
    return dist, dist / (E.dur_sec - E.scroll_hold_in_sec - E.scroll_hold_out_sec)


def endcard_overflow(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int], reserve: float = 0.0) -> list[str]:
    """롤 속도가 상한을 넘으면 그 사실 한 줄(읽을 수 없는 롤 = 넘침). 롤 없음·상한 안 롤 = []."""
    dist, v = endcard_roll(secs, place, reserve)
    mx = END_CARD.scroll_max_px_per_sec
    return [f"[endcard-overflow] 크레딧 롤 속도 {v:.1f} px/s > 상한 {mx:g}(롤 거리 {dist:.0f}px) — credits.yaml 절을 줄인다"] if v > mx else []


def endcard_roll_note(secs: list[tuple[str, list[tuple[str, str]]]], place: list[int], reserve: float = 0.0) -> list[str]:
    """상한 안 롤 — checks warning(검수자가 보게). 롤 없음·상한 초과(오류 쪽) = []."""
    dist, v = endcard_roll(secs, place, reserve)
    return [f"[endcard-roll] 크레딧이 넘쳐 롤 {dist:.0f}px · {v:.1f} px/s(상한 {END_CARD.scroll_max_px_per_sec:g})"] \
        if 0 < v <= END_CARD.scroll_max_px_per_sec else []


def version_stamp() -> str:
    """버전 도장 문자열 — 렌더 시점의 VERSION 파일 한 줄(C5.1 SSOT). 코드 상수·config 복사 금지(P3)."""
    return "v" + VERSION_FILE.read_text(encoding="utf-8").strip()


def version_stamp_box(notice: str | None) -> tuple[float, float, float, float]:
    """도장 글자 상자(x0, y0, x1, y1) — 기준선 = H − y_from_bottom, 오른쪽 끝 = W − x_from_right.
    안내 줄(notice, 왼쪽 x=64·기준선 H−26+dy)과 겹치면 notice 를 우선하고 도장을 STAMP.dy 만큼 위로 올린다(D-0124)."""

    s = version_stamp()
    w = adv(s, STAMP.size, STAMP.font)
    x1 = W_OUT - STAMP.x_from_right
    base = H_OUT - STAMP.y_from_bottom
    box = (x1 - w, base - STAMP.size, x1, base + STAMP.size * 0.25)
    if notice:
        ny = H_OUT - 26 + NOTICE.dy
        ns = min(NOTICE.size, INVEST.size)   # v7.4.0 — draw_endcard 맨 마지막 줄과 같은 크기
        nb = (64.0, ny - ns, 64 + adv(notice, ns, "sans"), ny + ns * 0.25)
        if box[0] < nb[2] and nb[0] < box[2] and box[1] < nb[3] and nb[1] < box[3]:
            box = (box[0], box[1] - STAMP.dy, box[2], box[3] - STAMP.dy)
    return box


def version_stamp_overflow(notice: str | None) -> list[str]:
    """도장이 화면 밖이면 한 줄 — checks offscreen [endcard-overflow] 에 포함(D-0124)."""
    x0, y0, x1, y1 = version_stamp_box(notice)
    return [] if 0 <= x0 and x1 <= W_OUT and 0 <= y0 and y1 <= H_OUT else \
        [f"[endcard-overflow] 버전 도장 {version_stamp()} 상자 ({x0:.0f},{y0:.0f})–({x1:.0f},{y1:.0f}) 가 화면 밖"]


def project_credit_sections(R: RenderCtx) -> list[tuple[str, list[tuple[str, str]]]]:  # noqa: N803
    """이번 렌더의 엔딩 카드 절 — draw_endcard 와 checks 가 같은 입력으로 본다."""
    if R.credits is None:
        raise RuntimeError("엔딩 카드에 크레딧 데이터가 없다(projects/<p>/credits.yaml)")
    secs = credit_sections(R.credits, R.assets.rights, R.assets.media, R.cache.get("credit_refs"), R.cache.get("cited_sources"),
                           R.cache.get("series_records"), missing_license=R.cache.get("missing_license"),
                           press=R.cache.get("press_by_scene"))   # v4.9.0 콘티 판만
    return [x for x, s in zip(secs, R.credits.sections) if s.slot == "column"]   # v7.4.0 — notice 칸은 두 열 밖(notice_lines)


def credit_place(R: RenderCtx) -> list[int]:  # noqa: N803
    """두 열 흐름 절의 열 번호(project_credit_sections 와 같은 순서, notice 칸 제외 — v7.4.0)."""
    return [s.column for s in R.credits.sections if s.slot == "column"]  # type: ignore[union-attr]


def notice_reserve(R: RenderCtx) -> float:  # noqa: N803
    return NOTICE_H if notice_line(R) else 0.0


def notice_line(R: RenderCtx) -> str | None:  # noqa: N803
    """v7.4.0 D-0229 §2.10 — slot: notice 절을 한 줄로("항목 · 라이선스 줄" 을 · 로 잇는다). 없으면 None."""
    secs = credit_sections(R.credits, R.assets.rights, R.assets.media, R.cache.get("credit_refs"), R.cache.get("cited_sources"),
                           R.cache.get("series_records"), missing_license=R.cache.get("missing_license"),
                           press=R.cache.get("press_by_scene"))
    parts = [p for (_t, items), s in zip(secs, R.credits.sections) if s.slot == "notice" for m, lic in items for p in (m, lic) if p]
    return " · ".join(parts) or None


def unverified_notice(R: RenderCtx) -> str | None:  # noqa: N803
    """엔딩 카드 마지막 줄(v4.5.0 사용자 결정 D85, C9) — 이 영상에 들어간 문장 중 검증 라벨이 붙은 문장 수 n.
    n = 0 이면 None(줄 없음). 라벨 표는 `R.cache["sentence_labels"]`(claims status → 규칙 표, engine.project)."""
    labels = R.cache.get("sentence_labels") or {}
    n = sum(1 for sid in R.tb.order if labels.get(sid))
    return NOTICE.template.replace("{n}", str(n)) if n else None


def template_label(R: RenderCtx) -> str | None:  # noqa: N803
    """v7.4.0 UF-147(D-0302 ⑤) — 장르 프로필 template_label(engine.project 가 R.cache 에 넣는다). 없으면 None."""
    return getattr(R, "cache", {}).get("template_label")


def title_subtitle(R: RenderCtx, plan: object = None) -> str:  # noqa: N803
    """타이틀 카드 부제 줄 — 템플릿 라벨이 있으면 "<라벨> · <부제>"(UF-147). draw_fullcards 와 checks 가 같은 함수로 본다.
    plan 을 주면 그 원고의 부제(검사 — 렌더 문맥 없이도 같은 문자열)."""
    sub = (plan if plan is not None else R.tb.plan).subtitle  # type: ignore[attr-defined]
    lab = template_label(R)
    return f"{lab}{TPL.sep}{sub}" if lab and sub else (lab or sub)


def last_notice(R: RenderCtx) -> str | None:  # noqa: N803
    """엔딩 카드 맨 마지막 줄 — 투자 고지(장르 invest_notice, D-0278 §4.3) · 검증 안내(D85) 를 · 로 잇는다. 둘 다 없으면 None."""
    parts = [INVEST.text if R.cache.get("invest_notice") else None, unverified_notice(R)]
    return TPL.sep.join(p for p in parts if p) or None


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
    k = ease_out((lt - 0.1) / MOTION["endcard_head_in_sec"])   # v7.4.0 UF-159 ×1.5
    text(ctx, "SOURCES  &  CREDITS", 64, 84 - (1 - k) * 6, 8.5, "mono", C["gold"], a * k, 0, "l", spacing=2.4, role="end_card")
    text(ctx, "자료 및 출처", 64, 110 - (1 - k) * 6, 17, "serif", (0.96, 0.95, 0.93), a * k, 0, "l", spacing=1.0, role="end_card")
    lab = template_label(R)
    if lab:   # v7.4.0 UF-147 — 템플릿 표시 줄(머리 줄 오른쪽, 모서리 아님)
        text(ctx, lab, W_OUT - 64, TPL.y - (1 - k) * 6, TPL.size, TPL.font, C["gold"], a * k * 0.9, 0, "r", role="end_card")
    ctx.set_source_rgba(*C["gold"], 0.9 * a * k)
    ctx.rectangle(64, 122, 36 * k, 1.1)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.08 * a * k)
    ctx.rectangle(64, 140, W_OUT - 128, 0.8)
    ctx.fill()
    secs = project_credit_sections(R)
    place = credit_place(R)
    rsv = notice_reserve(R)
    over = endcard_overflow(secs, place, rsv)
    if over:
        raise EndCardOverflowError("; ".join(over))
    dist, _v = endcard_roll(secs, place, rsv)   # D-0106 1-C — 넘치면 롤(잘림 금지, P6)
    off = 0.0
    if dist > 0:
        span = c.t1 - c.t0 - E.scroll_hold_in_sec - E.scroll_hold_out_sec  # type: ignore[attr-defined]
        off = dist * ease_io((lt - E.scroll_hold_in_sec) / span)
        ctx.save()
        ctx.rectangle(0, E.scroll_top, W_OUT, E.scroll_bottom - E.scroll_top + E.license_size - rsv)
        ctx.clip()

    def edge(y: float) -> float:
        if dist <= 0:
            return 1.0
        return max(0.0, min(1.0, (y - E.scroll_top) / E.scroll_fade_px, (E.scroll_bottom + E.license_size - rsv - y) / E.scroll_fade_px))

    n = 0
    for si, _ci, x, head, rows in endcard_layout(secs, place)[0]:
        sa = a * smooth((lt - 0.5 - si * 0.18) / MOTION["endcard_item_in_sec"])
        text(ctx, secs[si][0], x, head - off, 8.5, "sansb", C["gold"], sa * 0.9 * edge(head - off), 0, "l", spacing=1.4, role="end_card")
        for m, lic, y in rows:
            ia = a * smooth((lt - 0.6 - si * 0.18 - n * 0.03) / MOTION["endcard_item_in_sec"])
            n += 1
            y -= off
            ls = m.split("\n")
            for j, ln in enumerate(ls):   # v7.4.0 — 열 폭을 넘는 항목은 여러 줄(endcard_layout 과 같은 줄바꿈)
                yj = y + ITEM_LINE * j
                text(ctx, ln, x, yj, END_CARD.item_size, "sans", (0.86, 0.87, 0.9), ia * edge(yj), 0, "l", role="end_card")
            y += ITEM_LINE * (len(ls) - 1)
            for j, ll in enumerate(lic.split("\n") if lic else []):   # v7.4.0 — 열 폭을 넘는 라이선스 줄은 여러 줄(endcard_layout 과 같은 줄바꿈)
                yl = y + 11 + LICENSE_LINE * j
                text(ctx, ll, x, yl, END_CARD.license_size, "monom", C["muted"], ia * 0.9 * edge(yl), 0, "l", role="end_card")
    if dist > 0:
        ctx.restore()
    fa = a * smooth((lt - 1.6) / MOTION["endcard_foot_in_sec"])
    ctx.set_source_rgba(1, 1, 1, 0.08 * fa)
    ctx.rectangle(64, RULE_Y, W_OUT - 128, 0.8)
    ctx.fill()
    text(ctx, plan.date.replace(".", ". ") + " 기준", 64, H_OUT - 26, 7.8, "monom", C["muted"], fa, 0, "l", spacing=0.6, role="end_card")
    text(ctx, ENDCARD_NOTE, W_OUT - 64, H_OUT - 26, 7.8, "sans", C["muted"], fa, 0, "r", role="end_card")
    nl = notice_line(R)
    if nl:   # v7.4.0 D-0229 §2.10 — 표기 전용 줄(구분선 바로 위, 전체 폭, 가장 작은 글씨)
        text(ctx, nl, 64, RULE_Y - NOTICE_DY, END_CARD.license_size, "sans", C["muted"], fa, 0, "l", role="end_card")
    notice = last_notice(R)
    if notice:   # 맨 마지막 줄, 가장 작은 글씨 — 본문(자막·패널·카드)에는 검증 라벨을 그리지 않는다. 투자 고지가 앞(v7.4.0)
        text(ctx, notice, 64, H_OUT - 26 + NOTICE.dy, min(NOTICE.size, INVEST.size), "sans", C["muted"], fa, 0, "l", role="end_card")
    # v5.1.0 D-0124 — 버전 도장: 카드 등장과 함께(a), 롤 클립·스크롤 밖이라 고정, halo 없음. 검정 홀드(a = 0)에는 없음
    _x0, _y0, x1, y1 = version_stamp_box(notice)
    text(ctx, version_stamp(), x1, y1 - STAMP.size * 0.25, STAMP.size, STAMP.font, C["muted"], a * STAMP.alpha, 0, "r", role="end_card")


def draw_fullcards(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    plan = R.tb.plan
    for c in plan.cards:
        hold = c.kind == "end" and END_CARD.hold_black_after
        if not (c.t0 - 0.1 <= t <= c.t1 + 0.1) and not (hold and t > c.t1):
            continue
        a = window(t, c.t0, c.t1, *ELEM["fullcard"])   # v7.4.0 UF-159 ×1.5
        lt = t - c.t0
        if c.kind == "title":
            g = cairo.LinearGradient(0, 0, 0, H_OUT)
            for st, al in ((0, 0.86), (0.5, 0.7), (1, 0.92)):
                g.add_color_stop_rgba(st, 0.01, 0.015, 0.03, al * a)
            ctx.set_source(g)
            ctx.paint()
            k = ease_out(lt / MOTION["title_settle_sec"])
            text(ctx, plan.title, W_OUT / 2, 232 - (1 - k) * 10, title_fit_size(ctx, plan.title), "disp", (1, 1, 1),
                 a * smooth((lt - 0.1) / MOTION["title_text_in_sec"]), 0, "c")
            ctx.set_source_rgba(*C["gold"], 0.95 * a)
            lw = TITLE_CARD.rule_w * ease_io((lt - 0.5) / MOTION["title_rule_in_sec"])
            ctx.rectangle(W_OUT / 2 - lw / 2, 254, lw, 1.6)
            ctx.fill()
            text(ctx, title_subtitle(R), W_OUT / 2, 290, TITLE_CARD.subtitle_size, "serifb", (0.92, 0.9, 0.88),
                 a * smooth((lt - 0.8) / MOTION["title_text_in_sec"]), 0, "c")
            text(ctx, plan.date.replace(".", ". "), W_OUT / 2, 322, 12, "mono", C["gold"], a * smooth((lt - 1.1) / MOTION["title_text_in_sec"]), 0, "c")
        else:
            draw_endcard(ctx, R, t, c, a)

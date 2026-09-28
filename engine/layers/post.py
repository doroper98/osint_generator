"""X 게시물 카드 `post` (v3.2.0, docs/handoff/18 §5, back_and_forth D-0051 작업 9).

캡처 이미지를 쓰지 않고 자체 조판한다. X 로고(상표) 없음. 문구는 프로젝트 `intake/sources.json` 의 소스 레코드에서만
(`R.cache["sources"]`, engine.project 가 싣고 점검한다) — 연출은 소스 id·형광펜·원문 한 줄·자리만 정한다(D25 원칙).
- 공식 계정(official_*)이면 '공식 계정' 칩. 일반인 계정(private)은 이름·핸들·아이콘을 가리고 "개인 계정"(18 §5).
- 검증 라벨은 규칙 표(`script.labels.status_label` — 원고·패널과 같은 SSOT). 있으면 하단에 호박색 글자, 도장 없음.
- 삭제된 게시물은 하단에 "삭제된 게시물 · 캡처 YYYY. MM. DD"(18 §3-4).
기하·글자 크기·타이밍 = `rules layout_480p.post_card`(18 §5 수치).
"""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, CARD, W_OUT
from engine.timebase import ease_io, ease_out, window
from engine.typography import rrect, text, tw, wrap
from rules import load_rules

PC = load_rules().layout_480p.post_card


class PostSourceError(ValueError):
    """post 이벤트가 가리키는 소스가 없거나 쓸 수 없는 상태(미확인·미검증·X 게시물 아님)."""


def post_text(e: dict, sources: dict) -> dict:
    """카드 문구 — 소스 레코드에서. 없으면 PostSourceError(P6·P10)."""
    from script.labels import status_label  # noqa: PLC0415

    s = sources.get(e["src"])
    if s is None or s.type != "x_post":
        raise PostSourceError(f"post {e['src']}: intake/sources.json 에 X 게시물 소스가 없다")
    if not s.confirmed or s.verification is None:
        raise PostSourceError(f"post {e['src']}: 사용자 확인·검증을 거치지 않은 소스는 카드로 쓰지 않는다(18 §7)")
    private = s.account_class == "private"
    body = " ".join((s.text_ko or s.text_original).split())   # 캡처 판독 원문의 줄바꿈은 글리프가 아니다 — 공백으로(e2e 실측 ▯)
    if e.get("hl") and e["hl"] not in body:
        raise PostSourceError(f"post {e['src']}: 형광펜 {e['hl']!r} 가 번역문에 없다")
    orig = None
    if e.get("quote"):   # 원문 한 줄 — 번역이 있고 15단어 미만일 때만. 못 쓰면 조용히 빼지 않고 오류(P6)
        if not s.text_ko or len(s.text_original.split()) >= PC.orig_max_words:
            raise PostSourceError(f"post {e['src']}: quote 는 번역이 있고 원문이 {PC.orig_max_words}단어 미만일 때만(18 §5)")
        orig = " ".join(s.text_original.split())
    if s.posted_at is None:
        when = "게시 시각 미상"
    elif s.posted_at.tzinfo is None:      # 캡처 화면 시각 — 시간대를 모르면 UTC 라고 적지 않는다(사실 정확성)
        when = s.posted_at.strftime("%Y. %m. %d %H:%M") + " (게시 화면 시각)"
    else:
        from datetime import timezone  # noqa: PLC0415

        when = s.posted_at.astimezone(timezone.utc).strftime("%Y. %m. %d %H:%M (UTC)")
    return dict(name="개인 계정" if private else s.account_name, handle="" if private else s.handle,
                initial="" if private else s.account_name.strip()[:1].upper(), private=private,
                official=s.account_class.startswith("official"), body=body, hl=e.get("hl"), orig=orig, when=when,
                foot="X 게시물 · 번역" if s.text_ko else "X 게시물",
                label=status_label(s.verification.status),
                deleted=f"삭제된 게시물 · 캡처 {s.retrieved_at.strftime('%Y. %m. %d')}" if s.deleted else None)


def post_alpha(t: float, e: dict) -> float:
    return window(t, e["t0"], e["t1"], PC.fade_sec, PC.fade_sec)


def _head_h() -> float:
    return PC.pad + 2 * PC.icon_r + PC.pad / 2


def post_geom(ctx: cairo.Context, e: dict, sources: dict) -> tuple[float, float, float, float, list[str]]:
    """카드 상자 (x, y, 폭, 높이, 본문 줄) — 슬라이드 전 제자리. RESERVED(카드 영역)와 그리기가 같이 쓴다."""
    d = post_text(e, sources)
    lines = wrap(ctx, d["body"], PC.w - 2 * PC.pad, PC.body_size, "sansm")
    if len(lines) > PC.body_max_lines:
        raise PostSourceError(f"post {e['src']}: 번역문이 {len(lines)}줄 > {PC.body_max_lines}줄 — 짧은 게시물만 카드로(18 §5)")
    if d["orig"] and tw(ctx, d["orig"], PC.orig_size, "monom") > PC.w - 2 * PC.pad:
        raise PostSourceError(f"post {e['src']}: 원문 한 줄이 카드 폭을 넘는다 — quote 를 끈다(자르지 않는다)")
    h = _head_h() + len(lines) * PC.body_line + (PC.body_line if d["orig"] else 0) + PC.pad + PC.foot_size * 2 \
        + (PC.foot_size * 2 if (d["label"] or d["deleted"]) else 0)
    x = W_OUT - PC.w - CARD.x_right_margin if e.get("at", "card") == "card" else (W_OUT - PC.w) / 2
    y = PC.y if e.get("at", "card") == "card" else PC.panel_y
    return x, y, PC.w, h, lines


def draw_post(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = post_alpha(t, e)
    if a <= 0.01:
        return
    sources = R.cache["sources"]
    d = post_text(e, sources)
    x0, y, w, h, lines = post_geom(ctx, e, sources)
    lt = t - e["t0"]
    x = x0 + (1 - ease_out(lt / PC.fade_sec)) * PC.slide_px
    for d_, al in ((6, 0.12), (3, 0.2)):          # 그림자 2겹(기사 카드와 같은 값)
        rrect(ctx, x - d_ + 2, y - d_ + 4, w + 2 * d_, h + 2 * d_, PC.radius + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()
    rrect(ctx, x, y, w, h, PC.radius)
    bg = PC.bg
    ctx.set_source_rgba(bg[0], bg[1], bg[2], bg[3] * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, PC.border_alpha * a)
    ctx.set_line_width(1)
    ctx.stroke()
    # 1행 — 아이콘 원(이니셜) · 표시 이름 · 핸들 · 공식 계정 칩
    cx, cy = x + PC.pad + PC.icon_r, y + PC.pad + PC.icon_r
    ctx.arc(cx, cy, PC.icon_r, 0, 6.2832)
    ctx.set_source_rgba(*(C["muted"] if d["private"] else C["gold"]), a)
    ctx.fill()
    if d["initial"]:
        text(ctx, d["initial"], cx, cy + PC.icon_r * 0.45, PC.icon_r * 1.1, "disp", (0.07, 0.08, 0.11), a, 0, "c")
    nx = cx + PC.icon_r + PC.pad / 2
    text(ctx, d["name"], nx, cy - 1, PC.name_size, "sansb", (1, 1, 1), a, 0, "l")
    if d["handle"]:
        text(ctx, d["handle"], nx, cy + PC.handle_size + 3, PC.handle_size, "monom", C["muted"], a, 0, "l")
    if d["official"]:
        chip = "공식 계정"
        cw = tw(ctx, chip, PC.chip_size, "sans") + PC.pad / 2
        rrect(ctx, x + w - PC.pad - cw, cy - PC.chip_size, cw, PC.chip_size * 2, PC.chip_size)
        ctx.set_source_rgba(*C["teal"], a)
        ctx.set_line_width(1)
        ctx.stroke()
        text(ctx, chip, x + w - PC.pad - cw / 2, cy + PC.chip_size * 0.4, PC.chip_size, "sans", C["teal"], a, 0, "c")
    # 본문 — 번역문, 핵심 구절 형광펜(등장 뒤 hl_delay_sec)
    yy = y + _head_h() + PC.body_size
    hk = ease_io((lt - PC.hl_delay_sec) / PC.hl_sec)
    for ln in lines:
        if d["hl"] and d["hl"] in ln and hk > 0:
            i = ln.index(d["hl"])
            hx = x + PC.pad + tw(ctx, ln[:i], PC.body_size, "sansm")
            hw = tw(ctx, d["hl"], PC.body_size, "sansm")
            ctx.rectangle(hx - 2, yy - PC.body_size, (hw + 4) * hk, PC.body_size + 4)
            ctx.set_source_rgba(*C["gold"], 0.35 * a)
            ctx.fill()
        text(ctx, ln, x + PC.pad, yy, PC.body_size, "sansm", (1, 1, 1), a, 0, "l")
        yy += PC.body_line
    if d["orig"]:
        text(ctx, d["orig"], x + PC.pad, yy, PC.orig_size, "monom", C["muted"], a, 0, "l")
        yy += PC.body_line
    # 하단 — 게시 시각 / 'X 게시물 · 번역', 검증 라벨·삭제 표기(호박색, 도장 없음)
    fy = y + h - PC.pad
    if d["label"] or d["deleted"]:
        note = " · ".join(x_ for x_ in (d["label"], d["deleted"]) if x_)
        text(ctx, note, x + PC.pad, fy - PC.foot_size * 2, PC.foot_size, "sansb", C["amber"], a, 0, "l")
    text(ctx, d["when"], x + PC.pad, fy, PC.foot_size, "monom", C["muted"], a, 0, "l")
    text(ctx, d["foot"], x + w - PC.pad, fy, PC.foot_size, "sans", C["muted"], a, 0, "r")


__all__ = ["PostSourceError", "draw_post", "post_alpha", "post_geom", "post_text"]

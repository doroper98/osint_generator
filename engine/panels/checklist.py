"""패널 checklist — 확인된 사실(체크 2획 애니메이션) (v2.5.0, v2 render2 `P_check`, 08 §8). 수치는 `panels.charts.checklist`.

v7.4.0 UF-400·UF-401(영상 분석 D11) — style open: 가설·후보 목록. 번호 칸을 먼저 비워 보이고 at 시각에 채운다(체크 없음)."""

from __future__ import annotations

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.panels import skin_panel
from engine.panels.base import chart
from engine.style import C
from engine.timebase import ease_out, smooth
from engine.typography import rrect, text
from rules import load_rules

AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
K = load_rules().panels.charts.checklist
SP = skin_panel.P


def _draw_open(ctx: cairo.Context, t: float, e: dict, a: float) -> None:
    """열린 칸: 번호 칸(점선 테두리)이 차례로 나타나고, at[i] 에 칸이 채워지며 문구가 들어온다. 체크 표시 없음."""
    O = K.open  # noqa: N806
    lt = t - e["t0"]
    at = e.get("at") or [e["t0"] + K.appear_start_sec + i * K.appear_step_sec for i in range(len(e["items"]))]
    for i, s_ in enumerate(e["items"]):
        y = K.y0 + i * K.dy
        ra = a * smooth((lt - O.reveal_start_sec - i * O.reveal_step_sec) / O.reveal_fade_sec)
        if ra <= 0:
            continue
        top = y + K.box_top_dy - (O.slot_h - K.box) / 2
        fa = smooth((t - at[i]) / O.fill_fade_sec)
        rrect(ctx, K.box_x, top, O.slot_w, O.slot_h, O.slot_r)
        if fa > 0:
            ctx.set_source_rgba(*C["white"], O.fill_alpha * fa * ra)
            ctx.fill_preserve()
        ctx.set_source_rgba(*C["white"], O.slot_line_alpha * ra)
        ctx.set_line_width(O.slot_line_w)
        ctx.set_dash(O.slot_dash if fa < 1 else [])
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, str(i + 1), K.box_x + K.box / 2, y, O.num_size, "sansb", C["muted"], ra, 0, "c")
        text(ctx, s_, K.text_x, y, K.text_size, "sansb", C["white"], fa * ra, 0, "l")


SPLIT = " — "   # 항목 문구의 덧말 구분(줄표 앞뒤 빈칸) — 앞 = 굵은 항목, 뒤 = 오른쪽 맞춤 덧말


def item_times(e: dict) -> list[float]:
    """줄마다 나타나기 시작하는 시각 — 연출 at 이 있으면 그 시각, 없으면 패널 시작 + appear_start + i × appear_step."""
    return list(e.get("at") or [e["t0"] + K.appear_start_sec + i * K.appear_step_sec for i in range(len(e["items"]))])


def skin_reveals(e: dict) -> list[tuple[str, float]]:
    """skin 조판에서 부분마다 (이름, 완전히 보이는 시각) — engine.panel_parts 가 [panel-part-hold] 에 쓴다(그리기와 같은 값)."""
    L = SP.list  # noqa: N806
    out = [(f"항목 {i + 1} {s_!r}", ti + L.in_sec) for i, (s_, ti) in enumerate(zip(e["items"], item_times(e)))]
    if e.get("footer"):
        out.append((f"꼬리말 {e['footer']!r}", e["t0"] + L.footer.delay_sec + L.footer.fade_sec))
    return out


def skin_rows(e: dict) -> list[float]:
    """줄 기준선 y — 줄 묶음을 종이 가운데(list.cy)에 맞춘다."""
    L = SP.list  # noqa: N806
    n = len(e["items"])
    return [L.cy - (n - 1) * L.pitch / 2 + i * L.pitch for i in range(n)]


def _mix(c0: tuple, c1: tuple, k: float) -> tuple:
    return tuple(a_ + (b_ - a_) * k for a_, b_ in zip(c0, c1))


def _draw_skin(ctx: cairo.Context, t: float, e: dict, a: float) -> None:
    """v7.4.0 사용자 의견 UF-919(D936) — 목록 새 조판: 번호 칸 상자 없음. 두 자리 번호(mono) · 굵은 항목 · 오른쪽 맞춤 덧말 · 줄 사이 가는 선.
    줄은 제 시각에 통째로 떠오르고(빈 번호 칸을 미리 깔지 않는다), 지금 막 나타난 줄만 강조색(번호 + 왼쪽 막대). 기본 양식은 번호 자리에 체크 두 획,
    열린 양식(style open — 가설·후보)은 번호. 꼬리말은 패널과 함께 일찍 뜬다(UF-917). 값 = rules skin.panel.list."""
    from engine.typography import tw  # noqa: PLC0415

    L = SP.list  # noqa: N806
    op = e.get("style") == "open"
    ts = item_times(e)
    ys = skin_rows(e)
    n = len(ts)
    for i, s_ in enumerate(e["items"]):
        f = smooth((t - ts[i]) / L.in_sec)
        if f <= 0:
            continue
        nxt = smooth((t - ts[i + 1]) / L.in_sec) if i + 1 < n else 0.0
        cur = f * (1 - nxt)                       # 지금 줄(다음 줄이 뜨면 물러난다)
        y = ys[i] + (1 - f) * L.rise
        ra = a * f
        head, _, note = s_.partition(SPLIT)
        if i < n - 1:
            skin_panel.hline(ctx, L.x0, L.x1, ys[i] + L.rule_dy, ra)
        if cur > 0:
            ctx.new_path()
            ctx.rectangle(L.x0 + L.bar.dx, y + L.bar.dy, L.bar.w, L.bar.h)
            ctx.set_source_rgba(*skin.ACCENT_SHAPE, cur * a)
            ctx.fill()
        mark = _mix(skin.INK3, skin.ACCENT_INK, cur)
        if op:
            text(ctx, f"{i + 1:02d}", L.x0, y, L.num.size, L.num.font, mark, ra, 0, "l", spacing=L.num.track * L.num.size)
        else:
            ck = ease_out((t - ts[i] - K.check_delay_sec) / K.check_sec)
            (p0x, p0y), (p1x, p1y), (p2x, p2y) = ((L.x0 + px, y + py) for px, py in L.check.pts)
            short = min(1, ck * 2)
            ctx.new_path()
            ctx.move_to(p0x, p0y)
            ctx.line_to(p0x + (p1x - p0x) * short, p0y + (p1y - p0y) * short)
            if ck > 1 / 2:
                k = (ck - 1 / 2) * 2
                ctx.line_to(p1x + (p2x - p1x) * k, p1y + (p2y - p1y) * k)
            ctx.set_source_rgba(*_mix(skin.INK, skin.ACCENT_INK, cur), ra)
            ctx.set_line_width(L.check.w)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        hx = L.x0 + L.head.dx
        text(ctx, head, hx, y, L.head.size, L.head.font, skin.INK, ra, 0, "l")
        if note:
            wide = hx + tw(ctx, head, L.head.size, L.head.font) + L.note.gap + tw(ctx, note, L.note.size, L.note.font) > L.x1
            if wide:   # 한 줄에 안 들어가면 항목 아래 작은 줄로
                text(ctx, note, hx, y + L.note.dy, L.note.size, L.note.font, skin.INK2, ra, 0, "l")
            else:
                text(ctx, note, L.x1, y, L.note.size, L.note.font, skin.INK2, ra, 0, "r")
    if e["footer"]:
        F = L.footer  # noqa: N806
        fb = a * smooth((t - e["t0"] - F.delay_sec) / F.fade_sec)
        text(ctx, e["footer"], L.x0 + L.head.dx, F.y, F.size, F.font, skin.INK3, fb, 0, "l")


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    if skin.active():
        _draw_skin(ctx, t, e, a)
        return
    if e.get("style") == "open":
        _draw_open(ctx, t, e, a)
        if e["footer"]:
            text(ctx, e["footer"], K.text_x, K.footer_y, K.footer_size, "serif", C["muted"],
                 a * smooth((t - e["t0"] - K.footer_sec) / K.footer_fade_sec), 0, "l")
        return
    lt = t - e["t0"]
    b = K.box
    for i, s_ in enumerate(e["items"]):
        y = K.y0 + i * K.dy
        t_i = K.appear_start_sec + i * K.appear_step_sec
        f = smooth((lt - t_i) / K.appear_sec)
        if f <= 0:
            continue
        top = y + K.box_top_dy
        rrect(ctx, K.box_x, top, b, b, K.box_r)
        ctx.set_source_rgba(*C["green"], K.box_alpha * f * a)
        ctx.fill()
        ck = ease_out((lt - t_i - K.check_delay_sec) / K.check_sec)
        (p0x, p0y), (p1x, p1y), (p2x, p2y) = ((K.box_x + px, top + py) for px, py in K.check_points)
        short = min(1, ck * 2)                  # 앞 절반 = 짧은 획, 뒤 절반 = 긴 획
        ctx.new_path()
        ctx.move_to(p0x, p0y)
        ctx.line_to(p0x + (p1x - p0x) * short, p0y + (p1y - p0y) * short)
        if ck > 1 / 2:
            k = (ck - 1 / 2) * 2
            ctx.line_to(p1x + (p2x - p1x) * k, p1y + (p2y - p1y) * k)
        ctx.set_source_rgba(*C["green"], a)
        ctx.set_line_width(K.check_width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        text(ctx, s_, K.text_x, y, K.text_size, "sansb", C["white"], f * a, 0, "l")
    if e["footer"]:
        fb = a * smooth((lt - K.footer_sec) / K.footer_fade_sec)
        text(ctx, e["footer"], K.text_x, K.footer_y, K.footer_size, "serif", C["muted"], fb, 0, "l")

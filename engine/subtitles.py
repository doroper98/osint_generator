"""하단 자막 — 강조 구간 금색 (v2.1.0, render3 `draw_subtitle`, 09 §5).

v4.5.0(사용자 결정 D85, C9 개정, back_and_forth D-0096): 검증 라벨(`<미검증>`·`<논쟁>`)은 자막에 그리지 않는다
(v3.3.0 NB12 접두 폐지). 검증 상태는 claims·script_labels·provenance 에 기록되고, 화면에는 엔딩 카드 마지막 줄 한 줄만(engine.fullcards).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.style import C, SKIN, SUBTITLE, SUBTITLE_WRAP_PX, W_OUT
from engine.timebase import smooth
from engine.typography import font, ink_rgb, text, tw, wrap

if TYPE_CHECKING:
    from schemas.rules_models import SkinGlow


def emphasis_flags(segments: list[tuple[str, int]]) -> tuple[str, list[int]]:
    """segments → (자막 텍스트, 글자별 강조 플래그)."""
    flags: list[int] = []
    for seg, f in segments:
        flags += [f] * len(seg)
    return "".join(s for s, _ in segments), flags


def split_runs(ln: str, j: int, flags: list[int]) -> list[tuple[str, int]]:
    """줄 ln(자막 텍스트의 j 번째 글자부터) 을 같은 플래그 구간으로 자른다."""
    out = []
    k = 0
    while k < len(ln):
        f = flags[j + k] if j + k < len(flags) else 0
        k2 = k
        while k2 < len(ln) and (flags[j + k2] if j + k2 < len(flags) else 0) == f:
            k2 += 1
        out.append((ln[k:k2], f))
        k = k2
    return out


LEAD_SEC = 0.05     # 문장 시작보다 이만큼 먼저 나타나기 시작한다(종전 값)
IN_SEC = 0.18       # 나타남(종전 값)
OUT_HOLD_SEC = 0.25  # 문장 끝 뒤 이만큼까지 남는다(종전 값)
OUT_SEC = 0.2       # 사라짐(종전 값)


def bridged_sentences(tb: object, t: float) -> list[tuple[str, float]]:
    """디자인 시스템 무대의 자막 시간 모델(v7.4.0 UF-911, D927) → 시각 t 에 보이는 [(문장 id, 알파)].
    다음 문장과의 쉼이 rules skin.subtitle.bridge_gap_sec 이하면 앞 문장을 끄지 않고 다음 문장이 나타날 때까지 붙든 뒤
    그 순간 바로 바꾼다(한 시각에 한 문장 — 꺼졌다 켜지지 않고, 두 문장이 겹쳐 뭉개지지도 않는다). 쉼이 더 길면 종전처럼 사라졌다 나타난다."""
    S = SKIN.subtitle  # noqa: N806
    order = tb.order  # type: ignore[attr-defined]
    out: list[tuple[str, float]] = []
    for i, sid in enumerate(order):
        x = tb.sent[sid]  # type: ignore[attr-defined]
        prev = tb.sent[order[i - 1]] if i > 0 else None  # type: ignore[attr-defined]
        nxt = tb.sent[order[i + 1]] if i + 1 < len(order) else None  # type: ignore[attr-defined]
        t_in = x.t0 - LEAD_SEC
        from_prev = prev is not None and x.t0 - prev.t1 <= S.bridge_gap_sec
        to_next = nxt is not None and nxt.t0 - x.t1 <= S.bridge_gap_sec
        t_end = (nxt.t0 - LEAD_SEC) if to_next else x.t1 + OUT_HOLD_SEC  # type: ignore[union-attr]
        if not t_in <= t <= t_end or (to_next and t >= t_end):   # 이어지는 문장은 다음 문장이 나타나는 순간 바로 물러난다(한 시각에 한 문장)
            continue
        a_in = 1.0 if from_prev else smooth((t - t_in) / IN_SEC)
        a_out = 1.0 if to_next else smooth((x.t1 + OUT_HOLD_SEC - t) / OUT_SEC)
        out.append((sid, min(a_in, a_out)))
    return out


def _line_boxes(ctx: cairo.Context, x: object) -> list[tuple[float, float, float, float]]:
    """한 문장의 자막 줄 글자 상자(후광 제외, 설계 px)."""
    size = SUBTITLE.size
    txt, _ = emphasis_flags(x.segments)  # type: ignore[attr-defined]
    lines = wrap(ctx, txt, SUBTITLE_WRAP_PX, size, "sansm")
    base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap
    out = []
    for li, ln in enumerate(lines):
        w = tw(ctx, ln, size, "sansm")
        by = base_y + li * SUBTITLE.line_gap
        out.append((W_OUT / 2 - w / 2, by - size * 0.86, W_OUT / 2 + w / 2, by + size * 0.22))   # 글자 상자(후광 제외)
    return out


def subtitle_boxes(ctx: cairo.Context, tb: object, t: float) -> list[tuple[float, float, float, float]]:
    """시각 t 에 보이는 자막 줄 글자 상자(후광 제외 — 글자 자체, 설계 px) — draw_subtitle 과 같은 접기·기준선(v5.3.1 checks subtitle_overlap)."""
    if skin.active():   # v7.4.0 UF-911 — 이어지는 문장은 쉼 동안에도 남는다(그리기와 같은 시간 모델)
        vis = bridged_sentences(tb, t)
        if vis:
            return [b for sid, _ in vis for b in _line_boxes(ctx, tb.sent[sid])]  # type: ignore[attr-defined]
    for sid in tb.order:  # type: ignore[attr-defined]
        x = tb.sent[sid]  # type: ignore[attr-defined]
        if skin.active():
            break
        if x.t0 - 0.05 <= t <= x.t1 + 0.25:
            size = SUBTITLE.size
            txt, _ = emphasis_flags(x.segments)
            lines = wrap(ctx, txt, SUBTITLE_WRAP_PX, size, "sansm")
            base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap
            out = []
            for li, ln in enumerate(lines):
                w = tw(ctx, ln, size, "sansm")
                by = base_y + li * SUBTITLE.line_gap
                out.append((W_OUT / 2 - w / 2, by - size * 0.86, W_OUT / 2 + w / 2, by + size * 0.22))   # 글자 상자(후광 제외)
            return out
    h = tb.hold_at(t) if hasattr(tb, "hold_at") else None   # v7.4.0 D-0274 §2③ — 발언 자리 번역 자막
    if h is None:
        return []
    out = []
    lines = hold_lines(ctx, h)
    base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap
    for li, ln in enumerate(lines):
        w = tw(ctx, ln, SUBTITLE.size, "sansm")
        by = base_y + li * SUBTITLE.line_gap
        out.append((W_OUT / 2 - w / 2, by - SUBTITLE.size * 0.86, W_OUT / 2 + w / 2, by + SUBTITLE.size * 0.22))
    return out


def hold_lines(ctx: cairo.Context, h: object) -> list[str]:
    """발언 자리 자막 줄 — 원고가 준 줄(≤ 2)을 자막 폭으로 접는다(린트와 같은 폭)."""
    return [ln for s in h.subtitle for ln in wrap(ctx, s, SUBTITLE_WRAP_PX, SUBTITLE.size, "sansm")]  # type: ignore[attr-defined]


def _ctx_w(ctx: cairo.Context, s: str, size: float) -> float:
    """그리는 컨텍스트 기준 전진 폭(설계 px) — 장치 배율의 글자 전진 폭 반올림과 같은 값."""
    ctx.save()
    font(ctx, "sansm", size)
    w = ctx.text_extents(s).x_advance
    ctx.restore()
    return w


def draw_subtitle(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    """v7.4.0 C0.0·UF-906(D917) — 디자인 시스템 무대(skin.active)면 잉크 글자·테두리 없음·뒤 흰 번짐(skin.glow), 강조 = 팔레트 accent·
    skin.subtitle.emphasis_font. 줄바꿈·자리는 같다(린트와 공유)."""
    tb = R.tb
    on = skin.active()
    emph_font = SKIN.subtitle.emphasis_font if on else "sansb"
    halo = 0.0 if on else SUBTITLE.halo
    if on:   # v7.4.0 UF-911(D927) — 이어지는 문장은 끄지 않고 겹쳐 넘긴다(깜빡임 없음)
        vis = bridged_sentences(tb, t)
        if vis:
            draws = [_sentence_draw(ctx, tb.sent[sid], a, emph_font, halo) for sid, a in vis]

            def draw_all(c: cairo.Context) -> None:
                for d in draws:
                    d(c)
            _paint(ctx, draw_all, subtitle_boxes(ctx, tb, t), on, _map_glow(R))
            return
    for sid in tb.order:
        x = tb.sent[sid]
        if on:
            break
        if x.t0 - 0.05 <= t <= x.t1 + 0.25:
            a = min(smooth((t - x.t0 + 0.05) / 0.18), smooth((x.t1 + 0.25 - t) / 0.2))
            size = SUBTITLE.size
            txt, flags = emphasis_flags(x.segments)
            lines = wrap(ctx, txt, SUBTITLE_WRAP_PX, size, "sansm")   # 린트(script.lint)와 같은 폭 — 라벨 폭을 빼지 않는다
            base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap

            def draw(c: cairo.Context) -> None:
                pos = 0
                for li, ln in enumerate(lines):
                    j = txt.find(ln, pos)
                    pos = j + len(ln)
                    # v5.6.0 — 줄 가운데·구간 전진 폭은 그리는 컨텍스트(장치 배율 k)에서 잰다. 1배 측정 컨텍스트로 재면 글자 전진 폭
                    # 반올림이 배율마다 달라 720p 에서 강조어 앞뒤에 틈이 생겼다(사용자 시청 2026-10-04, RENDER-AP-010). 480p(k=1)는 같은 값
                    xx = W_OUT / 2 - _ctx_w(c, ln, size) / 2
                    for run, f in split_runs(ln, j, flags):
                        text(c, run, xx, base_y + li * SUBTITLE.line_gap, size, emph_font if f else "sansm",
                             C[SUBTITLE.emphasis_color] if f else ink_rgb(), a, halo, "l", halo_a=SUBTITLE.halo_alpha)
                        xx += _ctx_w(c, run, size)
            _paint(ctx, draw, subtitle_boxes(ctx, tb, t) if on else [], on, _map_glow(R))
            return
    h = tb.hold_at(t)   # v7.4.0 D-0274 §2③ — 발언 자리: 원음 위 번역 자막(강조 없음)
    if h is not None:
        a = min(smooth((t - h.t0 + 0.05) / 0.18), smooth((h.t1 + 0.25 - t) / 0.2))
        lines = hold_lines(ctx, h)
        base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap

        def draw_hold(c: cairo.Context) -> None:
            for li, ln in enumerate(lines):
                text(c, ln, W_OUT / 2 - _ctx_w(c, ln, SUBTITLE.size) / 2, base_y + li * SUBTITLE.line_gap, SUBTITLE.size, "sansm",
                     ink_rgb(), a, halo, "l", halo_a=SUBTITLE.halo_alpha)
        _paint(ctx, draw_hold, subtitle_boxes(ctx, tb, t) if on else [], on, _map_glow(R))


def _sentence_draw(ctx: cairo.Context, x: object, a: float, emph_font: str, halo: float) -> Callable[[cairo.Context], None]:
    """한 문장을 알파 a 로 그리는 함수(줄바꿈·자리·강조는 draw_subtitle 의 종전 경로와 같다)."""
    size = SUBTITLE.size
    txt, flags = emphasis_flags(x.segments)  # type: ignore[attr-defined]
    lines = wrap(ctx, txt, SUBTITLE_WRAP_PX, size, "sansm")
    base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap

    def draw(c: cairo.Context) -> None:
        pos = 0
        for li, ln in enumerate(lines):
            j = txt.find(ln, pos)
            pos = j + len(ln)
            xx = W_OUT / 2 - _ctx_w(c, ln, size) / 2
            for run, f in split_runs(ln, j, flags):
                text(c, run, xx, base_y + li * SUBTITLE.line_gap, size, emph_font if f else "sansm",
                     C[SUBTITLE.emphasis_color] if f else ink_rgb(), a, halo, "l", halo_a=SUBTITLE.halo_alpha)
                xx += _ctx_w(c, run, size)
    return draw


def _map_glow(R: RenderCtx) -> SkinGlow | None:  # noqa: N803
    """v7.4.0 4b-2 — skin 지도(지형·국경·국기 위) 자막 번짐 토큰(rules skin.map_overlays.subtitle_glow). 스튜디오 = None(skin.subtitle 그대로)."""
    from engine.stage import skin_map  # noqa: PLC0415

    return SKIN.map_overlays.subtitle_glow if skin_map(getattr(R, "stage", None)) else None


def _paint(ctx: cairo.Context, draw: Callable[[cairo.Context], None], boxes: list[tuple[float, float, float, float]], on: bool,
           g: SkinGlow | None = None) -> None:
    """디자인 시스템 무대면 글자 상자 합집합 둘레에 흰 번짐을 깔고 그린다(skin.glow), 아니면 그대로 그린다. g = 지도 위 번짐 토큰."""
    if not on or not boxes:
        draw(ctx)
        return
    rect = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    if g is None:
        skin.glow(ctx, draw, rect)
        return
    skin.glow(ctx, draw, rect, g.blur, g.gain, g.alpha)

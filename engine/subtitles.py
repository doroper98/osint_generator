"""하단 자막 — 강조 구간 금색 (v2.1.0, render3 `draw_subtitle`, 09 §5).

v4.5.0(사용자 결정 D85, C9 개정, back_and_forth D-0096): 검증 라벨(`<미검증>`·`<논쟁>`)은 자막에 그리지 않는다
(v3.3.0 NB12 접두 폐지). 검증 상태는 claims·script_labels·provenance 에 기록되고, 화면에는 엔딩 카드 마지막 줄 한 줄만(engine.fullcards).
"""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, SUBTITLE, SUBTITLE_WRAP_PX, W_OUT
from engine.timebase import smooth
from engine.typography import font, text, tw, wrap


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


def subtitle_boxes(ctx: cairo.Context, tb: object, t: float) -> list[tuple[float, float, float, float]]:
    """시각 t 에 보이는 자막 줄 글자 상자(후광 제외 — 글자 자체, 설계 px) — draw_subtitle 과 같은 접기·기준선(v5.3.1 checks subtitle_overlap)."""
    for sid in tb.order:  # type: ignore[attr-defined]
        x = tb.sent[sid]  # type: ignore[attr-defined]
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
    return []


def _ctx_w(ctx: cairo.Context, s: str, size: float) -> float:
    """그리는 컨텍스트 기준 전진 폭(설계 px) — 장치 배율의 글자 전진 폭 반올림과 같은 값."""
    ctx.save()
    font(ctx, "sansm", size)
    w = ctx.text_extents(s).x_advance
    ctx.restore()
    return w


def draw_subtitle(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    tb = R.tb
    for sid in tb.order:
        x = tb.sent[sid]
        if x.t0 - 0.05 <= t <= x.t1 + 0.25:
            a = min(smooth((t - x.t0 + 0.05) / 0.18), smooth((x.t1 + 0.25 - t) / 0.2))
            size = SUBTITLE.size
            txt, flags = emphasis_flags(x.segments)
            lines = wrap(ctx, txt, SUBTITLE_WRAP_PX, size, "sansm")   # 린트(script.lint)와 같은 폭 — 라벨 폭을 빼지 않는다
            base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap
            pos = 0
            for li, ln in enumerate(lines):
                j = txt.find(ln, pos)
                pos = j + len(ln)
                # v5.6.0 — 줄 가운데·구간 전진 폭은 그리는 컨텍스트(장치 배율 k)에서 잰다. 1배 측정 컨텍스트로 재면 글자 전진 폭
                # 반올림이 배율마다 달라 720p 에서 강조어 앞뒤에 틈이 생겼다(사용자 시청 2026-10-04, RENDER-AP-010). 480p(k=1)는 같은 값
                xx = W_OUT / 2 - _ctx_w(ctx, ln, size) / 2
                for run, f in split_runs(ln, j, flags):
                    text(ctx, run, xx, base_y + li * SUBTITLE.line_gap, size, "sansb" if f else "sansm",
                         C[SUBTITLE.emphasis_color] if f else (1, 1, 1), a, SUBTITLE.halo, "l", halo_a=SUBTITLE.halo_alpha)
                    xx += _ctx_w(ctx, run, size)
            return

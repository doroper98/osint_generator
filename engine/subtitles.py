"""하단 자막 — 강조 구간 금색 (v2.1.0, render3 `draw_subtitle`, 09 §5).

v3.3.0(NB12, C9): 검증 라벨이 있는 문장(claims.json status → `<미검증>`·`<논쟁>`)은 첫 줄 앞에 라벨을 붙인다.
문구는 규칙 `script_schema.labels`, 모양은 `layout_480p.subtitle.label_style`. 라벨 없는 문장(hormuz 전부)은 그대로.
"""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.style import C, SUBTITLE, SUBTITLE_WRAP_PX, W_OUT
from engine.timebase import smooth
from engine.typography import text, tw, wrap


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


def draw_subtitle(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    tb = R.tb
    for sid in tb.order:
        x = tb.sent[sid]
        if x.t0 - 0.05 <= t <= x.t1 + 0.25:
            a = min(smooth((t - x.t0 + 0.05) / 0.18), smooth((x.t1 + 0.25 - t) / 0.2))
            size = SUBTITLE.size
            txt, flags = emphasis_flags(x.segments)
            label = (R.cache.get("sentence_labels") or {}).get(sid)
            LS = SUBTITLE.label_style  # noqa: N806
            lsize = size * LS.size_ratio
            lw_label = (tw(ctx, label, lsize, "sansb") + LS.gap_px) if label else 0.0
            lines = wrap(ctx, txt, SUBTITLE_WRAP_PX - lw_label, size, "sansm")
            base_y = SUBTITLE.last_line_y - (len(lines) - 1) * SUBTITLE.line_gap
            pos = 0
            for li, ln in enumerate(lines):
                j = txt.find(ln, pos)
                pos = j + len(ln)
                lw = tw(ctx, ln, size, "sansm") + (lw_label if li == 0 else 0.0)
                xx = W_OUT / 2 - lw / 2
                if label and li == 0:
                    text(ctx, label, xx, base_y, lsize, "sansb", C[LS.color], a, SUBTITLE.halo, "l", halo_a=SUBTITLE.halo_alpha)
                    xx += lw_label
                for run, f in split_runs(ln, j, flags):
                    text(ctx, run, xx, base_y + li * SUBTITLE.line_gap, size, "sansb" if f else "sansm",
                         C[SUBTITLE.emphasis_color] if f else (1, 1, 1), a, SUBTITLE.halo, "l", halo_a=SUBTITLE.halo_alpha)
                    xx += tw(ctx, run, size, "sansm")
            return

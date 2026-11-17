"""패널 statement — 공동성명 서명국 + 동참국 (v2.1.0, render3 `P_statement`)."""

from __future__ import annotations

import cairo

from engine import skin
from engine.context import RenderCtx
from engine.layers.badges import badge_at
from engine.panels import skin_panel
from engine.panels.base import panel_title
from engine.style import MOTION, W_OUT, C
from engine.timebase import smooth

SP = skin_panel.P

AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
SIGNER_X0 = 110          # 첫 서명국 뱃지 가운데(v3 render3 P_statement)
SIGNER_PITCH = 92        # 서명국 사이 간격 — 8개국까지(v3 좌표 그대로)
SIGNER_PITCH_MIN = 64    # 뱃지 지름 48 + 이름표 여유 — 이보다 좁아야 들어가면 오류(패널을 나눈다)
SIGNER_V3_MAX = 8        # 이 수까지는 v3 좌표 그대로(화소 불변) — 넘으면 좌우 여백 안에서 고르게


class StatementOverflowError(ValueError):
    """서명국이 한 줄에 들어가지 않는다(조용히 화면 밖으로 밀지 않는다, 15 P6)."""


def signer_xs(n: int) -> list[float]:
    """서명국 뱃지 가운데 x(설계 px). 8개국까지는 v3 좌표, 9개국 이상은 같은 좌우 여백 안에서 간격을 줄인다 —
    v7.4.0 D935: 서명국 9곳(샌프란시스코 선언)의 아홉째 뱃지가 화면 오른쪽 밖으로 잘렸다(nvidia-chips-china-2026 프리뷰)."""
    if n <= 1:
        return [float(SIGNER_X0)] * n
    pitch = SIGNER_PITCH if n <= SIGNER_V3_MAX else (W_OUT - 2 * SIGNER_X0) / (n - 1)
    if pitch < SIGNER_PITCH_MIN:
        raise StatementOverflowError(f"statement 패널 서명국 {n}곳 — 한 줄에 들어가지 않는다(간격 {pitch:.0f}px < {SIGNER_PITCH_MIN}). 패널을 나눈다")
    return [SIGNER_X0 + i * pitch for i in range(n)]


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    panel_title(ctx, a, e["title"], e.get("subtitle"))
    for i, (s, x) in enumerate(zip(e["signers"], signer_xs(len(e["signers"])))):
        badge_at(ctx, R, x, 230, dict(kind="flag", flag=s["flag"], R=24, t0=e["t0"] + 0.5 + i * 0.22, label=s["label"],
                                      accent="muted"), t, a)
    j = e["joiner"]
    tj = max(e["t0"] + 2.2, j["t_join"])
    badge_at(ctx, R, W_OUT / 2, 345, dict(kind="flag", flag=j["flag"], R=30, t0=tj, label=j["label"], role=j["role"],
                                          accent="gold"), t, a)
    ka = a * smooth((t - tj) / MOTION["panel_item_in_sec"])   # v7.4.0 UF-159 ×1.5
    if skin.active():   # v7.4.0 C0.0 3a — 서명국 줄 아래 가는 잉크 점선(강조색은 동참국 뱃지 하나)
        ctx.set_source_rgba(*skin.INK, SP.axis.alpha * ka)
        ctx.set_line_width(SP.axis.w)
    else:
        ctx.set_source_rgba(*C["gold"], 0.5 * ka)
        ctx.set_line_width(1)
    ctx.set_dash([3, 4])
    ctx.move_to(110, 292)
    ctx.line_to(W_OUT - 190, 292)
    ctx.stroke()
    ctx.set_dash([])

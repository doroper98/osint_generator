"""패널 network — 이해관계자 관계도 (v2.5.0, v2 render2 `P_network` 를 08 §3.1 대로 고쳐 이식, D-0032 작업 5).

v2 에서 고친 것(08 §3 "너무 빨랐고 정돈되지 않음"):
- 선 타이밍: 0.18초 간격·0.8초 지속 → `panels.relation` 의 선 지속·간격(1.0~1.3초, 0.6~0.75초), 노드가 모두 뜬 뒤(규칙 1·2)
- 선 모양: 방향마다 부호가 바뀌는 2차 곡선 → 수평 접선 3차 베지어 하나(규칙 3), 같은 열끼리는 잇지 않는다(모델 검증)
- 라벨: 선과 동시 → 선이 다 그려진 뒤(규칙 4) / 강조: 내레이션이 부를 때(mentions[].at, 규칙 5) / 7개 초과 경고(규칙 6)
- 노드: 휘장 없는 기관을 문자 원으로 그리던 것 → 엔티티 레지스트리 뱃지만(인물·국기·휘장, 제한 휘장은 국기 대체 D5)
"""

from __future__ import annotations

import math

import cairo

from engine.context import RenderCtx
from engine.layers.badges import badge_at
from engine.panels.base import chart, edge_curve
from engine.style import C
from engine.timebase import ease_io, smooth
from engine.typography import text
from rules import load_rules

AXIS = "none"   # v4.3.0 D-0087 — 축 종류(값·날짜 축 없음). 정직성 검사 적용 = rules qa_checks.chart_targets
_R = load_rules().panels
N = _R.charts.network
REL = _R.relation
_ORDER = ("center", "left", "right")   # v2 등장 순서: 가운데 열 → 왼쪽 → 오른쪽


def layout(e: dict) -> dict[str, tuple[float, float, float, float]]:
    """노드 id → (x, y, R, 등장 오프셋)."""
    out: dict[str, tuple[float, float, float, float]] = {}
    for ci, col in enumerate(_ORDER):
        ns = [n for n in e["nodes"] if n["col"] == col]
        for i, n in enumerate(ns):
            y = N.cy + (i - (len(ns) - 1) / 2) * N.dy
            r = N.R_big if n["big"] else (N.R_person if n["kind"] == "person" else N.R_other)
            out[n["id"]] = (N.columns[col], y, r, N.node_start_sec + ci * N.col_step_sec + i * N.node_step_sec)
    return out


def edge_start(e: dict) -> float:
    return max(p[3] for p in layout(e).values()) + REL.edges_after_nodes_sec


@chart
def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    pos = layout(e)
    s0 = edge_start(e)
    for k, ed in enumerate(e["edges"]):
        t_k = s0 + k * REL.edge_gap_sec
        prog = ease_io((lt - t_k) / REL.edge_dur_sec)
        if prog <= 0:
            continue
        sx, sy, sr, _ = pos[ed["src"]]
        dx, dy, dr, _ = pos[ed["dst"]]
        sign = 1 if dx > sx else -1
        pts = edge_curve(sx + sign * (sr + REL.source.pad), sy, dx - sign * (dr + REL.target.pad), dy, prog, REL.curve_samples)
        st = N.styles[ed["type"]]
        ctx.new_path()
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        if st.dash:
            ctx.set_dash(st.dash)
        ctx.set_source_rgba(*C[st.color], st.alpha * a)
        ctx.set_line_width(REL.line_width)
        ctx.stroke()
        ctx.set_dash([])
        if ed["label"]:
            la = a * smooth((lt - t_k - REL.edge_dur_sec) / N.label_sec)   # 선이 다 자란 뒤(규칙 4)
            if la > 0:
                mx, my = edge_curve(sx, sy, dx, dy, 1, REL.curve_samples)[REL.curve_samples // 2]
                text(ctx, ed["label"], mx, my + N.label.y, N.label.size, "sansm", C[st.color], la, N.label.halo, "c")
    for n in e["nodes"]:
        x, y, r, dt = pos[n["id"]]
        t0 = e["t0"] + dt
        if t < t0:
            continue
        for m in e["mentions"]:
            if m["node"] == n["id"] and m["at"] - N.mention_lead_sec <= t <= m["at"] + N.mention_hold_sec:
                f = (t * N.mention_pulse_rate) % 1.0
                ctx.arc(x, y, r + N.mention_ring + N.mention_grow * f, 0, 2 * math.pi)
                ctx.set_source_rgba(*C["gold"], N.mention_alpha * (1 - f) * a)
                ctx.set_line_width(N.mention_width)
                ctx.stroke()
        badge_at(ctx, R, x, y, dict(kind=n["kind"], pid=n["pid"], flag=n["flag"], img=n["img"], R=r, t0=t0,
                                    label=n["label"], role=n["role"], accent=n["accent"]), t, a)


def lint(e: dict) -> list[str]:
    n = len(e["edges"])
    if n > N.max_edges:
        return [f"[network-too-many-edges] '{e['title']}' 선 {n}개 > {N.max_edges} — 패널을 둘로 나누는 것을 권한다 (08 §3 규칙 6)"]
    return []

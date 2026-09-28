"""관계 패널 — 누가 누구에게 무엇을(요구·거절·영향) (v2.5.0, 08 §3·§11-2, D-0032 작업 2).

입력은 데이터(`PanelRelation`: nodes·edges·state_changes), 기하·타이밍은 `rules/video_rules.yaml panels.relation`.
v3 `P_refusal`(요구와 거절)은 이 모델의 한 인스턴스다(hormuz 25컷 픽셀 무변경이 증명).

08 §3 정돈된 관계선 규칙 6개가 코드에 박힌 곳:
  1. 노드가 모두 뜬 뒤 선 — `edge_start()`   2. 선 지속·간격 — 규칙 값(범위는 규칙 모델이 검증)
  3. 같은 형태의 선 — `edge_curve()`(수평 접선 3차 베지어), 요구자 한쪽·대상 세로 열
  4. 라벨은 첫 선 시작 뒤 — `edge_label.delay_sec`, 앞서면 lint 경고(08 §3 v2.5.5 정정)   5. 상태 변화는 단어 앵커 — `state_changes[].at`
  6. 선 7개 초과 → `lint()` 경고 + `split_suggestion()`(제안만, 자동 분할 안 함 — P8)
"""

from __future__ import annotations

import cairo

from engine.context import RenderCtx
from engine.layers.badges import badge_at
from engine.panels.base import edge_curve, panel_title
from engine.style import C, W_OUT
from engine.timebase import ease_io, smooth, window
from engine.typography import text
from rules import load_rules

REL = load_rules().panels.relation


def column(e: dict, group: str) -> list[dict]:
    return [n for n in e["nodes"] if n["group"] == group]


def node_positions(e: dict) -> dict[str, tuple[float, float, float, float]]:
    """노드 id → (x, y, R, 등장 시각 오프셋). 열 세로 중심 cy 에 맞춰 dy 간격으로 쌓는다."""
    out: dict[str, tuple[float, float, float, float]] = {}
    for group, col in (("source", REL.source), ("target", REL.target)):
        nodes = column(e, group)
        y0 = col.cy - (len(nodes) - 1) / 2 * col.dy
        for i, n in enumerate(nodes):
            out[n["id"]] = (col.x, y0 + i * col.dy, col.R, col.t0 + i * col.step)
    return out


def edge_start(e: dict) -> float:
    """첫 선이 자라기 시작하는 시각(패널 시작 기준) — 마지막 노드 등장 뒤(규칙 1)."""
    return max(p[3] for p in node_positions(e).values()) + REL.edges_after_nodes_sec


Rgb = tuple[float, float, float]


def _style_at(t: float, e: dict, edge: dict) -> tuple[Rgb, float, list[float], str, Rgb, float]:
    """(선 색, 알파, 점선, 상태 라벨, 라벨 색, 라벨 알파) — 상태 변화를 at 순서로 겹쳐 섞는다.
    라벨 색은 섞지 않고 새 스타일 색 그대로다(v3 '거절' 라벨)."""
    base = REL.styles[edge["style"]]
    col = C[base.color]
    alpha = base.alpha
    dash = base.dash
    label, lcol, la = "", col, 0.0
    changes = sorted((c for c in e["state_changes"] if c["src"] == edge["src"] and c["dst"] == edge["dst"]),
                     key=lambda c: c["at"])
    for c in changes:
        r = smooth((t - c["at"]) / REL.state_fade_sec)
        if r <= 0:
            break
        st = REL.styles[c["style"]]
        col = tuple(col[j] * (1 - r) + C[st.color][j] * r for j in range(3))
        alpha = alpha * (1 - r) + st.alpha * r
        if r > REL.dash_after:
            dash = st.dash
        label, lcol, la = c["label"], C[st.color], r
    return col, alpha, dash, label, lcol, la


def draw(ctx: cairo.Context, R: RenderCtx, t: float, e: dict, a: float) -> None:  # noqa: N803
    lt = t - e["t0"]
    panel_title(ctx, a, e["title"], e.get("subtitle"))
    pos = node_positions(e)
    for n in e["nodes"]:
        x, y, r, dt = pos[n["id"]]
        b = dict(kind=n["kind"], pid=n["pid"], flag=n["flag"], img=n["img"], R=r, t0=e["t0"] + dt,
                 label=n["label"], role=n["role"], accent=n["accent"])
        if n["group"] == "target":
            b["side"] = "right"
        badge_at(ctx, R, x, y, b, t, a)
    s0 = edge_start(e)
    for i, edge in enumerate(e["edges"]):
        prog = ease_io((lt - s0 - i * REL.edge_gap_sec) / REL.edge_dur_sec)
        if prog <= 0:
            continue
        sx, sy, sr, _ = pos[edge["src"]]
        dx, dy, dr, _ = pos[edge["dst"]]
        col, alpha, dash, label, lcol, la = _style_at(t, e, edge)
        pts = edge_curve(sx + sr + REL.source.pad, sy, dx - dr - REL.target.pad, dy, prog, REL.curve_samples)
        ctx.new_path()
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        if dash:
            ctx.set_dash(dash)
        ctx.set_source_rgba(*col, alpha * a)
        ctx.set_line_width(REL.line_width)
        ctx.stroke()
        ctx.set_dash([])
        if la > 0:
            sl = REL.state_label
            text(ctx, label, dx + sl.dx, dy + sl.dy, sl.size, "sansb", lcol, a * la, sl.halo, "l")
    if e.get("edge_label") and lt > 0:
        el = REL.edge_label
        text(ctx, e["edge_label"], el.x, el.y, el.size, "sansb", C[REL.styles[e["edges"][0]["style"]].color],
             a * smooth((lt - el.delay_sec) / el.fade_sec), el.halo, "c")
    src = column(e, "source")
    for q in e["quotes"]:
        if q["at"] == "bottom":
            qs = REL.quote_bottom
            qa = a * window(t, q["t0"], q["t1"], qs.fade_sec, qs.fade_sec)
            if qa > 0:
                text(ctx, q["text"], W_OUT / 2, qs.y, qs.size, "serifb", C["white"], qa, qs.halo, "c")
        else:
            qs2 = REL.quote_source
            qa = a * window(t, q["t0"], q["t1"], qs2.fade_sec, qs2.fade_sec)
            if qa > 0:
                x, y, _, _ = pos[src[0]["id"]]
                text(ctx, q["text"], x, y + qs2.dy, qs2.size, "serifb", C[src[0]["accent"]], qa, qs2.halo, "c")


def lint(e: dict) -> list[str]:
    """관계 패널 경고(오류 아님). 선이 max_edges 를 넘으면 1건 — 08 §3 규칙 6."""
    out: list[str] = []
    n = len(e["edges"])
    if n > REL.max_edges:
        out.append(f"[relation-too-many-edges] '{e['title']}' 선 {n}개 > {REL.max_edges} — 패널을 둘로 나누는 것을 권한다"
                   f" (split_suggestion, 08 §3 규칙 6)")
    if e.get("edge_label") and REL.edge_label.delay_sec < edge_start(e):
        out.append(f"[relation-label-before-edge] '{e['title']}' 선 라벨 {REL.edge_label.delay_sec}초 < 첫 선 시작 "
                   f"{edge_start(e):.2f}초 (08 §3 규칙 4)")
    return out


def split_suggestion(e: dict) -> dict | None:
    """선이 많을 때 2분할 제안(JSON). 연출 확정은 LLM+사용자 몫이라 실행하지 않는다(P8)."""
    edges = e["edges"]
    if len(edges) <= REL.max_edges:
        return None
    half = (len(edges) + 1) // 2
    parts = []
    for chunk in (edges[:half], edges[half:]):
        ids = {x["src"] for x in chunk} | {x["dst"] for x in chunk}
        keys = {(x["src"], x["dst"]) for x in chunk}
        parts.append({"nodes": [n["id"] for n in e["nodes"] if n["id"] in ids],
                      "edges": [{"src": x["src"], "dst": x["dst"]} for x in chunk],
                      "state_changes": [{"src": c["src"], "dst": c["dst"]} for c in e["state_changes"]
                                        if (c["src"], c["dst"]) in keys]})
    return {"schema_version": 1, "kind": "relation_split_suggestion", "title": e["title"], "edges": len(edges),
            "max_edges": REL.max_edges, "parts": parts, "applied": False}


def main(argv: list[str] | None = None) -> int:
    """`python -m engine.panels.relation <event.yaml>` — 관계 패널 이벤트 하나를 검증하고 경고·분할 제안을 JSON 으로."""
    import argparse  # noqa: PLC0415
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    import yaml  # noqa: PLC0415

    from engine.events import PanelRelation  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="관계 패널 lint (08 §3 규칙 6)")
    ap.add_argument("event", type=Path, help="YAML — 최상위 event: 또는 이벤트 자체")
    args = ap.parse_args(argv)
    doc = yaml.safe_load(args.event.read_text(encoding="utf-8"))
    e = PanelRelation.model_validate(doc.get("event", doc)).model_dump()
    print(json.dumps({"warnings": lint(e), "split_suggestion": split_suggestion(e)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

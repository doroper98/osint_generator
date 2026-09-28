"""숏 문법 검사·전환 선택 — 한 곳 (v3.3.0, docs/handoff/05 §2·§7-2·§7-3, back_and_forth D-0056 작업 3·4).

6.9 결정적 검사(`engine.checks` shots, warning)·7 카메라 제안(`engine.camera_suggest`)이 **같은 함수**를 쓴다(D-0047 §0-4, 중복 구현 금지).
- `shot_issues`: 숏 머무름 < shot_min_hold_sec(다음 키가 move 일 때), 장면당 이동 > camera_moves_per_scene_max, 암전 빈도 > 1/dip_max_per_sec.
- `choose_transition`: 두 숏의 (중심 거리 / 평균 w) ≥ dip_if_dist_over_w 또는 w 비 ≥ dip_if_w_ratio_over → dip, 아니면 move.
임계는 `rules shot_grammar`(05 §2 v3 합격 값).
"""

from __future__ import annotations

import math
from typing import Literal, Protocol

from rules import load_rules

SG = load_rules().shot_grammar


class _Key(Protocol):
    t: float
    x: float
    y: float
    w: float
    dur: float
    mode: str


def choose_transition(a: tuple[float, float, float], b: tuple[float, float, float]) -> Literal["dip", "move"]:
    """a·b = (x, y, w) — x 경도, y = ym(위도)(카메라 내부 좌표), w 화면 폭(도)."""
    at = SG.auto_transition
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    ratio = max(a[2], b[2]) / min(a[2], b[2])
    return "dip" if dist / ((a[2] + b[2]) / 2) >= at.dip_if_dist_over_w or ratio >= at.dip_if_w_ratio_over else "move"


def scene_at(sentences: list, t: float) -> str:  # noqa: ANN001 — Plan.sentences(scene·t0)
    sc = sentences[0].scene
    for s in sentences:
        if s.t0 - 1.5 <= t:
            sc = s.scene
    return sc


def shot_issues(keys: list[_Key], sentences: list, events: list[dict], total: float) -> list[str]:  # noqa: ANN001
    out: list[str] = []
    ks = sorted(keys, key=lambda k: k.t)
    for a, b in zip(ks, ks[1:]):
        hold = b.t - (a.t + a.dur)
        if hold < SG.shot_min_hold_sec and b.mode == "move":
            out.append(f"숏 t={a.t:.1f}→{b.t:.1f} 머무름 {hold:.1f}s < {SG.shot_min_hold_sec}s")
    moves: dict[str, int] = {}
    for k in ks:
        if k.mode == "move" and k.t > 0:
            sc = scene_at(sentences, k.t)
            moves[sc] = moves.get(sc, 0) + 1
    out += [f"장면 {sc} 카메라 이동 {n} > {SG.camera_moves_per_scene_max}" for sc, n in moves.items()
            if n > SG.camera_moves_per_scene_max]
    dips = [e for e in events if e["type"] == "dip" and not e.get("under")]
    limit = max(1, int(total // SG.dip_max_per_sec) + 1)
    if len(dips) > limit:
        out.append(f"암전 {len(dips)}회 > {limit}(1/{SG.dip_max_per_sec}s)")
    return out


__all__ = ["choose_transition", "scene_at", "shot_issues"]

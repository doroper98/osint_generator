"""숏 문법 검사·전환 선택 — 한 곳 (v3.3.0, docs/handoff/05 §2·§7-2·§7-3, back_and_forth D-0056 작업 3·4).

6.9 결정적 검사(`engine.checks` shots, warning)·7 카메라 제안(`engine.camera_suggest`)이 **같은 함수**를 쓴다(D-0047 §0-4, 중복 구현 금지).
- `shot_issues`: 숏 머무름 < shot_min_hold_sec(다음 키가 move 일 때), 장면당 이동 > camera_moves_per_scene_max, 암전 빈도 > 1/dip_max_per_sec.
- `choose_transition`: 두 숏의 (중심 거리 / 평균 w) ≥ dip_if_dist_over_w 또는 w 비 ≥ dip_if_w_ratio_over → dip, 아니면 move.
임계는 `rules shot_grammar`(05 §2 v3 합격 값).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Optional, Protocol

from rules import load_rules

SG = load_rules().shot_grammar


@dataclass(frozen=True)
class ShotStage:
    """숏 하나의 무대·전환·월드 카메라(무대 연속성 검사 입력, v4.1.0 D-0077). mode 는 연출 원문(cut·move·dip)."""

    t: float
    mode: str
    stage: str
    x: float
    y: float
    w: float
    reason: Optional[str] = None   # v4.3.0 — 연출이 적은 되돌아가기 이유(timeline_backtrack)
    island: bool = False           # v5.1.0 D-0126 Q1 A — backdrop 주 무대의 차트 아일랜드 뷰포트 카메라(무대 전환이 아니다)


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
        if s.t0 - SG.scene_attach_lead_sec <= t:
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


def stage_continuity(shots: list[ShotStage]) -> list[tuple[str, str]]:
    """무대 연속성(v4.1.0 D-0076 작업 5·D-0077, docs/handoff/20 §2.2·§12) → [(규칙 키, 설명)]. 임계는 rules stage.
    max_secondary: 주 무대 1 + 보조 무대 ≤ stage.max_secondary
    switch_without_dip: 무대가 바뀌는 숏의 전환이 dip(암전 컷)이 아님
    teleport: 같은 무대의 연속한 두 숏에서 뒤 숏이 cut(t>0)인데 choose_transition 이 dip 을 요구하는 거리·배율(shot_grammar.auto_transition)
    max_switches: 무대가 바뀌는 지점 수 > stage.continuity.max_switches(장면마다 새 캔버스 = 슬라이드)
    다른 무대 사이의 좌표 거리는 비교하지 않는다(switch_without_dip 이 잡는다)."""
    st = load_rules().stage
    ks = sorted((s for s in shots if not s.island), key=lambda s: s.t)   # 아일랜드 카메라는 무대 전환이 아니다(D-0126 Q1)
    out: list[tuple[str, str]] = []
    names = list(dict.fromkeys(s.stage for s in ks))
    if len(names) - 1 > st.max_secondary:
        out.append(("max_secondary", f"무대 {names} — 주 무대 1 + 보조 {len(names) - 1} > {st.max_secondary}"))
    switches = 0
    for a, b in zip(ks, ks[1:]):
        if a.stage != b.stage:
            switches += 1
            if b.mode != "dip":
                out.append(("switch_without_dip", f"t={b.t:.2f} 무대 {a.stage} → {b.stage} 전환이 {b.mode} — 암전 컷(dip)만 허용"))
        elif b.mode == "cut" and b.t > 0 and choose_transition((a.x, a.y, a.w), (b.x, b.y, b.w)) == "dip":
            out.append(("teleport", f"t={b.t:.2f} 무대 {b.stage} 안 먼 cut(암전 없음) — shot_grammar.auto_transition 이 dip 을 요구하는 이동"))
    if switches > st.continuity.max_switches:
        out.append(("max_switches", f"무대 전환 {switches}회 > {st.continuity.max_switches} — 장면마다 새 캔버스(슬라이드 구성)"))
    return out


def timeline_backtrack(shots: list[ShotStage]) -> list[str]:
    """시간축 카메라 문법(20 §6, D-0084 작업 3): 기본은 왼쪽 → 오른쪽. 같은 시간축 무대의 연속 숏에서 카메라 중심이 왼쪽(과거)으로
    가는데 숏에 reason 이 없으면 경고 한 줄. 이유가 있으면 통과(끝 물러나기 등)."""
    ks = sorted(shots, key=lambda s: s.t)
    return [f"[timeline_backtrack] t={b.t:.2f} 시간축 카메라가 왼쪽(과거)으로 되돌아간다 — 숏 reason 에 이유를 적거나 순서를 바꾼다"
            for a, b in zip(ks, ks[1:]) if a.stage == b.stage == "timeline" and b.x < a.x and not b.reason]


def timeline_w_changes(shots: list[ShotStage], sentences: list) -> list[dict]:  # noqa: ANN001 — Plan.sentences(scene·t0)
    """시간축 축 스케일 변화(v5.1.0 D-0121 §A) — 시간축 무대 숏만(지도 무대 제외), 시각 순 연속한 두 숏의 w 가 다르면 한 건.
    첫 숏(설정)은 변화가 아니다. 장면 = scene_at(숏 시각, shot_grammar.scene_attach_lead_sec — 이동 선행 키는 다음 장면).
    반환 [{at, from, to, ratio, scene_from, scene_to, n}] — provenance timeline.w_changes[] 와 검사가 같은 값을 본다."""
    ks = [s for s in sorted(shots, key=lambda s: s.t) if s.stage == "timeline"]
    out: list[dict] = []
    for a, b in zip(ks, ks[1:]):
        if b.w != a.w:
            out.append({"at": round(b.t, 2), "from": a.w, "to": b.w, "ratio": round(max(a.w, b.w) / min(a.w, b.w), 3),
                        "scene_from": scene_at(sentences, a.t), "scene_to": scene_at(sentences, b.t), "n": len(out) + 1})
    return out


def timeline_rescale(changes: list[dict]) -> list[str]:
    """`[timeline-rescale] {at} w {a}→{b} ({이유})` — rules stage_timeline.axis_scale: ① scene_fixed 인데 같은 장면 안 변화
    ② 영상 전체 변화 수 > w_changes_per_video_max(초과분마다) ③ 비율 < w_change_ratio_min. 코드는 w 를 고치지 않는다(P8)."""
    ax = load_rules().stage_timeline.axis_scale
    out: list[str] = []
    for c in changes:
        why = []
        if ax.scene_fixed and c["scene_from"] == c["scene_to"]:
            why.append(f"장면 {c['scene_to']} 안")
        if c["n"] > ax.w_changes_per_video_max:
            why.append(f"영상 {c['n']}번째 > {ax.w_changes_per_video_max}")
        if c["ratio"] < ax.w_change_ratio_min:
            why.append(f"비율 {c['ratio']:g} < {ax.w_change_ratio_min:g}")
        if why:
            out.append(f"[timeline-rescale] t={c['at']:.2f} w {c['from']:g}→{c['to']:g} ({', '.join(why)})")
    return out


__all__ = ["ShotStage", "choose_transition", "scene_at", "shot_issues", "stage_continuity", "timeline_backtrack", "timeline_rescale",
           "timeline_w_changes"]

"""숏 단위 지명 라벨 일정 (v7.4.0 back_and_forth D-0311, 사용자 의견 UF-175 "지도가 확대 되거나 축소 될때 도시 이름이 나왔다 사라지거나 …
깜빡깜빡 거리는거 … 없애라고 했잖아").

옛 방식은 프레임마다 LOD·충돌 판정으로 라벨 집합을 새로 정해, 카메라 이동 중 라벨이 나타났다 사라지고 새 라벨이 끼어들어 기존 라벨을 밀어냈다.
여기서는 렌더 전 한 번, 숏(컷 키 사이)마다 카메라 경로를 훑어 라벨마다 보이는 구간을 정한다:
- 숏 시작 뷰에서 지금 규칙(LOD·free)으로 초기 집합.
- 이동 중 기존 라벨은 유지(폭 LOD 이력 = rules labels.stability.lod_hysteresis). 앵커가 화면 밖으로 나가거나 마커·막대 상자에 덮이면 퇴장(페이드),
  같은 숏에서 다시 들어오지 않는다.
- 새 라벨은 기존 라벨·예약 상자와 안 겹치고 숏 끝까지 남을 때만 들어온다(페이드인 한 번). 끼어들어 기존 라벨을 밀어내지 않는다.
렌더(engine.layers.labels.draw_labels)는 이 일정만 읽는다 — 병렬 구간 렌더에서도 같은 결과(결정적).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import cairo

from engine.projection import View
from rules import load_rules

if TYPE_CHECKING:
    from engine.stage import MercatorStage


@dataclass
class Span:
    t_in: float
    t_out: float
    fade_in: bool    # 숏 첫 순간이 아니면 페이드인
    fade_out: bool   # 숏 끝(컷)이 아니면 페이드아웃
    shot: int


@dataclass
class LabelPlan:
    spans: dict[str, list[Span]] = field(default_factory=dict)
    shots: list[tuple[float, float]] = field(default_factory=list)
    hard_end: list[bool] = field(default_factory=list)
    fade_sec: float = 0.5

    def active(self, t: float) -> dict[str, float]:
        """시각 t 에 보이는 라벨 id → 알파(0~1, 페이드)."""
        out: dict[str, float] = {}
        f = self.fade_sec
        for cid, ss in self.spans.items():
            for s in ss:
                if s.t_in <= t <= s.t_out:
                    a = 1.0
                    if s.fade_in:
                        a = min(a, (t - s.t_in) / f)
                    if s.fade_out:
                        a = min(a, (s.t_out - t) / f)
                    if a > 0.01:
                        out[cid] = max(0.0, min(1.0, a))
                    break
        return out

    def to_json(self) -> dict:
        return {"schema_version": 1, "fade_sec": self.fade_sec, "shots": [list(x) for x in self.shots], "hard_end": self.hard_end,
                "spans": {k: [[s.t_in, s.t_out, s.fade_in, s.fade_out, s.shot] for s in v] for k, v in sorted(self.spans.items())}}

    def stats(self) -> dict[str, int]:
        return {"shots": len(self.shots), "labels": len(self.spans), "events": sum(len(v) for v in self.spans.values())}


def _rect_hit(r: tuple, boxes: list) -> bool:
    x, y, w, h = r
    return any(x < c and x + w > a and y < d and y + h > b for (a, b, c, d) in boxes)


def _reserved_at(ctx: cairo.Context, view: View, events: list[dict], t: float) -> list[tuple]:
    """그 시각 지도 위 마커(부제 포함)·막대 상자 — 라벨이 피할 예약 상자(렌더의 R.reserved 와 같은 종류)."""
    from engine.layers.bars import bars_box  # noqa: PLC0415
    from engine.layers.markers import marker_box  # noqa: PLC0415

    out = []
    for e in events:
        if not (e["t0"] <= t <= e["t1"]) or e.get("in_island"):
            continue
        if e["type"] == "marker" and e.get("world") is not None:
            out.append(marker_box(ctx, e, *view.to_screen(*e["world"]), with_sub=True))
        elif e["type"] == "bars":
            out.append(bars_box(view, e)[0])
    return out


def shot_ranges(keys: list[Any], n_frames: int, fps: float) -> list[tuple[int, int, bool]]:
    """카메라 키마다 끊은 프레임 구간 [a, b) + 끝이 '단단한' 경계인지(다음 키가 cut·dip 이거나 영상 끝). 부드러운 경계(move·drift)는 라벨을 이어 간다."""
    marks: dict[int, bool] = {0: True, n_frames: True}
    for k in keys:
        f = min(n_frames, max(0, math.ceil(k.t * fps - 1e-9)))
        hard = k.mode == "cut"   # dip 은 카메라 키에서 cut 으로 들어온다
        marks[f] = marks.get(f, False) or hard
    fs = sorted(marks)
    return [(a, b, marks[b]) for a, b in zip(fs, fs[1:]) if b > a]


def build_plan(stage: "MercatorStage", cams: Any, keys: list[Any], events: list[dict], n_frames: int, fps: float) -> LabelPlan:
    """숏(카메라 키 구간)마다 라벨 일정. 표본 간격 = rules labels.stability.sample_every_frames.
    새 라벨은 그 숏 끝까지 매 표본에서 화면 안(이력 LOD)·예약 상자 밖일 때만 들어온다(앞을 내다본다). 퇴장한 라벨은 min_hold_sec 안에 다시 들이지 않는다."""
    from engine.layers.labels import city_cap, label_candidates  # noqa: PLC0415

    S = load_rules().labels.stability  # noqa: N806
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    plan = LabelPlan(fade_sec=S.fade_sec)
    cmax = city_cap(stage)
    active: dict[str, list] = {}   # id → [t_in, placed, kind, fade_in, shot]
    exited: dict[str, float] = {}

    def close(cid: str, t: float, fade: bool) -> None:
        t_in, _, _, fi, sh = active.pop(cid)
        plan.spans.setdefault(cid, []).append(Span(round(t_in, 3), round(t, 3), fi, fade, sh))
        exited[cid] = t

    for si, (a, b, hard_end) in enumerate(shot_ranges(keys, n_frames, fps)):
        plan.shots.append((a / fps, (b - 1) / fps))
        plan.hard_end.append(hard_end)
        frames = list(range(a, b, S.sample_every_frames))
        if frames[-1] != b - 1:
            frames.append(b - 1)
        samp = []
        for f in frames:
            v = View(stage, cams[f])
            samp.append((f / fps, v, {c.id: c for c in label_candidates(ctx, stage, v, lod_w=v.w / S.lod_hysteresis)},
                         _reserved_at(ctx, v, events, f / fps)))

        def survives(cid: str, j: int) -> bool:
            for _, _, relax, res in samp[j:]:
                c = relax.get(cid)
                if c is None or (c.test is not None and _rect_hit(c.test, res)):
                    return False
            return True

        for j, (t, v, relax, res) in enumerate(samp):
            for cid in list(active):   # 기존 라벨 — 화면·이력 LOD 밖이거나 예약 상자에 덮이면 퇴장
                c = relax.get(cid)
                if c is None or (c.test is not None and _rect_hit(c.test, res)):
                    close(cid, t, True)
                else:
                    active[cid][1] = c.placed
            placed = list(res) + [x[1] for x in active.values() if x[2] != "sea"]
            n_city = sum(1 for x in active.values() if x[2] == "city")
            first = j == 0 and (si == 0 or plan.hard_end[si - 1])   # 컷·dip·영상 첫 프레임 — 페이드 없이 시작
            if j > 0:   # 카메라가 움직이는 중에는 새 라벨을 들이지 않는다 — 멈춘 뒤 한꺼번에 페이드인(UF-175 "없던게 나온다")
                v0 = samp[j - 1][1]
                if abs(v.w - v0.w) / v0.w > S.still_eps or abs(v.x0 - v0.x0) / v.w > S.still_eps:
                    continue
            for c in label_candidates(ctx, stage, v):   # 새 라벨 — 지금 규칙의 후보 차례
                if c.id in active or t - exited.get(c.id, -1e9) < S.min_hold_sec:
                    continue
                if c.kind == "city" and n_city >= cmax:
                    continue
                if c.test is not None and _rect_hit(c.test, placed):
                    continue
                if not survives(c.id, j):   # 숏 끝까지 남지 않을 라벨은 들이지 않는다(잠깐 나왔다 사라지는 것 금지)
                    continue
                active[c.id] = [t, c.placed, c.kind, not first, si]
                if c.blocks:
                    placed.append(c.placed)
                if c.kind == "city":
                    n_city += 1
        if hard_end:
            for cid in list(active):
                close(cid, (b - 1) / fps, False)
    return plan


def flicker_report(plan: LabelPlan) -> tuple[list[str], list[str]]:
    """([label-flicker] hard, [label-churn] warning). 같은 라벨이 사라진 뒤 rules labels.stability.min_hold_sec 안에 다시 나타나거나(재등장),
    보인 구간이 min_hold_sec 미만이면(컷·dip·영상 처음과 끝에 잘린 구간 제외) flicker. 한 숏 안 새 등장 수 > max_events_per_shot = churn."""
    S = load_rules().labels.stability  # noqa: N806
    hard, warn = [], []
    per_shot: dict[int, set] = {}
    for cid, ss in plan.spans.items():
        xs = sorted(ss, key=lambda s: s.t_in)
        for p, q in zip(xs, xs[1:]):
            if q.t_in - p.t_out < S.min_hold_sec:
                hard.append(f"[label-flicker] {cid} {p.t_out:.2f}초에 사라졌다가 {q.t_in:.2f}초에 다시 나타난다(재등장 — UF-175)")
        for s in xs:
            if s.fade_in and s.fade_out and s.t_out - s.t_in < S.min_hold_sec:
                hard.append(f"[label-flicker] {cid} {s.t_in:.2f}~{s.t_out:.2f}초 — {s.t_out - s.t_in:.2f}초 < {S.min_hold_sec:g}초(UF-175)")
            if s.fade_in:   # 숏 안 새 등장 시각(같은 순간 한꺼번에 = 한 번). 화면 밖으로 나가는 퇴장은 카메라 이동의 결과라 세지 않는다
                per_shot.setdefault(s.shot, set()).add(round(s.t_in, 2))
    for shot, ts in sorted(per_shot.items()):
        n = len(ts)
        if n > S.max_events_per_shot:
            t0, t1 = plan.shots[shot]
            warn.append(f"[label-churn] 숏 {shot}({t0:.1f}~{t1:.1f}초) 숏 안 새 라벨 등장 시각 {n}번 > {S.max_events_per_shot}")
    return hard, warn


def plan_from_frames(selected: list[set[str]], shots: list[tuple[int, int]], fps: float) -> LabelPlan:
    """프레임별 선택 열(옛 방식) → 일정 — 검사가 옛 방식의 깜빡임을 잡는지 증명하는 시험용."""
    plan = LabelPlan()
    for si, (a, b) in enumerate(shots):
        plan.shots.append((a / fps, (b - 1) / fps))
        plan.hard_end.append(True)
        on: dict[str, int] = {}
        for f in range(a, b):
            cur = selected[f]
            for cid in list(on):
                if cid not in cur:
                    plan.spans.setdefault(cid, []).append(Span(on.pop(cid) / fps, f / fps, True, True, si))
            for cid in cur:
                on.setdefault(cid, f)
        for cid, f0 in on.items():
            plan.spans.setdefault(cid, []).append(Span(f0 / fps, (b - 1) / fps, f0 > a, False, si))
    return plan


__all__ = ["LabelPlan", "Span", "build_plan", "flicker_report", "plan_from_frames", "shot_ranges"]

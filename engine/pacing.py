"""정적 구간 `[static-window]`·느린 푸시인(creep) — 한 곳 (v4.11.0, back_and_forth D-0118 §1, 사용자 위임 D103).

원칙: 뷰 전환이 주 도구가 아니다. 같은 뷰 안에서 '동기 있는 변화'가 이어지면 지루하지 않다. 변화는 원고가 준다(P8 —
연출은 LLM, 검사는 코드). 값은 `rules pacing.static_window`(15 P3).

- `map_segments`: 지도 무대가 화면에 보이는 구간 — 숏 무대 mercator, 전면 카드(타이틀·엔딩)·패널 덮개 밖.
- `static_windows`: 구간 안 어떤 window_sec 창 [s, s+W](닫힌 구간)이든 change_kinds 변화(이벤트 t0·카메라 키 t) < min_changes
  → 겹치는 창을 이어 붙인 범위 [t0, t1] 하나씩. changes = 그 범위 창들의 최소 변화 수.
- `creep_ranges`: creep.enabled 이고 길이 ≥ min_window_sec 인 범위 → `engine.camera.build_camera` 가 w 를 선형으로 줄인다.
검사(engine.checks static_window)·provenance(pacing)·카메라가 **같은 결과**(load_project 가 R.cache["pacing"] 에 한 번)를 쓴다.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from typing import Callable, Sequence

from rules import load_rules

STEP_SEC = 0.1   # 창 시작 격자(구간 경계·변화 시각은 이 격자로 반올림하지 않는다 — 창 끝 판정은 닫힌 구간)


_SW = load_rules().pacing.static_window   # rules SSOT(프레임마다 파일을 읽지 않게 한 번)


def map_segments(total: float, stage_at: Callable[[float], str], covered: Callable[[float], bool],
                 step: float = STEP_SEC) -> list[tuple[float, float]]:
    """지도가 보이는 연속 구간 [(a, b)]. stage_at(t) = 그 시각 숏 무대, covered(t) = 전면 카드·패널이 지도를 덮음."""
    out: list[tuple[float, float]] = []
    start: float | None = None
    n = int(round(total / step))
    for i in range(n + 1):
        t = round(i * step, 3)
        vis = stage_at(t) == "mercator" and not covered(t)
        if vis and start is None:
            start = t
        elif not vis and start is not None:
            out.append((start, round(t - step, 3)))
            start = None
    if start is not None:
        out.append((start, round(n * step, 3)))
    return out


def change_times(events: Sequence[dict], key_times: Sequence[float], kinds: Sequence[str]) -> list[tuple[float, str]]:
    """변화 [(시각, 종류)] — 이벤트는 등장 시각 t0, 카메라는 키 시각(t > 0)."""
    ks = set(kinds)
    ch = [(float(e["t0"]), str(e["type"])) for e in events if e.get("type") in ks]
    if "camera" in ks:
        ch += [(float(t), "camera") for t in key_times if t > 0]
    return sorted(ch)


def static_windows(segments: Sequence[tuple[float, float]], changes: Sequence[tuple[float, str]],
                   window_sec: float | None = None, min_changes: int | None = None, step: float = STEP_SEC) -> list[dict]:
    """정적 범위 [{t0, t1, changes, kinds}] — 구간마다 창 시작 s 를 step 격자로 밀며 [s, s+W] 안 변화 수를 센다.
    W 보다 짧은 구간은 창이 없다. 연속으로 걸린 창은 한 범위로 합친다(changes = 그 창들의 최소, kinds = 범위 안 변화 종류)."""
    sw = _SW
    W = sw.window_sec if window_sec is None else window_sec  # noqa: N806
    m = sw.min_changes if min_changes is None else min_changes
    ts = [t for t, _ in changes]
    out: list[dict] = []
    eps = 1e-6
    for a, b in segments:
        if b - a < W - eps:
            continue
        n = int((b - a - W) / step + eps)
        starts = [round(a + i * step, 6) for i in range(n + 1)]
        if starts[-1] < b - W - eps:
            starts.append(round(b - W, 6))   # 구간 끝에 붙은 마지막 창
        run: list[tuple[float, int]] = []
        for s in starts + [None]:   # type: ignore[list-item]
            c = None if s is None else bisect_right(ts, s + W + eps) - bisect_left(ts, s - eps)
            if c is not None and c < m:
                run.append((s, c))
                continue
            if run:
                t0, t1 = run[0][0], run[-1][0] + W
                i0, i1 = bisect_left(ts, t0 - eps), bisect_right(ts, t1 + eps)
                out.append({"t0": round(t0, 2), "t1": round(t1, 2), "changes": min(c_ for _, c_ in run),
                            "kinds": sorted({k for _, k in changes[i0:i1]})})
                run = []
    return out


def creep_ranges(windows: Sequence[dict]) -> list[tuple[float, float]]:
    """느린 푸시인을 걸 범위 — creep.enabled 이고 길이 ≥ min_window_sec 인 정적 범위."""
    cr = _SW.creep
    if not cr.enabled:
        return []
    return [(w["t0"], w["t1"]) for w in windows if w["t1"] - w["t0"] >= cr.min_window_sec - 1e-6]


def creep_factor(t: float, settle: float, ranges: Sequence[tuple[float, float]], w_ratio: float | None = None) -> float:
    """시각 t 의 w 배율. settle = 지금 카메라 키의 이동이 끝난 시각(이동 중엔 이 값 > t → 배율 1).
    범위 (a, b) 안에서 max(a, settle) 부터 (1 − w_ratio)/(b − a) 초당 비율로 줄고, b 뒤에는 유지 — 다음 키가 오면 settle 이
    b 뒤로 가서 1 로 돌아가는데, 그 이동은 직전 프레임(줄어든 w)에서 출발하므로 끊기지 않는다(이동이 흡수)."""
    r = _SW.creep.w_ratio if w_ratio is None else w_ratio
    f = 1.0
    for a, b in ranges:
        if t <= a:
            continue
        p = (min(t, b) - max(a, settle)) / (b - a)
        if p > 0:
            f *= 1 - (1 - r) * p
    return f


__all__ = ["STEP_SEC", "change_times", "creep_factor", "creep_ranges", "map_segments", "static_windows"]

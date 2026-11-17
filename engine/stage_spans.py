"""렌더 무대 구간(v7.4.0 R9, UF-902) — 검사가 "지금 화면에 그려진 무대"를 render_frame 과 같은 규칙으로 고르게 하는 한 곳.

한 영상이 지도(mercator) ↔ 스튜디오(studio)를 dip 으로 오가면 `P.R.stage`·`P.cams` 는 주 무대 것이고, 다른 무대는
`R.cache["stage_switch"]["alt"]` 에 (무대, 카메라 트랙)으로 있다. 검사는 이 모듈로
- 구간 [(t0, t1, 무대 이름)] 과 시각 t 의 렌더 무대(`engine.direction.stage_at` — render_frame 과 같은 함수),
- 무대 이름 → (무대, 카메라 트랙),
- 지도 층(MAP_LAYER_ORDER) 이벤트를 그리는 무대 = 전환 영상이면 지도 무대, 한 무대 영상이면 주 무대
를 얻는다. 한 무대 영상은 구간 하나(주 무대 · 0 ~ 영상 끝)라 옛 판정과 같다.
"""

from __future__ import annotations

from typing import Any, Optional

from engine.projection import View
from engine.style import FPS

Span = tuple[float, float, str]


def _switch(P: Any) -> Optional[dict]:  # noqa: N803
    cache = getattr(getattr(P, "R", None), "cache", None)
    return cache.get("stage_switch") if isinstance(cache, dict) else None


def _total(P: Any) -> float:  # noqa: N803
    plan = getattr(P, "plan", None)
    if plan is not None and getattr(plan, "total", None) is not None:
        return float(plan.total)
    return float(getattr(P, "n_frames", 0)) / FPS


def is_switching(P: Any) -> bool:  # noqa: N803
    """무대 전환 영상인가(전환점이 하나 이상)."""
    sw = _switch(P)
    return bool(sw and sw.get("track"))


def stage_spans(P: Any) -> list[Span]:  # noqa: N803
    """렌더 무대 구간 [(t0, t1, 무대 이름)] — 전환 시각 t 부터 다음 무대(render_frame 과 같다, 전환 dip 한가운데 cut).
    한 무대 영상 = [(0, 영상 끝, 주 무대)]."""
    total = _total(P)
    sw = _switch(P)
    if not sw or not sw.get("track"):
        return [(0.0, total, getattr(P.R.stage, "name", ""))]
    out: list[Span] = []
    a, cur = 0.0, sw["main"]
    for t, _f, to in sw["track"]:
        if t > a:
            out.append((a, min(t, total), cur))
        a, cur = max(a, t), to
    if total > a:
        out.append((a, total, cur))
    return out


def stage_name_at(P: Any, t: float) -> str:  # noqa: N803
    """시각 t 의 렌더 무대 이름 — render_frame 과 같은 함수(engine.direction.stage_at)."""
    sw = _switch(P)
    if not sw or not sw.get("track"):
        return getattr(P.R.stage, "name", "")
    from engine.direction import stage_at  # noqa: PLC0415

    return stage_at(sw["track"], sw["main"], t)


def stage_cams(P: Any, name: str) -> tuple[Any, Any]:  # noqa: N803
    """무대 이름 → (무대, 카메라 트랙). 주 무대 = (P.R.stage, P.cams), 보조 렌더 무대 = stage_switch alt. 한 무대 영상 = 늘 주 무대."""
    if not is_switching(P) or name == getattr(P.R.stage, "name", None):
        return P.R.stage, P.cams
    sw = _switch(P)
    if not sw or name not in sw["alt"]:
        raise KeyError(f"렌더 무대 {name!r} 가 이 영상에 없다")
    return sw["alt"][name]


def frame_index(P: Any, t: float) -> int:  # noqa: N803
    """시각 t 의 프레임 번호(검사들이 쓰던 식 — 0 ~ n_frames-1 로 자른다)."""
    return min(P.n_frames - 1, max(0, int(t * FPS)))


def rendered_view(P: Any, t: float) -> View:  # noqa: N803
    """시각 t 에 화면에 그려진 무대의 View — render_frame 과 같은 무대 선택."""
    st, cams = stage_cams(P, stage_name_at(P, t))
    return View(st, cams[frame_index(P, t)])


def layer_stage_name(P: Any) -> str:  # noqa: N803
    """지도 층 이벤트(MAP_LAYER_ORDER — 마커·경로·비행·뱃지 등)를 그리는 무대 이름 — 전환 영상 = 지도(화면 공간 무대가 아닌) 렌더 무대,
    한 무대 영상 = 주 무대(project.load_project 의 map_st 와 같은 선택)."""
    from engine.stage import screen_stage  # noqa: PLC0415

    main = getattr(P.R.stage, "name", "")
    names = [n for _a, _b, n in stage_spans(P)]
    return next((n for n in dict.fromkeys(names) if not screen_stage(n)), main) if len(set(names)) > 1 else main


def layer_stage(P: Any) -> tuple[Any, Any]:  # noqa: N803
    """지도 층 이벤트의 (무대, 카메라 트랙)."""
    return stage_cams(P, layer_stage_name(P))


def layer_view(P: Any, t: float) -> View:  # noqa: N803
    """지도 층 이벤트의 시각 t View(지도 이벤트는 지도 구간 안에만 있다 — project.bind_event_stages 가 강제)."""
    st, cams = layer_stage(P)
    return View(st, cams[frame_index(P, t)])


def frame_mask(P: Any, name: str) -> Any:  # noqa: N803
    """프레임마다 그 무대가 렌더 무대인가(bool 배열, 길이 n_frames) — render_frame 과 같은 i / FPS 판정."""
    import numpy as np  # noqa: PLC0415

    n = int(P.n_frames)
    if not is_switching(P):
        return np.full(n, name == getattr(P.R.stage, "name", None))
    return np.array([stage_name_at(P, i / FPS) == name for i in range(n)], dtype=bool)

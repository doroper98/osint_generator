"""카메라 키프레임 (v2.1.0, 19 부록 D `CAM, cam, dip, build_camera`).

장면당 이동 1회, 먼 거리는 암전 컷(05 §2). v3 의 `CUT_TARGET` 큐 방식은 순서 실수 위험이 있어
`dip(t, lon, lat, w)` 인자형으로 바꿨다(19 §3.10). 보간: 위치 선형, 폭 로그, ease_io. 도착 후 드리프트.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal, Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

from engine.pacing import creep_factor
from engine.timebase import ease_io
from rules import load_rules

if TYPE_CHECKING:
    from engine.stage import Stage

_DRIFT = load_rules().shot_grammar.drift  # amount 0.03, tau 9.0 (v3 값, rules SSOT)
_PATH = load_rules().shot_grammar.move_path   # v5.5.0 — 이동+줌 경로(rules shot_grammar.move_path)
_W_SAME = np.finfo(float).eps ** 0.5           # 폭이 사실상 같으면 순수 이동(진행률 비례)


class CamKey(BaseModel):
    """카메라 키. (x, y, w) 는 무대의 월드 좌표(v4.1.0 D-0076 — 지도 무대면 x = 경도, y = Mercator 도 단위, 변환은
    engine.stage 에만). w = 화면 가로가 덮는 월드 폭.
    """

    model_config = ConfigDict(extra="forbid")

    t: float
    x: float
    y: float
    w: float
    dur: float = 3.0
    mode: Literal["move", "cut"] = "move"


def cam(t: float, x: float, y: float, w: float, dur: float = 3.0, mode: Literal["move", "cut"] = "move") -> CamKey:
    """월드 좌표 카메라 키. 앵커(경위도 등)는 호출하는 쪽이 stage.to_world 로 바꿔 넘긴다."""
    return CamKey(t=t, x=x, y=y, w=w, dur=dur, mode=mode)


def build_camera(keys: list[CamKey], n_frames: int, fps: int,
                 creep: Sequence[tuple[float, float]] = ()) -> "np.ndarray":
    """프레임별 (x, y, w) 배열. creep = 느린 푸시인 범위(v4.11.0 D-0118 §1, engine.pacing.creep_ranges) — 드리프트와 곱한다."""
    cams = sorted(keys, key=lambda c: c.t)
    out = np.zeros((n_frames, 3))
    cur = np.array([cams[0].x, cams[0].y, cams[0].w], float)
    frm = cur.copy()
    k = 0
    act: CamKey | None = None
    for i in range(n_frames):
        t = i / fps
        while k < len(cams) and cams[k].t <= t:
            act = cams[k]
            k += 1
            frm = out[i - 1].copy() if i > 0 and act.mode != "cut" else np.array([act.x, act.y, act.w], float)
        if act is None:
            v = cur.copy()
            da = t
        else:
            e = ease_io((t - act.t) / act.dur) if act.dur > 0 else 1.0
            w = math.exp(math.log(frm[2]) + (math.log(act.w) - math.log(frm[2])) * e)
            f = e
            if _PATH == "fixed_point" and not math.isclose(act.w, frm[2], rel_tol=_W_SAME):
                f = (w - frm[2]) / (act.w - frm[2])   # v5.5.0 — 중심을 폭에 비례로 → 고정점 기준 닮음 변환(지도 흐름 직선)
            v = np.array([frm[0] + (act.x - frm[0]) * f, frm[1] + (act.y - frm[1]) * f, w])
            da = t - (act.t + act.dur)
        if da > 0:
            v[2] *= 1 - _DRIFT.amount * (1 - math.exp(-da / _DRIFT.tau_sec))
        if creep:
            v[2] *= creep_factor(t, 0.0 if act is None else act.t + act.dur, creep)
        out[i] = v
    return out


class Director:
    """연출층 도우미 — v3 상단의 `cam()`·`ev()`·`dip()` 호출을 한 객체로 모은다.

    `dip(t, lon, lat, w)`: 1초 암전(t±0.5) + 그 한가운데 카메라 cut. 컷 목적지를 인자로 받는다(19 §3.10).
    이벤트는 dict 로 모으고, 렌더 전에 `engine.registry.validate_events`가 전부 검증한다.
    """

    def __init__(self, stage: "Stage") -> None:
        self.stage = stage   # 앵커(lon·lat) → 월드 좌표(v4.1.0)
        self.keys: list[CamKey] = []
        self.events: list[dict] = []

    def cam(self, t: float, lon: float, lat: float, w: float, dur: float = 3.0,
            mode: Literal["move", "cut"] = "move") -> None:
        self.keys.append(cam(t, *self.stage.to_world(lon=lon, lat=lat), w, dur, mode))

    def ev(self, typ: str, t0: float, t1: float, **kw: object) -> dict:
        d: dict = dict(type=typ, t0=t0, t1=t1)
        d.update(kw)
        self.events.append(d)
        return d

    def dip(self, t: float, lon: float, lat: float, w: float, under: bool = False) -> None:
        if under:
            self.ev("dip", t - 0.5, t + 0.5, under=True)
        else:
            self.ev("dip", t - 0.5, t + 0.5)
        self.cam(t, lon, lat, w, 0, "cut")

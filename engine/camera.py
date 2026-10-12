"""카메라 키프레임 (v2.1.0, 19 부록 D `CAM, cam, dip, build_camera`).

장면당 이동 1회, 먼 거리는 암전 컷(05 §2). v3 의 `CUT_TARGET` 큐 방식은 순서 실수 위험이 있어
`dip(t, lon, lat, w)` 인자형으로 바꿨다(19 §3.10). 보간: 위치 선형, 폭 로그, 이징 rules shot_grammar.move_ease(v5.21.9 quintic). 도착 후 드리프트.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal, Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

from engine.pacing import creep_factor
from engine.timebase import ease_io, ease_quintic
from rules import load_rules

if TYPE_CHECKING:
    from engine.stage import Stage

_DRIFT = load_rules().shot_grammar.drift  # amount 0.03, tau 9.0 (v3 값, rules SSOT)
_PATH = load_rules().shot_grammar.move_path   # v5.5.0 — 이동+줌 경로(rules shot_grammar.move_path)
_EASE = {"cubic": ease_io, "quintic": ease_quintic}[load_rules().shot_grammar.move_ease]   # v5.21.9 D-0191 §1-1
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
            e = _EASE((t - act.t) / act.dur) if act.dur > 0 else 1.0
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


def continuity(track: "np.ndarray", cut_frames: Sequence[int] = ()) -> dict[str, "np.ndarray"]:
    """카메라 연속성 측정(v5.21.9 D-0191 §1-1) — 프레임 (x, y, w) 배열에서 ln w·x/w·y/w 의 1·2·3차 차분 절댓값.

    SK-C1(sketch.common.checks.check_camera)과 같은 식에 3차(저크)를 더했다. 3차는 이징의 가속도 뒤집힘
    (조각 3차식 한가운데 +12 → −12)을 잡는다 — 1·2차 임계로는 보이지 않던 꺾임. cut_frames(컷 키 프레임)
    앞뒤로 차분 창이 걸치는 값은 0 으로 둔다(컷은 의도된 불연속).
    """
    w = track[:, 2]
    lw = np.log(w)
    out: dict[str, np.ndarray] = {"d1 ln w": np.abs(np.diff(lw))}
    for o in (2, 3):
        out[f"d{o} ln w"] = np.abs(np.diff(lw, o))
        for k in ("x", "y"):
            out[f"d{o} {k}/w"] = np.abs(np.diff(track[:, 0 if k == "x" else 1], o)) / w[1:len(w) - o + 1]
    for k, v in out.items():
        o = int(k[1])
        for c in cut_frames:   # 차분 i 는 프레임 i..i+o 를 쓴다 → 컷 프레임 c 를 포함하는 i = c-o..c-1
            v[max(0, c - o):max(0, c)] = 0
    return out


def speed(track: "np.ndarray", cut_frames: Sequence[int] = (), fps: float = 24.0) -> dict[str, "np.ndarray"]:
    """카메라 속도(v6.0.2 UF-97 D-0216) — 프레임 (x, y, w) 배열에서 프레임 i→i+1 사이
    pan = 중심 이동 거리 ÷ 평균 w × fps(화면 폭/초), zoom = |Δ ln w| × fps(/초). 컷 키 프레임으로 들어가는 차분은 0.
    본 엔진 camera_speed 와 스케치 SK-C1 이 같은 함수·같은 규칙 키(shot_grammar.camera_speed)."""
    x, y, w = track[:, 0], track[:, 1], track[:, 2]
    pan = np.hypot(np.diff(x), np.diff(y)) / ((w[1:] + w[:-1]) / 2) * fps
    zoom = np.abs(np.diff(np.log(w))) * fps
    for c in cut_frames:
        if 0 < c <= len(pan):
            pan[c - 1] = zoom[c - 1] = 0.0
    return {"pan": pan, "zoom": zoom}


def screen_track(stage: "Stage", track: "np.ndarray", viewport: "tuple[float, float] | None" = None) -> "np.ndarray":
    """화면에 실제로 그려진 카메라(v7.1.0 UF-99 D-0220) — 프레임마다 렌더와 같은 `engine.projection.View`(무대 경계 클램프)를
    거친 뒤의 (중심 x, 중심 y, w). 카메라 검사(camera_continuity·camera_speed·스케치 SK-C1)는 이 궤적을 잰다 —
    요청 궤적(build_camera 출력)은 경계에서 잘리면 화면과 달라진다(재는 것 ≠ 보이는 것, RENDER-AP-026)."""
    from engine.projection import View  # noqa: PLC0415

    out = np.empty((len(track), 3))
    for i, c in enumerate(track):
        v = View(stage, c, viewport)
        out[i] = (v.x0 + v.w / 2, v.y1 - v.h / 2, v.w)
    return out


def bounds_excess(stage: "Stage", track: "np.ndarray", viewport: "tuple[float, float] | None" = None) -> "np.ndarray":
    """요청 궤적과 화면 궤적의 차이 ÷ 요청 w(프레임 × [x, y, w]) — 0 이 아니면 그 프레임에서 렌더가 카메라를 무대 경계로 잘랐다.
    세로 척도를 무대가 고정하는 무대(시간축, y_px_per_unit)의 y 는 무대가 정하는 값이라 0 으로 둔다(카메라가 고르는 성분이 아니다)."""
    tr = np.asarray(track, dtype=float)
    d = np.abs(screen_track(stage, tr, viewport) - tr) / tr[:, 2:3]
    if getattr(stage, "y_px_per_unit", None) is not None:
        d[:, 1] = 0.0
    return d


def max_view_w(stage: "Stage", viewport: "tuple[float, float] | None" = None) -> float:
    """이 무대에서 클램프 없이 쓸 수 있는 최대 w(View 와 같은 식)."""
    from engine.projection import View  # noqa: PLC0415

    xmin, ymin, xmax, ymax = stage.bounds
    big = View(stage, np.array([(xmin + xmax) / 2, (ymin + ymax) / 2, float("inf")]), viewport)
    return float(big.w)


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

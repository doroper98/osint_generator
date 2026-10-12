"""숏 목록 → 카메라 (x, y, w) — 스케치 공통(D-0140 §3).

x = 경도, y = 메르카토르 y(engine.stage.ym), w = 화면 가로 폭(경도 °). engine.projection.View 가 그대로 받는다.
숏 안에서는 느린 푸시인(rules sketch.camera.push_in[kind]), 숏 사이 이동은 rules shot_grammar.move_ease(본 엔진과 같은 이징, v5.21.9 D-0191 §1-1)로 위치·log w 를 보간한다.
**이동은 앞 숏이 끝난 상태(푸시인까지 들어간 w)에서 시작한다** — 원래 w 에서 다시 시작하면 전환 첫 프레임에
줌이 push_in 만큼 튄다(멈칫 사고, docs/handoff/22 §2.6). 원본: 4d9dc65 `sketch_d1.camera`·`uranus_sketch.camera`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from engine.stage import MercatorStage, ym
from engine.timebase import clamp01, ease_io, ease_quintic, smooth
from rules import load_rules
from sketch.common.spec import Shot

EPS = 1e-6
_EASE = {"cubic": ease_io, "quintic": ease_quintic}[load_rules().shot_grammar.move_ease]


@dataclass(frozen=True)
class CameraPath:
    shots: tuple[Shot, ...]
    duration_sec: float
    push_in: float          # rules sketch.camera.push_in[kind]
    hold_min_sec: float     # rules sketch.camera.hold_min_sec

    def at(self, t: float) -> tuple[float, float, float]:
        """시각 t 의 카메라 (x, y, w)."""
        sh = self.shots
        i = max(j for j, s in enumerate(sh) if t >= s.t0) if t >= sh[0].t0 else 0
        cur = sh[i]
        if i == 0:
            px, py, pw = cur.lon, ym(cur.lat), cur.w
        else:
            prev = sh[i - 1]
            px, py, pw = prev.lon, ym(prev.lat), prev.w * (1 - self.push_in)   # 앞 숏의 끝 상태
        k = _EASE(clamp01((t - cur.t0) / max(EPS, cur.t1 - cur.t0))) if cur.t1 > cur.t0 else 1.0
        x = px + (cur.lon - px) * k
        y = py + (ym(cur.lat) - py) * k
        w = math.exp(math.log(pw) + (math.log(cur.w) - math.log(pw)) * k)
        nxt = sh[i + 1].t0 if i + 1 < len(sh) else self.duration_sec
        hold = clamp01((t - cur.t1) / max(self.hold_min_sec, nxt - cur.t1))
        return x, y, w * (1 - self.push_in * smooth(hold))

    def track(self, fps: int) -> np.ndarray:
        """프레임마다 (x, y, w) 배열(n×3, 검사 SK-C1 입력). 프레임 i 의 시각 = i / fps."""
        n = int(self.duration_sec * fps)
        return np.array([self.at(i / fps) for i in range(n)])


def bounds_stage(project: Path) -> MercatorStage:
    """카메라 경계만 아는 지도 무대(v7.1.0 UF-99 D-0220) — 경계 = 프로젝트 geo.yaml 티어 W bbox(tiers.pkl·콘티 판 막지도와 같은 값).
    지형 자산 없이 SK-C1 이 화면 궤적(engine.camera.screen_track)과 경계 클램프(camera_bounds 와 같은 식)를 잰다."""
    from geo.prep import load_conf  # noqa: PLC0415

    w = next((t for t in load_conf(project).tiers if t.name == "W"), None)
    if w is None:
        raise KeyError("티어 W(광역, 카메라 경계)가 없다 — geo.yaml tiers 에 name: W 를 둔다")
    return MercatorStage(None, tiers={"W": dict(lon0=w.bbox[0], lat0=w.bbox[1], lon1=w.bbox[2], lat1=w.bbox[3])})

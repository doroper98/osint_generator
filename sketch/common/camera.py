"""숏 목록 → 카메라 (x, y, w) — 스케치 공통(D-0140 §3).

x = 경도, y = 메르카토르 y(engine.stage.ym), w = 화면 가로 폭(경도 °). engine.projection.View 가 그대로 받는다.
숏 안에서는 느린 푸시인(rules sketch.camera.push_in[kind]), 숏 사이 이동은 ease_io 로 위치·log w 를 보간한다.
**이동은 앞 숏이 끝난 상태(푸시인까지 들어간 w)에서 시작한다** — 원래 w 에서 다시 시작하면 전환 첫 프레임에
줌이 push_in 만큼 튄다(멈칫 사고, CONVENTIONS §5). 원본: 4d9dc65 `sketch_d1.camera`·`uranus_sketch.camera`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from engine.stage import ym
from engine.timebase import clamp01, ease_io, smooth
from sketch.common.spec import Shot

EPS = 1e-6


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
        k = ease_io(clamp01((t - cur.t0) / max(EPS, cur.t1 - cur.t0))) if cur.t1 > cur.t0 else 1.0
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

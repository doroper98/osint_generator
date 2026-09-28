"""뷰 — 월드 좌표 → 화면 (v4.1.0, 19 부록 D `View` 를 무대 무관으로 일반화, docs/handoff/20 §2.3, back_and_forth D-0076 작업 2).

카메라 = (x, y, w): 월드 좌표 중심과 화면 가로가 덮는 월드 폭. 월드 좌표가 무엇인지는 무대(`engine.stage`)가 정한다
(지도 = Mercator 도 단위). 이 파일은 투영 수식을 모른다 — `View(stage, cam).to_screen(x, y)` 뿐이다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from engine.style import H_OUT, W_OUT

if TYPE_CHECKING:
    from engine.stage import Stage


class View:
    """한 프레임의 뷰포트. 카메라는 무대 경계(stage.bounds) 안으로 클램프한다."""

    def __init__(self, stage: "Stage", cam: "np.ndarray") -> None:
        x, y, w = cam
        self.stage = stage
        xmin, ymin, xmax, ymax = stage.bounds
        w = min(w, xmax - xmin - 0.01, (ymax - ymin - 0.01) * W_OUT / H_OUT)
        self.w = w
        self.h = w * H_OUT / W_OUT
        self.s = W_OUT / w
        self.x0 = min(max(x - w / 2, xmin), xmax - w)
        self.y1 = min(max(y + self.h / 2, ymin + self.h), ymax)

    def to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.x0) * self.s, (self.y1 - y) * self.s

    def to_screen_arr(self, xy: "np.ndarray") -> "np.ndarray":
        return np.column_stack([(xy[:, 0] - self.x0) * self.s, (self.y1 - xy[:, 1]) * self.s])

    def to_world(self, px: float, py: float) -> tuple[float, float]:
        """to_screen 의 역(배치 슬롯 point — 화면 점 → 월드 좌표)."""
        return self.x0 + px / self.s, self.y1 - py / self.s

    def visible(self, mn: "np.ndarray", mx: "np.ndarray") -> bool:
        return not (mx[0] < self.x0 or mn[0] > self.x0 + self.w or mx[1] < self.y1 - self.h or mn[1] > self.y1)

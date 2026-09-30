"""뷰 — 월드 좌표 → 화면 (v4.1.0, 19 부록 D `View` 를 무대 무관으로 일반화, docs/handoff/20 §2.3, back_and_forth D-0076 작업 2).

카메라 = (x, y, w): 월드 좌표 중심과 화면 가로가 덮는 월드 폭. 세로 배율은 기본이 가로와 같고(등방, 지도),
무대가 `y_px_per_unit` 을 주면 그 값으로 고정한다(v4.3.0 D-0085 A — 시간축: w 는 시간 폭만, 세로 위치는 `stage.frame_y1`). 월드 좌표가 무엇인지는 무대(`engine.stage`)가 정한다
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

    def __init__(self, stage: "Stage", cam: "np.ndarray", viewport: "tuple[float, float] | None" = None) -> None:
        """viewport = 화면 안 뷰포트 (폭, 높이) 설계 px(v5.1.0 D-0126 Q1 A — 차트 아일랜드 상자). 없으면 화면 전체.
        화면 좌표는 뷰포트 왼쪽 위가 원점이다(그리는 쪽이 상자 위치로 옮긴다)."""
        x, y, w = cam
        self.stage = stage
        self.vw, self.vh = viewport if viewport is not None else (float(W_OUT), float(H_OUT))
        xmin, ymin, xmax, ymax = stage.bounds
        fixed = getattr(stage, "y_px_per_unit", None)   # v4.3.0 D-0085 A — 무대가 세로 척도를 고정(시간축). 없으면 등방(지도)
        if fixed is None:
            w = min(w, xmax - xmin - 0.01, (ymax - ymin - 0.01) * self.vw / self.vh)
            self.w = w
            self.h = w * self.vh / self.vw
            self.s = self.vw / w
            self.sy = self.s
            self.x0 = min(max(x - w / 2, xmin), xmax - w)
            self.y1 = min(max(y + self.h / 2, ymin + self.h), ymax)
        else:
            w = min(w, xmax - xmin)
            self.w = w
            self.s = self.vw / w        # 가로 배율(월드 x 1 = s px)
            self.sy = fixed             # 세로 배율(월드 y 1 = sy px)
            self.h = self.vh / fixed
            self.x0 = min(max(x - w / 2, xmin), xmax - w)
            self.y1 = stage.frame_y1(y, self.h)  # type: ignore[attr-defined]

    def to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.x0) * self.s, (self.y1 - y) * self.sy

    def to_screen_arr(self, xy: "np.ndarray") -> "np.ndarray":
        return np.column_stack([(xy[:, 0] - self.x0) * self.s, (self.y1 - xy[:, 1]) * self.sy])

    def to_world(self, px: float, py: float) -> tuple[float, float]:
        """to_screen 의 역(배치 슬롯 point — 화면 점 → 월드 좌표)."""
        return self.x0 + px / self.s, self.y1 - py / self.sy

    def visible(self, mn: "np.ndarray", mx: "np.ndarray") -> bool:
        return not (mx[0] < self.x0 or mn[0] > self.x0 + self.w or mx[1] < self.y1 - self.h or mn[1] > self.y1)

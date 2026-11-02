"""v7.4.0 사용자 결정 UF-401 ③ — route flow(영상 분석 D3 선 위를 흐르는 점).

안 쓰면 dict 옛 모양. 점은 선이 다 그려진 뒤에만, 출발 → 도착 방향으로 흐른다. 출발·도착 근처는 옅다.
"""

from __future__ import annotations

import unittest

import numpy as np

from engine.layers.routes import FLOW, flow_points
from engine.registry import validate_events

RT = {"type": "route", "t0": 0.0, "t1": 8.0, "pts": [[125.7, 39.0], [116.4, 39.9]], "grow": 1.5, "col": "ru"}
LINE = np.array([[0.0, 0.0], [100.0, 0.0], [200.0, 0.0]])


class RouteFlowTest(unittest.TestCase):
    def test_plain_route_dict_unchanged(self) -> None:
        self.assertNotIn("flow", validate_events([RT])[0])
        self.assertTrue(validate_events([{**RT, "flow": True}])[0]["flow"])

    def test_no_dots_before_line_done(self) -> None:
        self.assertEqual(flow_points(LINE, 0.0), [])

    def test_dots_move_forward(self) -> None:
        a, b = flow_points(LINE, 0.5), flow_points(LINE, 0.6)
        self.assertEqual(len(a), FLOW.dots)
        da = [x for x, _, _ in a]
        db = [x for x, _, _ in b]
        moved = [q - p for p, q in zip(da, db) if q > p]   # 끝을 넘어 처음으로 돌아간 점은 뺀다
        self.assertTrue(moved and all(m > 0 for m in moved))
        self.assertTrue(all(0 <= x <= 200 for x in da))

    def test_edges_fade(self) -> None:
        pts = flow_points(LINE, 1e-3)
        self.assertLess(min(k for _, _, k in pts), 1.0)


if __name__ == "__main__":
    unittest.main()

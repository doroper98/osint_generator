"""v7.4.0 사용자 결정 UF-401 ③ — network 선 shape drop(영상 분석 D13 가계 내림선).

같은 열끼리 잇는 선은 drop 일 때만 허용. 내림선은 다른 선과 같은 시간에 자라며, 꺾은선 길이 비율로 그린다.
"""

from __future__ import annotations

import unittest

from engine.panels.network import partial_polyline
from engine.registry import RegistryError, validate_events

NODES = [{"id": "a", "col": "center", "kind": "flag", "flag": "kp", "label": "위"},
         {"id": "b", "col": "center", "kind": "flag", "flag": "kp", "label": "아래"},
         {"id": "c", "col": "right", "kind": "flag", "flag": "kr", "label": "옆"}]
NET = {"type": "panel", "kind": "network", "t0": 0.0, "t1": 10.0, "title": "가계", "nodes": NODES,
       "provenance": {"verification": "verified", "sources": ["시험 예시"]}}


class NetworkDropTest(unittest.TestCase):
    def test_same_column_only_with_drop(self) -> None:
        with self.assertRaises(RegistryError):
            validate_events([{**NET, "edges": [{"src": "a", "dst": "b", "type": "related"}]}])
        out = validate_events([{**NET, "edges": [{"src": "a", "dst": "b", "type": "related", "shape": "drop"}]}])[0]
        self.assertEqual(out["edges"][0]["shape"], "drop")

    def test_partial_polyline(self) -> None:
        path = [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0)]
        self.assertEqual(partial_polyline(path, 0.0), [(0.0, 0.0)])
        self.assertEqual(partial_polyline(path, 0.5)[-1], (0.0, 10.0))
        self.assertEqual(partial_polyline(path, 0.75)[-1], (5.0, 10.0))
        self.assertEqual(partial_polyline(path, 1.0)[-1], (10.0, 10.0))


if __name__ == "__main__":
    unittest.main()


class NetworkCrowdTest(unittest.TestCase):
    """v7.4.0 UF-401 ③(영상 분석 D4) — 노드 crowd 점 고리. 점 수는 장식(수치 아님) — rules per_ring 합과 같다."""

    def test_dots_count_and_rings(self) -> None:
        from engine.panels.network import N, crowd_dots  # noqa: PLC0415

        dots = crowd_dots(0.0, 0.0, 30.0)
        self.assertEqual(len(dots), sum(N.crowd.per_ring))
        r_in = min((x * x + y * y) ** (1 / 2) for x, y, i in dots if i == 0)
        r_out = max((x * x + y * y) ** (1 / 2) for x, y, i in dots if i == N.crowd.rings - 1)
        self.assertGreater(r_out, r_in)
        self.assertGreater(r_in, 30.0)

    def test_crowd_field(self) -> None:
        nodes = [{**NODES[0], "crowd": True}, NODES[2]]
        out = validate_events([{**NET, "nodes": nodes, "edges": [{"src": "a", "dst": "c", "type": "related"}]}])[0]
        self.assertTrue(out["nodes"][0]["crowd"])

    def test_drop_column_spacing(self) -> None:
        from engine.panels.network import N, layout  # noqa: PLC0415

        e = validate_events([{**NET, "edges": [{"src": "a", "dst": "b", "type": "related", "shape": "drop"}]}])[0]
        plain = validate_events([{**NET, "edges": [{"src": "a", "dst": "c", "type": "related"}]}])[0]
        gap = layout(e)["b"][1] - layout(e)["a"][1]
        self.assertAlmostEqual(gap, N.dy * N.drop.dy_scale)
        self.assertAlmostEqual(layout(plain)["b"][1] - layout(plain)["a"][1], N.dy)

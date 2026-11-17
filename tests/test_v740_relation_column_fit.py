"""관계 패널 노드 열이 디자인 시스템 종이 안에 머문다 (v7.4.0 D935, RENDER-AP-040).

대상 다섯 곳(panels.relation.target cy 262·dy 62·R 19)의 다섯째 원이 흰 종이 아래 끝(402)에 걸린 채 전달 직전까지 갔다
(nvidia-chips-china-2026 프리뷰 v2). 넘치지 않는 열은 종전 좌표 그대로다.
"""

from __future__ import annotations

import unittest

from engine.panels.relation import RelationOverflowError, column_ys
from rules import load_rules

R = load_rules()
REL = R.panels.relation
B = R.skin.panel.relation
BAND = (B.y_min, B.y_max, B.gap_min)


class ColumnFitTest(unittest.TestCase):
    def test_no_band_is_legacy_geometry(self) -> None:
        t = REL.target
        self.assertEqual(column_ys(5, t.cy, t.dy, t.R, None), [t.cy - 2 * t.dy + i * t.dy for i in range(5)])

    def test_columns_that_fit_keep_their_coordinates(self) -> None:
        t, s = REL.target, REL.source
        for n in (1, 2, 3, 4):
            with self.subTest(targets=n):
                self.assertEqual(column_ys(n, t.cy, t.dy, t.R, BAND), column_ys(n, t.cy, t.dy, t.R, None))
        self.assertEqual(column_ys(1, s.cy, s.dy, s.R, BAND), [s.cy])

    def test_five_targets_stay_inside_the_paper(self) -> None:
        t = REL.target
        ys = column_ys(5, t.cy, t.dy, t.R, BAND)
        self.assertGreaterEqual(ys[0] - t.R, B.y_min - 1e-6)
        self.assertLessEqual(ys[-1] + t.R, B.y_max + 1e-6)
        steps = {round(b - a, 6) for a, b in zip(ys, ys[1:])}
        self.assertEqual(len(steps), 1, "간격은 고르게")
        self.assertGreaterEqual(steps.pop(), 2 * t.R + B.gap_min)

    def test_too_many_nodes_is_error(self) -> None:
        t = REL.target
        with self.assertRaises(RelationOverflowError):
            column_ys(9, t.cy, t.dy, t.R, BAND)


if __name__ == "__main__":
    unittest.main()

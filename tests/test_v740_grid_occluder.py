"""v7.4.0 back_and_forth D-0344(UF-155) — [grid-text-cross] 가림 조건. 글자 아래에 실제로 그린 판의 알파가
rules qa_checks.grid_text_cross.occluder_alpha_min 이상이고 교차 구간을 다 덮으면 가려진 것. 라벨 종류로 건너뛰지 않는다 — 판의 측정값으로 판정."""

from __future__ import annotations

import unittest

from engine import checks
from rules import load_rules

SEG = [(100.0, 50.0, 300.0)]                       # 세로 격자선 x=100, y 50~300
BOX = [("끝값 라벨(policy_rate)", (90.0, 170.0, 130.0, 182.0))]
PLATE = (86.0, 166.0, 134.0, 186.0)                # 글자 + pad 4


class OccluderTest(unittest.TestCase):
    def test_no_plate_is_hard(self) -> None:
        self.assertEqual(len(checks.grid_text_crossings(SEG, 1.0, BOX)), 1)

    def test_opaque_plate_hides(self) -> None:
        self.assertEqual(checks.grid_text_crossings(SEG, 1.0, BOX, [(1.0, PLATE)]), [])

    def test_translucent_plate_still_hard(self) -> None:
        self.assertEqual(len(checks.grid_text_crossings(SEG, 1.0, BOX, [(0.72, PLATE)])), 1)   # 옛 판 알파

    def test_plate_must_cover_crossing(self) -> None:
        small = (95.0, 172.0, 125.0, 180.0)        # 교차 구간(169~183)을 다 덮지 못한다
        self.assertEqual(len(checks.grid_text_crossings(SEG, 1.0, BOX, [(1.0, small)])), 1)

    def test_rule_values(self) -> None:
        r = load_rules()
        self.assertEqual(r.qa_checks.grid_text_cross.occluder_alpha_min, 0.98)
        self.assertGreaterEqual(r.stage_timeline.series.end_label_plate.alpha, r.qa_checks.grid_text_cross.occluder_alpha_min)
        self.assertIn("chart_overload", r.qa_checks.regression_ref_checks)


if __name__ == "__main__":
    unittest.main()

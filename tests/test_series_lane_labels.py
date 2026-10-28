"""한 레인에 레코드 둘 이상 — 끝값 라벨 세로 분산·띠 라벨 없음·레인당 출처 한 줄 (v7.4.0, back_and_forth D-0256).

showcase_econ 콘티 판 v1 에서 금리 레인(목표 범위 띠 + 실효금리 계단) 오른쪽 끝 라벨이 "3.'3.63%" 로 겹치고 출처 줄 두 줄이 겹쳤다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine.layers import series as S
from engine.style import TIMELINE


class EndLabelSpreadTest(unittest.TestCase):
    def test_two_labels_in_one_lane_do_not_cross(self) -> None:
        """레코드 둘의 끝값 라벨 기준선이 같은 자리면 값 순으로 갈라져 간격 ≥ end_label_min_gap_px(작은 값이 아래)."""
        gap = TIMELINE.series.end_label_min_gap_px
        R = NS(cache={})  # noqa: N806
        y1 = S.place_end_label(R, 1.0, "policy_rate", 100.0, 4.0)
        R.cache["series_end_labels"]["lanes"]["policy_rate"].append((y1, 4.0, (0, y1 - 12, 40, y1)))
        y2 = S.place_end_label(R, 1.0, "policy_rate", 102.0, 3.63)
        self.assertGreaterEqual(abs(y2 - y1), gap)
        self.assertGreater(y2, y1)   # 작은 값 = 화면 아래(y 큼)
        y3 = S.place_end_label(R, 1.0, "inflation", 101.0, 3.35)   # 다른 레인은 그대로
        self.assertEqual(y3, 101.0)
        y4 = S.place_end_label(R, 2.0, "policy_rate", 100.0, 4.0)   # 다음 프레임은 새로 센다
        self.assertEqual(y4, 100.0)

    def test_lane_source_single_line(self) -> None:
        """레인 출처 줄은 load_project 가 붙인 lane_source(레인 전체) — 없으면 이벤트 자신의 출처."""
        self.assertEqual(S.lane_source_text({"lane_source": "A · 2026년 9월 기준 · B"}), "A · 2026년 9월 기준 · B")

    def test_rules_key(self) -> None:
        self.assertGreaterEqual(TIMELINE.series.end_label_min_gap_px, TIMELINE.series.value_size)

    def test_check_is_hard(self) -> None:
        from engine import checks

        self.assertIn("series_label_overlap", checks.HARD)


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 back_and_forth D-1010(사용자 의견 UF-305·UF-306) — 아일랜드 안쪽 여백·레인 미리 보기 선.

UF-305 원문: "차트를 감싸는 외곽 라인이 너무 타이트하게 붙어있는 점"
UF-306 원문: "첨부한 이미지의 빈 아래쪽 차트를 흐릿한 선으로라도 한번 보여주고 있으면 좋을것 같다"
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from engine.island import inner_box
from engine.stage_structure import StructureStage
from engine.style import ISLAND, TIMELINE


class InnerPadTest(unittest.TestCase):
    def test_rule_values(self) -> None:
        self.assertEqual(ISLAND.inner_pad, {"x": 16.0, "y": 12.0})
        self.assertEqual(inner_box((60, 52, 734, 344)), (76, 64, 702, 320))

    def test_structure_fits_inner_area(self) -> None:
        st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                    "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "t"})
        self.assertEqual((st.bw, st.bh), (702.0, 320.0))

    def test_preview_v2_flush_header_fails(self) -> None:
        """프리뷰 v2 상태 재현 — 여백 없이(뷰포트 = 상자) 머리 줄 오른쪽 끝이 상자 끝에 붙음 = 오류, 여백 안이면 통과."""
        head = [("total:2", (500.0, 4.0, 733.0, 17.0))]
        self.assertTrue(checks.inner_pad_hits(head, (734.0, 344.0), (734.0, 344.0)))
        self.assertEqual(checks.inner_pad_hits([("total:2", (480.0, 4.0, 701.0, 17.0))], (702.0, 320.0), (734.0, 344.0)), [])


class LanePreviewTest(unittest.TestCase):
    def _P(self) -> NS:  # noqa: N802
        lanes = [NS(id="bal"), NS(id="debt")]
        ser = [{"type": "series", "lane": "bal", "style": "line", "t0": 238.0, "t1": 282.0},
               {"type": "series", "lane": "debt", "style": "line", "t0": 262.2, "t1": 282.0}]
        isl = {"type": "island", "kind": "chart", "t0": 238.0, "t1": 282.0}
        return NS(R=NS(cache={"island_chart": {"stage": NS(lanes=lanes), "events": ser}}), events=[isl, *ser])

    def test_rule_values(self) -> None:
        self.assertEqual(TIMELINE.lane_preview, {"alpha": 0.35, "w": 1.2})

    def test_preview_covers_lanes(self) -> None:
        self.assertEqual(checks.check_lane_empty(self._P()), [])

    def test_preview_v2_act3_4_state_fails(self) -> None:
        """프리뷰 v2 act3_4 재현 — 미리 보기 없음이면 아래 국가채무 레인이 238~262초 빈 틀 = 오류."""
        with mock.patch.dict(TIMELINE.lane_preview, {"alpha": 0.0}):
            out = checks.check_lane_empty(self._P())
        self.assertTrue(out and "debt" in out[0])


if __name__ == "__main__":
    unittest.main()

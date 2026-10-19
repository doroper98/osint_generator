"""v7.4.0 back_and_forth D-0248(사용자 의견 UF-129 "그래프 넣는 씬에서 오른쪽 상단 아일랜드가 그래프를 가리지 않도록 해") — [card-over-panel] hard."""

from __future__ import annotations

import unittest

from engine import checks as C

PANEL = {"type": "panel", "kind": "dual_line", "title": "그래프", "t0": 10.0, "t1": 20.0}
TOP_RIGHT = (560.0, 60.0, 840.0, 160.0)   # 오른쪽 상단 카드 자리


def _boxes(e: dict) -> list[tuple] | None:
    return [TOP_RIGHT] if e["type"] == "card" else None


class CardOverPanelTest(unittest.TestCase):
    def test_card_on_panel_is_hard(self) -> None:
        card = {"type": "card", "tag": "수치", "t0": 12.0, "t1": 16.0}
        self.assertEqual(len(C.cards_over_panel([PANEL, card], _boxes)), 1)
        self.assertIn("card_over_panel", C.HARD)

    def test_card_ending_before_panel_passes(self) -> None:
        card = {"type": "card", "tag": "수치", "t0": 6.0, "t1": 10.5}   # 패널 페이드 안에서 끝남
        self.assertEqual(C.cards_over_panel([PANEL, card], _boxes), [])

    def test_date_badge_and_subtitles_only(self) -> None:
        self.assertEqual(C.cards_over_panel([PANEL], _boxes), [])
        badge = {"type": "badge", "kind": "flag", "t0": 12.0, "t1": 16.0}   # 지도 뱃지는 패널 덮개 아래(검사 대상 아님)
        self.assertEqual(C.cards_over_panel([PANEL, badge], _boxes), [])

    def test_article_counts_as_cover(self) -> None:
        art = {"type": "article", "mid": "a", "t0": 11.0, "t1": 15.0}
        self.assertEqual(len(C.cards_over_panel([PANEL, art], _boxes)), 1)


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 back_and_forth D-0248·D-0249(사용자 의견 UF-129 "그래프 넣는 씬에서 오른쪽 상단 아일랜드가 그래프를 가리지 않도록 해") — [card-over-panel] hard."""

from __future__ import annotations

import unittest

from engine import checks as C

PANEL = {"type": "panel", "kind": "dual_line", "title": "그래프", "t0": 10.0, "t1": 20.0,
         "series": [{"label": "x", "col": "ru", "values": [1, 2], "record": "RU_REFINERY_RUNS_2026"}]}   # 데이터 패널(record 보유)
STORY = {"type": "panel", "kind": "timeline", "title": "해협의 일곱 달", "t0": 10.0, "t1": 20.0}            # 서사 패널
TOP_RIGHT = (560.0, 60.0, 840.0, 160.0)   # 오른쪽 상단 카드 자리


def _boxes(e: dict) -> list[tuple] | None:
    return [TOP_RIGHT] if e["type"] == "cascade" else None


class CardOverPanelTest(unittest.TestCase):
    def test_card_on_panel_is_hard(self) -> None:
        card = {"type": "cascade", "tag": "수치", "t0": 12.0, "t1": 16.0}
        self.assertEqual(len(C.cards_over_panel([PANEL, card], _boxes)), 1)
        self.assertIn("card_over_panel", C.HARD)

    def test_card_ending_before_panel_passes(self) -> None:
        card = {"type": "cascade", "tag": "수치", "t0": 6.0, "t1": 10.5}   # 패널 페이드 안에서 끝남
        self.assertEqual(C.cards_over_panel([PANEL, card], _boxes), [])

    def test_date_badge_and_subtitles_only(self) -> None:
        self.assertEqual(C.cards_over_panel([PANEL], _boxes), [])   # 날짜 배지·자막은 이벤트가 아니다

    def test_media_on_data_panel_hard_story_panel_ok(self) -> None:   # D-0249(D260)
        photo = {"type": "photo", "mid": "p", "t0": 12.0, "t1": 16.0}
        self.assertEqual(len(C.cards_over_panel([PANEL, photo], _boxes)), 1)
        self.assertEqual(C.cards_over_panel([STORY, photo], _boxes), [])   # 골든 v3 서사 패널 위 사진·영상 유지
        badge = {"type": "badge", "kind": "flag", "t0": 12.0, "t1": 16.0}
        self.assertEqual(len(C.cards_over_panel([PANEL, badge], _boxes)), 1)
        vs = {"type": "panel", "kind": "versus", "title": "양측", "t0": 10.0, "t1": 20.0, "series": [{"record": "X"}]}
        self.assertEqual(C.cards_over_panel([vs, badge], _boxes), [])   # versus 위 뱃지는 badge_over_panel 이 보고

    def test_article_counts_as_cover(self) -> None:
        art = {"type": "article", "mid": "a", "t0": 11.0, "t1": 15.0}
        self.assertEqual(len(C.cards_over_panel([PANEL, art], _boxes)), 1)


if __name__ == "__main__":
    unittest.main()

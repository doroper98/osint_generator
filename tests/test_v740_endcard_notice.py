"""v7.4.0 back_and_forth D-0229 §2.10(D237 비차단 관찰) — 엔딩 카드: 표기 전용 줄(slot notice), 긴 항목 열 폭 줄바꿈."""

from __future__ import annotations

import types
import unittest
from unittest import mock

from engine import fullcards as fc
from engine.credits import CreditSection
from engine.typography import adv
from rules import load_rules

E = load_rules().layout_480p.end_card


class WrapTest(unittest.TestCase):
    def test_short_one_line(self) -> None:
        self.assertEqual(fc.item_lines("로이터", 0), ["로이터"])

    def test_long_wraps_within_column(self) -> None:
        m = "NNK(Independent Petroleum Company) 자산 보고서 · 하바롭스크 정유소 처리 능력과 2026년 1~8월 가동 현황 요약"
        ls = fc.item_lines(m, 0)
        self.assertGreater(len(ls), 1)
        self.assertTrue(all(adv(x, E.item_size, "sans") <= fc.COL_W[0] for x in ls))

    def test_layout_pushes_next_row(self) -> None:
        long = " ".join(["가나다라"] * 40)
        (_, _, _, _, rows), = fc.endcard_layout([("출처", [(long, ""), ("다음", "")])], [0])[0]
        self.assertGreater(rows[1][2] - rows[0][2], 14)


class NoticeSlotTest(unittest.TestCase):
    def _R(self) -> types.SimpleNamespace:  # noqa: N802
        secs = [CreditSection(title="출처", column=0, items=[{"main": "AP"}]),
                CreditSection(title="표기", column=1, slot="notice", items=[{"main": "비행 경로는 개략 표현", "license": "51%는 우크라이나 측 발표"}])]
        return types.SimpleNamespace(credits=types.SimpleNamespace(sections=secs), assets=types.SimpleNamespace(rights={}, media={}), cache={})

    def test_notice_out_of_columns(self) -> None:
        R = self._R()  # noqa: N806
        fake = [("출처", [("AP", "")]), ("표기", [("비행 경로는 개략 표현", "51%는 우크라이나 측 발표")])]
        with mock.patch.object(fc, "credit_sections", return_value=fake):
            self.assertEqual(fc.credit_place(R), [0])
            self.assertEqual([t for t, _ in fc.project_credit_sections(R)], ["출처"])
            self.assertEqual(fc.notice_line(R), "비행 경로는 개략 표현 · 51%는 우크라이나 측 발표")


if __name__ == "__main__":
    unittest.main()

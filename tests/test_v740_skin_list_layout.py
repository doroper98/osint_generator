"""목록 패널(checklist)의 디자인 시스템 조판 (v7.4.0 사용자 의견 UF-919, D936).

사용자 원문(2026-11-17): "저 조판이 그냥 마음에 안들기도 해. 저 표현 방식만 리팩터링 해. 디자인적으로 우수하게."
옛 조판 = 번호 칸(상자)을 두른 줄 목록. 새 조판 = 번호 · 굵은 항목 · 오른쪽 덧말 · 가는 선 · 강조 막대, 꼬리말은 종이 안.
"""

from __future__ import annotations

import unittest

from engine.panels import checklist
from rules import load_rules

R = load_rules()
L = R.skin.panel.list
MAX_ITEMS = 4   # engine.events.PanelChecklist.items max_length


def _ev(n: int = 4, footer: str | None = "모형 추정 — 적발률 가정에 따라 달라진다") -> dict:
    items = [f"항목 {i + 1} — 덧말 {i + 1}" for i in range(n)]
    return {"type": "panel", "kind": "checklist", "style": "open", "title": "제목", "t0": 10.0, "t1": 30.0, "items": items,
            "at": [10.5 + i for i in range(n)], "footer": footer}


class SkinListLayoutTest(unittest.TestCase):
    def test_boxed_number_layout_is_gone(self) -> None:
        self.assertFalse(hasattr(R.skin.panel, "check"), "번호 칸 조판의 규칙 키(skin.panel.check)가 되살아났다")
        self.assertFalse(hasattr(checklist, "_check"), "번호 칸을 그리던 함수가 되살아났다")

    def test_rows_are_centered_and_keep_fixed_positions(self) -> None:
        for n in range(1, MAX_ITEMS + 1):
            ys = checklist.skin_rows(_ev(n))
            self.assertAlmostEqual((ys[0] + ys[-1]) / 2, L.cy, places=6)
            self.assertTrue(all(abs((b_ - a_) - L.pitch) < 1e-9 for a_, b_ in zip(ys, ys[1:])))
            self.assertGreater(ys[0] - L.pitch / 2, R.layout_480p.panel.subtitle_y, "첫 줄이 패널 제목·부제에 닿는다")

    def test_footer_sits_below_the_last_row(self) -> None:
        last = checklist.skin_rows(_ev(MAX_ITEMS))[-1]
        self.assertGreater(L.footer.y - L.footer.size, last + L.pitch / 2 - 1e-9, "꼬리말이 마지막 줄(구분선)과 겹친다")

    def test_footer_appears_with_the_panel_not_after_the_items(self) -> None:
        e = _ev(4)
        rv = dict((name.split(" ")[0], tf) for name, tf in checklist.skin_reveals(e))
        self.assertLess(rv["꼬리말"], e["t0"] + 2.0, "꼬리말이 항목 뒤에 늦게 뜬다(UF-917 — 뜨자마자 패널이 사라졌다)")

    def test_item_splits_into_head_and_note(self) -> None:
        head, _, note = "게인 AI 법 — 미국 고객 우선 공급".partition(checklist.SPLIT)
        self.assertEqual((head, note), ("게인 AI 법", "미국 고객 우선 공급"))


if __name__ == "__main__":
    unittest.main()

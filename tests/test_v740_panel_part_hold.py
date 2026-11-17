"""패널 안에서 늦게 나타나는 부분의 노출 시간 [panel-part-hold] (v7.4.0 사용자 의견 UF-917·UF-919, D936).

사용자 원문(2026-11-17): "아래에 모형추정 이라고 써있는 글씨가 나오자 마자 다음 씬으로 넘어가 사라짐." ·
"이 씬도 이상하게 네번째 항목이 나오자 마자 다음 씬으로 넘어가."
[element-hold](UF-171)는 요소 전체만 봤다 — 패널 안에서 따로 나타나는 꼬리말·마지막 항목은 어떤 검사도 보지 않았다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine import checks, skin
from engine.panel_parts import PANEL_REVEALS, part_holds, reveals
from rules import load_rules

R = load_rules()
LO = R.qa_checks.panel_part_hold.min_sec
NO_LATE_PARTS = {"dots", "gantt", "dual_line"}   # 값 차트 — 선·막대가 패널 시작부터 자란다(따로 늦게 뜨는 글 없음)


def _epoch(t1: float, footer: str | None = "모형 추정 — 적발률 가정에 따라 달라진다") -> dict:
    """nvidia-chips-china-2026 완성본의 목록 패널(사용자가 짚은 장면) — 시작 186.14, 항목 187.74·189.04."""
    return {"type": "panel", "kind": "checklist", "style": "open", "title": "Epoch AI의 밀반입 추정", "t0": 186.14, "t1": t1,
            "items": ["중앙값 66만 개 (H100 환산)", "90% 구간 29만 ~ 160만 개"], "at": [187.74, 189.04], "footer": footer}


def _run(events: list[dict]) -> list[str]:
    return checks.check_panel_part_hold(SimpleNamespace(events=events))


class PanelPartHoldTest(unittest.TestCase):
    def setUp(self) -> None:
        skin.apply(None)

    def tearDown(self) -> None:
        skin.apply(None)

    def test_registered_hard(self) -> None:
        self.assertIn("panel_part_hold", checks.HARD)

    def test_user_case_footer_flashes(self) -> None:
        out = _run([_epoch(191.44)])
        self.assertTrue(any("꼬리말" in x for x in out), out)
        self.assertTrue(all(x.startswith("[panel-part-hold]") for x in out))
        self.assertLess(dict((n.split(" ")[0], h) for n, h in part_holds(_epoch(191.44)))["꼬리말"], 0, "꼬리말이 다 뜨기도 전에 패널이 사라진다")

    def test_long_enough_panel_passes(self) -> None:
        self.assertEqual(_run([_epoch(198.0)]), [])

    def test_skin_layout_shows_footer_early_but_last_item_still_checked(self) -> None:
        skin.apply("studio")
        names = [n for n, h in part_holds(_epoch(191.44)) if h < LO]
        self.assertFalse(any(n.startswith("꼬리말") for n in names), "새 조판의 꼬리말은 패널과 함께 일찍 뜬다(UF-917)")
        self.assertTrue(any(n.startswith("항목 2") for n in names), "마지막 항목은 여전히 본다(UF-919)")
        self.assertEqual(_run([_epoch(194.0)]), [])

    def test_versus_last_item(self) -> None:
        e = {"type": "panel", "kind": "versus", "title": "두 연구기관의 추정", "t0": 251.6, "t1": 261.0,
             "sides": [{"title": "밀반입", "items": [{"text": "66만 개", "t": 252.8}]}, {"title": "원격 임차", "items": [{"text": "100만 개", "t": 257.68}]}]}
        self.assertEqual(len(_run([e])), 1)
        self.assertEqual(_run([{**e, "t1": 262.0}]), [])

    def test_other_events_are_ignored(self) -> None:
        self.assertEqual(reveals({"type": "photo", "mid": "x", "t0": 0, "t1": 3}), [])
        self.assertEqual(_run([{"type": "badge", "t0": 0, "t1": 1}]), [])

    def test_every_panel_kind_is_covered_or_listed(self) -> None:
        kinds = set(R.registries.panel_kinds)
        self.assertEqual(kinds - set(PANEL_REVEALS) - NO_LATE_PARTS, set(), "새 패널 종류는 부분 노출 시각(engine.panel_parts)을 같이 정한다")


if __name__ == "__main__":
    unittest.main()

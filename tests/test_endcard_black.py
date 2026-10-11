"""v5.22.3 UF-35(D-0205 §3) — 엔딩 카드 뒤~끝 검정(endcard_black hard): 프레임을 실제로 그려 잰다."""

from __future__ import annotations

import unittest
from unittest import mock

import pytest

from engine.checks import HARD
from rules import load_rules
from tests.anti_inertia._ast_util import REPO

PROJ = REPO / "projects" / "hormuz_korea"


class TestRule(unittest.TestCase):
    def test_registered(self) -> None:
        self.assertIn("endcard_black", HARD)
        self.assertLess(load_rules().layout_480p.end_card.after_max_luma, 0.1)


@pytest.mark.slow   # C8.3(D187) — 프로젝트 로드·프레임 렌더
class TestHormuz(unittest.TestCase):
    def setUp(self) -> None:
        if not (PROJ / "plan.json").exists() or not (PROJ / "assets" / "geo.pkl").exists():
            raise RuntimeError("hormuz 자산 없음 — docs/handoff/reports/phase6_5/run_log.md §0")
        from engine.project import load_project  # noqa: PLC0415

        self.P = load_project(PROJ)

    def test_golden_end_is_black(self) -> None:
        from engine.checks import check_endcard_black, endcard_black_samples  # noqa: PLC0415

        self.assertEqual(len(endcard_black_samples(self.P)), 3)
        self.assertEqual(check_endcard_black(self.P), [])

    def test_regression_detected(self) -> None:
        """옛 결함 재현 — 검정 유지(hold_black_after)를 끄고 카드가 영상 끝 3초 전에 끝나면 지도가 다시 보인다 → hard."""
        from engine import fullcards  # noqa: PLC0415
        from engine.checks import check_endcard_black  # noqa: PLC0415

        end = next(c for c in self.P.R.tb.plan.cards if c.kind == "end")
        old = end.t1
        off = fullcards.END_CARD.model_copy(update={"hold_black_after": False})
        try:
            object.__setattr__(end, "t1", self.P.plan.total - 3.0)
            with mock.patch.object(fullcards, "END_CARD", off):
                out = check_endcard_black(self.P)
        finally:
            object.__setattr__(end, "t1", old)
        self.assertTrue(out and out[0].startswith("[endcard-black]"), out)

if __name__ == "__main__":
    unittest.main()

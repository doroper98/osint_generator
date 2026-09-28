"""checks `[label-hidden-by-card]` (v3.6.0, back_and_forth D-0068).

마커 라벨이 카드 영역 때문에 흐려진(알파 < 0.5) 시간 ÷ 마커 표시 시간 > `qa_checks.label_hidden_max_ratio` 이면 overlap hard.
설계된 숨김(D36 marker_label_strategy: hide)을 연출 LLM 이 오류로 받게 한다(NB23 과 같은 검사기 구멍).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from rules import load_rules

HORMUZ = Path(__file__).resolve().parent.parent / "projects" / "hormuz_korea"
_HAS = (HORMUZ / "assets" / "tiers.pkl").exists() and (HORMUZ / "plan.json").exists()


class RatioRuleTest(unittest.TestCase):
    def _P(self) -> NS:  # noqa: N802
        return NS(events=[{"type": "marker", "label": "모스크바", "t0": 52.8, "t1": 60.0}])

    def test_rule_value(self) -> None:
        self.assertEqual(load_rules().qa_checks.label_hidden_max_ratio, 0.5)

    def test_boundary(self) -> None:
        """비율이 정확히 임계면 통과, 넘으면 hard."""
        with mock.patch.object(checks, "label_hidden_ratio", return_value=(0.5, ["card:x"])):
            self.assertEqual(checks.check_label_hidden(self._P()), [])
        with mock.patch.object(checks, "label_hidden_ratio", return_value=(0.51, ["card:x"])):
            out = checks.check_label_hidden(self._P())
        self.assertEqual(len(out), 1)
        self.assertIn("[label-hidden-by-card]", out[0])
        self.assertIn("모스크바", out[0])
        self.assertIn("card:x", out[0])
        self.assertIn("자리를 옮겨라", out[0])

    def test_only_markers(self) -> None:
        P = NS(events=[{"type": "badge", "label": "b", "t0": 0, "t1": 1}])  # noqa: N806
        with mock.patch.object(checks, "label_hidden_ratio", return_value=(1.0, [])) as m:
            self.assertEqual(checks.check_label_hidden(P), [])
        m.assert_not_called()


@unittest.skipIf(not _HAS or checks.missing_fonts(), "hormuz 자산·글꼴 없음(run_log §0)")
class HormuzRegressionTest(unittest.TestCase):
    def test_hormuz_zero(self) -> None:
        """v3 합격본(D36 hide 전략 포함)은 hard 0 — 사용자 합격 영상과 임계가 충돌하지 않는다(D-0068 요건 2)."""
        from engine.project import load_project  # noqa: PLC0415

        P = load_project(HORMUZ)  # noqa: N806
        self.assertEqual(checks.check_label_hidden(P), [])
        ratios = [checks.label_hidden_ratio(P, e)[0] for e in P.events if e["type"] == "marker"]
        self.assertGreater(len(ratios), 5)
        self.assertLessEqual(max(ratios), load_rules().qa_checks.label_hidden_max_ratio)


if __name__ == "__main__":
    unittest.main()

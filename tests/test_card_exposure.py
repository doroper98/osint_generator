"""v5.21.10 D-0191 §1-2 — 기사·인용 카드 완전 노출 ≥ qa_checks.card_full_exposure_min_sec(사용자 의견: 0.5초도 안 돼 사라짐)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine.checks import HARD, check_card_exposure
from engine.layers.article import article_full_span, article_phase
from engine.quote import quote_alpha, quote_full_span
from rules import load_rules

MIN = load_rules().qa_checks.card_full_exposure_min_sec


def _art(t0: float, t1: float) -> dict:
    return {"type": "article", "t0": t0, "t1": t1, "mid": "m"}


def _quote(t0: float, t1: float) -> dict:
    return {"type": "quote", "t0": t0, "t1": t1, "speaker": "s"}


class TestSpans(unittest.TestCase):
    def test_rule_value(self) -> None:
        self.assertEqual(MIN, 2.5)
        self.assertIn("card_exposure", HARD)

    def test_article_span_matches_drawing(self) -> None:
        """구간 안 = 글자 알파 1, 구간 밖 바로 옆 = 1 미만(그리기와 같은 식)."""
        e = _art(10.0, 20.0)
        a, b = article_full_span(e)
        for t in (a + 1e-3, (a + b) / 2, b - 1e-3):
            self.assertAlmostEqual(article_phase(t, e)[1], 1.0, places=3)
        self.assertLess(article_phase(a - 0.05, e)[1], 1.0)
        self.assertLess(article_phase(b + 0.05, e)[1], 1.0)

    def test_quote_span_matches_drawing(self) -> None:
        e = _quote(5.0, 12.0)
        a, b = quote_full_span(e)
        self.assertAlmostEqual(quote_alpha((a + b) / 2, e), 1.0, places=3)
        self.assertAlmostEqual(quote_alpha(a + 1e-3, e), 1.0, places=3)
        self.assertLess(quote_alpha(a - 0.05, e), 1.0)


class TestCheck(unittest.TestCase):
    def test_gulf_opening_card_fails(self) -> None:
        """gulf 본영상 첫 기사(art_0001, 10.52~12.92) — 옛 전환(UF-159 전) 완전 노출 0.40초 → hard. v7.4.0 D-0325 전환 ×1.5 뒤에는 0초대.
        기대값은 그리는 함수(article_full_span)에서 — 전환 규칙 값이 바뀌어도 같은 판정."""
        e = _art(10.52, 12.92)
        out = check_card_exposure(SimpleNamespace(events=[e]))
        self.assertEqual(len(out), 1)
        a, b = article_full_span(e)
        self.assertTrue(out[0].startswith(f"[card-exposure] article m 완전 노출 {max(0.0, b - a):.2f}초"), out[0])

    def test_boundary_and_quote(self) -> None:
        a0, a1 = article_full_span(_art(0.0, 0.0))
        need = MIN - (a1 - a0)   # 완전 노출이 정확히 MIN 이 되는 길이
        ok = check_card_exposure(SimpleNamespace(events=[_art(0.0, need)]))
        bad = check_card_exposure(SimpleNamespace(events=[_art(0.0, need - 0.05), _quote(0.0, 2.0), _quote(5.0, 9.0)]))
        self.assertEqual(ok, [])
        self.assertEqual(len(bad), 2)
        self.assertTrue(any(s.startswith("[card-exposure] quote s") for s in bad))

    def test_other_events_ignored(self) -> None:
        ev = [{"type": "badge", "t0": 0.0, "t1": 0.5}, {"type": "cascade", "t0": 0.0, "t1": 0.5}]
        self.assertEqual(check_card_exposure(SimpleNamespace(events=ev)), [])

    def test_direction_grammar_line(self) -> None:
        """연출 프롬프트에 한 줄(P3 — 규칙 파일에서만)."""
        self.assertEqual(sum("[card-exposure]" in g for g in load_rules().direction_grammar), 1)


if __name__ == "__main__":
    unittest.main()

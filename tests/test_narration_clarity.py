"""내레이션 명료도(v7.4.0 back_and_forth D-0626·D-0628) — 목소리 음역 내레이션 대 (음악+효과음) 에너지 비 하한.

UF-256 으로 장르 하한을 푼 곡(코리올란)의 가림 위험을 실제 믹스에서 잰다. 임계 rules audio.qa.narration_clarity.min_db(15 dB),
hard_genres(전쟁사)는 hard, 그 밖 장르는 warning(narration_clarity_note — 승격은 최종 감독). 실측 근거(R-0331):
호르무즈 골든 21.92 · 칸나이 v1 16.27 · 칸나이+코리올란(세기 조정 전) 12.24 dB. 효과음이 든 믹스면 효과음도 가리는 쪽으로 센다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from audio.qa import SR, narration_clarity
from engine.checks import check_narration_clarity
from rules import load_rules


def _sent(sid: str, t0: float, t1: float) -> dict:
    return {"sid": sid, "t0": t0, "t1": t1}


class ClarityMeasureTest(unittest.TestCase):
    def setUp(self) -> None:
        n = SR * 4
        t = np.arange(n) / SR
        self.vo = (0.3 * np.sin(2 * np.pi * 800 * t)).astype(np.float32)        # 목소리 음역 안
        self.music_mid = (0.3 * np.sin(2 * np.pi * 1200 * t)).astype(np.float32)   # 같은 음역 = 가림
        self.music_low = (0.3 * np.sin(2 * np.pi * 80 * t)).astype(np.float32)     # 음역 밖 = 가리지 않음

    def test_masking_in_band_lowers_ratio(self) -> None:
        s = [_sent("a", 0.5, 3.5)]
        loud = narration_clarity(self.vo + self.music_mid, self.vo, s)["a"]
        low = narration_clarity(self.vo + self.music_low, self.vo, s)["a"]
        self.assertLess(loud, 3.0)       # 같은 세기·같은 음역 ≈ 0 dB
        self.assertGreater(low, 30.0)    # 음역 밖 음악은 명료도를 거의 깎지 않는다

    def test_quieter_music_raises_ratio(self) -> None:
        s = [_sent("a", 0.5, 3.5)]
        a = narration_clarity(self.vo + self.music_mid, self.vo, s)["a"]
        b = narration_clarity(self.vo + 0.1 * self.music_mid, self.vo, s)["a"]
        self.assertAlmostEqual(b - a, 20.0, delta=0.5)   # 음악 −20 dB → 명료도 +20 dB


class ClaritySeverityTest(unittest.TestCase):
    def _p(self, genre: str, min_db: float) -> SimpleNamespace:
        return SimpleNamespace(R=SimpleNamespace(cache={"genre": {"name": genre},
                                                        "narration_clarity": {"min_db": min_db, "worst": [("x_1", min_db)], "sentences": 1}}))

    def test_threshold_and_genre_split(self) -> None:
        cfg = load_rules().audio.qa.narration_clarity
        self.assertEqual(cfg.min_db, 15.0)
        low = 12.24   # 칸나이+코리올란 세기 조정 전
        self.assertTrue(check_narration_clarity(self._p("war_history", low), hard=True))
        self.assertEqual(check_narration_clarity(self._p("war_history", low), hard=False), [])
        self.assertTrue(check_narration_clarity(self._p("no_such_genre", low), hard=False))   # hard_genres 밖 = warning 쪽(경로는 남긴다)
        self.assertEqual(check_narration_clarity(self._p("no_such_genre", low), hard=True), [])
        for ok in (21.92, 16.27):   # 골든·칸나이 v1 통과
            self.assertEqual(check_narration_clarity(self._p("war_history", ok), hard=True), [])

    def test_all_registered_genres_hard(self) -> None:
        """v7.4.0 D349 — 모든 장르 hard. 등록 장르(genres/*.yaml) ⊆ hard_genres, 그래서 warning 쪽(narration_clarity_note)은 0."""
        from genres.load import genre_names  # noqa: PLC0415

        cfg = load_rules().audio.qa.narration_clarity
        names = genre_names()
        self.assertTrue(names)
        self.assertLessEqual(set(names), set(cfg.hard_genres), "새 장르는 rules audio.qa.narration_clarity.hard_genres 에 넣는다(D349)")
        low = 12.24
        for g in names:
            self.assertTrue(check_narration_clarity(self._p(g, low), hard=True), g)
            self.assertEqual(check_narration_clarity(self._p(g, low), hard=False), [], g)   # narration_clarity_note = 0

    def test_no_mix_no_finding(self) -> None:
        P = SimpleNamespace(R=SimpleNamespace(cache={"genre": {"name": "war_history"}, "narration_clarity": None}))  # noqa: N806
        self.assertEqual(check_narration_clarity(P, hard=True), [])


if __name__ == "__main__":
    unittest.main()

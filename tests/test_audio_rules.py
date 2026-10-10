"""audio 규칙 이관(v3.4.0, D-0060 §0) — 코덱 상수 일치·v3 값 보존."""

from __future__ import annotations

import unittest

from rules import load_rules


class AudioRulesTest(unittest.TestCase):
    def test_sample_rate_matches_codec_constants(self) -> None:
        from audio.mix import SR as MIX_SR  # noqa: PLC0415
        from audio.qa import SR as QA_SR  # noqa: PLC0415
        from engine.mux import SR as MUX_SR  # noqa: PLC0415

        sr = load_rules().audio.sample_rate
        self.assertEqual(MIX_SR, sr)
        self.assertEqual(MUX_SR, sr)
        self.assertEqual(QA_SR, sr)

    def test_user_approved_bed_values_unchanged(self) -> None:
        """사용자 합격 베드·덕킹(10 §3) — duck 0.5 는 바꾸지 않는다(D-0060 §3). bed_gain 은 v5.17.0 D-0169(D163)에서
        0.47(edge InJoon 피크 정규화 기준) → 0.43(Supertonic M3 재보정 — 같은 음악/내레이션 균형 ≈ −9.8 dB)."""
        a = load_rules().audio
        self.assertEqual((a.bed_gain, a.duck_depth), (0.43, 0.5))


if __name__ == "__main__":
    unittest.main()

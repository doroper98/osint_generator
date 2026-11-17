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
        """사용자 결정 값 — 바꾸려면 사용자 지적 → 규칙 개정(C0.2). 이력: bed_gain 0.47 → 0.43(v5.17.0 D163, Supertonic 재보정, duck 0.5)
        → v7.4.0 사용자 의견 UF-922(D937 "배경음악이 나레이션을 방해하는 수준이야. 아예 아주 낮게 죽여놔. 나레이션의 사이사이에 볼륨을 키우는
        노력을 기울일 필요 없어"): 0.057, 문장 사이 복귀 없음(duck_depth 0)."""
        a = load_rules().audio
        self.assertEqual((a.bed_gain, a.duck_depth), (0.057, 0.0))


if __name__ == "__main__":
    unittest.main()

"""음악 베드는 아주 낮게, 내레이션 사이에서도 같은 높이 (v7.4.0 사용자 의견 UF-922, D937).

사용자 원문(2026-11-17): "배경음악이 나레이션을 방해하는 수준이야. 아예 아주 낮게 죽여놔. 나레이션의 사이사이에 볼륨을 키우는 노력을 기울일 필요 없어"
옛 믹서는 문장이 끝나면 덕킹을 풀어 음악을 6 dB 올렸다(duck_depth 0.5). 문장 사이 0.9초마다 음악이 솟았다.
"""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import numpy as np

from rules import load_rules

AU = load_rules().audio
SR = AU.sample_rate


def _db(x: np.ndarray) -> float:
    return 20 * math.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-12)


def _mix(tmp: Path, depth: float | None = None) -> np.ndarray:
    """내레이션을 무음으로 둔 믹스 — 나오는 소리는 음악 베드뿐이다(문장 구간 3~7초·11~15초, 사이 7~11초)."""
    import audio.mix as am  # noqa: PLC0415

    np.save(tmp / "s.npy", np.zeros(SR * 4, np.float32))
    plan = NS(total=20.0, sentences=[NS(npy=str(tmp / "s.npy"), t0=3.0, t1=7.0), NS(npy=str(tmp / "s.npy"), t0=11.0, t1=15.0)],
              cards=[], scene_start={"a": 0.0})
    snd = am.Sound.model_validate({"bgm": "music.x", "intensity": [(0.0, 0.6), (20.5, 0.6)]})
    t = np.arange(SR * 30) / SR
    raw = np.stack([np.sin(2 * np.pi * 440 * t) * 0.5] * 2, 1).astype(np.float32)
    if depth is None:
        y, _ = am.mix(plan, snd, raw)
    else:
        with mock.patch.object(am, "AU", AU.model_copy(update={"duck_depth": depth})):
            y, _ = am.mix(plan, snd, raw)
    return y[:, 0]


class BedFlatLowTest(unittest.TestCase):
    def test_bed_does_not_rise_between_sentences(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            y = _mix(Path(d))
        under = _db(y[int(4 * SR):int(6 * SR)])     # 문장 안
        gap = _db(y[int(8 * SR):int(10 * SR)])      # 문장 사이
        self.assertAlmostEqual(gap, under, delta=0.2, msg="음악이 문장 사이에서 올라간다(UF-922)")

    def test_old_ducking_would_have_risen(self) -> None:
        """장치가 실제로 그 문제를 재는지 — 옛 값(duck_depth 0.5)이면 문장 사이가 약 6 dB 높다."""
        with tempfile.TemporaryDirectory() as d:
            y = _mix(Path(d), depth=0.5)
        self.assertGreater(_db(y[int(8 * SR):int(10 * SR)]) - _db(y[int(4 * SR):int(6 * SR)]), 5.0)

    def test_rule_values(self) -> None:
        self.assertEqual(AU.duck_depth, 0.0)
        self.assertLessEqual(AU.bed_gain, 0.06)

    def test_too_loud_music_is_hard(self) -> None:
        """내레이션 구간 음악이 범위 위 끝(−20.5 dB)보다 크면 오디오 QA 가 hard 를 낸다 — mux 가 멈춘다."""
        from audio.qa import AudioQA  # noqa: PLC0415

        lo, hi = AU.qa.music_under_narration_db
        self.assertLessEqual(hi, -20.0)
        q = AudioQA(mix_peak=0.5, narration_rms_db=-17.7, music_rms_in_narration_db=-34.1, music_under_narration_db=-16.4,
                    narration_seconds=1, music_level_ok=False, peak_ok=True)
        self.assertTrue(any("내레이션 구간 음악" in x for x in q.issues()))


if __name__ == "__main__":
    unittest.main()

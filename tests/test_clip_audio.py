"""클립 원음 트랙 (v7.4.0, back_and_forth D-0274 §2③·D-0276, 사용자 의견 UF-141 "영상에 대한 목소리도 들리도록 해").

main 클립 = 원음 피크 narration_peak × main_gain_db, 그 구간 음악 베드 bed_duck_db. broll = broll_gain_db. 내레이션이 겹치면 narration_duck_db 더.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from audio import mix as M

SR = M.SR
C = M.AU.clip


def _tone(sec: float) -> np.ndarray:
    t = np.arange(int(sec * SR)) / SR
    a = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    return np.stack([a, a], 1)


class ClipTrackTest(unittest.TestCase):
    def test_values(self) -> None:
        self.assertEqual((C.main_gain_db, C.broll_gain_db, C.narration_duck_db, C.bed_duck_db, C.duck_fade_sec), (0, -18, -18, -18, 0.3))

    def test_main_full_broll_low_and_bed_mark(self) -> None:
        n = 20 * SR
        clips = [M.ClipTrack(mid="a", role="main", t0=2.0, t1=8.0, pcm=_tone(8)), M.ClipTrack(mid="b", role="broll", t0=12.0, t1=16.0, pcm=_tone(6))]
        out, main = M.clip_track(clips, n, np.zeros(n, np.float32))
        pk_main = np.abs(out[int(4 * SR):int(6 * SR), 0]).max()
        pk_broll = np.abs(out[int(13 * SR):int(15 * SR), 0]).max()
        self.assertAlmostEqual(pk_main, M.AU.narration_peak, places=2)
        self.assertAlmostEqual(pk_broll / pk_main, M.db(C.broll_gain_db), places=2)
        self.assertEqual(main[int(5 * SR)], 1.0)
        self.assertEqual(main[int(14 * SR)], 0.0)   # broll 은 베드를 낮추지 않는다
        self.assertEqual(np.abs(out[int(9 * SR):int(11 * SR)]).max(), 0.0)   # 이벤트 밖 무음(길이 = 이벤트)

    def test_narration_ducks_clip(self) -> None:
        n = 10 * SR
        duck = np.zeros(n, np.float32)
        duck[int(4 * SR):int(6 * SR)] = 1
        out, _ = M.clip_track([M.ClipTrack(mid="a", role="broll", t0=1.0, t1=9.0, pcm=_tone(8))], n, duck)
        free = np.abs(out[int(2 * SR):int(3 * SR), 0]).max()
        under = np.abs(out[int(4.5 * SR):int(5.5 * SR), 0]).max()
        self.assertAlmostEqual(under / free, M.db(C.narration_duck_db), places=2)

    def test_missing_wav_is_error(self) -> None:
        ev = [{"type": "clip", "mid": "niovi", "role": "main", "t0": 1.0, "t1": 7.0}]
        with self.assertRaisesRegex(ValueError, "클립 원음 없음"):
            M.load_clips(Path("/nonexistent_proj"), ev)


if __name__ == "__main__":
    unittest.main()

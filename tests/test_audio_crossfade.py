"""곡 교체 교차 페이드(v3.4.0, D-0060 작업 5, 10 §7-3) — 합성 사인 픽스처(미사용 CC BY 곡은 파일이 없어 시연 불가)."""

from __future__ import annotations

import unittest

import numpy as np
from pydantic import ValidationError

from audio.mix import SR, bed, crossfade_weights, segment_bed
from rules import load_rules

AU = load_rules().audio
USED = "music.zabriskie_patriarch"


def _sine(hz: float, sec: float) -> np.ndarray:
    t = np.arange(int(sec * SR)) / SR
    y = (np.sin(2 * np.pi * hz * t) * 0.5).astype(np.float32)
    return np.stack([y, y], 1)


class CrossfadeTest(unittest.TestCase):
    def test_weights_sum_to_one_and_fade_length(self) -> None:
        n = int(20 * SR)
        w = crossfade_weights([0.0, 10.0], n)
        self.assertTrue(np.allclose(w.sum(0), 1.0, atol=1e-6))
        ramp = np.nonzero((w[1] > 0) & (w[1] < 1))[0]
        self.assertAlmostEqual((ramp[-1] - ramp[0] + 1) / SR, AU.crossfade_sec, delta=2 / SR)
        self.assertAlmostEqual((ramp[0] + ramp[-1]) / 2 / SR, 10.0, delta=2 / SR)   # 경계 가운데 정렬

    def test_segment_bed_continuous(self) -> None:
        n = int(20 * SR)
        y = segment_bed([(0.0, _sine(220, 30)), (10.0, _sine(330, 30))], n)
        d = np.abs(np.diff(y[:, 0]))
        step_max = 2 * np.pi * 330 / SR * 1.05          # 사인 한 샘플 최대 변화(정규화 뒤 진폭 1) + 여유
        self.assertLess(float(d.max()), step_max)          # 경계에 튀는 불연속 없음
        mid = int(10 * SR)
        self.assertGreater(float(np.abs(y[mid - SR // 4: mid + SR // 4, 0]).max()), 0.3)   # 교차 구간에 소리 끊김 없음

    def test_single_segment_equals_plain_bed(self) -> None:
        """문자열 1곡 = 목록 1곡(from 0) — 같은 베드."""
        n = int(12 * SR)
        raw = _sine(220, 30)
        self.assertTrue(np.array_equal(segment_bed([(0.0, raw)], n), bed(raw, n)))

    def test_too_close_segments_error(self) -> None:
        with self.assertRaises(ValueError):
            segment_bed([(0.0, _sine(220, 10)), (AU.crossfade_sec / 2, _sine(330, 10))], int(10 * SR))


class SegmentSchemaTest(unittest.TestCase):
    def _s(self, bgm: object) -> object:
        from engine.direction import Sound  # noqa: PLC0415

        return Sound.model_validate({"bgm": bgm, "intensity": [[0, 0.5], [1, 0.0]]})

    def test_string_equals_one_item_list(self) -> None:
        a, b = self._s(USED), self._s([{"id": USED}])
        self.assertEqual(a.music_ids(), b.music_ids())
        self.assertEqual([g.id for g in a.segments()], [g.id for g in b.segments()])

    def test_list_rules(self) -> None:
        self._s([{"id": USED}, {"id": USED, "from": {"scene_start": "b"}}])
        for bad in ([], [{"id": USED, "from": 5}], [{"id": "music.nope"}], [{"id": USED, "at": 0}]):
            with self.assertRaises(ValidationError):
                self._s(bad)


if __name__ == "__main__":
    unittest.main()

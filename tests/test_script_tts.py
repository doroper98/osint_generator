"""TTS 트림 오프셋·ElevenLabs 요청 형태 (v2.3.0, back_and_forth D-0021 작업 3). 네트워크 없음."""

from __future__ import annotations

import os
import unittest
from unittest import mock

import numpy as np

from script.schema import PlanSentence
from script.tts import elevenlabs
from script.tts.cache import cache_key
from script.tts.trim import PRE_SEC, SR, trim


class TrimOffsetTest(unittest.TestCase):
    def test_offset_is_leading_cut(self) -> None:
        a = np.zeros(SR * 2, np.float32)
        a[SR: SR + SR // 2] = 0.5          # 1.0초에 소리 시작
        out, start = trim(a)
        self.assertAlmostEqual(start / SR, 1.0 - PRE_SEC, places=4)
        self.assertLess(len(out), len(a))

    def test_offset_zero_when_sound_at_start(self) -> None:
        a = np.full(SR, 0.5, np.float32)
        _, start = trim(a)
        self.assertEqual(start, 0)

    def test_plan_sentence_trim_offset_optional(self) -> None:
        base = dict(sid="a_0", scene="a", date="2026", text="t", tts="t", segments=[("t", 0)],
                    mp3="x.mp3", npy="x.npy", dur=1.0, t0=0.0, t1=1.0)
        self.assertIsNone(PlanSentence.model_validate(base).trim_offset)
        self.assertEqual(PlanSentence.model_validate({**base, "trim_offset": 0.12}).trim_offset, 0.12)


class ElevenRequestTest(unittest.TestCase):
    def test_body_has_context_and_settings(self) -> None:
        body = elevenlabs.request_body("가", "앞", "뒤")
        self.assertEqual(body["previous_text"], "앞")
        self.assertEqual(body["next_text"], "뒤")
        self.assertIn("stability", body["voice_settings"])
        body = elevenlabs.request_body("가", None, None)
        self.assertNotIn("previous_text", body)
        self.assertNotIn("next_text", body)

    def test_voice_label_truncated(self) -> None:
        with mock.patch.dict(os.environ, {"ELEVENLABS_VOICE_ID": "abcdefghijkl"}):
            self.assertEqual(elevenlabs.voice_label(), "elevenlabs:abcd…")
            self.assertNotIn("efgh", elevenlabs.voice_label())

    def test_cache_key_salted_by_voice(self) -> None:
        self.assertNotEqual(cache_key("가나다", None), cache_key("가나다", "v1"))
        self.assertNotEqual(cache_key("가나다", "v1"), cache_key("가나다", "v2"))


if __name__ == "__main__":
    unittest.main()

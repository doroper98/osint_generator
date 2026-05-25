"""forced-alignment 백엔드 선택 + graceful 폴백 테스트.

실제 정렬(whisper)은 모델 가중치 + 실제 음성이 필요해 사용자 머신 전용이라, 여기선
백엔드 선택과 폴백(None 반환) 경로만 검증한다. 어떤 경우도 예외 없이 None 으로 흡수.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from orchestrator.subtitle_align import align_backend, align_cues, alignment_enabled
from schemas.models import SubtitleCue


class TestSubtitleAlign(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("OSINT_ALIGN_BACKEND", None)

    def tearDown(self) -> None:
        os.environ.pop("OSINT_ALIGN_BACKEND", None)

    def _cues(self):
        return [SubtitleCue(text="첫 문장.", startSec=0.0, durationSec=1.0)]

    def test_default_backend_is_none(self) -> None:
        self.assertEqual(align_backend(), "none")
        self.assertFalse(alignment_enabled())

    def test_none_backend_returns_none(self) -> None:
        # 백엔드 미설정 → 정렬 안 함(호출자가 비례 큐 유지).
        self.assertIsNone(align_cues(self._cues(), Path("/no/such.wav")))

    def test_enabled_but_audio_missing_returns_none(self) -> None:
        os.environ["OSINT_ALIGN_BACKEND"] = "whisper"
        self.assertTrue(alignment_enabled())
        self.assertIsNone(align_cues(self._cues(), Path("/no/such.wav")))

    def test_enabled_empty_audio_returns_none(self) -> None:
        os.environ["OSINT_ALIGN_BACKEND"] = "whisper"
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            self.assertIsNone(align_cues(self._cues(), Path(f.name)))  # 0바이트(무음/stub) → 폴백

    def test_unknown_backend_returns_none(self) -> None:
        os.environ["OSINT_ALIGN_BACKEND"] = "madeup"
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF....")  # 비어있지 않은 파일
            name = f.name
        try:
            self.assertIsNone(align_cues(self._cues(), Path(name)))  # 미지원 백엔드 → 폴백
        finally:
            os.unlink(name)


if __name__ == "__main__":
    unittest.main()

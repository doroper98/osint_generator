"""수직 슬라이스 V4 — TTS 백엔드 추상화 + build-audio CLI (stub 백엔드).

full_script → 나레이션 wav + audio_manifest.json. 백엔드 교체 가능성(stub/local/
elevenlabs)을 stub 로 검증한다. local/elevenlabs 는 엔진/키/네트워크가 필요해 단위
테스트 대상이 아니며 미설정 시 명확히 실패하는지만 확인.

실행: python -m unittest tests.test_audio_flow
"""

from __future__ import annotations

import contextlib
import wave
from pathlib import Path

from orchestrator.audio_service import build_audio
from orchestrator.main import main as cli_main
from schemas.models import AudioManifest, ProjectState
from tests.test_script_flow import _ScriptHarness
from workers.tts_backends import TTSError, get_backend


class _AudioHarness(_ScriptHarness):
    def _advance_to_script(self) -> None:
        from tests.test_script_flow import VALID_SCRIPT_JSON

        self._advance_to_research_in_progress()
        self._stub(VALID_SCRIPT_JSON)
        self.assertEqual(cli_main(["build-script", "demo3"]), 0)
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SCRIPT_WRITING.value,
        )


class TestStubBackend(_AudioHarness):
    def test_stub_writes_wav_with_duration(self) -> None:
        backend = get_backend("stub")
        out = Path(self._tmp.name) / "x.wav"
        dur = backend.synthesize("안녕하세요 테스트 나레이션입니다.", out, None)
        self.assertTrue(out.exists())
        self.assertGreater(dur, 0)
        with contextlib.closing(wave.open(str(out), "rb")) as w:
            self.assertEqual(w.getnchannels(), 1)
            self.assertAlmostEqual(w.getnframes() / w.getframerate(), dur, places=1)

    def test_unknown_backend_raises(self) -> None:
        with self.assertRaises(TTSError):
            get_backend("nope")

    def test_local_backend_without_cmd_raises(self) -> None:
        import os

        os.environ.pop("OSINT_TTS_CMD", None)
        with self.assertRaises(TTSError):
            get_backend("local").synthesize("t", Path(self._tmp.name) / "y.wav", None)

    def test_elevenlabs_without_key_raises(self) -> None:
        import os

        os.environ.pop("ELEVENLABS_API_KEY", None)
        with self.assertRaises(TTSError):
            get_backend("elevenlabs").synthesize("t", Path(self._tmp.name) / "z.wav", None)

    def test_voicebox_backend_registered(self) -> None:
        from workers.tts_backends import BACKEND_CHOICES, VoiceboxTTSBackend

        self.assertIn("voicebox", BACKEND_CHOICES)
        self.assertIsInstance(get_backend("voicebox"), VoiceboxTTSBackend)

    def test_voicebox_without_profile_raises(self) -> None:
        import os

        os.environ.pop("OSINT_VOICEBOX_PROFILE", None)
        # profile 미지정 → 네트워크 호출 전에 TTSError (테스트가 localhost 를 안 침).
        with self.assertRaises(TTSError):
            get_backend("voicebox").synthesize("t", Path(self._tmp.name) / "v.wav", None)


class TestBuildAudioCLI(_AudioHarness):
    def test_build_audio_stub_creates_manifest_and_wavs(self) -> None:
        self._advance_to_script()
        rc = cli_main(["build-audio", "demo3", "--backend", "stub"])
        self.assertEqual(rc, 0)

        path = self.projects_root / "demo3" / "08_audio" / "audio_manifest.json"
        self.assertTrue(path.exists())
        manifest = AudioManifest.model_validate_json(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.backend, "stub")
        self.assertEqual(len(manifest.segments), 3)
        self.assertGreater(manifest.total_duration_sec, 0)
        # 각 세그먼트 wav 가 실제로 생성됨.
        for seg in manifest.segments:
            wav = self.projects_root / "demo3" / seg.audio_path
            self.assertTrue(wav.exists(), f"missing wav: {wav}")
        # segment_id 가 full_script 와 대응.
        self.assertEqual(
            [s.segment_id for s in manifest.segments], ["seg_01", "seg_02", "seg_03"]
        )

    def test_build_audio_via_service_default_local_without_cmd_errors(self) -> None:
        import os

        self._advance_to_script()
        os.environ.pop("OSINT_TTS_CMD", None)
        # 기본 backend=local 인데 OSINT_TTS_CMD 미설정 → CLI exit 1.
        rc = cli_main(["build-audio", "demo3"])
        self.assertEqual(rc, 1)

    def test_missing_full_script_errors(self) -> None:
        self._create_demo3()
        self.assertEqual(cli_main(["build-audio", "demo3", "--backend", "stub"]), 1)

    def test_invalid_project_id_rejected(self) -> None:
        self.assertEqual(cli_main(["build-audio", "../etc", "--backend", "stub"]), 1)

    def test_service_total_matches_segment_sum(self) -> None:
        self._advance_to_script()
        manifest = build_audio("demo3", backend="stub")
        self.assertAlmostEqual(
            manifest.total_duration_sec,
            sum(s.duration_sec for s in manifest.segments),
            places=1,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()

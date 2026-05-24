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


class _MockVoiceboxServer:
    """Voicebox 모양의 가짜 로컬 서버 (POST /generate → wav). 통합 테스트용.

    실제 Voicebox 의 신경망 합성은 흉내내지 않고, 문서화된 요청 계약
    (`{text, profile_id, language}`)을 받아 무음 wav 를 반환한다. 우리 voicebox 백엔드
    → audio_manifest 의 HTTP/파일/길이측정 경로가 실제 소켓에서 도는지 검증한다.
    """

    def __init__(self, *, as_json_base64: bool = False) -> None:
        import http.server

        self.as_json_base64 = as_json_base64
        self.requests: list[dict] = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):  # noqa: ANN001, D401
                pass

            def do_POST(self):  # noqa: N802
                import json as _json
                import wave as _wave
                from io import BytesIO

                length = int(self.headers.get("content-length", 0))
                body = _json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append({"path": self.path, "body": body})

                # 텍스트 길이에 비례한 무음 wav 생성 (실제 합성 대체).
                text = body.get("text", "")
                n = max(1, len(text) * 320)  # 16kHz 기준 대략적 프레임 수
                buf = BytesIO()
                with _wave.open(buf, "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(16000)
                    w.writeframes(b"\x00\x00" * n)
                wav_bytes = buf.getvalue()

                if outer.as_json_base64:
                    import base64

                    payload = _json.dumps(
                        {"audio": base64.b64encode(wav_bytes).decode("ascii")}
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("content-type", "application/json")
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.send_response(200)
                    self.send_header("content-type", "audio/wav")
                    self.send_header("content-length", str(len(wav_bytes)))
                    self.end_headers()
                    self.wfile.write(wav_bytes)

        self._Handler = Handler

    def __enter__(self) -> str:
        import http.server
        import threading

        self._srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self._Handler)
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True)
        self._thread.start()
        port = self._srv.server_address[1]
        return f"http://127.0.0.1:{port}"

    def __exit__(self, *exc) -> None:
        self._srv.shutdown()
        self._srv.server_close()
        self._thread.join(timeout=5)


class TestVoiceboxIntegration(_AudioHarness):
    """voicebox 백엔드를 Voicebox-모양 mock 서버에 물려 전 체인 검증 (실 소켓)."""

    def _set_voicebox_env(self, url: str) -> None:
        import os

        for k in ("OSINT_VOICEBOX_URL", "OSINT_VOICEBOX_PROFILE", "OSINT_VOICEBOX_LANG"):
            self.addCleanup(lambda k=k: os.environ.pop(k, None))
        os.environ["OSINT_VOICEBOX_URL"] = url
        os.environ["OSINT_VOICEBOX_PROFILE"] = "test_profile"

    def test_voicebox_audio_bytes_response(self) -> None:
        self._advance_to_script()
        with _MockVoiceboxServer() as url:
            self._set_voicebox_env(url)
            rc = cli_main(["build-audio", "demo3", "--backend", "voicebox"])
            self.assertEqual(rc, 0, "voicebox(audio/wav) 백엔드 build-audio 실패")

        manifest = AudioManifest.model_validate_json(
            (self.projects_root / "demo3" / "08_audio" / "audio_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest.backend, "voicebox")
        self.assertEqual(len(manifest.segments), 3)
        for seg in manifest.segments:
            self.assertGreater(seg.duration_sec, 0)
            self.assertTrue((self.projects_root / "demo3" / seg.audio_path).exists())

    def test_voicebox_json_base64_response(self) -> None:
        self._advance_to_script()
        with _MockVoiceboxServer(as_json_base64=True) as url:
            self._set_voicebox_env(url)
            manifest = build_audio("demo3", backend="voicebox", voice="p1")
        # JSON+base64 응답 경로도 wav 로 복원되어 길이 측정됨.
        self.assertEqual(len(manifest.segments), 3)
        self.assertTrue(all(s.duration_sec > 0 for s in manifest.segments))

    def test_voicebox_request_follows_documented_contract(self) -> None:
        # mock 이 받은 요청이 POST /generate {text, profile_id, language} 계약을 따르는지.
        import os

        from workers.tts_backends import get_backend

        server = _MockVoiceboxServer()
        with server as url:
            for k in ("OSINT_VOICEBOX_URL", "OSINT_VOICEBOX_PROFILE", "OSINT_VOICEBOX_LANG"):
                self.addCleanup(lambda k=k: os.environ.pop(k, None))
            os.environ["OSINT_VOICEBOX_URL"] = url
            os.environ["OSINT_VOICEBOX_LANG"] = "ko"
            out = Path(self._tmp.name) / "vb.wav"
            dur = get_backend("voicebox").synthesize("테스트 문장", out, "prof_42")

        self.assertGreater(dur, 0)
        self.assertTrue(out.exists())
        self.assertEqual(len(server.requests), 1)
        req = server.requests[0]
        self.assertEqual(req["path"], "/generate")
        self.assertEqual(req["body"]["text"], "테스트 문장")
        self.assertEqual(req["body"]["profile_id"], "prof_42")
        self.assertEqual(req["body"]["language"], "ko")


class _MockElevenLabsServer:
    """ElevenLabs 모양 mock 서버: GET /v1/voices + POST /v1/text-to-speech/{id} → PCM."""

    def __init__(self) -> None:
        import http.server

        self.requests: list[dict] = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):  # noqa: ANN001
                pass

            def do_GET(self):  # noqa: N802
                import json as _json

                outer.requests.append({"method": "GET", "path": self.path,
                                       "headers": dict(self.headers)})
                if self.path.startswith("/v1/voices"):
                    body = _json.dumps(
                        {"voices": [{"voice_id": "auto_voice_1", "name": "Default"}]}
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("content-type", "application/json")
                    self.send_header("content-length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):  # noqa: N802
                import json as _json

                length = int(self.headers.get("content-length", 0))
                body = _json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append({"method": "POST", "path": self.path,
                                       "headers": dict(self.headers), "body": body})
                # 16-bit PCM(무음) — 텍스트 길이 비례.
                n = max(1, len(body.get("text", "")) * 320)
                pcm = b"\x00\x00" * n
                self.send_response(200)
                self.send_header("content-type", "audio/pcm")
                self.send_header("content-length", str(len(pcm)))
                self.end_headers()
                self.wfile.write(pcm)

        self._Handler = Handler

    def __enter__(self) -> str:
        import http.server
        import threading

        self._srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self._Handler)
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True)
        self._thread.start()
        return f"http://127.0.0.1:{self._srv.server_address[1]}"

    def __exit__(self, *exc) -> None:
        self._srv.shutdown()
        self._srv.server_close()
        self._thread.join(timeout=5)


class TestElevenLabsIntegration(_AudioHarness):
    """elevenlabs 백엔드를 ElevenLabs-모양 mock 에 물려 검증 (키만 있으면 기본 목소리)."""

    def _set_env(self, url: str) -> None:
        import os

        for k in ("ELEVENLABS_API_KEY", "ELEVENLABS_BASE_URL", "ELEVENLABS_VOICE_ID"):
            self.addCleanup(lambda k=k: os.environ.pop(k, None))
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        os.environ["ELEVENLABS_BASE_URL"] = url
        os.environ.pop("ELEVENLABS_VOICE_ID", None)

    def test_autovoice_and_synthesis(self) -> None:
        self._advance_to_script()
        server = _MockElevenLabsServer()
        with server as url:
            self._set_env(url)
            rc = cli_main(["build-audio", "demo3", "--backend", "elevenlabs"])
            self.assertEqual(rc, 0)

        manifest = AudioManifest.model_validate_json(
            (self.projects_root / "demo3" / "08_audio" / "audio_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest.backend, "elevenlabs")
        self.assertEqual(len(manifest.segments), 3)
        self.assertTrue(all(s.duration_sec > 0 for s in manifest.segments))
        # voice 미지정 → GET /v1/voices 로 자동 선택, POST 는 그 voice_id 로.
        methods = [(r["method"], r["path"]) for r in server.requests]
        self.assertIn(("GET", "/v1/voices"), [(m, p.split("?")[0]) for m, p in methods])
        post = next(r for r in server.requests if r["method"] == "POST")
        self.assertIn("/v1/text-to-speech/auto_voice_1", post["path"])
        self.assertIn("output_format=pcm_16000", post["path"])
        self.assertEqual(post["headers"].get("xi-api-key"), "test-key")

    def test_missing_key_via_cli_errors(self) -> None:
        import os

        self._advance_to_script()
        os.environ.pop("ELEVENLABS_API_KEY", None)
        self.assertEqual(cli_main(["build-audio", "demo3", "--backend", "elevenlabs"]), 1)

    def test_key_with_trailing_space_is_stripped(self) -> None:
        # Windows `set VAR=v ` 가 붙이는 뒤 공백이 .strip() 되어 헤더 오류 없이 동작.
        import os

        self._advance_to_script()
        with _MockElevenLabsServer() as url:
            for k in ("ELEVENLABS_API_KEY", "ELEVENLABS_BASE_URL", "ELEVENLABS_VOICE_ID"):
                self.addCleanup(lambda k=k: os.environ.pop(k, None))
            os.environ["ELEVENLABS_API_KEY"] = "test-key \t"  # 뒤 공백/탭
            os.environ["ELEVENLABS_BASE_URL"] = url + "  "
            os.environ.pop("ELEVENLABS_VOICE_ID", None)
            manifest = build_audio("demo3", backend="elevenlabs")
        self.assertEqual(len(manifest.segments), 3)
        self.assertTrue(all(s.duration_sec > 0 for s in manifest.segments))


if __name__ == "__main__":
    import unittest

    unittest.main()

"""유료 TTS 호출 차단(v5.13.0 back_and_forth D-0153 Q0 §3-1, 가이드 23 §19 P0, 사용자 결정 D127).

plan·provider(`eleven_one`)·probe(`tools/tts_align_probe.py`) 세 경로 모두 `requests.post` 0회, 차단 메시지,
키가 있어도 자동 전환 없음, 허용일 때만 요청이 나간다(차단 지점이 한 곳), 설정을 읽는 코드는 `require_allowed` 하나.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from script.tts import elevenlabs
from tests.anti_inertia._ast_util import REPO

KEYS = {"ELEVENLABS_API_KEY": "test-key-not-real", "ELEVENLABS_VOICE_ID": "voice-test"}
TEXT = "시험 문장입니다."


def _proj(d: str) -> Path:
    proj = Path(d)
    (proj / "script.yaml").write_text(yaml.safe_dump({
        "title": "t", "subtitle": "s", "date": "2026.10.10", "scenes": [{"id": "a", "sentences": [
            {"text": TEXT, "tts": TEXT, "date": "2026.10.10"}]}]}, allow_unicode=True), encoding="utf-8")
    return proj


class PaidBlockTest(unittest.TestCase):
    def test_plan_path_no_request(self) -> None:
        from script import plan as plan_mod  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, KEYS), \
                mock.patch("requests.post") as post:
            with self.assertRaises(elevenlabs.ElevenLabsRefused) as cm:
                plan_mod.build(_proj(d), "elevenlabs")
            self.assertFalse((Path(d) / "tts").exists())            # 린트·폴더 생성 전에 거부
        post.assert_not_called()
        self.assertIn("거부", str(cm.exception))

    def test_provider_path_no_request(self) -> None:
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, KEYS), \
                mock.patch("requests.post") as post:
            p = Path(d) / "a.mp3"
            with self.assertRaises(elevenlabs.ElevenLabsRefused):
                elevenlabs.eleven_one(TEXT, p, None, None)
            self.assertFalse(p.exists())
        post.assert_not_called()

    def test_probe_path_no_request(self) -> None:
        import importlib.util  # noqa: PLC0415

        spec = importlib.util.spec_from_file_location("tts_align_probe", REPO / "tools" / "tts_align_probe.py")
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)  # type: ignore[union-attr]
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, KEYS), \
                mock.patch("requests.post") as post:
            proj = _proj(d)
            rc = probe.main([str(proj), "--sids", "a_0", "--out", str(Path(d) / "o.json")])
            self.assertEqual(rc, 2)
            self.assertFalse((proj / "tts_el").exists())             # 과금 폴더도 만들지 않는다
        post.assert_not_called()

    def test_keys_present_no_auto_switch(self) -> None:
        """키가 있어도 기본 백엔드(supertonic)는 ElevenLabs 를 부르지 않는다."""
        from script import plan as plan_mod  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, KEYS), \
                mock.patch("requests.post") as post, \
                mock.patch.object(plan_mod, "lint", return_value=mock.Mock(errors=[], warnings=[])), \
                mock.patch.object(plan_mod, "load_claims_for", return_value=None), \
                mock.patch.object(plan_mod.supertonic, "synth_all",
                                  side_effect=lambda jobs, cfg=None: [p.write_bytes(b"x" * 2000) for _, p in jobs]), \
                mock.patch.object(plan_mod, "trim_to_npy", return_value=(Path(d) / "x.npy", 1.0, 0.0)), \
                mock.patch.object(plan_mod, "forced_alignment", return_value={"source": "mms_forced_alignment"}):
            pl = plan_mod.build(_proj(d), plan_mod.load_config().tts.backend_default)
        post.assert_not_called()
        self.assertTrue(pl.voice.startswith("supertonic"))

    def test_gate_is_the_only_switch(self) -> None:
        """허용(설정 true)일 때만 요청이 나간다 — 차단 지점은 require_allowed 하나."""
        cfg = elevenlabs.load_config().model_copy(deep=True)
        cfg.tts.elevenlabs_allowed = True
        resp = mock.Mock(status_code=200, json=lambda: {"audio_base64": "", "alignment": {
            "characters": list("가"), "character_start_times_seconds": [0.0], "character_end_times_seconds": [0.1]}})
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, KEYS), \
                mock.patch.object(elevenlabs, "load_config", return_value=cfg), \
                mock.patch("requests.post", return_value=resp) as post:
            elevenlabs.eleven_one(TEXT, Path(d) / "a.mp3", None, None)
        post.assert_called_once()

    def test_single_reader_of_setting(self) -> None:
        """설정 속성 `.elevenlabs_allowed` 를 읽는 코드는 require_allowed 하나(문서·메시지 문자열 제외, AST)."""
        import ast  # noqa: PLC0415

        hits = []
        for p in [*(REPO / "script").rglob("*.py"), *(REPO / "tools").glob("*.py"), *(REPO / "orchestrator").rglob("*.py"),
                  *(REPO / "engine").rglob("*.py")]:
            rel = p.relative_to(REPO).as_posix()
            if rel == "orchestrator/config.py":
                continue
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.FunctionDef):
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Attribute) and sub.attr == "elevenlabs_allowed":
                            hits.append(f"{rel}:{node.name}")
        self.assertEqual(hits, ["script/tts/elevenlabs.py:require_allowed"])

if __name__ == "__main__":
    unittest.main()

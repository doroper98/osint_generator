"""Supertonic 3 백엔드(v5.11.0 back_and_forth D-0152 V1, 사용자 결정 D146·설계 D147).

결정성(2회 바이트 동일 wav·mp3), 시드 분리, 캐시 키 분리(edge·설정값), 자산 없음 오류(plan 까지),
조각 분할 경계·조각 사이 무음, mp3 길이 = wav 길이 ±0.1초, plan 기록(목소리·조각·정렬 없음), 기본 백엔드·ElevenLabs 거부 유지.
실제 합성 테스트는 자산을 받은 환경에서만(사유 있는 skip — `python tools/fetch_data.py supertonic`).
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import yaml

from script.tts import supertonic as st
from script.tts import supertonic_assets as sa
from script.tts.align import align_path
from script.tts.cache import cache_key
from script.tts.supertonic_runtime import TextToSpeech, chunk_text

CFG = st.config()
HAS_ASSETS = sa.mismatches(CFG) == []
SKIP = "Supertonic 자산 없음 — python tools/fetch_data.py supertonic"
TEXT = "호르무즈 해협은 세계 원유 수송량의 오분의 일이 지나는 길목입니다."
MP3_TOL_SEC = 0.1


def _mp3_seconds(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


@unittest.skipUnless(HAS_ASSETS, SKIP)
class SynthTest(unittest.TestCase):
    def test_deterministic_wav_and_mp3(self) -> None:
        w1, sr, parts = st.synth_wav(TEXT, CFG)
        w2, _, _ = st.synth_wav(TEXT, CFG)
        self.assertEqual(w1.tobytes(), w2.tobytes())
        self.assertEqual(parts, [TEXT])
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.mp3", Path(d) / "b.mp3"
            st.synth_one(TEXT, a, CFG)
            st.synth_one(TEXT, b, CFG)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertFalse(align_path(a).exists())            # V1 은 정렬을 쓰지 않는다(V2 강제 정렬)
            self.assertLessEqual(abs(_mp3_seconds(a) - len(w1) / sr), MP3_TOL_SEC)

    def test_different_text_different_audio(self) -> None:
        w1, _, _ = st.synth_wav(TEXT, CFG)
        w2, _, _ = st.synth_wav(TEXT.replace("일이", "일 이상이"), CFG)
        self.assertNotEqual(hashlib.sha1(w1.tobytes()).hexdigest(), hashlib.sha1(w2.tobytes()).hexdigest())


class SeedAndKeyTest(unittest.TestCase):
    def test_seed_fixed_per_text_and_salt(self) -> None:
        self.assertEqual(st.seed(TEXT, CFG), st.seed(TEXT, CFG))
        self.assertNotEqual(st.seed(TEXT, CFG), st.seed(TEXT + " ", CFG))
        self.assertNotEqual(st.seed(TEXT, CFG), st.seed(TEXT, CFG.model_copy(update={"seed_salt": "v2"})))

    def test_cache_key_separated(self) -> None:
        salt = st.cache_salt(CFG)
        self.assertTrue(salt.startswith(f"|st|{CFG.voice_style}|{CFG.speed}|{CFG.total_step}|"))
        k = cache_key(TEXT, None, None, salt)
        self.assertNotIn(k, {cache_key(TEXT, None), cache_key(TEXT, None, "ko-KR-HyunsuNeural")})   # edge 키와 겹치지 않음
        for upd in ({"speed": 1.0}, {"voice_style": "M1"}, {"total_step": 8}, {"seed_salt": "v2"}, {"silence_sec": 0.5}):
            self.assertNotEqual(k, cache_key(TEXT, None, None, st.cache_salt(CFG.model_copy(update=upd))), upd)


class ChunkTest(unittest.TestCase):
    def test_chunk_boundaries(self) -> None:
        one = "가" * 150 + "."
        self.assertEqual(chunk_text(one, 120), [one])                       # 문장 하나는 길어도 자르지 않는다(원본 규칙)
        a, b = "가" * 70 + ".", "나" * 70 + "."
        self.assertEqual(chunk_text(f"{a} {b}", 120), [a, b])                # 합쳐 120 초과 → 두 조각
        self.assertEqual(chunk_text(f"{a} {b}", 200), [f"{a} {b}"])
        self.assertEqual(st.chunks(f"{a} {b}", CFG), chunk_text(f"{a} {b}", CFG.max_chunk_len))

    def test_silence_between_chunks(self) -> None:
        eng = TextToSpeech.__new__(TextToSpeech)
        eng.sample_rate = 100
        lens = iter([1.5, 2.0])
        with mock.patch.object(TextToSpeech, "infer",
                               side_effect=lambda *a, **k: (np.ones(500, np.float32), next(lens))):
            wav, parts = eng.synth("가가. 나나.", mock.Mock(), 1, 1.0, 0.3, 3, np.random.default_rng(0))
        self.assertEqual(parts, ["가가.", "나나."])
        self.assertEqual(len(wav), 150 + 30 + 200)                           # 조각마다 예측 길이로 자르고 0.3초 무음
        self.assertTrue(np.all(wav[150:180] == 0))


class PlanTest(unittest.TestCase):
    def _proj(self, d: str) -> Path:
        proj = Path(d)
        (proj / "script.yaml").write_text(yaml.safe_dump({
            "title": "t", "subtitle": "s", "date": "2026.10.10", "scenes": [{"id": "a", "sentences": [
                {"text": TEXT, "tts": TEXT, "date": "2026.10.10"}]}]}, allow_unicode=True), encoding="utf-8")
        return proj

    def test_plan_records_voice_chunks_and_no_alignment(self) -> None:
        from script import plan as plan_mod  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            proj = self._proj(d)
            seen: list[str] = []

            def fake(jobs: list[tuple[str, Path]], cfg: object = None) -> None:
                for t, p in jobs:
                    seen.append(t)
                    p.write_bytes(b"x" * 2000)

            with mock.patch.object(plan_mod, "lint", return_value=mock.Mock(errors=[], warnings=[])), \
                 mock.patch.object(plan_mod, "load_claims_for", return_value=None), \
                 mock.patch.object(plan_mod.supertonic, "synth_all", side_effect=fake), \
                 mock.patch.object(plan_mod.edge, "synth_all", side_effect=AssertionError("edge 로 넘어가면 안 된다")), \
                 mock.patch.object(plan_mod, "trim_to_npy", return_value=(proj / "x.npy", 1.0, 0.0)):
                pl = plan_mod.build(proj, "supertonic")
                again = plan_mod.build(proj, "supertonic")        # 캐시 — 정렬이 없어도 재합성하지 않는다(V1)
        self.assertEqual(len(seen), 1)
        self.assertEqual(pl.voice, f"supertonic-3 {CFG.voice_style} ×{CFG.speed}")
        s = pl.sentences[0]
        self.assertEqual(s.chunks, [s.tts])                                  # 발음 사전 뒤 텍스트(원유 → 워뉴)
        self.assertIn(cache_key(s.tts, None, None, st.cache_salt(CFG)), s.mp3)
        self.assertEqual((pl.tts_resynthesized, again.tts_resynthesized), ([], []))

    def test_missing_assets_fail_without_fallback(self) -> None:
        from script import plan as plan_mod  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            proj = self._proj(d)
            bad = CFG.model_copy(update={"asset_dir": str(Path(d) / "없는폴더")})
            st._engine.cache_clear()
            with mock.patch.object(plan_mod, "lint", return_value=mock.Mock(errors=[], warnings=[])), \
                 mock.patch.object(plan_mod, "load_claims_for", return_value=None), \
                 mock.patch.object(plan_mod.supertonic, "config", return_value=bad), \
                 mock.patch.object(plan_mod.edge, "synth_all", side_effect=AssertionError("edge 폴백 금지")):
                with self.assertRaises(sa.SupertonicAssetError) as cm:
                    plan_mod.build(proj, "supertonic")
        self.assertIn(sa.FETCH_CMD, str(cm.exception))

    def test_default_backend_and_elevenlabs_still_refused(self) -> None:
        from orchestrator.config import load_config  # noqa: PLC0415
        from script import plan as plan_mod  # noqa: PLC0415

        self.assertEqual(load_config().tts.backend_default, "supertonic")      # D146
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError) as cm:
                plan_mod.build(self._proj(d), "elevenlabs")
        self.assertIn("거부", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

"""V5 문장 끝 억양 보정 (v5.20.0, back_and_forth D-0175, 사용자 결정 D169 시안 C).

구간 선택(끝 3글자·문장부호) · "니다" 로 안 끝나면 바이트 동일 + 기록 · 구간 앞 샘플 바이트 동일 · 끝 f0 ≈ 원음 −4반음(같은 추적기) ·
길이 같음 · 결정성 · 규칙 값 코드 상수 없음 · 트림 자리 = 원음(정렬·게이트 시각 영향 0) · provenance features.prosody 집계.
합성 신호(배음 모음, 120Hz)로 시험한다 — 저장소 밖 음성 파일에 기대지 않는다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import numpy as np
import pyworld as pw

from rules import load_rules
from script.tts import prosody, trim
from script.tts.prosody import SR, final_fall, span_start_index

REPO = Path(__file__).resolve().parent.parent
CFG = load_rules().tts_rules.prosody.final_fall
TEXT = "갔습니다."


def _vowel(dur: float = 1.6, f0: float = 120.0, lead: float = 0.2) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in range(1, 12)) * 0.25
    env = ((t > lead) & (t < dur - lead)).astype(np.float64)
    env = np.convolve(env, np.hanning(441) / np.hanning(441).sum(), mode="same")
    return (x * env).astype(np.float32)


def _align(text: str = TEXT, start: float = 0.3, step: float = 0.22) -> dict:
    st = [round(start + k * step, 4) for k in range(len(text))]
    return {"alignment_source": "mms_forced_alignment", "characters": list(text),
            "character_start_times_seconds": st, "character_end_times_seconds": [s + step for s in st]}


class SpanTest(unittest.TestCase):
    def test_last_three_chars_with_punctuation(self) -> None:
        self.assertEqual(span_start_index("갔습니다.", CFG), 1)                  # 습
        self.assertEqual(span_start_index("결론입니다", CFG), 2)                 # 입
        self.assertEqual(span_start_index("발표였습니다”.", CFG), 3)             # 끝 문장부호 여러 개
        self.assertIsNone(span_start_index("그렇다.", CFG))
        self.assertIsNone(span_start_index("니다", CFG))                         # 3글자보다 짧다

    def test_non_suffix_sentence_is_untouched_and_recorded(self) -> None:
        x = _vowel()
        y, rec = final_fall(x, _align("갔다고 했다."), "갔다고 했다.", CFG)
        self.assertIs(y, x)
        self.assertEqual((rec.applied, rec.reason), (False, "'니다' 로 끝나지 않는다"))


class FallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.x = _vowel()
        cls.y, cls.rec = final_fall(cls.x, _align(), TEXT, CFG)

    def test_prefix_bytes_identical_and_length_same(self) -> None:
        self.assertTrue(self.rec.applied)
        cs = int(round(self.rec.region_sec[0] * SR))
        self.assertGreater(cs, 0)
        self.assertEqual(self.x[:cs].tobytes(), self.y[:cs].tobytes())
        self.assertEqual((len(self.y), self.y.dtype), (len(self.x), self.x.dtype))   # 길이 같음(±1ms 보다 엄격)
        t_start = _align()["character_start_times_seconds"][1] - CFG.pre_sec
        self.assertAlmostEqual(self.rec.region_sec[0], t_start, delta=CFG.frame_ms / 1000)   # 구간 시작 = '습' 시작 − pre_sec

    def test_end_pitch_four_semitones_down(self) -> None:
        def track(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            d = a.astype(np.float64)
            f0, t = pw.harvest(d, SR, f0_floor=CFG.f0_floor_hz, f0_ceil=CFG.f0_ceil_hz, frame_period=CFG.frame_ms)
            return pw.stonemask(d, f0, t, SR), t

        f_in, t = track(self.x)
        f_out, _ = track(self.y)
        k = int(np.searchsorted(t, self.rec.region_sec[1] - 0.05))   # 구간 끝 직전(마지막 유성 프레임 50ms 앞)
        k0 = int(np.searchsorted(t, self.rec.region_sec[0] - 0.05))  # 구간 앞 = 원음
        self.assertAlmostEqual(12 * np.log2(f_out[k] / f_in[k]), -CFG.semitones, delta=1.0)
        self.assertAlmostEqual(12 * np.log2(f_out[k0] / f_in[k0]), 0.0, delta=0.3)

    def test_deterministic(self) -> None:
        y2, rec2 = final_fall(self.x, _align(), TEXT, CFG)
        self.assertEqual(y2.tobytes(), self.y.tobytes())
        self.assertEqual(rec2, self.rec)

    def test_trim_cut_points_follow_original(self) -> None:
        a0, s0 = trim.trim(self.x)
        a1, s1 = trim.trim(self.y, ref=self.x)
        self.assertEqual((s0, len(a0)), (s1, len(a1)))   # trim_offset·길이 그대로 → 정렬 시각·게이트(음향 발화 시작) 영향 0


class OctaveCleanTest(unittest.TestCase):
    """v5.20.2 D-0180 §3 — 끝 구간 추적기 옥타브 오류 정리·기록 f0 = 게이트 중앙값."""

    OC = CFG.octave_clean

    def test_clean_halves_doubles_and_leaves_rest(self) -> None:
        f0 = np.array([100.0, 210.0, 0.0, 100.0, 48.0, 104.0, 230.0])
        out, n = prosody.clean_octaves(f0, 1, 5, 104.0, self.OC.ratio_hi, self.OC.ratio_lo)
        np.testing.assert_allclose(out, [100.0, 105.0, 0.0, 100.0, 96.0, 104.0, 230.0])   # 구간 1..5 만, 무성 0 그대로, 밖(230) 그대로
        self.assertEqual(n, 2)

    def test_gate_excludes_quiet_and_unvoiced(self) -> None:
        x = _vowel()
        t = np.arange(0, len(x) / SR, CFG.frame_ms / 1000)
        f0 = np.where((t > 0.3) & (t < 1.2), 120.0, 0.0)
        g = prosody.gate_mask(x.astype(np.float64), f0, t, self.OC.gate_db, self.OC.rms_ms)
        self.assertFalse(g[t < 0.15].any())      # 무음 앞부분
        self.assertTrue(g[(t > 0.5) & (t < 1.0)].all())
        self.assertFalse(g[t > 1.25].any())       # 무성(f0 0)

    def test_record_is_gated_median_and_fall_audible(self) -> None:
        _, rec = final_fall(_vowel(), _align(), TEXT, CFG)
        self.assertIsInstance(rec.octave_fixed_n, int)
        st = 12 * np.log2(rec.f0_end_hz / rec.f0_start_hz)
        self.assertLess(st, -1.0)                 # 들리는 끝 음이 내려간다(구간 끝 = 마지막 유성 프레임이라 −4 전부는 아님)
        self.assertGreater(st, -CFG.semitones - 0.5)

    def test_disabled_keeps_v5_20_0_path(self) -> None:
        cfg = CFG.model_copy(deep=True)
        cfg.octave_clean.enabled = False
        y1, r1 = final_fall(_vowel(), _align(), TEXT, cfg)
        y2, _ = final_fall(_vowel(), _align(), TEXT, CFG)
        self.assertEqual(r1.octave_fixed_n, 0)
        self.assertEqual(y1.tobytes(), y2.tobytes())   # 깨끗한 합성 신호 = 고칠 프레임 없음 → 바이트 동일


class RuleSourceTest(unittest.TestCase):
    def test_no_rule_values_in_module(self) -> None:
        src = (REPO / "script" / "tts" / "prosody.py").read_text(encoding="utf-8")
        code = "\n".join(line.split("#")[0] for line in src.splitlines() if not line.lstrip().startswith(("#", '"', "-", "    -")))
        body = code[code.index("SR = "):]   # docstring 뒤 코드만
        for v in ('"니다"', "4.0", "0.03", "260", "60.0", "harvest(x, SR, f0_floor=6", "1.5", "0.6", "-30", "20 /", "[:10]", "[-10:]"):
            self.assertNotIn(v, body, f"규칙 값 {v} 가 모듈 상수 — rules tts_rules.prosody.final_fall 에서(P3)")
        self.assertTrue(re.search(r"cfg\.semitones", body) and re.search(r"cfg\.suffix", body))

    def test_missing_pyworld_is_error(self) -> None:
        import builtins  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        real = builtins.__import__

        def no_pw(name, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202
            if name == "pyworld":
                raise ImportError("no pyworld")
            return real(name, *a, **k)

        with mock.patch("builtins.__import__", side_effect=no_pw), self.assertRaises(prosody.ProsodyError):
            final_fall(_vowel(), _align(), TEXT, CFG)


class ProvenanceTest(unittest.TestCase):
    def test_features_prosody_counts_only_when_ran(self) -> None:
        from engine.provenance import build  # noqa: PLC0415
        from script.schema import Plan  # noqa: PLC0415

        row = {"sid": "a_0", "scene": "a", "date": "2026", "text": "t", "tts": "t", "segments": [["t", 1]], "mp3": "m", "npy": "n",
               "dur": 1.0, "t0": 0.0, "t1": 1.0}
        base = {"cards": [], "scene_start": {"a": 0.0}, "total": 1.0, "voice": "v", "title": "t", "subtitle": "s", "date": "2026"}
        p0 = Plan.model_validate({**base, "sentences": [row]})
        self.assertNotIn("prosody", build(p0, [], [], "x", {})["features_used"])
        p1 = Plan.model_validate({**base, "sentences": [{**row, "prosody": {"final_fall": {"applied": True, "semitones": 4.0}}},
                                                        {**row, "sid": "a_1", "prosody": {"final_fall": {"applied": False, "reason": "r"}}}]})
        self.assertEqual(build(p1, [], [], "x", {})["features_used"]["prosody"], {"final_fall": {"applied_n": 1, "skipped_n": 1}})


if __name__ == "__main__":
    unittest.main()

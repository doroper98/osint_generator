"""G6(v4.6.0, back_and_forth D-0097, 사용자 결정 D86) — 베드 저음 보강(audio/mix.py process_bed)·베드 저역 QA(audio/qa.py)."""

from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import numpy as np

from rules import load_rules

REPO = Path(__file__).resolve().parents[1]
AU = load_rules().audio
SR = AU.sample_rate


def _band_db(x: np.ndarray, lo: float, hi: float) -> float:
    from audio.qa import band_rms_db  # noqa: PLC0415

    return band_rms_db(x, (lo, hi))


def _plan(tmp: Path, scene_start: dict[str, float]) -> NS:
    npy = tmp / "s0.npy"
    np.save(npy, (np.sin(np.arange(22050) / 10) * 0.3).astype(np.float32))
    return NS(total=8.0, sentences=[NS(npy=str(npy), t0=1.0, t1=1.5)], cards=[], scene_start=scene_start)


class BedBassRulesTest(unittest.TestCase):
    def test_no_rule_literals_in_mix(self) -> None:
        """규칙 값(셸프·서브·스웰)을 코드에 다시 적지 않는다(15 P3) — 숫자 리터럴이 규칙 값과 겹치지 않는다."""
        b = AU.bed_bass
        vals = {b.shelf.freq_hz, b.shelf.gain_db, b.shelf.q, *b.sub.band_hz, b.sub.out_lp_hz, b.sub.filter_order, b.sub.gain,
                b.sub.env_attack_sec, b.sub.env_release_sec, b.sub.env_block_sec, b.swell.sec, b.swell.depth, b.norm_ref,
                *AU.qa.bed_bass_rise_db, *AU.qa.bed_bass_band_hz, *AU.qa.bed_mid_band_hz} - {0, 1, 2, 3}
        for rel in ("audio/mix.py", "audio/qa.py"):
            lits = {n.value for n in ast.walk(ast.parse((REPO / rel).read_text(encoding="utf-8")))
                    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)}
            self.assertEqual(lits & vals - {44100, 10, 20, 4}, set(), rel)

    def test_user_values_kept(self) -> None:
        self.assertEqual((AU.bed_gain, AU.duck_depth), (0.47, 0.5))


class ProcessBedTest(unittest.TestCase):
    def test_shelf_raises_low_band_on_white_noise(self) -> None:
        from audio.mix import lfilter, low_shelf_ba  # noqa: PLC0415

        sh = AU.bed_bass.shelf
        x = np.random.default_rng(0).standard_normal(SR * 8)
        y = lfilter(*low_shelf_ba(sh.freq_hz, sh.gain_db, sh.q), x)
        lo, hi = AU.qa.bed_bass_band_hz[0], sh.freq_hz / 2   # 셸프 주파수 한 옥타브 아래(셸프 전 이득 구간)
        rise = (_band_db(y, lo, hi) - _band_db(x, lo, hi)) - (_band_db(y, *AU.qa.bed_mid_band_hz) - _band_db(x, *AU.qa.bed_mid_band_hz))
        self.assertGreaterEqual(rise, sh.gain_db - 1)

    def test_sub_octave_of_110hz_is_55hz(self) -> None:
        from audio.mix import sub_octave  # noqa: PLC0415

        t = np.arange(SR * 4) / SR
        sub = sub_octave(np.sin(2 * np.pi * 110 * t) * 0.5, np.ones(len(t)))
        f = np.fft.rfftfreq(len(t), 1 / SR)
        self.assertAlmostEqual(float(f[np.argmax(np.abs(np.fft.rfft(sub)))]), 55.0, delta=0.5)

    def test_swell_timing_and_length(self) -> None:
        from audio.mix import swell_gain  # noqa: PLC0415

        w = AU.bed_bass.swell
        n = int(SR * (2 + w.sec + 2))
        g = swell_gain(n, [2.0])
        i0, m = int(2.0 * SR), int(w.sec * SR)
        self.assertEqual(float(g[i0 - 1]), 1.0)
        self.assertAlmostEqual(float(g[i0]), 1 + w.depth)
        self.assertTrue(np.all(np.diff(g[i0:i0 + m]) < 0))      # 선형 하강
        self.assertTrue(np.all(g[i0 + m:] == 1.0))              # sec 뒤 1

    def test_mix_swells_skip_first_scene_and_record_stats(self) -> None:
        from audio.mix import Sound, mix  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            plan = _plan(Path(d), {"a": 0.0, "b": 4.0})
            snd = Sound.model_validate({"bgm": "music.x", "intensity": [(0.0, 0.6), (8.0, 0.0)]})
            t = np.arange(SR * 10) / SR
            raw = np.stack([np.sin(2 * np.pi * 110 * t) * 0.3 + np.sin(2 * np.pi * 880 * t) * 0.3] * 2, 1).astype(np.float32)
            st: dict = {}
            mix(plan, snd, raw, st)
        self.assertEqual(st["swell_at"], [4.0])
        self.assertGreater(st["rise_db"], 0)


class NormRefTest(unittest.TestCase):
    def test_norm_ref_endpoints(self) -> None:
        """norm_ref 1 = 처리 후 피크로 정규화(베드 피크 1), 0 = 처리 전 피크 기준(처리로 커진 만큼 1 을 넘음)."""
        import audio.mix as am  # noqa: PLC0415

        t = np.arange(SR * 4) / SR
        raw = np.stack([np.sin(2 * np.pi * 110 * t) * 0.4 + np.sin(2 * np.pi * 880 * t) * 0.2] * 2, 1).astype(np.float32)
        peaks = {}
        for k in (0.0, 1.0):
            au = AU.model_copy(update={"bed_bass": AU.bed_bass.model_copy(update={"norm_ref": k})})
            with mock.patch.object(am, "AU", au):
                peaks[k] = float(np.abs(am.bed(raw, len(raw), [1.0])).max())
        self.assertAlmostEqual(peaks[1.0], 1.0, places=4)
        self.assertGreater(peaks[0.0], 1.0)


class NullBgmUntouchedTest(unittest.TestCase):
    def test_null_bgm_never_processes_and_writes_no_stats(self) -> None:
        """무음악 경로: process_bed·측정이 돌지 않는다(바이트 동일 — 실측은 reports/phaseG6)."""
        import audio.mix as am  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            plan = _plan(Path(d), {"a": 0.0, "b": 4.0})
            snd = am.Sound.model_validate({"bgm": None, "intensity": [(0.0, 0.6), (8.0, 0.0)]})
            st: dict = {}
            with mock.patch.object(am, "process_bed", side_effect=AssertionError("process_bed 호출")), \
                    mock.patch.object(am, "bed_stats", side_effect=AssertionError("bed_stats 호출")):
                y, _ = am.mix(plan, snd, None, st)
        self.assertEqual(st, {})
        self.assertGreater(float(np.abs(y).max()), 0.0)


class BedBassQATest(unittest.TestCase):
    def _qa(self, stats: dict | None, n: int) -> list[str]:
        from audio.qa import audio_qa  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            npy = out / "s0.npy"
            np.save(npy, (np.sin(np.arange(22050) / 10) * 0.3).astype(np.float32))
            y = np.zeros((n, 2), np.float32)
            y[SR:SR + 22050, :] = (np.sin(np.arange(22050) / 10) * 0.24)[:, None]
            y += 0.01
            y.tofile(out / "mix.f32")
            if stats is not None:
                (out / "bed_stats.json").write_text(json.dumps(stats), encoding="utf-8")
            return audio_qa(out, [{"npy": str(npy), "t0": 1.0, "t1": 1.5, "sid": "s0"}], has_music=True).issues()

    def _stats(self, rise: float, n: int) -> dict:
        from audio.qa import BedStats  # noqa: PLC0415

        return BedStats(bass_band_hz=AU.qa.bed_bass_band_hz, mid_band_hz=AU.qa.bed_mid_band_hz,
                        before={"bass_db": -8, "mid_db": -20, "ratio_db": 12}, after={"bass_db": -8 + rise, "mid_db": -20, "ratio_db": 12 + rise},
                        rise_db=rise, swell_at=[], applied=AU.bed_bass, mix_samples=n).model_dump(mode="json")

    def test_out_of_range_is_hard(self) -> None:
        n = SR * 3
        lo, hi = AU.qa.bed_bass_rise_db   # D-0102 1-A — 판정은 상승폭(절대 비율은 기록만)
        self.assertTrue(any("베드 저역 비율" in i for i in self._qa(self._stats(hi + 2, n), n)))
        self.assertTrue(any("베드 저역 비율" in i for i in self._qa(self._stats(lo - 2, n), n)))
        self.assertFalse(any("베드 저역" in i for i in self._qa(self._stats((lo + hi) / 2, n), n)))

    def test_missing_or_stale_stats_is_hard(self) -> None:
        n = SR * 3
        self.assertTrue(any("bed_stats.json 없음" in i for i in self._qa(None, n)))
        self.assertTrue(any("낡은 기록" in i for i in self._qa(self._stats(5, n - 1), n)))


if __name__ == "__main__":
    unittest.main()

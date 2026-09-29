"""오디오 QA 검사기 하나(v3.4.0, D-0060 작업 6) — audio/qa.py 임계를 합성 픽스처로 안/밖 확인."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

from audio.qa import SR, AudioQA, Loudness, audio_qa, loudnorm_two_pass
from rules import load_rules

AU = load_rules().audio
REPO = Path(__file__).resolve().parents[1]


def _fixture(d: Path, music_db: float) -> list:
    """내레이션(사인 400Hz, 믹서처럼 0.8 피크) + 음악(사인 97Hz, 내레이션 대비 music_db) mix.f32."""
    n = int(6 * SR)
    t = np.arange(n) / SR
    voice = (np.sin(2 * np.pi * 400 * t[: 4 * SR]) * 0.5).astype(np.float32)
    np.save(d / "s0.npy", voice)
    vo = np.zeros(n, np.float32)
    vo[SR: 5 * SR] = voice / np.abs(voice).max() * AU.narration_peak
    vo_rms = float(np.sqrt(np.mean(vo[SR: 5 * SR] ** 2)))
    mu = np.sin(2 * np.pi * 97 * t).astype(np.float32)
    mu *= vo_rms * 10 ** (music_db / 20) / float(np.sqrt(np.mean(mu[SR: 5 * SR] ** 2)))
    y = (vo + mu).astype(np.float32)
    np.stack([y, y], 1).astype(np.float32).tofile(d / "mix.f32")
    return [NS(npy=str(d / "s0.npy"), t0=1.0, t1=5.0)]


class AudioQATest(unittest.TestCase):
    def test_rules_follow_user_approved_v3(self) -> None:
        """D-0061: 음악 레벨 범위는 사용자 합격본 기준 — v3 −12.7 안, 사용자 거절 v2 −17.8 밖."""
        lo, hi = AU.qa.music_under_narration_db
        self.assertTrue(lo <= -12.7 <= hi)
        self.assertFalse(lo <= -17.8 <= hi)

    def test_sentence_rms_outlier_is_warning_only(self) -> None:
        """D-0061 쟁점 2 A: 문장 RMS 편차는 warning 만(정규화 없음)."""
        from audio.qa import rms_outliers, sentence_rms  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            t = np.arange(2 * SR) / SR
            tone = np.sin(2 * np.pi * 400 * t).astype(np.float32)
            normal = [f"n{i}" for i in range(10)]              # 평균이 정상 문장 쪽에 있도록 충분히
            for k in normal:
                np.save(p / f"{k}.npy", tone)
            spiky = tone * 0.05
            spiky[:200] = 1.0                                   # 피크 하나 → 피크 정규화 뒤 RMS 가 크게 낮아진다
            np.save(p / "c.npy", spiky.astype(np.float32))
            srms = sentence_rms([NS(npy=str(p / f"{k}.npy"), sid=k) for k in [*normal, "c"]])
            self.assertEqual(rms_outliers(srms), ["c"])
            base = dict(mix_peak=0.5, narration_rms_db=-16, music_rms_in_narration_db=-29, music_under_narration_db=-13,
                        narration_seconds=1, music_level_ok=True, peak_ok=True, sentence_rms_db=srms, sentence_rms_outliers=["c"])
            q = AudioQA(**base)
            self.assertEqual(q.issues(), [])                    # hard 아님
            self.assertEqual(len(q.warnings()), 1)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg 없음 — loudnorm 2패스는 ffmpeg 가 측정한다(환경 의존, D-0062 NB22)")
    def test_two_pass_record(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            _fixture(Path(d), -13.0)
            af, rec = loudnorm_two_pass(Path(d) / "mix.f32", 6.0)
            self.assertIn("linear=true", af)
            self.assertIn("measured_I=", af)
            self.assertIn(rec["pass2"]["normalization_type"], ("linear", "dynamic"))   # 어느 쪽이든 기록한다(숨기지 않음)
            self.assertTrue(af.endswith(":level=false:attack=1:release=50") and ",alimiter=limit=" in af)   # RENDER-AP-004
            self.assertEqual(rec["post_limiter_dbfs"], AU.post_limiter_dbfs)

    def test_music_level_inside_and_outside(self) -> None:
        lo, hi = AU.qa.music_under_narration_db
        for db, ok in (((lo + hi) / 2, True), (hi + 3, False), (lo - 3, False)):
            with tempfile.TemporaryDirectory() as d, self.subTest(db=db):
                q = audio_qa(Path(d), _fixture(Path(d), db))
                self.assertAlmostEqual(q.music_under_narration_db, db, delta=0.3)
                self.assertEqual(q.music_level_ok, ok)
                self.assertIsNone(q.final_loudness)            # final.mp4 없으면 음량 판정 없음(지어내지 않음)

    def test_no_music_is_not_judged(self) -> None:
        """bgm null(음악 없음)이면 음악 레벨은 판정 대상이 아니다 — 무음을 '범위 밖'으로 지적하지 않는다."""
        with tempfile.TemporaryDirectory() as d:
            q = audio_qa(Path(d), _fixture(Path(d), -60.0), has_music=False)
            self.assertIsNone(q.music_level_ok)
            self.assertEqual(q.issues(), [])

    def test_loudness_and_true_peak_issues(self) -> None:
        ln = AU.loudnorm
        base = dict(mix_peak=0.5, narration_rms_db=-16, music_rms_in_narration_db=-32, music_under_narration_db=-16,
                    narration_seconds=1, music_level_ok=True, peak_ok=True)
        good = AudioQA(**base, final_loudness=Loudness(I=ln.I, TP=ln.TP - 1, LRA=5), loudness_ok=True, true_peak_ok=True)
        self.assertEqual(good.warnings(), [])
        self.assertEqual(good.issues(), [])
        bad = AudioQA(**base, final_loudness=Loudness(I=ln.I - 3, TP=ln.TP + 1, LRA=5), loudness_ok=False, true_peak_ok=False)
        self.assertEqual(len(bad.issues()), 2)

    def test_one_measurement_path(self) -> None:
        """측정 코드는 audio/qa.py 하나 — tools·checks 는 호출만(loudnorm·stems 재구현 없음)."""
        for rel in ("tools/audio_report.py", "engine/checks.py", "engine/mux.py"):
            src = (REPO / rel).read_text(encoding="utf-8")
            with self.subTest(rel=rel):
                self.assertNotIn("print_format=json", src)
                self.assertNotIn("def stems", src)
        self.assertIn("from audio.qa import audio_qa", (REPO / "tools" / "audio_report.py").read_text(encoding="utf-8"))
        self.assertIn("from audio.qa import audio_qa", (REPO / "engine" / "checks.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

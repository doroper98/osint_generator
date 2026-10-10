"""V2 강제 정렬·게이트 (v5.16.0, back_and_forth D-0164 §5·D-0165, 사용자 결정 D151, DECISIONS D159).

순수 함수(가중치 없이): 출처 등재·글자 수 대조·at_word 정렬 없음 오류·가중치 없음 오류 메시지·게이트 대응 규칙(대응 없음 = 실패 계상)·
간격 일치(상수 치우침 소거)·발화 시작 참값·문턱 = trim 문턱·plan 정렬 재사용.
가중치가 있는 환경(`python tools/fetch_data.py mms_fa`): 픽스처 10문장 게이트(절대 시각·간격 일치)·글자 단조·무음 오류·
신뢰도 미달 오류(다른 문장 원고)·결정성·이동 불변(앞 0.5초 무음 → 0.5초 ± 20ms).
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from rules import load_rules
from script.schema import Plan
from script.tts import align as tts_align
from script.tts import align_gate as G
from script.tts import forced_align as FA
from script.tts import trim

FIX = Path(__file__).parent / "fixtures" / "tts" / "align_gate"
MAN = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))["sentences"]


def _has_assets() -> bool:
    try:
        FA.require_assets()
    except FA.ForcedAlignError:
        return False
    return True


HAS = _has_assets()
SKIP = "강제 정렬 가중치 없음 — python tools/fetch_data.py mms_fa"
SHIFT_TOL = 0.02


def _plan(tmp: Path, mp3: Path) -> Plan:
    return Plan.model_validate({
        "sentences": [{"sid": "s0", "scene": "a", "date": "", "text": "가나 다라", "tts": "가나 다라", "segments": [["가나 다라", 0]],
                       "mp3": str(mp3), "npy": str(tmp / "x.npy"), "dur": 1.0, "t0": 0.0, "t1": 1.0, "trim_offset": 0.0}],
        "cards": [], "scene_start": {"a": 0.0}, "total": 1.0, "voice": "v", "title": "t", "subtitle": "", "date": ""})


class PureTest(unittest.TestCase):
    def test_unregistered_source_is_error(self) -> None:
        with self.assertRaises(tts_align.AlignmentError):
            tts_align.check_source("whisper_words")
        self.assertIn("mms_forced_alignment", load_rules().tts_rules.alignment_sources)

    def test_char_count_mismatch_is_error(self) -> None:
        spans = [FA.CharSpan("가", 0.0, 0.1, 0.9)]
        with self.assertRaises(tts_align.AlignmentError):
            tts_align.from_forced_alignment("가나", spans)
        al = tts_align.from_forced_alignment("가", spans)
        self.assertEqual(al["alignment_source"], "mms_forced_alignment")

    def test_at_word_without_alignment_is_error(self) -> None:
        from engine.timebase import AlignmentMissingError, Timebase  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            tb = Timebase(_plan(Path(d), Path(d) / "none.mp3"))
            with self.assertRaises(AlignmentMissingError):
                tb.at_word("s0", "다라")

    def test_missing_assets_message_names_fetch_command(self) -> None:
        with tempfile.TemporaryDirectory() as d, mock.patch.object(FA, "asset_dir", return_value=Path(d)):
            with self.assertRaises(FA.ForcedAlignError) as cm:
                FA.require_assets()
        self.assertIn("python tools/fetch_data.py mms_fa", str(cm.exception))

    def test_silence_threshold_matches_trim(self) -> None:
        self.assertEqual(load_rules().tts_rules.forced_align.silence_thr, trim.THRESH)

    def test_onsets_sentence_start_and_after_long_silence(self) -> None:
        sr = trim.SR
        a = np.zeros(int(2.0 * sr), np.float32)
        a[int(0.40 * sr):int(0.80 * sr)] = 0.2
        a[int(0.90 * sr):int(1.00 * sr)] = 0.2      # 0.10초 쉼 — 문턱(0.15) 미만이라 참값 아님
        a[int(1.30 * sr):int(1.60 * sr)] = 0.2      # 0.30초 쉼 뒤
        self.assertEqual([round(t, 3) for t in G.onsets(a, sr)], [0.4, 1.3])

    def test_match_counts_unmatched_as_failure(self) -> None:
        win = load_rules().tts_rules.forced_align.match_window_sec
        errs = G.match([0.40, 1.30, 2.50], [0.42, 0.90, 1.31])
        self.assertAlmostEqual(errs[0], 0.02)
        self.assertAlmostEqual(errs[1], 0.01)
        self.assertEqual(errs[2], win)              # 창 안 후보 없음 → 빼지 않고 창 값으로 계상
        # 단조: 이미 쓴 어절 뒤에서만 찾는다
        self.assertEqual(G.match([0.40, 0.41], [0.40])[1], win)

    def test_interval_check_cancels_constant_bias(self) -> None:
        edge = [0.1, 0.6, 1.0, 1.5]
        mms = [t + 0.1 for t in edge]
        sil = [(0.0, 0.35)]                          # 첫 어절은 쉼 뒤 → 제외
        errs = G.interval_errors(mms, edge, sil)
        self.assertEqual(len(errs), 2)
        self.assertTrue(all(abs(e) < 1e-9 for e in errs))

    def test_plan_reuses_matching_alignment(self) -> None:
        import script.plan as P  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            mp3 = Path(d) / "a.mp3"
            al = {"alignment_source": "mms_forced_alignment", "characters": list("가나"),
                  "character_start_times_seconds": [0.1, 0.2], "character_end_times_seconds": [0.2, 0.3],
                  "score_mean": 0.9, "elapsed_ms": 900}
            tts_align.write(mp3, al)
            with mock.patch.object(FA, "align_file", side_effect=AssertionError("다시 정렬하면 안 된다")):
                self.assertEqual(P.forced_alignment(mp3, "가나"),
                                 {"source": "mms_forced_alignment", "score_mean": 0.9, "elapsed_ms": 900})
            with mock.patch.object(FA, "align_file", return_value={**al, "characters": list("다라")}) as m:
                P.forced_alignment(mp3, "다라")      # 발음 텍스트가 바뀌면 다시 정렬
                m.assert_called_once()
            with mock.patch.object(FA, "align_file", side_effect=FA.ForcedAlignError("x")), self.assertRaises(ValueError):
                P.forced_alignment(mp3, "마바")


@unittest.skipUnless(HAS, SKIP)
class ModelTest(unittest.TestCase):
    def _mp3(self, k: int) -> tuple[Path, str]:
        return FIX / MAN[k]["mp3"], MAN[k]["tts"]

    def test_fixture_gate_absolute_and_interval(self) -> None:
        abs_err, int_err = [], []
        for s in MAN:
            mp3 = FIX / s["mp3"]
            edge = G.word_starts_of(tts_align.read(mp3), s["tts"])
            mms = FA.word_starts(FA.align_sentence(mp3, s["tts"]), s["tts"])
            row = G.sentence_rows(mp3, s["tts"], mms, edge)
            abs_err += row["abs_err"]
            int_err += row["interval_err"]
        a, i = G.stats(abs_err), G.stats(int_err)
        self.assertTrue(a.passed, a)
        self.assertTrue(i.passed, i)
        self.assertGreaterEqual(a.n, 15)

    def test_char_spans_monotonic_no_overlap(self) -> None:
        mp3, text = self._mp3(0)
        spans = FA.align_sentence(mp3, text)
        self.assertEqual("".join(s.char for s in spans), text)
        for a, b in zip(spans, spans[1:]):
            self.assertLessEqual(a.start, a.end)
            self.assertLessEqual(a.end, b.start + 1e-9)

    def test_silent_audio_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "silence.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(p)], check=True)
            with self.assertRaises(FA.ForcedAlignError):
                FA.align_sentence(p, "구월 십팔일")

    def test_wrong_script_below_min_score_is_error(self) -> None:
        mp3, _ = self._mp3(0)
        with self.assertRaises(FA.ForcedAlignError) as cm:
            FA.align_sentence(mp3, MAN[7]["tts"])
        self.assertIn("min_score", str(cm.exception))

    def test_deterministic(self) -> None:
        mp3, text = self._mp3(2)
        self.assertEqual(FA.align_file(mp3, text) | {"elapsed_ms": 0}, FA.align_file(mp3, text) | {"elapsed_ms": 0})

    def test_shift_invariance(self) -> None:
        mp3, text = self._mp3(1)
        with tempfile.TemporaryDirectory() as d:
            shifted = Path(d) / "shift.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-af", "adelay=500:all=1", str(shifted)], check=True)
            a = FA.word_starts(FA.align_sentence(mp3, text), text)
            b = FA.word_starts(FA.align_sentence(shifted, text), text)
        for x, y in zip(a, b):
            self.assertAlmostEqual(y - x, 0.5, delta=SHIFT_TOL)


if __name__ == "__main__":
    unittest.main()

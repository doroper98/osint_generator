"""at_word 정렬 경로 (v2.3.0, back_and_forth D-0021 작업 4, D31 (a)).

픽스처 `tests/fixtures/tts/*.align.json` 은 ElevenLabs with-timestamps 실제 응답(3문장)의 alignment 와
문장 메타(텍스트·트림 후 길이·trim_offset)다. 음성·voice_id 는 없다(D-0022). 키 없이 돈다.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.provenance import build as build_prov
from engine.timebase import AlignmentMissingError, Timebase
from script.schema import Card, Plan
from script.tts import align

FIX = Path(__file__).resolve().parent / "fixtures" / "tts"
T0 = 10.0


def _plan(tmp: Path, sid: str, with_align: bool) -> Plan:
    fx = json.loads((FIX / f"{sid}.align.json").read_text(encoding="utf-8"))
    mp3 = tmp / f"{sid}_x.mp3"
    if with_align:
        Path(str(mp3) + ".align.json").write_text(json.dumps(fx["alignment"], ensure_ascii=False), encoding="utf-8")
    s = dict(sid=sid, scene=sid.split("_")[0], date="2026", text=fx["text"], tts=fx["tts"],
             segments=[(fx["text"], 0)], mp3=str(mp3), npy="x.npy", dur=fx["dur"], t0=T0, t1=T0 + fx["dur"],
             trim_offset=fx["trim_offset"])
    return Plan(sentences=[s], cards=[Card(kind="title", t0=0.0, t1=5.0)], scene_start={s["scene"]: T0},
                total=T0 + fx["dur"] + 2, voice="x", title="t", subtitle="s", date="2026")


class AtWordAlignedTest(unittest.TestCase):
    def test_aligned_uses_pronunciation_start_minus_trim(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tb = Timebase(_plan(Path(d), "ask_1", True))
            fx = json.loads((FIX / "ask_1.align.json").read_text(encoding="utf-8"))
            al = fx["alignment"]
            for word in ("독일", "영국", "일본", "호주", "한국"):
                i = "".join(al["characters"]).find(word)
                want = T0 + al["character_start_times_seconds"][i] - fx["trim_offset"]
                self.assertAlmostEqual(tb.at_word("ask_1", word), want, places=6)
            self.assertEqual({a["mode"] for a in tb.word_anchors}, {"aligned"})
            # 국가명은 문장 안에서 앞에서 뒤로 발음된다
            ts = [a["t"] for a in tb.word_anchors]
            self.assertEqual(ts, sorted(ts))

    def test_error_without_alignment(self) -> None:
        """v5.16.0 사용자 결정 D151 — 정렬 파일 없음 = 오류(옛 비율 폴백 삭제). 비율은 '단어가 발음 텍스트에 없음'만(아래)."""
        with tempfile.TemporaryDirectory() as d:
            tb = Timebase(_plan(Path(d), "ask_1", False))
            with self.assertRaises(AlignmentMissingError):
                tb.at_word("ask_1", "한국")
            self.assertEqual(tb.word_anchors, [])

    def test_word_missing_in_tts_falls_back_with_note(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tb = Timebase(_plan(Path(d), "past_3", True))
            tb.at_word("past_3", "2020")         # 자막에만 있고 발음 텍스트는 "이천이십"
            a = tb.word_anchors[0]
            self.assertEqual(a["mode"], "ratio")
            self.assertIn("note", a)

    def test_provenance_records_mode(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _plan(Path(d), "ask_4", True)
            tb = Timebase(p)
            tb.at_word("ask_4", "한국")
            prov = build_prov(p, [], [], "2.3.0", {}, tb.word_anchors)
            self.assertEqual(prov["word_anchor"], "aligned")
            self.assertEqual(prov["word_anchors"][0]["alignment_source"], "elevenlabs_timestamps")
            self.assertEqual(prov["features_used"]["at_word"], {"aligned": 1, "ratio": 0})
            self.assertEqual(prov["tts"], {"resynthesized": []})
            self.assertEqual(prov["word_anchors"][0]["word"], "한국")
            self.assertEqual(build_prov(p, [], [], "2.3.0", {})["word_anchor"], "none")


class AlignFormatTest(unittest.TestCase):
    """표준 음성(Supertonic) 강제 정렬 → 공통 형식(D34·v5.16.0 D-0164). v5.23.0 V4(D-0212): edge WordBoundary 경로 삭제로 이쪽으로 바꿈."""

    @staticmethod
    def _spans(text: str, t0: float = 0.3, step: float = 0.1) -> list:
        from script.tts.forced_align import CharSpan

        return [CharSpan(c, t0 + step * k, t0 + step * (k + 1), 0.9) for k, c in enumerate(text)]

    def test_char_spans_become_alignment(self) -> None:
        text = "다음 날 독일, 영국"
        al = align.from_forced_alignment(text, self._spans(text))
        self.assertEqual(al["alignment_source"], "mms_forced_alignment")
        self.assertEqual(len(al["characters"]), len(text))
        st = al["character_start_times_seconds"]
        self.assertAlmostEqual(st[text.find("독일")], 0.3 + 0.1 * text.find("독일"))
        self.assertEqual(st, sorted(st))
        self.assertAlmostEqual(al["character_end_times_seconds"][-1], round(0.3 + 0.1 * len(text), 4))

    def test_mismatched_spans_is_error(self) -> None:
        with self.assertRaises(align.AlignmentError):
            align.from_forced_alignment("다음 날", self._spans("모레"))
        with self.assertRaises(align.AlignmentError):
            align.from_forced_alignment("다음 날", [])

    def test_unregistered_source_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            mp3 = Path(d) / "a.mp3"
            with self.assertRaises(align.AlignmentError):
                align.write(mp3, {"alignment_source": "whisper", "characters": [], "character_start_times_seconds": []})
            with self.assertRaises(align.AlignmentError):   # v5.23.0 V4 — edge 출처는 등재에서 빠졌다
                align.write(mp3, {"alignment_source": "edge_word_boundary", "characters": [], "character_start_times_seconds": []})
            align.align_path(mp3).write_text(json.dumps({"characters": ["가"], "character_start_times_seconds": [0.0]}))
            with self.assertRaises(align.AlignmentError):
                align.read(mp3)

    def test_forced_alignment_drives_at_word(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _plan(Path(d), "ask_1", False)
            x = p.sentences[0]
            align.write(Path(x.mp3), align.from_forced_alignment(x.tts, self._spans(x.tts, 0.2, 0.05)))
            tb = Timebase(p)
            t = tb.at_word("ask_1", "한국")
            self.assertAlmostEqual(t, T0 + 0.2 + 0.05 * x.tts.find("한국") - x.trim_offset, places=4)
            self.assertEqual(tb.word_anchors[0]["alignment_source"], "mms_forced_alignment")


if __name__ == "__main__":
    unittest.main()

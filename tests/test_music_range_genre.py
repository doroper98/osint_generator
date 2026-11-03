"""장르별 음악 레벨 범위(v7.4.0 back_and_forth D-0629 §1, D737 — 잠정, 사용자 v2 청취 판정 대기·UF-256 후속).

- 공통 범위 audio.qa.music_under_narration_db 는 그대로 [-13, -9](사용자 합격 v3 −12.7 안, 거절 v2 −17.8 밖).
- 장르 키(music_under_narration_db_by_genre)는 등록 장르만, 위 끝은 공통과 같고 아래 끝만 내린다.
- 같은 믹스(−20 dB)가 전쟁사에서는 통과, 다른 장르·장르 없음에서는 실패 — 갈림은 장르 키로만 생긴다.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from audio.qa import audio_qa, music_range
from rules import load_rules
from tests.test_audio_qa import _fixture

AU = load_rules().audio
REPO = Path(__file__).resolve().parents[1]
GENRES = {p.stem for p in (REPO / "genres").glob("*.yaml")}


class MusicRangeGenreTest(unittest.TestCase):
    def test_common_range_unchanged(self) -> None:
        self.assertEqual(tuple(AU.qa.music_under_narration_db), (-13.0, -9.0))

    def test_genre_keys_registered_and_lower_end_only(self) -> None:
        by = AU.qa.music_under_narration_db_by_genre
        self.assertTrue(set(by) <= GENRES, set(by) - GENRES)
        lo_c, hi_c = AU.qa.music_under_narration_db
        for g, (lo, hi) in by.items():
            self.assertEqual(hi, hi_c, g)   # 위 끝 = 공통(평소 크기 곡이 막히지 않게)
            self.assertLess(lo, lo_c, g)
        self.assertEqual(tuple(by["war_history"]), (-21.5, -9.0))

    def test_music_range_lookup(self) -> None:
        self.assertEqual(music_range("war_history"), (-21.5, -9.0))
        for g in GENRES - set(AU.qa.music_under_narration_db_by_genre):
            self.assertEqual(music_range(g), tuple(AU.qa.music_under_narration_db))
        self.assertEqual(music_range(None), tuple(AU.qa.music_under_narration_db))

    def test_same_mix_split_by_genre_only(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sents = _fixture(Path(d), -20.0)
            war = audio_qa(Path(d), sents, genre="war_history")
            geo = audio_qa(Path(d), sents, genre="geopolitics")
            none = audio_qa(Path(d), sents)
        self.assertAlmostEqual(war.music_under_narration_db, -20.0, delta=0.3)
        self.assertTrue(war.music_level_ok)
        self.assertFalse(geo.music_level_ok)
        self.assertFalse(none.music_level_ok)
        self.assertTrue(any("[-13, -9]" in x for x in geo.issues()))
        self.assertEqual(war.music_range, (-21.5, -9.0))


if __name__ == "__main__":
    unittest.main()

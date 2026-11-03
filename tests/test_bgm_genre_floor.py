"""전쟁사 장르 BGM 하한(v7.4.0 back_and_forth D-0626, 사용자 결정 UF-256 원문 "coriolan").

감독이 견본 둘(코리올란·Zabriskie)과 수치를 설명하고 Zabriskie 를 권한 뒤 사용자가 코리올란을 골랐다 = 장르 하한 개정의 사람 승인(C11 P11).
고정하는 것: ① 장르 몫 하한은 rules audio.bgm_floor_by_genre.war_history 키로만 갈린다 ② 공통 하한 audio.bgm_floor 는 그대로(UF-100 값)
③ bed_gain 0.43 불변(C0.2) ④ 장르 몫 곡을 다른 장르 영상에 쓰면 오류(렌더·믹스 같은 함수 audio.registry.genre_errors).
"""

from __future__ import annotations

import unittest

from audio.bgm_measure import BgmMeasure, floor_failures
from audio.registry import genre_errors, load_registry
from rules import load_rules

CORIOLAN = BgmMeasure(beat_clarity=3.69, onsets_per_min=75.3, voice_band=0.63)


class BgmGenreFloorTest(unittest.TestCase):
    def test_common_floor_unchanged(self) -> None:
        f = load_rules().audio.bgm_floor
        self.assertEqual((f.beat_clarity_min, f.onsets_per_min_min, f.voice_band_max), (6.0, 300.0, 0.10))   # UF-100 값 그대로
        self.assertEqual(load_rules().audio.bed_gain, 0.43)   # C0.2 고정

    def test_only_war_history_has_genre_floor(self) -> None:
        self.assertEqual(sorted(load_rules().audio.bgm_floor_by_genre), ["war_history"])

    def test_coriolan_passes_only_genre_floor(self) -> None:
        self.assertTrue(floor_failures(CORIOLAN))                       # 공통 하한 미달
        self.assertEqual(floor_failures(CORIOLAN, "war_history"), [])   # 전쟁사 하한 통과
        self.assertTrue(floor_failures(CORIOLAN, "geopolitics"))        # 하한이 없는 장르 = 오류 줄

    def test_registry_genre_restriction(self) -> None:
        t = load_registry().tracks["music.beethoven_coriolan"]
        self.assertEqual(t.genres, ["war_history"])
        self.assertEqual(genre_errors({"music.beethoven_coriolan"}, "war_history"), [])
        self.assertTrue(genre_errors({"music.beethoven_coriolan"}, "geopolitics"))
        self.assertEqual(genre_errors({"music.zabriskie_mario_bava"}, "geopolitics"), [])   # 공통 하한 곡은 어느 장르나


if __name__ == "__main__":
    unittest.main()

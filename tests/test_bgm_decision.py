"""v5.22.2 UF-16·30·93(D-0205 §3) — 배경음악 없음은 결정 번호(sound.no_music_decision)가 있어야 한다(bgm_decision hard)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from engine.checks import HARD, check_bgm_decision
from engine.direction import Sound


def _P(music: dict | None) -> SimpleNamespace:  # noqa: N802
    return SimpleNamespace(R=SimpleNamespace(cache={} if music is None else {"music": music}))


class TestBgmDecision(unittest.TestCase):
    def test_registered_hard(self) -> None:
        self.assertIn("bgm_decision", HARD)

    def test_no_music_without_decision_fails(self) -> None:
        """gulf 콘티 판(연출가 bgm null) — 사용자 "음악을 넣고 만들고" 전에 조용히 음악이 빠졌다."""
        self.assertEqual(len(check_bgm_decision(_P({"bgm": [], "no_music_decision": None}))), 1)
        self.assertEqual(len(check_bgm_decision(_P(None))), 1)

    def test_music_or_decision_passes(self) -> None:
        self.assertEqual(check_bgm_decision(_P({"bgm": ["music.zabriskie_patriarch"], "no_music_decision": None})), [])
        self.assertEqual(check_bgm_decision(_P({"bgm": [], "no_music_decision": "D-0084"})), [])

    def test_decision_format(self) -> None:
        Sound.model_validate({"bgm": None, "intensity": [[0, 0.5]], "no_music_decision": "D-0084"})
        with self.assertRaises(ValidationError):
            Sound.model_validate({"bgm": None, "intensity": [[0, 0.5]], "no_music_decision": "그냥"})


if __name__ == "__main__":
    unittest.main()

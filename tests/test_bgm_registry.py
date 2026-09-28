"""BGM 레지스트리 SSOT (v3.4.0, back_and_forth D-0060 작업 1·2)."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

from pydantic import ValidationError

from audio.registry import BGM_DIR, BgmError, bgm_path, card_line, description_line, load_registry, rights_music, track
from rules import load_rules

REPO = Path(__file__).resolve().parents[1]
USED = "music.zabriskie_patriarch"
CR = load_rules().credits


class RegistryParityTest(unittest.TestCase):
    def test_rights_md_attribution_verbatim(self) -> None:
        """사용 곡 표기 문구 = RIGHTS.md '작가 표준 표기' 그대로(줄바꿈만 합침)."""
        md = (BGM_DIR / "RIGHTS.md").read_text(encoding="utf-8")
        m = re.search(r"작가 표준 표기: \"(.+?)\"", md, re.S)
        assert m is not None
        self.assertEqual(" ".join(m.group(1).split()), track(USED).attribution)

    def test_rights_md_sha1_and_files_listed(self) -> None:
        md = (BGM_DIR / "RIGHTS.md").read_text(encoding="utf-8")
        self.assertIn(f"sha1 `{track(USED).sha1}`", md)
        for t in load_registry().tracks.values():
            self.assertIn(t.file, md)

    @unittest.skipUnless((BGM_DIR / track(USED).file).exists(), "BGM mp3 없음 — `python tools/fetch_data.py bgm`")
    def test_file_sha1_matches(self) -> None:
        p = bgm_path(USED)
        self.assertEqual(hashlib.sha1(p.read_bytes()).hexdigest(), track(USED).sha1)

    def test_ids_match_credit_rights_keys(self) -> None:
        """레지스트리 id = 권리 키(music.<이름>) — 엔진 권리 music 절이 레지스트리에서 나온다."""
        self.assertEqual({f"music.{k}" for k in rights_music()}, set(load_registry().tracks))

    def test_unavailable_track_cannot_be_used(self) -> None:
        off = [k for k, t in load_registry().tracks.items() if not t.available]
        self.assertTrue(off)
        with self.assertRaises(BgmError):
            bgm_path(off[0])

    def test_unknown_id_error(self) -> None:
        with self.assertRaises(BgmError):
            track("music.nope")
        with self.assertRaises(BgmError):
            track("The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3")   # 파일명은 id 가 아니다

    def test_available_requires_measurement(self) -> None:
        from audio.registry import BgmTrack  # noqa: PLC0415

        raw = track(USED).model_dump() | {"sha1": None}
        with self.assertRaises(ValidationError):
            BgmTrack.model_validate(raw)

    def test_card_and_description_text_equal_v3_handwritten(self) -> None:
        """레지스트리에서 만든 문구 = v3 수기 문구(credits.yaml·description.yaml 이관 전)."""
        self.assertEqual(card_line(USED, CR.music_card_license),
                         ("The Life and Death of a Certain K. Zabriskie, Patriarch", "Chris Zabriskie · CC BY 4.0"))
        self.assertEqual(description_line(USED, CR.music_description),
                         'Music: "The Life and Death of a Certain K. Zabriskie, Patriarch" — Chris Zabriskie (CC BY 4.0)')


class SoundIdTest(unittest.TestCase):
    def _sound(self, bgm: str) -> object:
        from engine.direction import Sound  # noqa: PLC0415

        return Sound.model_validate({"bgm": bgm, "intensity": [[0, 0.5], [1, 0.0]]})

    def test_sound_bgm_must_be_registered_id(self) -> None:
        self.assertEqual(self._sound(USED).music_ids(), {USED})
        for bad in ("bed.mp3", "music.nope", track(USED).file):
            with self.assertRaises(ValidationError):
                self._sound(bad)

    def test_credit_music_not_used_is_rights_error(self) -> None:
        from engine.credits import Credits, RightsError, check_credits  # noqa: PLC0415

        cr = Credits.model_validate({"sections": [{"title": "음악", "column": 1, "items": [{"music": USED}]}]})
        rights = {"music": rights_music()}
        check_credits(cr, rights, {}, {USED})               # 쓰고 표기함 → 통과
        with self.assertRaises(RightsError):
            check_credits(cr, rights, {}, set())            # 표기했는데 연출이 안 씀 → 불일치
        empty = Credits.model_validate({"sections": [{"title": "음악", "column": 1, "items": [{"main": "x", "license": "y"}]}]})
        with self.assertRaises(RightsError):
            check_credits(empty, rights, {}, {USED})         # 쓰는데 표기 없음 → 누락

    def test_music_credit_row_forbids_handwritten_text(self) -> None:
        from engine.credits import CreditItem  # noqa: PLC0415

        with self.assertRaises(ValidationError):
            CreditItem.model_validate({"music": USED, "license": "CC BY 4.0"})
        with self.assertRaises(ValidationError):
            CreditItem.model_validate({"music": USED, "main": "x"})

    def test_all_project_directions_use_ids(self) -> None:
        from engine.direction import yaml_load  # noqa: PLC0415

        for p in [*REPO.glob("projects/*/direction*.yaml"), REPO / "prompts" / "examples" / "hormuz_direction.yaml"]:
            if "legacy" in str(p):
                continue
            snd = (yaml_load(p.read_text(encoding="utf-8")) or {}).get("sound")
            if snd:
                with self.subTest(p=p.name):
                    track(snd["bgm"])

    def test_description_placeholder_without_music_is_error(self) -> None:
        from engine.mux import Description, build_description  # noqa: PLC0415

        d = Description.model_validate({"headline": "h", "summary": "s", "chapters": [{"at": "a", "label": "l"}],
                                        "footer": ["{music} · 내레이션"]})
        plan = type("P", (), {"cards": [], "scene_start": {"a": 0.0}})()
        self.assertIn("Music:", build_description(plan, d, [USED]))
        with self.assertRaises(ValueError):
            build_description(plan, d, [])


if __name__ == "__main__":
    unittest.main()

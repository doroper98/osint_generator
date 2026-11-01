"""F1(v3.4.0, D-0060 작업 3): 음악 크레딧 없는 프로젝트 — sound.bgm null 명시 상태, 연출가 입력 {music_list}."""

from __future__ import annotations

import pytest
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

REPO = Path(__file__).resolve().parents[1]


def _plan(tmp: Path) -> NS:
    npy = tmp / "s0.npy"
    np.save(npy, (np.sin(np.arange(22050) / 10) * 0.3).astype(np.float32))
    sent = NS(npy=str(npy), t0=1.0, t1=1.5)
    return NS(total=8.0, sentences=[sent], cards=[], scene_start={"a": 0.0, "b": 4.0})


class NullBgmMixTest(unittest.TestCase):
    def test_null_bgm_is_bed_free_mix(self) -> None:
        from audio.mix import Sound, mix  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            plan = _plan(Path(d))
            snd = Sound.model_validate({"bgm": None, "intensity": [(0.0, 0.6), (8.0, 0.0)]})
            y, _ = mix(plan, snd, None)
            z, _ = mix(plan, snd, np.zeros((44100 * 10, 2), np.float32))   # 무음 베드와 같다 = 베드가 섞이지 않았다
            self.assertTrue(np.array_equal(y, z))
            self.assertGreater(float(np.abs(y).max()), 0.0)        # 내레이션·효과음은 있다

    def test_sound_schema_accepts_null_bgm(self) -> None:
        from engine.direction import Sound  # noqa: PLC0415

        s = Sound.model_validate({"bgm": None, "intensity": [[0, 0.5], [1, 0.0]]})
        self.assertEqual(s.music_ids(), set())


@pytest.mark.slow   # C8.3(D187) — 느린 묶음(빠른 묶음 -m "not slow" 밖)
class MusicListTest(unittest.TestCase):
    def test_list_from_credits_and_empty_notice(self) -> None:
        from workers.direction_io import music_list_text  # noqa: PLC0415

        self.assertIn("music.zabriskie_patriarch", music_list_text(REPO / "projects" / "hormuz_korea"))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "credits.yaml").write_text("sections:\n  - title: 음성\n    column: 1\n    items:\n      - main: 내레이션\n"
                                           "        rights: [narration.tts]\n", encoding="utf-8")
            txt = music_list_text(p)
            self.assertIn("null", txt)
            self.assertNotIn("music.", txt)

    def test_director_prompt_has_music_list(self) -> None:
        tpl = (REPO / "prompts" / "director_user.md").read_text(encoding="utf-8")
        self.assertIn("{music_list}", tpl)
        src = (REPO / "workers" / "director_worker.py").read_text(encoding="utf-8")
        self.assertIn('.replace("{music_list}"', src)

    @unittest.skipUnless((REPO / "projects" / "hormuz_korea" / "plan.json").exists(), "hormuz plan.json 없음(생성물)")
    def test_null_bgm_needs_no_music_credit(self) -> None:
        """bgm null 이면 음악 권리가 요구되지 않는다 — 음악 크레딧 없는 프로젝트가 권리 실패 없이 로드된다."""
        from engine.credits import RightsError  # noqa: PLC0415
        from engine.project import load_project  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "hz"
            shutil.copytree(REPO / "projects" / "hormuz_korea", proj, ignore=shutil.ignore_patterns("prev", "out", "tts"))
            (proj / "tts").symlink_to(REPO / "projects" / "hormuz_korea" / "tts")
            dy = (proj / "direction.yaml").read_text(encoding="utf-8").replace("bgm: music.zabriskie_patriarch", "bgm: null")
            (proj / "direction.yaml").write_text(dy, encoding="utf-8")
            with self.assertRaises(RightsError):          # 크레딧에 음악이 남아 있으면 불일치 = 권리 오류
                load_project(proj)
            cr = (proj / "credits.yaml").read_text(encoding="utf-8")
            cr = "\n".join(ln for ln in cr.splitlines() if "music: music." not in ln) + "\n"
            (proj / "credits.yaml").write_text(cr, encoding="utf-8")
            P = load_project(proj)  # noqa: N806
            self.assertFalse({r for r in P.R.cache["credit_refs"] if r.startswith("music.")})


if __name__ == "__main__":
    unittest.main()


class NoMusicDecisionMixTest(unittest.TestCase):
    """UF-207 렌더 중 발견(감독 지시) — 연출 sound.no_music_decision(UF-16)이 있는 음악 없는 영상이 audio.mix 에서
    extra_forbidden 으로 실패했다. 믹서 Sound 는 연출 Sound 의 칸을 모두 받아야 하고, 결정 번호 정의는 한 곳이다."""

    def test_mix_accepts_direction_sound_with_decision(self) -> None:
        from audio.mix import Sound, mix  # noqa: PLC0415
        from engine.direction import Sound as DirSound  # noqa: PLC0415

        sd = DirSound.model_validate({"bgm": None, "intensity": [[0, 0.6], [8, 0.0]], "no_music_decision": "D-0205"})
        resolved = {"bgm": None, "intensity": [(float(t), v) for t, v in sd.intensity], "cues": [],
                    "no_music_decision": sd.no_music_decision}   # engine.direction 앵커 해석 뒤 모양(load_direction 반환)
        snd = Sound.model_validate(resolved)
        self.assertEqual(snd.no_music_decision, "D-0205")
        with tempfile.TemporaryDirectory() as d:
            y, _ = mix(_plan(Path(d)), snd, None)
            self.assertGreater(float(np.abs(y).max()), 0.0)

    def test_mixer_sound_covers_direction_sound_fields(self) -> None:
        from audio.mix import Sound  # noqa: PLC0415
        from engine.direction import Sound as DirSound  # noqa: PLC0415

        self.assertLessEqual(set(DirSound.model_fields), set(Sound.model_fields))
        self.assertEqual(DirSound.model_fields["no_music_decision"].metadata, Sound.model_fields["no_music_decision"].metadata)
        with self.assertRaises(ValueError):
            Sound.model_validate({"bgm": None, "intensity": [(0.0, 0.0), (1.0, 0.0)], "no_music_decision": "결정"})


class MuxDescriptionSkipTest(unittest.TestCase):
    """스케치·렌더 전용 프로젝트(description.yaml·project_manifest.json 없음)는 mux 가 설명문을 건너뛰고 사유를 남긴다.
    오케스트레이터 프로젝트(매니페스트 있음)는 설명문이 없으면 그대로 오류(load_description)."""

    def test_skip_only_without_description_and_manifest(self) -> None:
        from engine.mux import description_needed  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            rec = description_needed(p)
            self.assertFalse(rec["written"])
            self.assertIn("description.yaml", rec["reason"])
            (p / "project_manifest.json").write_text("{}", encoding="utf-8")
            self.assertTrue(description_needed(p)["written"])   # 파이프라인 프로젝트는 건너뛰지 않는다
            (p / "project_manifest.json").unlink()
            (p / "description.yaml").write_text("", encoding="utf-8")
            self.assertTrue(description_needed(p)["written"])

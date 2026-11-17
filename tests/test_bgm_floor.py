"""v7.2.0 UF-100(D-0222) — 사용자 청취 합격 BGM 등록 + 등록 실측 하한.

사용자 원문(2026-10-12): "1번만 합격. 약간 박진감이 느껴지는 부분에서 점수를 줬어."
- 레지스트리 available 곡은 실측(measured)이 있고 rules audio.bgm_floor 를 넘는다 — 못 넘는 곡은 등록 자체가 실패.
- 불합격 후보의 실측(조사 세션: 명확도 3.2~4.3·온셋 25~302)은 하한에서 걸린다.
- 새 영상 권장 BGM 첫째 = 합격곡(rules audio.bgm_default). 파일이 있으면 재측정이 기록값과 같다(측정식 고정).
"""

from __future__ import annotations

import copy
import hashlib
import unittest

import pytest
import yaml
from pydantic import ValidationError

from audio.bgm_measure import BgmMeasure, floor_failures, measure
from audio.registry import BGM_DIR, REGISTRY, BgmError, BgmRegistry, BgmTrack, bed_scale, bgm_path, load_registry, require_noncommercial_ok
from rules import load_rules

MARIO = "music.zabriskie_mario_bava"
USER = "music.yk_two_instruments"   # v7.4.0 UF-910 — 사용자 제공 곡


class FloorTest(unittest.TestCase):
    def test_user_track_registered(self) -> None:
        """v7.4.0 UF-910(D922·D923) — 사용자 제공 곡 "두 개의 악기": 권리(비상업)·실측·하한 면제·음량 배율이 기록돼 있고 파일이 저장소에 있다."""
        t = load_registry().tracks[USER]
        self.assertEqual((t.name, t.author), ("두 개의 악기", "_yk"))
        self.assertTrue(t.available and t.noncommercial and t.floor_waiver)
        self.assertIn("비상업", t.license)
        self.assertTrue(floor_failures(t.measured))                      # 하한 미달은 사실 그대로 — 면제로만 켜진다
        self.assertAlmostEqual(bed_scale(USER), 0.56)
        self.assertEqual(bed_scale(MARIO), 1.0)
        self.assertEqual(hashlib.sha1(bgm_path(USER).read_bytes()).hexdigest(), t.sha1)   # 파일 보관(.gitignore 예외)

    def test_noncommercial_needs_decision(self) -> None:
        """비상업 전용 곡은 "수익화하지 않는다"는 결정 번호 없이는 연출에서 못 쓴다(C9) — 번호가 있으면 통과, 다른 곡은 무관."""
        from engine.direction import Sound  # noqa: PLC0415

        base = {"intensity": [[0, 0.5], [10, 0.5]]}
        with self.assertRaises(ValueError):
            Sound.model_validate({**base, "bgm": USER})
        with self.assertRaises(ValueError):
            Sound.model_validate({**base, "bgm": [{"id": MARIO, "from": 0}, {"id": USER, "from": 5}]})
        self.assertEqual(Sound.model_validate({**base, "bgm": USER, "noncommercial_ok": "D923"}).bgm, USER)
        self.assertEqual(Sound.model_validate({**base, "bgm": MARIO}).bgm, MARIO)
        with self.assertRaises(BgmError):
            require_noncommercial_ok([USER], None)

    def test_waiver_required_below_floor(self) -> None:
        """하한 미달 곡은 floor_waiver(사용자 결정) 없이 available 로 등록할 수 없다."""
        raw = load_registry().tracks[USER].model_dump()
        with self.assertRaises(ValueError):
            BgmTrack.model_validate({**raw, "floor_waiver": None})

    def test_available_tracks_pass_floor(self) -> None:
        reg = load_registry()
        av = {k: t for k, t in reg.tracks.items() if t.available}
        self.assertIn(MARIO, av)
        self.assertIn("music.zabriskie_patriarch", av)   # 기준 곡(명확도 7.12)도 통과
        for k, t in av.items():
            self.assertIsNotNone(t.measured, k)
            if t.floor_waiver is None:   # 면제 곡(사용자 결정, UF-910)은 test_user_track_registered 가 본다
                self.assertEqual(floor_failures(t.measured), [], k)

    def test_rejected_candidates_fail_floor(self) -> None:
        """불합격 2~4위 실측(조사 세션 0~360초) — 박 명확도·온셋에서 걸린다."""
        for clar, ons, band in ((3.20, 302.0, 0.096), (3.17, 120.0, 0.050), (4.34, 250.0, 0.242)):
            self.assertTrue(floor_failures(BgmMeasure(beat_clarity=clar, onsets_per_min=ons, voice_band=band)))

    def test_registry_rejects_below_floor(self) -> None:
        raw = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
        bad = copy.deepcopy(raw)
        bad["tracks"][MARIO]["measured"]["beat_clarity"] = 3.2
        with self.assertRaisesRegex(ValidationError, "하한 미달"):
            BgmRegistry.model_validate(bad)
        miss = copy.deepcopy(raw)
        del miss["tracks"][MARIO]["measured"]
        with self.assertRaisesRegex(ValidationError, "measured"):
            BgmRegistry.model_validate(miss)

    def test_default_first_is_user_pass(self) -> None:
        self.assertEqual(load_rules().audio.bgm_default[0], MARIO)
        for i in load_rules().audio.bgm_default:
            self.assertTrue(load_registry().tracks[i].available, i)

    def test_attribution_and_banned(self) -> None:
        reg = load_registry().tracks
        for k in (MARIO, "music.zabriskie_patriarch"):
            self.assertIn("From the album Vendaface", reg[k].attribution)
            self.assertIn("creativecommons.org/licenses/by/4.0/", reg[k].attribution)
        d = reg["music.macleod_drone_in_d"]
        self.assertFalse(d.available)
        self.assertIn("Content ID", d.unavailable_reason or "")


@pytest.mark.slow
class RemeasureTest(unittest.TestCase):
    def test_measure_matches_record(self) -> None:
        """측정식 고정 — 파일 재측정 = 기록값(조사 세션과 같은 값: Patriarch 7.12·2.9 %, Mario Bava 6.55·8.8 %)."""
        reg = load_registry().tracks
        for k in (MARIO, "music.zabriskie_patriarch"):
            p = BGM_DIR / reg[k].file
            if not p.exists():
                self.skipTest(f"{p} 없음 — python tools/fetch_data.py bgm")
            self.assertEqual(measure(p).model_dump(), reg[k].measured.model_dump(), k)   # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()

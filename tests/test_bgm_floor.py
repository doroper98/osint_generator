"""v7.2.0 UF-100(D-0222) — 사용자 청취 합격 BGM 등록 + 등록 실측 하한.

사용자 원문(2026-10-12): "1번만 합격. 약간 박진감이 느껴지는 부분에서 점수를 줬어."
- 레지스트리 available 곡은 실측(measured)이 있고 rules audio.bgm_floor 를 넘는다 — 못 넘는 곡은 등록 자체가 실패.
- 불합격 후보의 실측(조사 세션: 명확도 3.2~4.3·온셋 25~302)은 하한에서 걸린다.
- 새 영상 권장 BGM 첫째 = 합격곡(rules audio.bgm_default). 파일이 있으면 재측정이 기록값과 같다(측정식 고정).
"""

from __future__ import annotations

import copy
import unittest

import pytest
import yaml
from pydantic import ValidationError

from audio.bgm_measure import BgmMeasure, floor_failures, measure
from audio.registry import BGM_DIR, REGISTRY, BgmRegistry, load_registry
from rules import load_rules

MARIO = "music.zabriskie_mario_bava"


class FloorTest(unittest.TestCase):
    def test_available_tracks_pass_floor(self) -> None:
        reg = load_registry()
        av = {k: t for k, t in reg.tracks.items() if t.available}
        self.assertIn(MARIO, av)
        self.assertIn("music.zabriskie_patriarch", av)   # 기준 곡(명확도 7.12)도 통과
        for k, t in av.items():
            self.assertIsNotNone(t.measured, k)
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

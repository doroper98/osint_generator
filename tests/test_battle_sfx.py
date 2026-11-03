"""녹음 효과음 층(v7.4.0 back_and_forth D-0627 §2·D-0628 §3·D-0629 §2, 사용자 의견 UF-258) — 레지스트리·큐 종류(스키마·믹서·프리뷰 예제)·겹치기 조건·[battle-sfx].

- 큐 종류 = rules registries.sound_cue_kinds. 종류마다 프리뷰 예제가 있고 audio.mix Cue 를 통과하며 믹서가 처리한다(15 P10).
- 겹치기 조건(D-0629 §2): 같은 녹음 테이크·사본만, 사본마다 음높이·속도 ±pitch_pct_max %(≤ 5) 안, 말 울음 큐 하나에 많아야 하나, 기록 남김.
- [battle-sfx]: 부대 기록에 없는 부대·병종 표에 없는 소리(칸나이 활·투석) = 실패, CC BY 원천은 크레딧 sfx 행, 쓰지 않는 크레딧 행 = 실패.
실제 녹음 파일(저장소 미추적)을 쓰는 렌더 시험은 slow 묶음이다.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

import audio.sfx as S
from audio.mix import SR, Cue, Sfx
from engine import checks as C
from engine.credits import CreditItem
from engine.direction import SoundCue, _cue
from rules import load_rules

FIX = Path(__file__).resolve().parent / "fixtures" / "preview"
BS = load_rules().audio.battle_sfx
UNITS = {"로마 중무장보병": "heavy_inf", "아프리카 중무장보병": "heavy_inf", "누미디아 기병": "light_cav", "로마 기병": "heavy_cav"}


def _clicks(n_sec: float = 4.0, every: float = 0.5) -> np.ndarray:
    y = np.zeros(int(n_sec * SR), np.float32)
    for k in range(int(n_sec / every)):
        i = int((k * every + 0.1) * SR)
        y[i:i + 400] = np.hanning(400) * np.sin(np.arange(400) * 0.6)
    return y


class CueRegistryTest(unittest.TestCase):
    def test_every_kind_has_fixture_and_model(self) -> None:
        kinds = load_rules().registries.sound_cue_kinds
        self.assertEqual(set(kinds), {"whoosh", "boom", "tick", "battle"})
        for k in kinds:
            with self.subTest(kind=k):
                doc = yaml.safe_load((FIX / f"sound_cue_{k}.yaml").read_text(encoding="utf-8"))
                self.assertEqual(doc["key"], f"sound_cue:{k}")
                self.assertEqual(Cue.model_validate(doc["cue"]).kind, k)

    def test_mixer_handles_every_kind(self) -> None:
        sfx = Sfx(int(12 * SR), np.random.default_rng(3))
        for k in load_rules().registries.sound_cue_kinds:
            cue = Cue.model_validate(yaml.safe_load((FIX / f"sound_cue_{k}.yaml").read_text(encoding="utf-8"))["cue"])
            with mock.patch.object(S, "render_battle", return_value=(np.ones(SR, np.float32) * 0.1, {"sound": cue.sound, "ids": []})):
                sfx.cue(cue)
        self.assertGreater(float(np.abs(sfx.fx).max()), 0)
        self.assertEqual(len(sfx.log), 1)   # battle 만 기록

    def test_bad_cues(self) -> None:
        with self.assertRaises(ValidationError):
            Cue.model_validate({"kind": "bow", "t": 1.0})                       # 등록 밖 종류
        with self.assertRaises(ValidationError):
            Cue.model_validate({"kind": "battle", "t": 1.0, "dur": 4.0, "sound": "gallop", "dist": "far"})   # units 없음
        with self.assertRaises(ValidationError):
            Cue.model_validate({"kind": "boom", "t": 1.0, "sound": "gallop"})   # 합성 큐에 녹음 칸

    def test_direction_end_anchor_to_dur(self) -> None:
        d = yaml.safe_load((FIX / "sound_cue_battle.yaml").read_text(encoding="utf-8"))["direction"]
        sc = SoundCue.model_validate({**d, "t": 3.0, "end": 11.5})
        got = _cue(sc, None)   # 숫자 앵커는 Timebase 없이 해석된다
        self.assertEqual((got["t"], got["dur"], got["sound"], got["units"]), (3.0, 8.5, "melee_metal", d["units"]))
        Cue.model_validate(got)


class LayerRulesTest(unittest.TestCase):
    def test_pitch_limit_and_whinny(self) -> None:
        self.assertLessEqual(BS.layer.pitch_pct_max, 5.0)   # D-0629 §2-2
        self.assertLessEqual(BS.layer.whinny_max_per_cue, 1)   # D-0628 §3
        self.assertEqual(set(BS.licenses), {"PD", "PDM", "CC0", "CC BY 4.0"})   # D-0627 §2-4
        self.assertNotIn("bow", BS.kinds)   # 칸나이 활 소리 없음(D-0627 §2-3)

    def test_repitch_changes_length_only_by_factor(self) -> None:
        y = np.sin(np.arange(SR) * 0.05).astype(np.float32)
        self.assertEqual(len(S.repitch(y, 1.05)), round(SR / 1.05))

    def test_onsets_find_takes(self) -> None:
        self.assertEqual(len(S.onsets(_clicks())), 8)

    def test_whinny_one_call(self) -> None:
        """파일에 울음이 여럿이어도 큐 하나에 울음 한 번(D-0628 §3) — 실측 Wiehern 2·Briefer S1 3."""
        y = np.zeros(int(3.0 * SR), np.float32)
        for a in (0.2, 1.2, 2.2):   # 울음 사이 0.5초 > merge_gap_sec
            i = int(a * SR)
            y[i:i + int(0.5 * SR)] = np.sin(np.arange(int(0.5 * SR)) * 0.08)
        self.assertEqual(len(S.calls(y)), 3)
        with mock.patch.object(S, "decode", return_value=y), mock.patch.object(S, "ids_for", return_value=["sfx.w"]):
            out, rec = S.render_battle("whinny", 4.0, "far", 1.0, np.random.default_rng(7))
        (c0, c1), = [p["call_sec"] for p in rec["parts"]]
        self.assertLess(c1 - c0, 0.5 + 2 * BS.call.pre_sec + 0.1)   # 울음 한 번 길이

    def test_render_rules_with_synthetic_sources(self) -> None:
        srcs = {"sfx.a": _clicks(), "sfx.b": _clicks(3.0, 0.4), "sfx.g": np.sin(np.arange(20 * SR) * 0.01).astype(np.float32)}
        kinds = {"melee_metal": ["sfx.a", "sfx.b"], "gallop": ["sfx.g"], "whinny": ["sfx.a"], "crowd": ["sfx.g"]}
        with mock.patch.object(S, "decode", side_effect=lambda sid: srcs[sid]), mock.patch.object(S, "ids_for", side_effect=lambda k: kinds[k]):
            for snd in BS.kinds:
                with self.subTest(sound=snd):
                    y1, r1 = S.render_battle(snd, 6.0, "far", 0.8, np.random.default_rng(7))
                    y2, _ = S.render_battle(snd, 6.0, "far", 0.8, np.random.default_rng(7))
                    np.testing.assert_array_equal(y1, y2)                      # 결정성(시드)
                    self.assertEqual(len(y1), int(6.0 * SR))
                    self.assertLessEqual(float(np.abs(y1).max()), BS.peak * 0.8 + 1e-6)
                    lo, hi = r1["pitch_range"]
                    self.assertGreaterEqual(lo, 1 - BS.layer.pitch_pct_max / 100 - 1e-9)
                    self.assertLessEqual(hi, 1 + BS.layer.pitch_pct_max / 100 + 1e-9)
                    self.assertTrue(set(r1["ids"]) <= set(kinds[snd]))         # 그 종류 녹음만
                    if snd == "whinny":
                        self.assertLessEqual(r1["layers"], BS.layer.whinny_max_per_cue)
            with self.assertRaises(S.SfxError):
                S.render_battle("melee_metal", 6.0, "near", 0.8, np.random.default_rng(7))   # 가까운 소리 없음


class RegistryTest(unittest.TestCase):
    def test_registry_entries_rights(self) -> None:
        reg = S.load_sfx_registry()
        self.assertTrue(reg.sounds)
        for sid, e in reg.sounds.items():
            with self.subTest(sid=sid):
                self.assertIn(e.license, BS.licenses)
                self.assertTrue(e.recorded)
                self.assertTrue(e.license_basis and "PENDING" not in e.license_basis)
                self.assertRegex(e.sha1, r"^[0-9a-f]{40}$")
        self.assertEqual({e.kind for e in reg.sounds.values()}, set(BS.kinds))   # 종류마다 녹음이 하나 이상

    def test_entry_validation(self) -> None:
        base = dict(file="x.ogg", sha1="0" * 40, duration_sec=1.0, kind="whinny", recorded=True, title="t", author="a",
                    license="CC0", license_basis="q", page_url="u", media_url="m", source="s")
        S.SfxEntry.model_validate(base)
        for bad in ({"license": "CC BY-SA 4.0"}, {"license": "CC BY-NC 4.0"}, {"recorded": False}, {"kind": "bow"},
                    {"license": "CC BY 4.0"}):   # 마지막 = CC BY 인데 attribution 없음
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                S.SfxEntry.model_validate({**base, **bad})

    def test_credit_row(self) -> None:
        self.assertEqual(CreditItem.model_validate({"sfx": "sfx.bsb_gallop_1850"}).label, "sfx.bsb_gallop_1850")
        with self.assertRaises(ValidationError):
            CreditItem.model_validate({"sfx": "sfx.bsb_gallop_1850", "license": "CC0"})
        with self.assertRaises(ValidationError):
            CreditItem.model_validate({"sfx": "sfx.a", "music": "music.b"})


class BattleSfxCheckTest(unittest.TestCase):
    def _cue(self, **kw: object) -> dict:
        return {"kind": "battle", "t": 10.0, "dur": 8.0, "v": 0.8, "sound": "melee_metal", "dist": "far", "units": ["로마 중무장보병"], **kw}

    def _hits(self, cues: list[dict], credited: set[str] = frozenset()) -> list[str]:   # type: ignore[assignment]
        with mock.patch.object(S, "sfx_path", return_value=Path("x")):
            return C.battle_sfx_hits(cues, UNITS, set(credited))

    def test_ok(self) -> None:
        self.assertEqual(self._hits([self._cue(), self._cue(sound="gallop", units=["누미디아 기병"])]), [])

    def test_unit_missing_or_wrong_sound(self) -> None:
        self.assertTrue(any("부대 기록" in x for x in self._hits([self._cue(units=["로마 궁병"])])))
        self.assertTrue(any("unit_sounds" in x for x in self._hits([self._cue(sound="gallop")])))   # 보병에 말 소리
        self.assertTrue(any("kinds 밖" in x for x in self._hits([self._cue(sound="bow")])))          # 활 소리(칸나이 없음)

    def test_credit_consistency(self) -> None:
        self.assertTrue(any("쓰지 않는다" in x for x in self._hits([self._cue()], {"sfx.bsb_gallop_1850"})))
        e = S.entry("sfx.commons_wiehern").model_copy(update={"license": "CC BY 4.0", "attribution": "x"})
        with mock.patch.object(S, "entry", return_value=e):
            got = self._hits([self._cue(sound="whinny", units=["누미디아 기병"])])
        self.assertTrue(any("크레딧 sfx 행 없음" in x for x in got))

    def test_registered_as_hard_and_warning(self) -> None:
        self.assertIn("battle_sfx", C.HARD)
        self.assertIn("battle_sfx_missing", C.WARN)


@pytest.mark.slow   # C8.3(D187) — 실제 녹음 파일(assets/audio/sfx/files, 저장소 미추적)
class RealSourcesTest(unittest.TestCase):
    def test_real_render(self) -> None:
        for sid in S.load_sfx_registry().sounds:
            S.sfx_path(sid)   # 없거나 sha1 불일치 = 오류(조용히 빼지 않음)
        for snd in BS.kinds:
            y, rec = S.render_battle(snd, 10.0, "far", 1.0, np.random.default_rng(BS.seed))
            self.assertGreater(float(np.abs(y).max()), 0, snd)
            self.assertTrue(rec["ids"], snd)


if __name__ == "__main__":
    unittest.main()

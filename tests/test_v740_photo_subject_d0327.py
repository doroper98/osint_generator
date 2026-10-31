"""v7.4.0 back_and_forth D-0327 — 사진의 주된 피사체가 문장 대상이어야 한다(사용자 의견 UF-201 "블라디보스토크항의 이미지로 이런 통통배(터그선)이미지가
크게 박힌 이미지를 쓰는게 맞아?"). 레지스트리 main_subject·background, 연출 photo for·age_reason, [photo-subject-background]·[photo-subject-unmatched] hard,
[photo-age] warning."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

import yaml

from engine import checks
from engine.media_registry import load_media_registry
from tests.anti_inertia._ast_util import REPO

TUG = "diesel_road_2026_vladivostok_port_1992"


class RegistryTest(unittest.TestCase):
    def test_showcase_photos_have_subjects(self) -> None:
        reg = load_media_registry()
        for pid in ("showcase_geo", "showcase_econ"):
            d = yaml.safe_load((REPO / "projects" / pid / "direction.yaml").read_text(encoding="utf-8"))
            for e in d["events"]:
                if e.get("type") == "photo":
                    self.assertTrue(reg[e["mid"]].main_subject, e["mid"])
                    self.assertTrue(e.get("for"), e["mid"])

    def test_tug_is_tug(self) -> None:
        a = load_media_registry()[TUG]
        self.assertEqual(a.main_subject, ["예인선"])
        self.assertIn("블라디보스토크 항(금각만)", a.background)


class CheckTest(unittest.TestCase):
    def _P(self, ev: dict, sdate: str = "2026.08") -> NS:
        a = NS(main_subject=["예인선"], background=["블라디보스토크 항(금각만)"], file_note="자료사진 · 1992. 09", date="1992-09-23")
        return NS(events=[ev], R=NS(assets=NS(media_assets={"m": a}), cache={"genre": {"name": "geopolitics"}}),
                  plan=NS(sentences=[NS(t0=0.0, t1=5.0, date=sdate)]))

    def test_background_only_is_hard(self) -> None:
        P = self._P({"type": "photo", "mid": "m", "t0": 1.0, "t1": 4.0, "for_": "블라디보스토크 항(금각만)"})  # noqa: N806
        self.assertEqual(len(checks.check_photo_subject_background(P)), 1)
        self.assertEqual(checks.check_photo_subject_unmatched(P), [])
        self.assertIn("photo_subject_background", checks.HARD)

    def test_missing_for_is_unmatched(self) -> None:
        P = self._P({"type": "photo", "mid": "m", "t0": 1.0, "t1": 4.0})  # noqa: N806
        self.assertEqual(len(checks.check_photo_subject_unmatched(P)), 1)
        self.assertIn("photo_subject_unmatched", checks.HARD)

    def test_age_warning_and_reason(self) -> None:
        ev = {"type": "photo", "mid": "m", "t0": 1.0, "t1": 4.0, "for_": "예인선"}
        self.assertEqual(len(checks.check_photo_age(self._P(ev))), 1)   # 1992 → 2026 = 33.9년 > 15
        self.assertEqual(checks.check_photo_age(self._P({**ev, "age_reason": "현존 사진 없음"})), [])
        self.assertIn("photo_age", checks.WARN)
        with mock.patch("genres.load.load_genre", return_value=NS(photo_age_check=False)):
            self.assertEqual(checks.check_photo_age(self._P(ev)), [])   # 역사 장르는 끔


if __name__ == "__main__":
    unittest.main()

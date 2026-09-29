"""장르 프로필 스키마 (v4.2.0, docs/handoff/20 §3, back_and_forth D-0081 작업 1·9).

미등록 무대·요소·qa_extra = 로드 오류(15 P10), approved 가 planned 참조 = 오류, proposed 는 planned 허용.
"""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

from genres.load import GenreError, load_genre_file
from schemas.genre_models import GenreProfile, check_ids, registered_elements

BASE: dict = {
    "genre": "sample",
    "status": "approved",
    "stage": {"primary": "mercator", "secondary": []},
    "color_semantics": {"confrontation": "ru", "hike": "#ff7a59", "band": "rgba(232,184,96,0.15)"},
    "primitives": {"reuse": ["marker", "card", "versus", "person"], "new": []},
    "badges": {"people": "from_library"},
    "qa_extra": ["stage_continuity"],
}


def prof(**over: object) -> dict:
    d = copy.deepcopy(BASE)
    for k, v in over.items():
        d[k] = v
    return d


class GenreProfileSchemaTest(unittest.TestCase):
    def test_minimal_passes(self) -> None:
        p = GenreProfile.model_validate(prof())
        self.assertEqual(p.elements(), {"marker", "card", "versus", "person"})

    def test_extra_key_forbidden(self) -> None:
        with self.assertRaises(ValidationError):
            GenreProfile.model_validate(prof(tone="dramatic"))

    def test_unregistered_stage(self) -> None:
        with self.assertRaisesRegex(ValidationError, "레지스트리에 없음"):
            GenreProfile.model_validate(prof(stage={"primary": "globe"}))

    def test_approved_planned_stage_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "stages_planned"):
            GenreProfile.model_validate(prof(stage={"primary": "timeline"}))

    def test_proposed_planned_stage_allowed(self) -> None:
        p = GenreProfile.model_validate(prof(status="proposed", stage={
            "primary": "timeline", "secondary": ["chart_wall"],
            "timeline": {"lanes": [{"id": "rate", "label": "기준금리", "kind": "step", "unit": "%"}]}}))
        self.assertEqual(p.stage.names(), ["timeline", "chart_wall"])

    def test_secondary_limit(self) -> None:
        with self.assertRaisesRegex(ValidationError, "max_secondary"):
            GenreProfile.model_validate(prof(status="proposed", stage={"primary": "timeline", "secondary": ["chart_wall", "flow"]}))

    def test_settings_for_unused_stage(self) -> None:
        with self.assertRaisesRegex(ValidationError, "주·보조 무대가 아닌"):
            GenreProfile.model_validate(prof(stage={"primary": "mercator", "timeline": {"lanes": [{"id": "a", "label": "a", "kind": "line"}]}}))

    def test_unregistered_reuse(self) -> None:
        for bad in ("timeline_panel", "occupied"):   # 레지스트리 밖 / event_types_planned
            with self.subTest(bad=bad), self.assertRaisesRegex(ValidationError, "등록 요소가 아님"):
                GenreProfile.model_validate(prof(primitives={"reuse": ["card", bad]}))

    def test_unregistered_new(self) -> None:
        with self.assertRaisesRegex(ValidationError, "registries.primitives 에 없음"):
            GenreProfile.model_validate(prof(primitives={"reuse": ["card"], "new": ["hologram"]}))

    def test_reuse_new_overlap(self) -> None:
        with self.assertRaises(ValidationError):
            GenreProfile.model_validate(prof(primitives={"reuse": ["card"], "new": ["card"]}))

    def test_qa_extra_unknown(self) -> None:
        with self.assertRaisesRegex(ValidationError, "결정적 검사 id 가 아님"):
            GenreProfile.model_validate(prof(qa_extra=["vibes"]))

    def test_qa_extra_planned(self) -> None:
        with self.assertRaisesRegex(ValidationError, "qa_checks.planned"):
            GenreProfile.model_validate(prof(qa_extra=["chart_honesty"]))
        GenreProfile.model_validate(prof(status="proposed", qa_extra=["chart_honesty", "overlap"]))

    def test_color_values(self) -> None:
        for bad in ("red", "#ff00", "rgba(300,0,0,0.5)", "rgba(0,0,0,1.5)"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValidationError, "color_semantics"):
                GenreProfile.model_validate(prof(color_semantics={"x": bad}))

    def test_registry_views(self) -> None:
        self.assertIn("panel", registered_elements())
        self.assertIn("versus", registered_elements())
        self.assertIn("stage_continuity", check_ids())


class GenreLoaderTest(unittest.TestCase):
    def test_file_name_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "other.yaml"
            p.write_text(yaml.safe_dump(prof(), allow_unicode=True), encoding="utf-8")
            with self.assertRaisesRegex(GenreError, "파일 이름"):
                load_genre_file(p)
            ok = Path(d) / "sample.yaml"
            ok.write_text(yaml.safe_dump(prof(), allow_unicode=True), encoding="utf-8")
            self.assertEqual(load_genre_file(ok).genre, "sample")

    def test_missing_genre(self) -> None:
        from genres.load import load_genre  # noqa: PLC0415

        with self.assertRaisesRegex(GenreError, "장르 프로필 없음"):
            load_genre("no_such_genre")


if __name__ == "__main__":
    unittest.main()

"""direction `genre` 키·무대-프로필 대조·checks genre_elements (v4.2.0, back_and_forth D-0081 작업 3·9)."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from pydantic import ValidationError

from engine.checks import HARD, check_genre_elements
from engine.direction import Direction, load_direction_doc
from genres.elements import event_elements, outside, used_elements
from genres.load import load_genre
from schemas.genre_models import GenreProfile

REPO = Path(__file__).resolve().parent.parent
DOC: dict = {
    "version": 1,
    "places": {"hormuz": [56.35, 26.55]},
    "shots": [{"at": 0, "mode": "cut", "dur": 0, "camera": {"place": "hormuz", "w": 14}}],
    "events": [{"type": "marker", "start": 0.2, "end": 10.0, "at_place": "hormuz", "label": "호르무즈 해협"}],
}
TIMELINE_GENRE = GenreProfile.model_validate({
    "genre": "tl_only", "status": "proposed", "stage": {"primary": "timeline"},
    "color_semantics": {"hike": "#ff7a59"}, "primitives": {"reuse": ["card"]}})


def doc(**over: object) -> dict:
    d = copy.deepcopy(DOC)
    d.update(over)
    return d


def fake_load_genre(name: str) -> GenreProfile:
    return TIMELINE_GENRE if name == "tl_only" else load_genre(name)


class GenreDirectionTest(unittest.TestCase):
    def test_default_genre(self) -> None:
        d = Direction.model_validate(doc())
        self.assertIsNone(d.genre)
        self.assertEqual(d.genre_name(), "geopolitics")
        self.assertEqual(d.main_stage(), "mercator")   # 프로필 primary

    def test_declared_genre(self) -> None:
        d = Direction.model_validate(doc(genre="geopolitics", stage="mercator"))
        self.assertEqual((d.genre_name(), d.main_stage()), ("geopolitics", "mercator"))

    def test_unknown_genre(self) -> None:
        with self.assertRaisesRegex(ValidationError, "장르 프로필 없음"):
            Direction.model_validate(doc(genre="astrology"))

    def test_stage_outside_profile(self) -> None:
        with mock.patch("genres.load.load_genre", fake_load_genre):
            with self.assertRaisesRegex(ValidationError, "프로필 무대"):
                Direction.model_validate(doc(genre="tl_only", stage="mercator"))
            shots = [dict(DOC["shots"][0], stage="mercator")]
            with self.assertRaisesRegex(ValidationError, r"shots\[0\]\.stage"):
                Direction.model_validate(doc(genre="tl_only", shots=shots))

    def test_stage_default_from_profile(self) -> None:
        with mock.patch("genres.load.load_genre", fake_load_genre):
            d = Direction.model_validate(doc(genre="tl_only"))
            self.assertEqual(d.main_stage(), "timeline")   # 프로필 primary(무대 구현은 G3 — 렌더 시 StageError)


class GenreElementsTest(unittest.TestCase):
    def test_event_elements(self) -> None:
        self.assertEqual(event_elements({"type": "panel", "kind": "versus"}), ["versus"])
        self.assertEqual(event_elements({"type": "panel", "data": {"kind": "dots"}}), ["dots"])
        self.assertEqual(event_elements({"type": "primitive", "id": "statement_diff"}), ["statement_diff"])
        self.assertEqual(event_elements({"type": "badge", "kind": "person"}), ["badge", "person"])
        self.assertEqual(event_elements({"type": "marker"}), ["marker"])

    def test_golden_projects_inside_geopolitics(self) -> None:
        allowed = load_genre("geopolitics").elements()
        for proj in ("hormuz_korea", "ratcliffe2026"):
            with self.subTest(proj=proj):
                d = load_direction_doc(REPO / "projects" / proj / "direction.yaml")
                used = used_elements(d.events)
                self.assertTrue(used)
                self.assertEqual(outside(used, allowed), {})

    def test_check_is_hard_and_fails_outside(self) -> None:
        self.assertIn("genre_elements", HARD)
        ev = [{"type": "marker"}, {"type": "primitive", "id": "statement_diff"}, {"type": "panel", "kind": "versus"}]
        P = SimpleNamespace(R=SimpleNamespace(cache={"genre": {"name": "geopolitics", "elements_used": used_elements(ev)}}))  # noqa: N806
        out = check_genre_elements(P)
        self.assertEqual(len(out), 1)
        self.assertIn("statement_diff", out[0])
        P.R.cache["genre"]["elements_used"] = used_elements(ev[:1] + ev[2:])
        self.assertEqual(check_genre_elements(P), [])


if __name__ == "__main__":
    unittest.main()

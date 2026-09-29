"""direction `stage`·`shots[].stage` 와 무대 인스턴스 (v4.1.0, back_and_forth D-0076 작업 4·D-0077 쟁점 1·3B)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import yaml

from engine import stage as S
from engine.direction import Direction, DirectionError, build, load_direction_doc, shot_stages
from engine.stage import MercatorStage, StageSet, ym
from engine.timebase import Timebase
from genres.load import load_genre
from rules import load_rules
from schemas.genre_models import GenreProfile
from tests.test_direction_schema import _plan

REPO = Path(__file__).resolve().parent.parent
PREVIEW = REPO / "tests" / "fixtures" / "preview"


class DirectionStageKeyTest(unittest.TestCase):
    def test_v3_direction_is_undeclared_mercator(self) -> None:
        """v3 원본 direction.yaml 무수정(D-0056) — stage 없음 = mercator, declared false."""
        doc = load_direction_doc(REPO / "projects" / "hormuz_korea" / "direction.yaml")
        self.assertIsNone(doc.stage)
        self.assertEqual(doc.main_stage(), "mercator")
        self.assertTrue(all(s.stage is None for s in doc.shots))

    def test_unregistered_stage_is_schema_error(self) -> None:
        raw = yaml.safe_load((PREVIEW / "stage_mercator.yaml").read_text(encoding="utf-8"))["direction"]
        for bad in ({**raw, "stage": "timeline"}, {**raw, "shots": [{**raw["shots"][0], "stage": "chart_wall"}]}):
            with self.assertRaises(ValueError):
                Direction.model_validate(bad)

    def test_shot_on_other_stage_is_not_rendered(self) -> None:
        """보조 무대 렌더는 G3 — 주 무대와 다른 숏은 조용히 지도로 그리지 않고 오류(P6)."""
        rules = load_rules()
        fake = rules.model_copy(update={"registries": rules.registries.model_copy(update={"stages": ["mercator", "timeline"]})})
        with mock.patch("rules.load_rules", return_value=fake), mock.patch.dict(S.STAGE_CLASSES, {"timeline": MercatorStage}):
            # v4.2.0 D-0081 작업 3 — 숏 무대는 장르 프로필 무대 안이어야 한다: timeline 을 보조 무대로 둔 가짜 장르
            geo = load_genre("geopolitics").model_dump()
            prof = GenreProfile.model_validate({**geo, "stage": {"primary": "mercator", "secondary": ["timeline"]}})
            stack = mock.patch("genres.load.load_genre", return_value=prof)
            stack.start()
            self.addCleanup(stack.stop)
            raw = yaml.safe_load((PREVIEW / "stage_mercator.yaml").read_text(encoding="utf-8"))["direction"]
            doc = Direction.model_validate({**raw, "shots": [raw["shots"][0], {**raw["shots"][1], "stage": "timeline"}]})
            with self.assertRaises(DirectionError):
                build(doc, Timebase(_plan()), MercatorStage())
            ss = StageSet()
            shots = shot_stages(doc, Timebase(_plan()), ss.get)
        self.assertEqual([s.stage for s in shots], ["mercator", "timeline"])
        self.assertEqual([s.mode for s in shots], ["cut", "dip"])
        self.assertEqual((shots[1].x, shots[1].y), (127.0, ym(37.45)))


class StageRegistryPreviewTest(unittest.TestCase):
    def test_every_stage_has_preview_example(self) -> None:
        """레지스트리 무대마다 구현·프리뷰 예제(스키마 통과) — 세 곳 동시(C7, P10)."""
        for name in load_rules().registries.stages:
            self.assertIn(name, S.STAGE_CLASSES)
            ex = yaml.safe_load((PREVIEW / f"stage_{name}.yaml").read_text(encoding="utf-8"))
            doc = Direction.model_validate(ex["direction"])
            self.assertEqual(doc.main_stage(), name)
            self.assertEqual(tuple(ex["anchor_keys"]), S.STAGE_CLASSES[name].anchor_keys)


class StageSetTest(unittest.TestCase):
    def test_one_instance_per_name(self) -> None:
        ss = StageSet()
        a = ss.get("mercator")
        b = ss.get("mercator")
        self.assertIs(a, b)
        self.assertEqual(ss.created, {"mercator": 1})

    def test_make_stage_called_once(self) -> None:
        with mock.patch("engine.stage.make_stage", wraps=S.make_stage) as mk:
            ss = StageSet()
            for _ in range(5):
                ss.get("mercator")
        self.assertEqual(mk.call_count, 1)


if __name__ == "__main__":
    unittest.main()

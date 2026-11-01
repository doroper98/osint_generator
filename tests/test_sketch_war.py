"""sketch.war(v7.4.0 전쟁사 W3·W4, back_and_forth D-0600 §5·§6) — spec·키프레임·작품 라벨·부호 세트 검사."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

from schemas.era_date import parse_era_date
from schemas.media_models import MediaRegistryFile
from schemas.war_history import era_of, period_art_label, symbol_set_mixed
from sketch.war.scene import card_texts
from sketch.war.spec import WarSpec
from sketch.war.units import key_at

REPO = Path(__file__).resolve().parents[1]
CASES = ("cannae_sketch", "inchon_sketch")


def spec(pid: str) -> WarSpec:
    return WarSpec.model_validate(yaml.safe_load((REPO / "projects" / pid / "sketch.yaml").read_text(encoding="utf-8")))


class SpecTest(unittest.TestCase):
    def test_cases_load_and_era(self) -> None:
        self.assertEqual(era_of(spec("cannae_sketch").dates[0].date), "ancient")
        self.assertEqual(era_of(spec("inchon_sketch").dates[0].date), "modern")

    def test_cases_use_own_symbol_set(self) -> None:
        for pid in CASES:
            s = spec(pid)
            self.assertEqual(symbol_set_mixed(era_of(s.dates[0].date), [u.symbol for u in s.units]), [], pid)

    def test_mixed_symbol_is_caught(self) -> None:
        s = spec("cannae_sketch")
        self.assertTrue(symbol_set_mixed(era_of(s.dates[0].date), [u.symbol for u in s.units] + ["app6_inf"]))

    def test_keyframes_smooth_and_held(self) -> None:
        u = next(u for u in spec("cannae_sketch").units if u.name == "로마 중무장보병")
        a, b = u.keys[1], u.keys[2]
        mid = key_at(u, (a.t + b.t) / 2)
        self.assertTrue(min(a.lat, b.lat) < mid.lat < max(a.lat, b.lat))
        self.assertEqual(key_at(u, u.keys[-1].t + 10).lat, u.keys[-1].lat)
        self.assertEqual(key_at(u, 0).lat, u.keys[0].lat)


class EvidenceTest(unittest.TestCase):
    def test_cannae_labels(self) -> None:
        m = MediaRegistryFile.model_validate(json.loads((REPO / "projects/cannae_sketch/media.json").read_text(encoding="utf-8"))).assets
        ev = parse_era_date("-216.08.02")
        self.assertEqual(period_art_label(m["cannae_coin"].created, ev), "당대 묘사")
        self.assertTrue(period_art_label(m["cannae_bust"].created, ev).startswith("후대의 묘사"))
        self.assertEqual(period_art_label(m["cannae_trumbull"].created, ev), "후대의 묘사(1773)")
        cap, credit = card_texts(m["cannae_bust"], "-216.08.02")
        self.assertEqual(cap, "한니발로 추정되는 대리석 흉상")
        self.assertTrue(credit.startswith("후대의 묘사"))

    def test_inchon_records(self) -> None:
        m = MediaRegistryFile.model_validate(json.loads((REPO / "projects/inchon_sketch/media.json").read_text(encoding="utf-8"))).assets
        self.assertEqual({a.kind for a in m.values()}, {"photo", "document", "video"})   # v2 — 기록 영상 clip 층(D-0607 §2)
        self.assertTrue(all(a.archive_id for a in m.values()))


if __name__ == "__main__":
    unittest.main()


class AncientGeoUntrackedTest(unittest.TestCase):
    def test_extracted_geodata_not_tracked(self) -> None:
        """D-0601 ① c — 고대 지리 추출 자료(AWMC ODbL·Pleiades)는 저장소에 올리지 않는다(프로젝트 ancient_geo/·캐시 .cache/)."""
        import subprocess

        files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual([f for f in files if "/ancient_geo/" in f or f.startswith(".cache/") or "Cultural-Data/" in f], [])

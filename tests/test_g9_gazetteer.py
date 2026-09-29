"""v4.10.0 G9 — 지명 사전(`data/gazetteer.yaml`)과 `[geo-mismatch]` hard (back_and_forth D-0116 작업 1, B-1)."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import yaml

from engine.checks import HARD, WARN, check_geo_mismatch, check_geo_unsourced
from engine.direction import Direction, geo_unsourced, load_direction_doc
from geo.gazetteer import Gazetteer, GazetteerEntry, check_doc, haversine_km, load_gazetteer, norm_name
from rules import load_rules
from tools.build_gazetteer import build, dump, ne_entries

REPO = Path(__file__).resolve().parent.parent


def _doc(events: list, places: dict | None = None, paths: dict | None = None) -> Direction:
    return Direction.model_validate({"places": places or {}, "paths": paths or {},
                                     "shots": [{"at": 0, "mode": "cut", "dur": 0, "camera": {"lon": 127.0, "lat": 38.0, "w": 6}}],
                                     "events": events})


def _entry(eid: str, names: list[str], lonlat: tuple[float, float], tol: float, kind: str = "city") -> GazetteerEntry:
    return GazetteerEntry(id=eid, names=names, lonlat=lonlat, tol_km=tol, kind=kind, src="test")


GZ = Gazetteer(source={}, manual=[_entry("gulf_of_aden", ["Gulf of Aden", "아덴만"], (48.0, 12.0), 400, "gulf")],
               ne=[_entry("aden_yem", ["Aden", "아덴"], (45.0095, 12.7797), 25), _entry("seoul_kor", ["Seoul", "서울"], (126.9978, 37.5683), 25)])


class GazetteerFileTest(unittest.TestCase):
    def test_tracked_file_valid_and_sourced(self) -> None:
        g = load_gazetteer()
        self.assertGreater(len(g.ne), 3000)                       # 수도 + 인구 10만 이상
        self.assertTrue(g.source["ne"].endswith("ne_10m_populated_places.geojson"))
        self.assertRegex(g.source["ne_md5"], r"^[0-9a-f]{32}$")
        self.assertEqual(g.source["ne_tol_km"], load_rules().geo.gazetteer.ne_tol_km)
        ids = [e.id for e in g.entries()]
        self.assertEqual(len(ids), len(set(ids)))
        for e in g.manual:                                        # 수기 항목 = 출처·허용 오차 필수(D-0116)
            self.assertNotEqual(e.src, "ne", e.id)
            self.assertGreater(len(e.src), 10, e.id)
        want = {"strait_of_hormuz", "kharg_island", "gulf_of_aden", "vnukovo_airport", "poland", "us_embassy_seoul"}
        self.assertLessEqual(want, {e.id for e in g.manual})

    def test_ne_md5_matches_local_source_when_present(self) -> None:
        src = REPO / "data" / "geo" / "ne" / "ne_10m_populated_places.geojson"
        if not src.exists():
            self.skipTest("NE 원본 없음 — python tools/fetch_data.py ne")
        raw = src.read_bytes()
        self.assertEqual(load_gazetteer().source["ne_md5"], hashlib.md5(raw).hexdigest())  # noqa: S324
        g = build(raw, load_gazetteer().manual)                   # 도구 재실행 = 추적 파일과 같은 내용(결정적)
        self.assertEqual(dump(g), (REPO / load_rules().geo.gazetteer.path).read_text(encoding="utf-8"))


class BuildToolTest(unittest.TestCase):
    def test_filter_and_names(self) -> None:
        def feat(name: str, pop: int, cap: int, **kw: object) -> dict:
            return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
                    "properties": {"NAME": name, "NAMEASCII": name, "POP_MAX": pop, "ADM0CAP": cap, "ADM0_A3": "XXX", **kw}}

        raw = json.dumps({"features": [feat("Smallcap", 5_000, 1), feat("Town", 50_000, 0), feat("Irbil", 926_000, 0, NAMEALT="Arbil|Erbil"),
                                       feat("Seoul", 9_796_000, 1, NAME_KO="서울특별시")]}).encode()
        got = {e.id: e for e in ne_entries(raw, 100_000, 25)}
        self.assertEqual(set(got), {"smallcap_xxx", "irbil_xxx", "seoul_xxx"})   # 수도는 인구와 무관, 5만 도시는 제외
        self.assertEqual(got["smallcap_xxx"].kind, "capital")
        self.assertEqual(got["irbil_xxx"].names, ["Irbil", "Arbil", "Erbil"])
        self.assertEqual(got["seoul_xxx"].names, ["Seoul", "서울특별시", "서울"])   # 행정 접미사 뗀 표기(자막 라벨)

    def test_dump_roundtrip(self) -> None:
        self.assertEqual(Gazetteer.model_validate(yaml.safe_load(dump(GZ))), GZ)


class MatchTest(unittest.TestCase):
    def test_norm_and_distance(self) -> None:
        self.assertEqual(norm_name(" Paju_2015 "), "paju 2015")
        self.assertAlmostEqual(haversine_km((0, 0), (1, 0)), 111.2, delta=0.1)

    def test_within_tolerance_is_matched(self) -> None:
        doc = _doc([{"type": "marker", "start": 0, "end": 5, "at_place": "seoul", "label": "서울"}], places={"seoul": [126.98, 37.57]})
        r = check_doc(doc, geo_unsourced(doc), GZ)
        self.assertEqual((len(r["matched"]), r["mismatch"], r["unsourced"]), (1, [], []))
        self.assertEqual(r["matched"][0]["gazetteer"], "seoul_kor")

    def test_far_coordinate_is_mismatch_hard(self) -> None:
        doc = _doc([], places={"seoul": [37.57, 126.98]})   # 경위도 뒤바뀜
        r = check_doc(doc, geo_unsourced(doc), GZ)
        self.assertEqual(len(r["mismatch"]), 1)
        errs = check_geo_mismatch(NS(R=NS(cache={"geo_check": r})))
        self.assertTrue(errs[0].startswith("[geo-mismatch] place seoul"), errs)
        self.assertIn("geo_mismatch", HARD)
        self.assertIn("geo_unsourced", WARN)

    def test_homonym_label_picks_gulf_not_city(self) -> None:
        """place 키 aden = 도시 Aden 과 같은 이름이지만 marker label 아덴만 = Gulf of Aden — 맞은 항목 중 하나라도 오차 안이면 통과."""
        doc = _doc([{"type": "marker", "start": 0, "end": 5, "at_place": "aden", "label": "아덴만"}], places={"aden": [46.8, 12.4]})
        r = check_doc(doc, geo_unsourced(doc), GZ)
        self.assertEqual(r["mismatch"], [])
        self.assertEqual(r["matched"][0]["gazetteer"], "gulf_of_aden")
        bare = _doc([], places={"aden": [46.8, 12.4]})   # label 없이 키만 = 도시 Aden 에서 약 190km → hard
        self.assertEqual(len(check_doc(bare, geo_unsourced(bare), GZ)["mismatch"]), 1)

    def test_unknown_name_and_paths_stay_unsourced(self) -> None:
        doc = _doc([{"type": "marker", "start": 0, "end": 5, "at_place": "site", "label": "폭발 지점", "sub": "좌표 비공개"},
                    {"type": "marker", "start": 0, "end": 5, "lon": 126.99, "lat": 37.56, "label": "서울"}],
                   places={"site": [127.0, 38.2]}, paths={"route": [[126.0, 37.0], [127.0, 38.0]]})
        r = check_doc(doc, geo_unsourced(doc), GZ)
        self.assertEqual(sorted(it["kind"] for it in r["unsourced"]), ["path", "place"])
        self.assertEqual([it["kind"] for it in r["matched"]], ["marker"])   # 인라인 marker 는 label 로 대조
        warns = check_geo_unsourced(NS(R=NS(cache={"geo_check": r})))
        self.assertTrue(all(w.startswith("[geo-unsourced]") for w in warns))


class GoldenUnchangedTest(unittest.TestCase):
    """hormuz·랫클리프 골든 좌표는 고치지 않는다 — 사전과 맞는 지명은 전부 허용 오차 안이어야 한다(D-0116)."""

    def test_golden_places_within_tolerance(self) -> None:
        want = {"hormuz_korea": {"busan_kor", "gulf_of_aden", "irbil_irq", "kharg_island", "seoul_kor", "strait_of_hormuz", "ulsan_kor",
                                 "us_embassy_seoul"},
                "ratcliffe2026": {"kiev_ukr", "moscow_rus", "poland", "riga_lva", "strait_of_hormuz", "vnukovo_airport"}}
        for proj, ids in want.items():
            doc = load_direction_doc(REPO / "projects" / proj / "direction.yaml")
            r = check_doc(doc, geo_unsourced(doc))
            self.assertEqual(r["mismatch"], [], proj)
            self.assertEqual({it["gazetteer"] for it in r["matched"]}, ids, proj)
            self.assertTrue(all(it["kind"] in ("path", "route") for it in r["unsourced"]), proj)


if __name__ == "__main__":
    unittest.main()

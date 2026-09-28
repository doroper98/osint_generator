"""Phase 5 엔티티 레지스트리 테스트 (v2.4.0, back_and_forth D-0029 작업 2·8).

라이브러리 조인, 별칭 조회, 별칭 충돌, 미등재 참조 → RegistryError(P10), 예시 파리티(entities.yaml 이 스키마 통과).
"""

from __future__ import annotations

import unittest

from engine.entities import build_registry, check_event_refs, load_entities
from engine.registry import RegistryError
from schemas.entity_models import EntitiesFile

LIB = {"people": [{"person_id": "trump", "name_ko": "도널드 트럼프", "name_en": "Donald Trump", "aliases": [], "role": ""}]}


def _file(extra: dict) -> EntitiesFile:
    base = {"kr": {"kind": "country", "names": ["대한민국"], "flag": "kr", "rights": "flags.flag_icons"},
            "us": {"kind": "country", "names": ["미국"], "flag": "us", "rights": "flags.flag_icons"}}
    return EntitiesFile.model_validate({"schema_version": 1, "entities": {**base, **extra}})


class EntityRegistryTest(unittest.TestCase):
    def test_repo_entities_parse_and_cover_hormuz(self) -> None:
        reg = load_entities()
        for eid in ("lee_jae_myung", "roh_moo_hyun", "trump", "khamenei", "navcent", "irgc", "centcom"):
            self.assertIn(eid, reg.entities)
        self.assertGreaterEqual(len(reg.of_kind("country")), 12)
        self.assertGreaterEqual(len(reg.of_kind("person")), 24 + 2)  # 라이브러리 24인 조인 + 라이브러리 밖 2명

    def test_library_join_adds_aliases(self) -> None:
        reg = build_registry(_file({"trump": {"kind": "person", "names": ["트럼프"], "flag": "us"}}), LIB)
        e = reg.lookup("트럼프")
        self.assertEqual(e.id, "trump")
        self.assertEqual(e.library, "trump")
        self.assertEqual(e.rights, "library.trump")
        self.assertIs(reg.lookup("Donald Trump"), e)

    def test_alias_collision_is_error(self) -> None:
        with self.assertRaises(RegistryError):
            build_registry(_file({"x": {"kind": "country", "names": ["미국"], "flag": "us", "rights": "flags.flag_icons"}}), LIB)

    def test_unknown_alias_is_registry_error(self) -> None:
        with self.assertRaises(RegistryError):
            load_entities().lookup("존재하지 않는 사람")

    def test_unregistered_refs_in_events(self) -> None:
        reg = build_registry(_file({}), LIB)
        evs = [dict(type="badge", t0=1.0, t1=2.0, kind="person", pid="nobody", flag="kr"),
               dict(type="badge", t0=1.0, t1=2.0, kind="flag", flag="zz"),
               dict(type="badge", t0=1.0, t1=2.0, kind="emblem", img="cia")]
        errs = check_event_refs(evs, reg)
        self.assertEqual(len(errs), 3, errs)
        ok = [dict(type="badge", t0=1.0, t1=2.0, kind="person", pid="trump", flag="us")]
        self.assertEqual(check_event_refs(ok, reg), [])

    def test_org_needs_fallback_flag(self) -> None:
        with self.assertRaises(ValueError):
            build_registry(_file({"o": {"kind": "org", "names": ["기관"], "emblem": "o", "rights": "emblems.o"}}), LIB)


if __name__ == "__main__":
    unittest.main()

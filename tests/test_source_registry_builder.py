"""SourceRegistryBuilder 단위 테스트 (Phase 5, v0.5.3).

검증 범위
--------
1. happy path — 다수 partial 결합, 입력 순서 보존, 빈 partial 통계만 반영.
2. fail-fast invariant 5 종:
   - cross-partial source_id 충돌
   - cross-partial input_item_id 충돌
   - intra-partial source_id 중복
   - schema_version 불일치
   - project_id 불일치
3. 경계: 빈 입력 / 단일 partial / 빈 partial 만 / input_item_id=None.
4. registry 의 schema_version 이 partial 의 schema_version 과 일치.
5. partial_counter — 빈 partial 도 partial_count 에 +1.

실행:
    python -m unittest tests.test_source_registry_builder
"""

from __future__ import annotations

import unittest

from schemas.models import (
    RightsStatus,
    SourceCollectionPartial,
    SourceEntry,
    SourceRegistry,
)
from orchestrator.source_registry_builder import (
    build_source_registry,
    partial_counter,
)


def _entry(sid: str, **overrides) -> SourceEntry:
    base = dict(source_id=sid, platform="x", source_type="post")
    base.update(overrides)
    return SourceEntry(**base)


def _partial(
    task_id: str,
    input_item_id: str | None,
    sources: list[SourceEntry],
    *,
    project_id: str = "proj_001",
    schema_version: int | None = None,
) -> SourceCollectionPartial:
    kwargs: dict = dict(
        project_id=project_id,
        task_id=task_id,
        input_item_id=input_item_id,
        collected_sources=sources,
    )
    if schema_version is not None:
        kwargs["schema_version"] = schema_version
    return SourceCollectionPartial(**kwargs)


class HappyPathTests(unittest.TestCase):
    def test_empty_partials_yields_empty_registry(self):
        reg = build_source_registry("proj_001", [])
        self.assertIsInstance(reg, SourceRegistry)
        self.assertEqual(reg.project_id, "proj_001")
        self.assertEqual(reg.sources, [])

    def test_single_partial_passes_through(self):
        p = _partial("t1", "i1", [_entry("s1"), _entry("s2")])
        reg = build_source_registry("proj_001", [p])
        self.assertEqual([s.source_id for s in reg.sources], ["s1", "s2"])

    def test_multi_partial_preserves_input_order(self):
        p1 = _partial("t1", "i1", [_entry("s1"), _entry("s2")])
        p2 = _partial("t2", "i2", [_entry("s3")])
        p3 = _partial("t3", "i3", [_entry("s4"), _entry("s5")])
        reg = build_source_registry("proj_001", [p1, p2, p3])
        self.assertEqual(
            [s.source_id for s in reg.sources],
            ["s1", "s2", "s3", "s4", "s5"],
        )

    def test_empty_partial_contributes_no_sources_but_no_error(self):
        p1 = _partial("t1", "i1", [_entry("s1")])
        p2 = _partial("t2", "i2", [])  # collector ran, no candidates
        p3 = _partial("t3", "i3", [_entry("s2")])
        reg = build_source_registry("proj_001", [p1, p2, p3])
        self.assertEqual([s.source_id for s in reg.sources], ["s1", "s2"])

    def test_all_empty_partials_yields_empty_sources(self):
        p1 = _partial("t1", "i1", [])
        p2 = _partial("t2", "i2", [])
        reg = build_source_registry("proj_001", [p1, p2])
        self.assertEqual(reg.sources, [])

    def test_input_item_id_none_is_allowed_and_skips_collision_check(self):
        # input_item_id=None 인 partial 이 여럿 있어도 충돌로 보지 않음
        # (도메인적으로는 source_collector 가 항상 set 하므로 일반적이지 않은 케이스).
        p1 = _partial("t1", None, [_entry("s1")])
        p2 = _partial("t2", None, [_entry("s2")])
        reg = build_source_registry("proj_001", [p1, p2])
        self.assertEqual([s.source_id for s in reg.sources], ["s1", "s2"])

    def test_registry_schema_version_matches_partials(self):
        # partial 의 schema_version 이 1 이면 registry 도 1.
        p = _partial("t1", "i1", [_entry("s1")])
        self.assertEqual(p.schema_version, 1)
        reg = build_source_registry("proj_001", [p])
        self.assertEqual(reg.schema_version, 1)

    def test_field_values_passed_through(self):
        p = _partial(
            "t1",
            "i1",
            [
                _entry(
                    "s1",
                    rights_status=RightsStatus.RIGHTS_CLEAR,
                    reliability_score=0.9,
                    risk_flags=["ad_content"],
                    usage_plan=["full_quote"],
                )
            ],
        )
        reg = build_source_registry("proj_001", [p])
        s = reg.sources[0]
        self.assertEqual(s.rights_status, RightsStatus.RIGHTS_CLEAR.value)
        self.assertEqual(s.reliability_score, 0.9)
        self.assertEqual(s.risk_flags, ["ad_content"])
        self.assertEqual(s.usage_plan, ["full_quote"])


class CrossPartialCollisionTests(unittest.TestCase):
    def test_cross_partial_source_id_collision_raises(self):
        p1 = _partial("t1", "i1", [_entry("s_dup")])
        p2 = _partial("t2", "i2", [_entry("s_dup")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p1, p2])
        msg = str(ctx.exception)
        self.assertIn("cross-partial source_id 충돌", msg)
        self.assertIn("s_dup", msg)
        self.assertIn("t1", msg)
        self.assertIn("t2", msg)
        # LLM-AP-003 신호 메시지 명시.
        self.assertIn("LLM-AP-003", msg)

    def test_cross_partial_input_item_id_collision_raises(self):
        p1 = _partial("t1", "i_dup", [_entry("s1")])
        p2 = _partial("t2", "i_dup", [_entry("s2")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p1, p2])
        msg = str(ctx.exception)
        self.assertIn("input_item_id 충돌", msg)
        self.assertIn("i_dup", msg)
        self.assertIn("t1", msg)
        self.assertIn("t2", msg)

    def test_input_item_id_collision_detected_before_source_id_collision(self):
        # 두 종류의 충돌이 동시 존재해도 input_item_id 충돌이 먼저 잡힘 (순서 보장).
        p1 = _partial("t1", "i_dup", [_entry("s_dup")])
        p2 = _partial("t2", "i_dup", [_entry("s_dup")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p1, p2])
        self.assertIn("input_item_id", str(ctx.exception))


class IntraPartialDuplicateTests(unittest.TestCase):
    def test_intra_partial_source_id_duplicate_raises(self):
        p = _partial("t1", "i1", [_entry("s1"), _entry("s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        msg = str(ctx.exception)
        self.assertIn("intra-partial source_id 중복", msg)
        self.assertIn("t1", msg)
        self.assertIn("s1", msg)
        # LLM-AP-003 production breach 신호 메시지.
        self.assertIn("LLM-AP-003", msg)

    def test_intra_partial_duplicate_detected_in_later_partial(self):
        p1 = _partial("t1", "i1", [_entry("s1")])
        p2 = _partial("t2", "i2", [_entry("s2"), _entry("s2")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p1, p2])
        self.assertIn("t2", str(ctx.exception))


class SchemaVersionMismatchTests(unittest.TestCase):
    def test_schema_version_mismatch_raises(self):
        p1 = _partial("t1", "i1", [_entry("s1")], schema_version=1)
        # 가상의 미래 schema_version=2 partial. 현재 모델은 default=1 이지만
        # 빌더는 혼재 자체를 거부해야 함.
        p2 = _partial("t2", "i2", [_entry("s2")], schema_version=2)
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p1, p2])
        msg = str(ctx.exception)
        self.assertIn("schema_version 불일치", msg)
        self.assertIn("[1, 2]", msg)


class ProjectIdMismatchTests(unittest.TestCase):
    def test_project_id_mismatch_raises(self):
        p1 = _partial("t1", "i1", [_entry("s1")], project_id="proj_001")
        p2 = _partial("t2", "i2", [_entry("s2")], project_id="proj_002")
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p1, p2])
        msg = str(ctx.exception)
        self.assertIn("project_id 불일치", msg)
        self.assertIn("proj_002", msg)
        self.assertIn("t2", msg)

    def test_all_partials_must_match_requested_project_id(self):
        # 요청 project_id 와 모든 partial 이 같아야 함 (partial 끼리만 일치해도 불충분).
        p1 = _partial("t1", "i1", [_entry("s1")], project_id="proj_AAA")
        p2 = _partial("t2", "i2", [_entry("s2")], project_id="proj_AAA")
        with self.assertRaises(ValueError):
            build_source_registry("proj_BBB", [p1, p2])


class PartialCounterTests(unittest.TestCase):
    def test_counter_counts_empty_partials(self):
        p1 = _partial("t1", "i1", [_entry("s1"), _entry("s2")])
        p2 = _partial("t2", "i2", [])
        p3 = _partial("t3", "i3", [_entry("s3")])
        stats = partial_counter([p1, p2, p3])
        self.assertEqual(
            stats,
            {"partial_count": 3, "empty_partial_count": 1, "source_count": 3},
        )

    def test_counter_on_empty_input(self):
        self.assertEqual(
            partial_counter([]),
            {"partial_count": 0, "empty_partial_count": 0, "source_count": 0},
        )

    def test_counter_all_empty(self):
        p1 = _partial("t1", "i1", [])
        p2 = _partial("t2", "i2", [])
        stats = partial_counter([p1, p2])
        self.assertEqual(stats["partial_count"], 2)
        self.assertEqual(stats["empty_partial_count"], 2)
        self.assertEqual(stats["source_count"], 0)


if __name__ == "__main__":
    unittest.main()

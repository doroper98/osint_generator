"""SourceRegistryBuilder 단위 테스트 (Phase 5, v0.5.3 / v0.5.4).

검증 범위
--------
1. happy path — 다수 partial 결합, 입력 순서 보존, 빈 partial 통계만 반영.
2. fail-fast invariant 5 종 (v0.5.3):
   - cross-partial source_id 충돌
   - cross-partial input_item_id 충돌
   - intra-partial source_id 중복
   - schema_version 불일치
   - project_id 불일치
3. v0.5.4 추가 invariant (codex 1차 외부 리뷰 흡수):
   - input_item_id=None (strict default raise / lenient skip)
   - 식별자 정규화 (전후 공백 / NFC / case-sensitive contract)
4. 경계: 빈 입력 / 단일 partial / 빈 partial 만.
5. registry 의 schema_version 이 partial 의 schema_version 과 일치.
6. partial_counter — 빈 partial 도 partial_count 에 +1.
7. sentinel: 충돌이 미래에도 항상 raise (dedupe 모드 도입 시 docstring 정책과
   본 sentinel 을 같이 갱신해야 함).

실행:
    python -m unittest tests.test_source_registry_builder
"""

from __future__ import annotations

import unicodedata
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
    base: dict[str, object] = dict(source_id=sid, platform="x", source_type="post")
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
    kwargs: dict[str, object] = dict(
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
        # v0.5.4: operator action hint 노출.
        self.assertIn("action", msg)

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
        # v0.5.4: operator action hint 노출.
        self.assertIn("action", msg)

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
        # v0.5.4: operator action hint 노출.
        self.assertIn("action", msg)

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
        # v0.5.4: operator action hint.
        self.assertIn("action", msg)


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
        # v0.5.4: operator action hint.
        self.assertIn("action", msg)

    def test_all_partials_must_match_requested_project_id(self):
        # 요청 project_id 와 모든 partial 이 같아야 함 (partial 끼리만 일치해도 불충분).
        p1 = _partial("t1", "i1", [_entry("s1")], project_id="proj_AAA")
        p2 = _partial("t2", "i2", [_entry("s2")], project_id="proj_AAA")
        with self.assertRaises(ValueError):
            build_source_registry("proj_BBB", [p1, p2])


class InputItemIdNoneStrictModeTests(unittest.TestCase):
    """v0.5.4 — codex 1차 리뷰 High#1 흡수.

    pipeline production path 의 default 는 strict=True (raise). 도메인 재사용
    측면에서 strict=False (lenient, v0.5.3 동작) 도 보존.
    """

    def test_strict_default_raises_on_none_input_item_id(self):
        p = _partial("t1", None, [_entry("s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        msg = str(ctx.exception)
        self.assertIn("input_item_id=None", msg)
        self.assertIn("t1", msg)
        # action hint 노출.
        self.assertIn("strict_input_item_id=False", msg)

    def test_strict_default_raises_even_when_only_one_partial(self):
        # 단일 partial 이라 cross-collision 발생 자체가 불가능해도 strict 면 raise.
        p = _partial("t_only", None, [])
        with self.assertRaises(ValueError):
            build_source_registry("proj_001", [p])

    def test_lenient_mode_allows_multiple_none(self):
        # strict=False 시 v0.5.3 동작과 동일 — None 끼리는 충돌 검사 skip.
        p1 = _partial("t1", None, [_entry("s1")])
        p2 = _partial("t2", None, [_entry("s2")])
        reg = build_source_registry(
            "proj_001", [p1, p2], strict_input_item_id=False
        )
        self.assertEqual([s.source_id for s in reg.sources], ["s1", "s2"])

    def test_lenient_mode_still_catches_non_none_collision(self):
        # lenient 라도 non-None 끼리의 input_item_id 충돌은 raise.
        p1 = _partial("t1", "i_dup", [_entry("s1")])
        p2 = _partial("t2", "i_dup", [_entry("s2")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry(
                "proj_001", [p1, p2], strict_input_item_id=False
            )
        self.assertIn("input_item_id 충돌", str(ctx.exception))


class IdentifierNormalizationContractTests(unittest.TestCase):
    """v0.5.4 — codex 1차 리뷰 High#2 흡수.

    식별자 contract: case-sensitive + NFC + 전후 공백 금지.
    정규화 후 매칭이 아니라 의심 변이 자체를 reject.
    """

    # --- case-sensitive (충돌 아님) ---

    def test_case_difference_is_not_a_collision_in_source_id(self):
        # contract: case-sensitive. ABC vs abc 는 두 개의 별개 식별자.
        p1 = _partial("t1", "i1", [_entry("ABC")])
        p2 = _partial("t2", "i2", [_entry("abc")])
        reg = build_source_registry("proj_001", [p1, p2])
        self.assertEqual([s.source_id for s in reg.sources], ["ABC", "abc"])

    def test_case_difference_is_not_a_collision_in_input_item_id(self):
        p1 = _partial("t1", "I1", [_entry("s1")])
        p2 = _partial("t2", "i1", [_entry("s2")])
        reg = build_source_registry("proj_001", [p1, p2])
        self.assertEqual([s.source_id for s in reg.sources], ["s1", "s2"])

    # --- 전후 공백 (의심 변이, raise) ---

    def test_leading_whitespace_in_source_id_raises(self):
        p = _partial("t1", "i1", [_entry(" s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        msg = str(ctx.exception)
        self.assertIn("식별자 정규화 위반", msg)
        self.assertIn("source_id", msg)

    def test_trailing_whitespace_in_source_id_raises(self):
        p = _partial("t1", "i1", [_entry("s1 ")])
        with self.assertRaises(ValueError):
            build_source_registry("proj_001", [p])

    def test_whitespace_in_input_item_id_raises(self):
        p = _partial("t1", " i1", [_entry("s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        self.assertIn("input_item_id", str(ctx.exception))

    def test_whitespace_in_project_id_arg_raises(self):
        p = _partial("t1", "i1", [_entry("s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001 ", [p])
        self.assertIn("project_id", str(ctx.exception))

    def test_whitespace_in_project_id_arg_raises_even_for_empty_partials(self):
        # empty partial list path 도 project_id 정규화를 검증해야 함.
        with self.assertRaises(ValueError):
            build_source_registry(" proj_001", [])

    def test_whitespace_in_task_id_raises(self):
        p = _partial("t1 ", "i1", [_entry("s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        self.assertIn("task_id", str(ctx.exception))

    # --- NFC 정규화 (의심 변이, raise) ---

    def test_nfd_source_id_raises(self):
        # "한" 의 NFD 형식은 NFC 와 다른 byte sequence. NFC normalize 결과와
        # 다르면 raise.
        nfd_value = unicodedata.normalize("NFD", "한글")
        # sanity: NFD 와 NFC 가 다른지 확인 (다르지 않으면 본 테스트는 의미 없음).
        self.assertNotEqual(nfd_value, unicodedata.normalize("NFC", nfd_value))
        p = _partial("t1", "i1", [_entry(nfd_value)])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        self.assertIn("식별자 정규화 위반", str(ctx.exception))
        self.assertIn("NFC", str(ctx.exception))

    def test_nfd_input_item_id_raises(self):
        nfd_iid = unicodedata.normalize("NFD", "항목")
        p = _partial("t1", nfd_iid, [_entry("s1")])
        with self.assertRaises(ValueError) as ctx:
            build_source_registry("proj_001", [p])
        self.assertIn("input_item_id", str(ctx.exception))

    def test_nfc_identifier_is_accepted(self):
        # 정상 NFC 식별자는 그대로 통과해야 함 (한글 / 영문 / 숫자 혼합).
        s_id = unicodedata.normalize("NFC", "src_한글_001")
        p = _partial("t1", "i1", [_entry(s_id)])
        reg = build_source_registry("proj_001", [p])
        self.assertEqual(reg.sources[0].source_id, s_id)


class CollisionAlwaysRaisesSentinelTests(unittest.TestCase):
    """Sentinel — 미래 dedupe 모드 도입 시 본 클래스가 깨지면, builder
    docstring 의 "머지 정책" 섹션도 같이 갱신해야 함을 마킹.

    본 sentinel 은 현재 API (build_source_registry 가 충돌 시 *반드시* raise)
    의 invariant 를 코드 레벨에서 잠금. raise 정책상 dead path 인 docstring 머지
    정책을 미래에 활성화하려면 (1) 본 클래스의 expectation 을 갱신, (2) 동시에
    docstring 의 머지 정책을 executable 화 (테스트 + 코드 path) — 두 변경이
    한 PATCH 에 함께 들어가야 한다.
    """

    def test_source_id_collision_always_raises_default(self):
        p1 = _partial("t1", "i1", [_entry("s_dup")])
        p2 = _partial("t2", "i2", [_entry("s_dup")])
        with self.assertRaises(ValueError):
            build_source_registry("proj_001", [p1, p2])

    def test_source_id_collision_always_raises_lenient_mode(self):
        # lenient input_item_id 모드라도 source_id 충돌은 여전히 raise.
        p1 = _partial("t1", None, [_entry("s_dup")])
        p2 = _partial("t2", None, [_entry("s_dup")])
        with self.assertRaises(ValueError):
            build_source_registry(
                "proj_001", [p1, p2], strict_input_item_id=False
            )

    def test_intra_partial_source_id_duplicate_always_raises(self):
        p = _partial("t1", "i1", [_entry("s1"), _entry("s1")])
        with self.assertRaises(ValueError):
            build_source_registry("proj_001", [p])


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

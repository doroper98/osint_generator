"""SourceCollectionPartial[] → SourceRegistry 빌더 (Phase 5, v0.5.3).

`02_sources/partials/*.json` 에 영속화된 `SourceCollectionPartial` 들을 모아
정식 `02_sources/source_registry.json` (`SourceRegistry`) 으로 합칩니다.

본 모듈은 **순수 함수만** 제공합니다. 디스크 I/O 없음 (partial 로딩과
source_registry.json 영속화는 호출자 책임 — 후속 PATCH 의 CLI / orchestrator).

설계 결정 (v0.5.3, 사용자 확정)
-------------------------------

본 빌더는 **fail-fast** 정책. partial 간 또는 partial 내부의 일관성 위반을
조용히 merge 하지 않고 raise 합니다. 근거: LLM-AP-003 (echo identifier 무결성)
의 production 사용자인 SourceCollectorWorker 가 발급한 source_id 는 task 단위로
고유해야 하므로, 충돌 자체가 worker / planner 단의 버그 신호이거나 buggy
upstream 의 사고. 조용히 dedupe 하면 무결성 사고가 은폐된다.

1. **cross-partial source_id 충돌**     → raise (ValueError)
2. **cross-partial input_item_id 충돌** → raise (한 input_item_id 는 한 partial)
3. **intra-partial source_id 중복**     → raise (Pydantic 가 list uniqueness 강제
                                          안 함, builder 진입 전 검증)
4. **schema_version 불일치**            → raise (현재 v1 만 존재, 향후 mismatch 는
                                          작업자 개입 필요)
5. **빈 partial** (collected_sources 가 빈 배열)
                                        → 통계 (partial_count) 에는 +1, sources
                                          기여 없음. "collector 가 실행됐으나 후보
                                          없음" 을 구분 가능하게.

머지 정책 (raise 정책상 도달 불가, 향후 dedupe 모드 도입 시 재사용)
-------------------------------------------------------------------

현재 정책에서는 source_id 충돌이 raise 되므로 본 머지 로직은 실행되지 않지만,
향후 "충돌 시 dedup" 모드를 도입하게 되면 동일 정책을 재사용합니다:

- **rights_status**: 보수적 strict 우선순위
    `do_not_use > review_required > rights_unknown > rights_clear`
    (그 외 download_failed / login_required / private_or_deleted /
    manual_user_provided 는 사용자 개입 신호 → strict 측에 동치)
- **verification_status**: 의심 우선 (legal-safe)
    `disputed > unverified > cross_checked > official`
    official 이 가장 낮은 우선순위인 게 맞음 — 분쟁 시 보수적으로 낮춤.
    자동 머지가 임의로 official 로 승격하면 안 됨.
- **reliability_score**: `min(a, b)` (정보 손실 최소화 — 평균은 누락 가능)
- **risk_flags / usage_plan**: 순서 보존 합집합 (정보 보존)
- **나머지 필드** (title / author / language / 본문 등): 첫 partial 우선

본 정책은 docstring 으로만 명문화. 코드 구현은 raise 정책상 dead path.
"""

from __future__ import annotations

from schemas.models import (
    __schema_version__,
    SourceCollectionPartial,
    SourceEntry,
    SourceRegistry,
)


def _validate_partial_internal(partial: SourceCollectionPartial) -> None:
    """한 partial 내부의 일관성 검증.

    raise:
        ValueError: 같은 partial 안에 동일 source_id 가 2 번 이상 등장하면.
    """
    seen: set[str] = set()
    for entry in partial.collected_sources:
        if entry.source_id in seen:
            raise ValueError(
                f"intra-partial source_id 중복: partial task_id={partial.task_id!r} "
                f"안에 source_id={entry.source_id!r} 가 2 번 이상 등장. "
                f"SourceCollectorWorker 출력 단계에서 식별자 무결성이 깨졌음 — "
                f"LLM-AP-003 (echo identifier) 의 production breach 신호."
            )
        seen.add(entry.source_id)


def build_source_registry(
    project_id: str,
    partials: list[SourceCollectionPartial],
) -> SourceRegistry:
    """SourceCollectionPartial[] 을 합쳐 SourceRegistry 생성.

    parameters
    ----------
    project_id : str
        대상 프로젝트 식별자. 모든 partial 의 project_id 가 일치해야 함.
    partials : list[SourceCollectionPartial]
        `02_sources/partials/*.json` 에서 로드한 partial 들. 호출자가 입력 순서를
        담당 (예: task_id sort) — 본 함수는 입력 순서를 보존한다.

    returns
    -------
    SourceRegistry
        합쳐진 정식 레지스트리. `schema_version` 은 partial 의 schema_version 과
        일치 (모두 동일해야 함, 위반 시 raise).

    raise
    -----
    ValueError
        - project_id 불일치
        - schema_version 불일치 (서로 다른 정수값 혼재)
        - cross-partial source_id 충돌
        - cross-partial input_item_id 충돌
        - intra-partial source_id 중복
    """
    if not partials:
        return SourceRegistry(project_id=project_id, sources=[])

    # 1. project_id 정합.
    for p in partials:
        if p.project_id != project_id:
            raise ValueError(
                f"partial project_id 불일치: task_id={p.task_id!r} 의 "
                f"project_id={p.project_id!r} 가 요청된 project_id={project_id!r} "
                f"와 다름. partial 들이 다른 프로젝트와 섞였을 가능성."
            )

    # 2. schema_version 정합. 현재 v1 만 존재. 향후 mismatch 는 작업자 개입 필요.
    versions = {p.schema_version for p in partials}
    if len(versions) > 1:
        raise ValueError(
            f"partial schema_version 불일치: 혼재된 버전={sorted(versions)}. "
            f"C3 의 additive-first 원칙상 같은 프로젝트 안에서는 한 버전만 존재해야 "
            f"하며, 충돌 시 자동 머지는 의미 손실 위험이 있어 작업자가 개입해야 함."
        )

    # 3. input_item_id 충돌 검사. 한 input_item_id 당 한 partial 이 원칙.
    seen_input_items: dict[str, str] = {}  # input_item_id -> 처음 발견한 task_id
    for p in partials:
        iid = p.input_item_id
        if iid is None:
            # schema 상 optional 이지만 source_collector 는 항상 set 함.
            # None 은 본 빌더의 충돌 검사 대상 외 (다른 도메인에서 재사용 시 보존).
            continue
        if iid in seen_input_items:
            raise ValueError(
                f"cross-partial input_item_id 충돌: input_item_id={iid!r} 가 "
                f"task_id={seen_input_items[iid]!r} 와 task_id={p.task_id!r} 두 "
                f"partial 에서 등장. 한 UserDecision 은 한 partial 에만 대응해야 함 "
                f"— planner / task_queue 의 idempotency 가드가 깨졌을 가능성."
            )
        seen_input_items[iid] = p.task_id

    # 4. 각 partial 내부 source_id 중복 검사.
    for p in partials:
        _validate_partial_internal(p)

    # 5. cross-partial source_id 충돌 검사 + 합치기.
    seen_source_ids: dict[str, str] = {}  # source_id -> 처음 발견한 task_id
    sources: list[SourceEntry] = []
    for p in partials:
        for entry in p.collected_sources:
            sid = entry.source_id
            if sid in seen_source_ids:
                raise ValueError(
                    f"cross-partial source_id 충돌: source_id={sid!r} 가 "
                    f"task_id={seen_source_ids[sid]!r} 와 task_id={p.task_id!r} 두 "
                    f"partial 에서 등장. SourceCollectorWorker 가 task 마다 고유한 "
                    f"source_id 를 발급해야 한다는 invariant 가 깨졌음 — LLM-AP-003 "
                    f"production breach 신호. 충돌은 조용히 dedup 하지 않는다."
                )
            seen_source_ids[sid] = p.task_id
            sources.append(entry)

    # 6. registry schema_version 은 partial 의 schema_version 과 일치.
    return SourceRegistry(
        project_id=project_id,
        schema_version=partials[0].schema_version,
        sources=sources,
    )


def partial_counter(partials: list[SourceCollectionPartial]) -> dict[str, int]:
    """빌드 통계 (빈 partial 도 포함). 호출자가 로그·검증에 활용.

    returns
    -------
    dict[str, int]
        - partial_count: 입력 partial 수 (빈 것도 +1).
        - empty_partial_count: collected_sources 가 빈 partial 수.
        - source_count: 합쳐진 SourceEntry 총수.
    """
    empty = sum(1 for p in partials if not p.collected_sources)
    total = sum(len(p.collected_sources) for p in partials)
    return {
        "partial_count": len(partials),
        "empty_partial_count": empty,
        "source_count": total,
    }


__all__ = [
    "build_source_registry",
    "partial_counter",
    "__schema_version__",
]

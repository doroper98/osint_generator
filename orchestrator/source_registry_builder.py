"""SourceCollectionPartial[] → SourceRegistry 빌더 (Phase 5, v0.5.3 / v0.5.4).

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

v0.5.4 추가 invariant (codex 1차 외부 리뷰 흡수)
------------------------------------------------

6. **input_item_id=None 거부 (default strict)** — pipeline production path 에서는
   source_collector 가 항상 input_item_id 를 set 한다. None 자체가 planner/worker
   drift 신호이므로 raise. 도메인 재사용 (다른 collector 가 input_item_id 를 안
   쓰는 경우) 을 위해 `strict_input_item_id=False` 키워드로 lenient 모드 유지 —
   이 경우 v0.5.3 동작과 동일 (None 끼리는 충돌 검사 skip). 기본은 strict=True.

7. **식별자 정규화 contract** — 모든 식별자 (project_id / task_id /
   input_item_id / source_id) 는:
   - **case-sensitive** (`ABC` vs `abc` 는 의도된 별개 식별자, 충돌 아님)
   - **NFC 정규화 강제** (NFD / 혼합 Unicode 변이는 의심 입력으로 raise)
   - **전후 공백 금지** (`'  s1  '` vs `'s1'` 같은 직렬화 사고 차단)

   정규화 후 매칭이 아니라 **의심 변이 자체를 reject**. 정규화 후 매칭은 정상
   case 차이를 충돌로 오인할 수 있고 (`ABC` ↔ `abc`), 침묵 정규화는 식별자
   무결성을 약화시킨다. cross-partial 정규화 충돌이 실제로 들어오면 fail-fast
   로 raise 하여 upstream 의 string formatting / OS 정규화 차이를 즉시 노출.

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
**미래 dedupe 모드 도입 시**: `tests/test_source_registry_builder.py` 의
`CollisionAlwaysRaisesSentinelTests` 가 sentinel — 본 sentinel 이 깨지면 본
docstring 의 머지 정책도 같이 갱신해야 함.
"""

from __future__ import annotations

import unicodedata

from schemas.models import (
    __schema_version__,
    SourceCollectionPartial,
    SourceEntry,
    SourceRegistry,
)


def _validate_identifier(field: str, value: str, *, where: str) -> None:
    """식별자 정규화 contract 검증 (v0.5.4).

    contract:
        - case-sensitive (`ABC` vs `abc` 는 의도된 별개 식별자)
        - NFC 정규화 강제 (NFD / 혼합 Unicode 변이는 의심 입력으로 raise)
        - 전후 공백 금지

    위반 시 raise — 정규화 후 매칭이 아니라 의심 변이 자체를 reject.

    parameters
    ----------
    field : str
        식별자 필드 이름 (에러 메시지에 노출). 예: "source_id".
    value : str
        검증 대상 문자열.
    where : str
        식별자의 위치 컨텍스트 (에러 메시지에 노출). 예: "task_id='t1'".
    """
    if value != value.strip():
        raise ValueError(
            f"식별자 정규화 위반 ({field}={value!r}, where={where}): "
            f"전후 공백 포함. 식별자는 strip 결과와 동일해야 함. "
            f"action: upstream 의 string formatting / JSON 직렬화 단계에서 "
            f"식별자에 공백이 섞이지 않는지 확인 (planner.task_id_for / "
            f"source_collector echo 단)."
        )
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError(
            f"식별자 정규화 위반 ({field}={value!r}, where={where}): "
            f"NFC 정규화 결과와 다름. Unicode 변이 (NFD / 혼합) 가 식별자에 섞임. "
            f"action: 식별자 생성 파이프라인에서 unicodedata.normalize('NFC', ...) "
            f"적용 여부 확인. OS 파일시스템 정규화 차이 (macOS HFS+ NFD) 가 "
            f"의심되는 경우 ingest 단에서 정규화를 명시적으로 박을 것."
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
                f"LLM-AP-003 (echo identifier) 의 production breach 신호. "
                f"action: (1) worker 의 task_result 와 LLM raw response 를 비교, "
                f"(2) 동일 task 의 partial 만 inspect (cross-task contamination 아님), "
                f"(3) merge 재실행하지 말고 worker 단의 source_id 발급 로직 수정 후 "
                f"partial 재생성."
            )
        seen.add(entry.source_id)


def build_source_registry(
    project_id: str,
    partials: list[SourceCollectionPartial],
    *,
    strict_input_item_id: bool = True,
) -> SourceRegistry:
    """SourceCollectionPartial[] 을 합쳐 SourceRegistry 생성.

    parameters
    ----------
    project_id : str
        대상 프로젝트 식별자. 모든 partial 의 project_id 가 일치해야 함.
    partials : list[SourceCollectionPartial]
        `02_sources/partials/*.json` 에서 로드한 partial 들.

        **호출자는 결정론적 순서를 제공해야 함** (recommended: `task_id` 오름차순).
        본 함수는 입력 순서를 그대로 보존하며 내부 정렬을 수행하지 않음. 다른
        loader (e.g. `os.listdir` 의 OS-dependent 순서) 와 mix 하면 같은 입력에
        다른 출력이 나올 수 있음 — 그 경우 호출자 책임으로 sort 후 전달.
    strict_input_item_id : bool, default True
        True (default, pipeline production path): partial 의 `input_item_id` 가
        None 이면 raise. SourceCollectorWorker 는 항상 set 하므로 None 자체가
        planner / worker drift 신호.

        False (lenient, 다른 도메인 재사용 시): None 은 충돌 검사 대상에서 제외
        (v0.5.3 동작). 도메인적으로 input_item_id 가 의미 없는 다른 collector 가
        본 빌더를 재사용할 때만 사용.

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
        - strict_input_item_id=True 이고 input_item_id=None 인 partial 발견
        - 식별자 정규화 위반 (NFC / 공백 / 의심 변이)
    """
    if not partials:
        _validate_identifier("project_id", project_id, where="build_source_registry arg")
        return SourceRegistry(project_id=project_id, sources=[])

    # 0. 요청 project_id 정규화 contract.
    _validate_identifier("project_id", project_id, where="build_source_registry arg")

    # 1. project_id 정합 + 정규화 검증.
    for p in partials:
        _validate_identifier(
            "partial.project_id", p.project_id, where=f"task_id={p.task_id!r}"
        )
        _validate_identifier("partial.task_id", p.task_id, where=f"task_id={p.task_id!r}")
        if p.project_id != project_id:
            raise ValueError(
                f"partial project_id 불일치: task_id={p.task_id!r} 의 "
                f"project_id={p.project_id!r} 가 요청된 project_id={project_id!r} "
                f"와 다름. partial 들이 다른 프로젝트와 섞였을 가능성. "
                f"action: partials/ 로드 경로가 한 project 디렉토리 안인지 "
                f"확인, planner 의 project_id propagation 검증."
            )

    # 2. schema_version 정합. 현재 v1 만 존재. 향후 mismatch 는 작업자 개입 필요.
    versions = {p.schema_version for p in partials}
    if len(versions) > 1:
        raise ValueError(
            f"partial schema_version 불일치: 혼재된 버전={sorted(versions)}. "
            f"C3 의 additive-first 원칙상 같은 프로젝트 안에서는 한 버전만 존재해야 "
            f"하며, 충돌 시 자동 머지는 의미 손실 위험이 있어 작업자가 개입해야 함. "
            f"action: 모든 partial 의 schema_version 을 inspect 후, 옛 버전 partial 은 "
            f"migration script 로 변환하거나 worker 를 재실행하여 동일 버전으로 통일."
        )

    # 3. input_item_id 충돌 검사 + (strict 모드) None 거부.
    seen_input_items: dict[str, str] = {}  # input_item_id -> 처음 발견한 task_id
    for p in partials:
        iid = p.input_item_id
        if iid is None:
            if strict_input_item_id:
                raise ValueError(
                    f"input_item_id=None: task_id={p.task_id!r} 의 partial 에서 "
                    f"input_item_id 가 None. pipeline production path 에서는 "
                    f"SourceCollectorWorker 가 항상 set 하므로 None 자체가 "
                    f"planner / worker drift 신호. action: (1) 해당 task 의 "
                    f"build_user_prompt / preflight 가 input_item_id 를 정확히 "
                    f"전달했는지 확인, (2) 다른 도메인 재사용이라면 호출자에서 "
                    f"strict_input_item_id=False 명시."
                )
            # lenient: 검사 대상 제외 (다른 도메인 재사용 시 None 보존).
            continue
        _validate_identifier(
            "partial.input_item_id", iid, where=f"task_id={p.task_id!r}"
        )
        if iid in seen_input_items:
            raise ValueError(
                f"cross-partial input_item_id 충돌: input_item_id={iid!r} 가 "
                f"task_id={seen_input_items[iid]!r} 와 task_id={p.task_id!r} 두 "
                f"partial 에서 등장. 한 UserDecision 은 한 partial 에만 대응해야 함 "
                f"— planner / task_queue 의 idempotency 가드가 깨졌을 가능성. "
                f"action: (1) planner.task_id_for 의 dedupe 로그 확인, "
                f"(2) task_queue 에 같은 input_item_id 가 2 회 enqueue 됐는지 inspect, "
                f"(3) 두 partial 중 어느 것이 정합인지 작업자 판단 후 잘못된 task 의 "
                f"partial 파일 삭제 + 재머지."
            )
        seen_input_items[iid] = p.task_id

    # 4. 각 partial 내부 source_id 중복 검사.
    for p in partials:
        _validate_partial_internal(p)

    # 5. cross-partial source_id 충돌 검사 + 합치기 (식별자 정규화도 함께).
    seen_source_ids: dict[str, str] = {}  # source_id -> 처음 발견한 task_id
    sources: list[SourceEntry] = []
    for p in partials:
        for entry in p.collected_sources:
            sid = entry.source_id
            _validate_identifier(
                "source_id", sid, where=f"task_id={p.task_id!r}"
            )
            if sid in seen_source_ids:
                raise ValueError(
                    f"cross-partial source_id 충돌: source_id={sid!r} 가 "
                    f"task_id={seen_source_ids[sid]!r} 와 task_id={p.task_id!r} 두 "
                    f"partial 에서 등장. SourceCollectorWorker 가 task 마다 고유한 "
                    f"source_id 를 발급해야 한다는 invariant 가 깨졌음 — LLM-AP-003 "
                    f"production breach 신호. 충돌은 조용히 dedup 하지 않는다. "
                    f"action: (1) 두 task 의 LLM raw response 비교하여 worker 의 "
                    f"source_id 발급 로직이 task 간 격리됐는지 확인, "
                    f"(2) source_id 가 동일 URL/플랫폼에서 derive 됐다면 collector 의 "
                    f"id 정책 (e.g. {{platform}}_{{post_id}}) 충돌 가능성 검토, "
                    f"(3) 머지 재실행하지 말고 worker 수정 후 partial 재생성."
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

"""SourceRegistry → SourceCompletenessReport ('부족 자료 식별') 빌더 (Phase 5, v0.6.0).

`source_registry.json` 을 받아 부족·위험 항목을 식별하여
`source_completeness_report.json` (`SourceCompletenessReport`) 을 생성합니다.
docs/12_QA_AND_REVIEW_SPEC.md §1 의 Review Gate 2 (`source_completeness_review`)
의 입력입니다.

본 모듈은 **순수 함수만** 제공합니다 (디스크 I/O 없음 — 영속화는
`source_registry_io.persist_source_completeness_report` 가 담당).

판정 기준 (docs/06_SOURCE_AND_RIGHTS_POLICY.md §2 근거)
------------------------------------------------------

- **사용 가능 (✅)**: `rights_clear`, `manual_user_provided`. → usable_sources 에 집계.
- **조건부 (⚠️ Review Gate)**: `rights_unknown` → INFO 이슈.
- **사용 불가 (❌)**:
    - `review_required` → WARNING (검토 전 사용 금지).
    - `do_not_use`      → WARNING (사용 금지).
    - `download_failed` / `login_required` / `private_or_deleted`
      → WARNING (자동 수집 실패·접근 불가, 사용자 개입 신호).
- **신뢰도 낮음**: `reliability_score < reliability_threshold` (default 0.5) → WARNING.
- **위험 플래그**: `risk_flags` 비어있지 않음 → WARNING (정책 §5, Review Gate 명시 승인).

severity 정책 (v0.6.0, 사용자 확정)
-----------------------------------

**사용 가능 자료가 0개일 때만 blocker** (`NO_USABLE_SOURCES`). 자료 자체가 없거나
(`total_sources == 0`) 모든 자료의 권리가 미확보된 경우 모두 해당. 그 외 권리·신뢰
도·위험 이슈는 warning/info 로, Review Gate 에서 사용자가 '보완 또는 계속 진행' 을
판단합니다.

overall_status
--------------
- `insufficient`    : usable_sources == 0.
- `needs_attention` : usable_sources > 0 이고 warning 이슈 존재.
- `ready`           : usable_sources > 0 이고 warning 없음.
"""

from __future__ import annotations

from schemas.models import (
    CompletenessIssue,
    CompletenessIssueType,
    CompletenessSeverity,
    RightsStatus,
    SourceCompletenessReport,
    SourceEntry,
    SourceRegistry,
)


DEFAULT_RELIABILITY_THRESHOLD: float = 0.5

# 정책 §2 ✅ — 무조건 사용 가능한 권리 상태.
_USABLE_RIGHTS: frozenset[str] = frozenset(
    {RightsStatus.RIGHTS_CLEAR.value, RightsStatus.MANUAL_USER_PROVIDED.value}
)

# 정책 §2 ❌ 중 자동 수집 실패·접근 불가 (사용자 개입 신호).
_UNUSABLE_RIGHTS: frozenset[str] = frozenset(
    {
        RightsStatus.DOWNLOAD_FAILED.value,
        RightsStatus.LOGIN_REQUIRED.value,
        RightsStatus.PRIVATE_OR_DELETED.value,
    }
)


def _rights_value(entry: SourceEntry) -> str:
    """SourceEntry.rights_status 를 문자열로 (use_enum_values 로 이미 str 일 수 있음)."""
    rs = entry.rights_status
    return rs if isinstance(rs, str) else rs.value


def _rights_issue(entry: SourceEntry) -> CompletenessIssue | None:
    """권리 상태 기반 이슈 1건 (없으면 None)."""
    rv = _rights_value(entry)
    if rv in _USABLE_RIGHTS:
        return None
    if rv == RightsStatus.DO_NOT_USE.value:
        return CompletenessIssue(
            issue_type=CompletenessIssueType.RIGHTS_DO_NOT_USE,
            severity=CompletenessSeverity.WARNING,
            source_id=entry.source_id,
            detail=f"rights_status={rv} — 사용 금지 자료.",
            recommendation="영상에서 제외하거나 대체 자료를 확보하십시오.",
        )
    if rv == RightsStatus.REVIEW_REQUIRED.value:
        return CompletenessIssue(
            issue_type=CompletenessIssueType.RIGHTS_REVIEW_REQUIRED,
            severity=CompletenessSeverity.WARNING,
            source_id=entry.source_id,
            detail=f"rights_status={rv} — 사람 검토 전 사용 금지.",
            recommendation="Review Gate 에서 권리를 확인한 뒤 사용하십시오.",
        )
    if rv in _UNUSABLE_RIGHTS:
        return CompletenessIssue(
            issue_type=CompletenessIssueType.SOURCE_UNUSABLE,
            severity=CompletenessSeverity.WARNING,
            source_id=entry.source_id,
            detail=f"rights_status={rv} — 자동 수집 실패 또는 접근 불가.",
            recommendation="사용자가 직접 업로드하거나 자료를 재수집하십시오.",
        )
    if rv == RightsStatus.RIGHTS_UNKNOWN.value:
        return CompletenessIssue(
            issue_type=CompletenessIssueType.RIGHTS_UNKNOWN,
            severity=CompletenessSeverity.INFO,
            source_id=entry.source_id,
            detail=f"rights_status={rv} — 권리 정보 미상.",
            recommendation="Review Gate 통과 시 사용 가능. 출처/라이선스 확인을 권장합니다.",
        )
    # 알 수 없는 신규 권리 상태 (스키마 drift) — 보수적으로 WARNING 으로 표면화.
    # known REVIEW_REQUIRED 와 구분되는 전용 issue_type 으로 진단을 선명하게.
    return CompletenessIssue(
        issue_type=CompletenessIssueType.RIGHTS_STATUS_UNKNOWN_VALUE,
        severity=CompletenessSeverity.WARNING,
        source_id=entry.source_id,
        detail=f"rights_status={rv} — 정책에 정의되지 않은 권리 상태.",
        recommendation="docs/06_SOURCE_AND_RIGHTS_POLICY.md §2 에 분류를 추가하십시오.",
    )


def check_source_completeness(
    registry: SourceRegistry,
    *,
    reliability_threshold: float = DEFAULT_RELIABILITY_THRESHOLD,
) -> SourceCompletenessReport:
    """SourceRegistry 를 받아 부족 자료를 식별한 SourceCompletenessReport 생성.

    parameters
    ----------
    registry : SourceRegistry
        `source_registry.json` 으로 영속화될/된 정식 레지스트리.
    reliability_threshold : float, default 0.5
        `reliability_score < threshold` 인 소스를 '신뢰도 낮음' 으로 표시.
        SourceEntry 의 reliability_score 기본값 (0.5) 자체는 통과 (strict `<`).

    returns
    -------
    SourceCompletenessReport
        registry 와 동일한 project_id. 디스크 I/O 없음.
    """
    sources = registry.sources
    issues: list[CompletenessIssue] = []
    usable = 0

    for entry in sources:
        if _rights_value(entry) in _USABLE_RIGHTS:
            usable += 1

        rights_issue = _rights_issue(entry)
        if rights_issue is not None:
            issues.append(rights_issue)

        if entry.reliability_score < reliability_threshold:
            issues.append(
                CompletenessIssue(
                    issue_type=CompletenessIssueType.LOW_RELIABILITY,
                    severity=CompletenessSeverity.WARNING,
                    source_id=entry.source_id,
                    detail=(
                        f"reliability_score={entry.reliability_score} < "
                        f"threshold={reliability_threshold}."
                    ),
                    recommendation="교차 검증하거나 신뢰도 높은 대체 출처를 보강하십시오.",
                )
            )

        if entry.risk_flags:
            issues.append(
                CompletenessIssue(
                    issue_type=CompletenessIssueType.RISK_FLAG_PRESENT,
                    severity=CompletenessSeverity.WARNING,
                    source_id=entry.source_id,
                    detail=f"risk_flags={entry.risk_flags}.",
                    recommendation=(
                        "정책 §5 에 따라 Review Gate 에서 사용자 명시 승인이 필요합니다."
                    ),
                )
            )

    # 사용 가능 자료 0개 — 유일한 blocker.
    if usable == 0:
        issues.insert(
            0,
            CompletenessIssue(
                issue_type=CompletenessIssueType.NO_USABLE_SOURCES,
                severity=CompletenessSeverity.BLOCKER,
                source_id=None,
                detail=(
                    f"사용 가능 (rights_clear / manual_user_provided) 자료가 0개 "
                    f"(total={len(sources)})."
                ),
                recommendation=(
                    "자료를 보완하십시오 — 사용자 직접 업로드, 권리 확보, 또는 "
                    "source_collector 재실행."
                ),
            ),
        )

    # use_enum_values=True 라 i.severity 는 런타임에 str 이지만, config 변경에
    # 결합되지 않도록 str() 로 정규화한 뒤 enum .value 와 비교한다.
    def _sev_count(target: CompletenessSeverity) -> int:
        return sum(1 for i in issues if str(i.severity) == target.value)

    blocker_count = _sev_count(CompletenessSeverity.BLOCKER)
    warning_count = _sev_count(CompletenessSeverity.WARNING)
    info_count = _sev_count(CompletenessSeverity.INFO)

    if usable == 0:
        overall_status = "insufficient"
    elif warning_count > 0:
        overall_status = "needs_attention"
    else:
        overall_status = "ready"

    return SourceCompletenessReport(
        project_id=registry.project_id,
        reliability_threshold=reliability_threshold,
        total_sources=len(sources),
        usable_sources=usable,
        blocker_count=blocker_count,
        warning_count=warning_count,
        info_count=info_count,
        overall_status=overall_status,
        issues=issues,
    )


__all__ = [
    "check_source_completeness",
    "DEFAULT_RELIABILITY_THRESHOLD",
]

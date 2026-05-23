"""source_completeness_checker 단위 테스트 (Phase 5, v0.6.0).

검증 범위
--------
1. happy path — 사용 가능 자료만 → ready, 이슈 없음.
2. usable_sources 집계 (rights_clear / manual_user_provided 만).
3. severity 분류 (사용자 확정):
   - 사용 가능 자료 0개 → blocker (NO_USABLE_SOURCES), overall=insufficient.
   - do_not_use / review_required / 수집실패 → warning.
   - rights_unknown → info.
   - reliability_score < threshold → warning (경계: == threshold 는 통과).
   - risk_flags 존재 → warning.
4. overall_status 분기 (ready / needs_attention / insufficient).
5. 임계값 파라미터화.
6. 빈 registry — blocker + insufficient.

실행:
    python -m unittest tests.test_source_completeness_checker
"""

from __future__ import annotations

import unittest

from schemas.models import (
    CompletenessIssueType,
    CompletenessSeverity,
    RightsStatus,
    SourceCompletenessReport,
    SourceEntry,
    SourceRegistry,
)
from orchestrator.source_completeness_checker import check_source_completeness


def _entry(sid: str, **overrides) -> SourceEntry:
    base: dict[str, object] = dict(source_id=sid, platform="x", source_type="post")
    base.update(overrides)
    return SourceEntry(**base)


def _registry(sources: list[SourceEntry], *, project_id: str = "proj_001") -> SourceRegistry:
    return SourceRegistry(project_id=project_id, sources=sources)


def _types(report: SourceCompletenessReport) -> set[str]:
    return {i.issue_type for i in report.issues}


class HappyPathTests(unittest.TestCase):
    def test_all_clear_is_ready_no_issues(self):
        reg = _registry(
            [
                _entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry("s2", rights_status=RightsStatus.MANUAL_USER_PROVIDED),
            ]
        )
        report = check_source_completeness(reg)
        self.assertEqual(report.overall_status, "ready")
        self.assertEqual(report.issues, [])
        self.assertEqual(report.usable_sources, 2)
        self.assertEqual(report.total_sources, 2)
        self.assertEqual(report.blocker_count, 0)

    def test_report_project_id_matches_registry(self):
        reg = _registry([_entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR)], project_id="proj_X")
        report = check_source_completeness(reg)
        self.assertEqual(report.project_id, "proj_X")


class UsableCountTests(unittest.TestCase):
    def test_only_clear_and_manual_count_as_usable(self):
        reg = _registry(
            [
                _entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry("s2", rights_status=RightsStatus.MANUAL_USER_PROVIDED),
                _entry("s3", rights_status=RightsStatus.RIGHTS_UNKNOWN),
                _entry("s4", rights_status=RightsStatus.REVIEW_REQUIRED),
            ]
        )
        report = check_source_completeness(reg)
        self.assertEqual(report.usable_sources, 2)
        self.assertEqual(report.total_sources, 4)


class NoUsableSourcesBlockerTests(unittest.TestCase):
    def test_empty_registry_is_insufficient_blocker(self):
        report = check_source_completeness(_registry([]))
        self.assertEqual(report.overall_status, "insufficient")
        self.assertEqual(report.blocker_count, 1)
        self.assertEqual(report.usable_sources, 0)
        self.assertEqual(report.total_sources, 0)
        self.assertIn(CompletenessIssueType.NO_USABLE_SOURCES.value, _types(report))
        # blocker 이슈는 registry-level (source_id=None).
        blocker = report.issues[0]
        self.assertEqual(blocker.severity, CompletenessSeverity.BLOCKER.value)
        self.assertIsNone(blocker.source_id)

    def test_all_unusable_rights_is_insufficient(self):
        reg = _registry(
            [
                _entry("s1", rights_status=RightsStatus.REVIEW_REQUIRED),
                _entry("s2", rights_status=RightsStatus.DO_NOT_USE),
            ]
        )
        report = check_source_completeness(reg)
        self.assertEqual(report.usable_sources, 0)
        self.assertEqual(report.overall_status, "insufficient")
        self.assertEqual(report.blocker_count, 1)
        # blocker 가 맨 앞에 삽입됨.
        self.assertEqual(report.issues[0].issue_type, CompletenessIssueType.NO_USABLE_SOURCES.value)


class RightsSeverityTests(unittest.TestCase):
    def test_do_not_use_is_warning(self):
        reg = _registry(
            [
                _entry("ok", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry("bad", rights_status=RightsStatus.DO_NOT_USE),
            ]
        )
        report = check_source_completeness(reg)
        issue = next(i for i in report.issues if i.source_id == "bad")
        self.assertEqual(issue.issue_type, CompletenessIssueType.RIGHTS_DO_NOT_USE.value)
        self.assertEqual(issue.severity, CompletenessSeverity.WARNING.value)
        self.assertEqual(report.overall_status, "needs_attention")

    def test_review_required_is_warning(self):
        reg = _registry(
            [
                _entry("ok", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry("rev", rights_status=RightsStatus.REVIEW_REQUIRED),
            ]
        )
        report = check_source_completeness(reg)
        issue = next(i for i in report.issues if i.source_id == "rev")
        self.assertEqual(issue.issue_type, CompletenessIssueType.RIGHTS_REVIEW_REQUIRED.value)
        self.assertEqual(issue.severity, CompletenessSeverity.WARNING.value)

    def test_unusable_rights_are_warning_source_unusable(self):
        for rs in (
            RightsStatus.DOWNLOAD_FAILED,
            RightsStatus.LOGIN_REQUIRED,
            RightsStatus.PRIVATE_OR_DELETED,
        ):
            with self.subTest(rights_status=rs):
                reg = _registry(
                    [
                        _entry("ok", rights_status=RightsStatus.RIGHTS_CLEAR),
                        _entry("u", rights_status=rs),
                    ]
                )
                report = check_source_completeness(reg)
                issue = next(i for i in report.issues if i.source_id == "u")
                self.assertEqual(
                    issue.issue_type, CompletenessIssueType.SOURCE_UNUSABLE.value
                )
                self.assertEqual(issue.severity, CompletenessSeverity.WARNING.value)

    def test_rights_unknown_is_info(self):
        reg = _registry(
            [
                _entry("ok", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry("unk", rights_status=RightsStatus.RIGHTS_UNKNOWN),
            ]
        )
        report = check_source_completeness(reg)
        issue = next(i for i in report.issues if i.source_id == "unk")
        self.assertEqual(issue.issue_type, CompletenessIssueType.RIGHTS_UNKNOWN.value)
        self.assertEqual(issue.severity, CompletenessSeverity.INFO.value)
        self.assertEqual(report.info_count, 1)
        # info 만 있으면 needs_attention 이 아니라 ready (warning 0).
        self.assertEqual(report.overall_status, "ready")


class ReliabilityThresholdTests(unittest.TestCase):
    def test_default_threshold_passes_default_score(self):
        # SourceEntry 기본 reliability_score=0.5, 조건 < 0.5 → 통과 (이슈 없음).
        reg = _registry([_entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR)])
        report = check_source_completeness(reg)
        self.assertNotIn(CompletenessIssueType.LOW_RELIABILITY.value, _types(report))

    def test_below_threshold_is_warning(self):
        reg = _registry(
            [_entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR, reliability_score=0.3)]
        )
        report = check_source_completeness(reg)
        issue = next(
            i for i in report.issues if i.issue_type == CompletenessIssueType.LOW_RELIABILITY.value
        )
        self.assertEqual(issue.severity, CompletenessSeverity.WARNING.value)
        self.assertEqual(report.overall_status, "needs_attention")

    def test_boundary_equal_threshold_passes(self):
        # score == threshold → strict `<` 이므로 통과.
        reg = _registry(
            [_entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR, reliability_score=0.5)]
        )
        report = check_source_completeness(reg, reliability_threshold=0.5)
        self.assertNotIn(CompletenessIssueType.LOW_RELIABILITY.value, _types(report))

    def test_custom_threshold(self):
        reg = _registry(
            [_entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR, reliability_score=0.55)]
        )
        report = check_source_completeness(reg, reliability_threshold=0.6)
        self.assertIn(CompletenessIssueType.LOW_RELIABILITY.value, _types(report))
        self.assertEqual(report.reliability_threshold, 0.6)


class RiskFlagTests(unittest.TestCase):
    def test_risk_flag_present_is_warning(self):
        reg = _registry(
            [
                _entry(
                    "s1",
                    rights_status=RightsStatus.RIGHTS_CLEAR,
                    risk_flags=["graphic_content"],
                )
            ]
        )
        report = check_source_completeness(reg)
        issue = next(
            i for i in report.issues if i.issue_type == CompletenessIssueType.RISK_FLAG_PRESENT.value
        )
        self.assertEqual(issue.severity, CompletenessSeverity.WARNING.value)
        self.assertIn("graphic_content", issue.detail)

    def test_no_risk_flags_no_issue(self):
        reg = _registry([_entry("s1", rights_status=RightsStatus.RIGHTS_CLEAR)])
        report = check_source_completeness(reg)
        self.assertNotIn(CompletenessIssueType.RISK_FLAG_PRESENT.value, _types(report))


class MultipleIssuesPerSourceTests(unittest.TestCase):
    def test_one_source_can_yield_multiple_issues(self):
        # 사용 불가 권리 + 낮은 신뢰도 + 위험 플래그 → 한 소스에서 3 이슈.
        reg = _registry(
            [
                _entry("ok", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry(
                    "multi",
                    rights_status=RightsStatus.REVIEW_REQUIRED,
                    reliability_score=0.1,
                    risk_flags=["death_visible"],
                ),
            ]
        )
        report = check_source_completeness(reg)
        multi_issues = [i for i in report.issues if i.source_id == "multi"]
        self.assertEqual(len(multi_issues), 3)
        self.assertEqual(report.warning_count, 3)
        self.assertEqual(report.overall_status, "needs_attention")


class CountsConsistencyTests(unittest.TestCase):
    def test_counts_match_issue_list(self):
        reg = _registry(
            [
                _entry("a", rights_status=RightsStatus.RIGHTS_CLEAR),
                _entry("b", rights_status=RightsStatus.RIGHTS_UNKNOWN),
                _entry("c", rights_status=RightsStatus.DO_NOT_USE),
            ]
        )
        report = check_source_completeness(reg)
        self.assertEqual(
            report.blocker_count,
            sum(1 for i in report.issues if i.severity == CompletenessSeverity.BLOCKER.value),
        )
        self.assertEqual(
            report.warning_count,
            sum(1 for i in report.issues if i.severity == CompletenessSeverity.WARNING.value),
        )
        self.assertEqual(
            report.info_count,
            sum(1 for i in report.issues if i.severity == CompletenessSeverity.INFO.value),
        )


if __name__ == "__main__":
    unittest.main()

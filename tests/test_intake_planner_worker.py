"""IntakePlannerWorker 단위 테스트 (Phase 3, v0.3.0).

실제 LLM 호출은 `OSINT_LLM_STUB=1` 로 우회합니다. claude / codex 두 backend 의
출력 wrapper 흐름을 stub mode pass-through 로 검증.

검증 범위
--------
1. system_prompt 가 IntakePlan 스키마 / IntakeMode enum / 카테고리별 가이드 hook
   을 포함하는지.
2. CATEGORY_GUIDANCE 가 GOAL.md G2 의 5 카테고리를 모두 커버하는지.
3. build_user_prompt 가 manifest 메타데이터를 모두 치환해 반영하는지 + 미등록
   카테고리에 대한 폴백.
4. output_path 가 `01_intake/intake_plan.json` 으로 고정되는지.
5. run() 통합: stub 응답 → IntakePlan 검증 → 파일 영속화 + LLMCallRecord 영속화.
6. backend 전환 (claude → codex) 시에도 동일 흐름.

실행:
    python -m unittest tests.test_intake_planner_worker
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path

from schemas.models import (
    Category,
    IntakeMode,
    IntakePlan,
    LLMCallRecord,
    ProjectManifest,
    ProjectState,
    TaskPriority,
    TaskQueueItem,
    TaskStatus,
)
from workers.intake_planner_worker import (
    CATEGORY_GUIDANCE,
    IntakePlannerWorker,
)


VALID_PLAN_JSON = json.dumps(
    {
        "schema_version": 1,
        "project_id": "demo3",
        "topic": "테스트 주제",
        "category": "geopolitics",
        "target_duration_min": 18,
        "orchestrator_assessment": "본 주제의 핵심 위험과 자료 확보 난이도 평가.",
        "required_items": [
            {
                "item_id": "core_event",
                "label": "핵심 사건",
                "description": "본 영상의 본문이 되는 사건.",
                "why_needed": "주제의 발단이 되는 1차 사건이 없으면 서사 구성 불가.",
                "priority": "must_use",
                "expected_input_types": ["url", "text"],
                "default_mode": "link_provide",
                "user_options": ["link_provide", "ai_delegate", "skip"],
                "ai_delegate_task": "공식 발표 / 1차 보도 자동 수집",
                "risk_notice": None,
                "status": "pending",
            }
        ],
    },
    ensure_ascii=False,
)


def _write_manifest_file(project_root: Path, project_id: str, category: Category) -> None:
    pdir = project_root / project_id
    pdir.mkdir(parents=True, exist_ok=True)
    manifest = ProjectManifest(
        project_id=project_id,
        title="중동 정세 격동",
        category=category,
        target_duration_min=18,
        topic_summary="유가·해운 운임 충격",
        current_state=ProjectState.INTAKE_PLANNING,
    )
    (pdir / "project_manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# 1. 정적 검증
# ---------------------------------------------------------------------------


class TestSystemPromptStructure(unittest.TestCase):
    """system_prompt 가 LLM 에 IntakePlan 스키마를 정확히 안내하는지."""

    def setUp(self) -> None:
        self.prompt = IntakePlannerWorker.system_prompt

    def test_mentions_intake_plan_schema(self) -> None:
        for key in [
            "schema_version",
            "project_id",
            "category",
            "target_duration_min",
            "required_items",
            "orchestrator_assessment",
        ]:
            self.assertIn(key, self.prompt, f"missing IntakePlan key: {key}")

    def test_mentions_intake_item_fields(self) -> None:
        for key in [
            "item_id",
            "label",
            "why_needed",
            "priority",
            "default_mode",
            "user_options",
        ]:
            self.assertIn(key, self.prompt, f"missing IntakePlanItem key: {key}")

    def test_mentions_intake_mode_enum_values(self) -> None:
        for mode in IntakeMode:
            self.assertIn(mode.value, self.prompt, f"missing IntakeMode: {mode.value}")

    def test_uses_replace_only_placeholders_not_format(self) -> None:
        # JSON 예시 안의 `{...}` 가 .format() 으로 해석되지 않게 — 정상이라면
        # `.format()` 호출 시 KeyError 가 난다. 본 테스트는 검증을 위해 직접 호출.
        with self.assertRaises((KeyError, IndexError, ValueError)):
            self.prompt.format()  # pragma: no cover


class TestCategoryGuidance(unittest.TestCase):
    def test_all_g2_categories_covered(self) -> None:
        for cat in Category:
            self.assertIn(cat.value, CATEGORY_GUIDANCE, f"missing category: {cat.value}")

    def test_guidance_strings_nonempty(self) -> None:
        for cat, guidance in CATEGORY_GUIDANCE.items():
            self.assertTrue(guidance.strip(), f"empty guidance for {cat}")


# ---------------------------------------------------------------------------
# 2. build_user_prompt / output_path
# ---------------------------------------------------------------------------


class TestBuildUserPrompt(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.projects_root = self.root / "projects"
        _write_manifest_file(self.projects_root, "demo3", Category.GEOPOLITICS)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _args(self) -> argparse.Namespace:
        # 절대경로 projects_root: BaseWorker.project_dir 가 그대로 사용 →
        # REPO_ROOT 의 실제 projects/ 를 건드리지 않고 임시 디렉토리만 사용.
        return argparse.Namespace(
            project_id="demo3",
            task_id="intake-1",
            projects_root=str(self.projects_root),
        )

    def _task(self) -> TaskQueueItem:
        return TaskQueueItem(
            task_id="intake-1",
            task_type="intake_planning",
            assigned_worker="intake_planner",
            description="test",
            output_refs=["01_intake/intake_plan.json"],
        )

    def test_includes_manifest_fields(self) -> None:
        prompt = IntakePlannerWorker().build_user_prompt(self._args(), self._task())
        self.assertIn("demo3", prompt)
        self.assertIn("중동 정세 격동", prompt)
        self.assertIn("geopolitics", prompt)
        self.assertIn("18", prompt)
        self.assertIn("유가·해운 운임 충격", prompt)

    def test_includes_category_guidance(self) -> None:
        prompt = IntakePlannerWorker().build_user_prompt(self._args(), self._task())
        # geopolitics 가이드에서 한 줄을 골라 포함 검증.
        self.assertIn("지정학 카테고리 표준 항목", prompt)

    def test_fallback_for_unknown_category_guidance(self) -> None:
        # CATEGORY_GUIDANCE 에 없는 카테고리 (mock) — Category enum 에는 모두 있지만
        # 만약 추가될 경우 폴백 메시지가 노출되는지 검증.
        worker = IntakePlannerWorker()
        original = IntakePlannerWorker.CATEGORY_GUIDANCE
        try:
            IntakePlannerWorker.CATEGORY_GUIDANCE = {}  # type: ignore[misc]
            prompt = worker.build_user_prompt(self._args(), self._task())
            self.assertIn("표준 가이드가 등록되지 않았습니다", prompt)
        finally:
            IntakePlannerWorker.CATEGORY_GUIDANCE = original  # type: ignore[misc]


class TestOutputPath(unittest.TestCase):
    def test_output_path_under_intake_dir(self) -> None:
        worker = IntakePlannerWorker()
        args = argparse.Namespace(
            project_id="demo3",
            task_id="intake-1",
            projects_root="projects",
        )
        task = TaskQueueItem(
            task_id="intake-1",
            task_type="intake_planning",
            assigned_worker="intake_planner",
            description="test",
        )
        path = worker.output_path(args, task)
        self.assertTrue(
            str(path).endswith(os.path.join("01_intake", "intake_plan.json")),
            f"unexpected output_path: {path}",
        )


# ---------------------------------------------------------------------------
# 3. run() 통합 — stub backend
# ---------------------------------------------------------------------------


class _IntegrationBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.projects_root = self.root / "projects"
        _write_manifest_file(self.projects_root, "demo3", Category.GEOPOLITICS)
        self._saved_env = {
            "OSINT_LLM_STUB": os.environ.get("OSINT_LLM_STUB"),
            "OSINT_LLM_STUB_RESPONSE": os.environ.get("OSINT_LLM_STUB_RESPONSE"),
        }

    def tearDown(self) -> None:
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def _stub(self, response: str) -> None:
        os.environ["OSINT_LLM_STUB"] = "1"
        os.environ["OSINT_LLM_STUB_RESPONSE"] = response

    def _args(self) -> argparse.Namespace:
        return argparse.Namespace(
            project_id="demo3",
            task_id="intake-1",
            projects_root=str(self.projects_root),
        )

    def _task(self) -> TaskQueueItem:
        return TaskQueueItem(
            task_id="intake-1",
            task_type="intake_planning",
            assigned_worker="intake_planner",
            description="test",
            output_refs=["01_intake/intake_plan.json"],
        )


class TestRunOkClaude(_IntegrationBase):
    def test_run_ok_persists_intake_plan_and_record(self) -> None:
        self._stub(VALID_PLAN_JSON)
        result = IntakePlannerWorker().run(self._args(), self._task())
        self.assertEqual(result.status, TaskStatus.COMPLETED)

        outp = self.projects_root / "demo3" / "01_intake" / "intake_plan.json"
        self.assertTrue(outp.exists(), f"intake_plan.json 미생성: {outp}")
        plan = IntakePlan.model_validate_json(outp.read_text(encoding="utf-8"))
        self.assertEqual(plan.project_id, "demo3")
        self.assertEqual(len(plan.required_items), 1)
        self.assertEqual(plan.required_items[0].priority, TaskPriority.MUST_USE.value)

        # LLMCallRecord 영속화
        records = list((self.projects_root / "demo3" / "llm_calls").glob("*.json"))
        self.assertEqual(len(records), 1)
        record = LLMCallRecord.model_validate_json(records[0].read_text(encoding="utf-8"))
        self.assertEqual(record.parsed_status, "ok")
        self.assertEqual(record.backend, "claude")
        self.assertEqual(record.mode, "response")


class TestRunOkCodex(_IntegrationBase):
    """codex backend 도 stub mode 에서 동일 흐름이 동작하는지."""

    def test_codex_backend_passthrough(self) -> None:
        self._stub(VALID_PLAN_JSON)
        worker = IntakePlannerWorker()
        worker.llm_backend = "codex"  # 인스턴스 attribute override (ClassVar)
        result = worker.run(self._args(), self._task())
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        records = list((self.projects_root / "demo3" / "llm_calls").glob("*.json"))
        self.assertEqual(len(records), 1)
        record = LLMCallRecord.model_validate_json(records[0].read_text(encoding="utf-8"))
        self.assertEqual(record.backend, "codex")


class TestRunValidationFailed(_IntegrationBase):
    def test_schema_mismatch_yields_validation_failed(self) -> None:
        # required_items 누락 → IntakePlan validation 통과지만 forbid 필드 추가로 실패 유도.
        bad = json.dumps(
            {
                "schema_version": 1,
                "project_id": "demo3",
                "topic": "x",
                "category": "geopolitics",
                "target_duration_min": 18,
                "unknown_extra_field": "boom",
            },
            ensure_ascii=False,
        )
        self._stub(bad)
        result = IntakePlannerWorker().run(self._args(), self._task())
        self.assertEqual(result.status, TaskStatus.FAILED)
        records = list((self.projects_root / "demo3" / "llm_calls").glob("*.json"))
        self.assertEqual(len(records), 1)
        record = LLMCallRecord.model_validate_json(records[0].read_text(encoding="utf-8"))
        self.assertEqual(record.parsed_status, "validation_failed")


if __name__ == "__main__":
    unittest.main()

"""Phase 3 인테이크 흐름 통합 테스트 — CLI plan-intake / submit-intake + Web POST.

검증 흐름
--------
1. `plan-intake demo3` 가 IntakePlannerWorker 를 호출하고 `intake_plan.json` 을
   생성하며 state 를 `created → intake_planning → intake_pending_user` 로 진행.
2. `submit-intake demo3 --file <path>` 가 SourceIntake 파일을 영속화하고 state 를
   `intake_pending_user → source_collecting` 으로 전이.
3. FastAPI `POST /intake/{pid}/submit` 가 form 데이터를 받아 동일 결과를 만든다.

본 테스트는 LLM stub (`OSINT_LLM_STUB=1`) 모드로 실 CLI 호출을 우회한다.

실행:
    python -m unittest tests.test_intake_flow
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from orchestrator import config as orch_config
from orchestrator.main import main as cli_main
from schemas.models import (
    Category,
    IntakeMode,
    IntakePlan,
    ProjectManifest,
    ProjectState,
    SourceIntake,
)


VALID_PLAN_JSON = json.dumps(
    {
        "schema_version": 1,
        "project_id": "demo3",
        "topic": "테스트",
        "category": "geopolitics",
        "target_duration_min": 18,
        "orchestrator_assessment": "평가",
        "required_items": [
            {
                "item_id": "core_event",
                "label": "핵심 사건",
                "description": "본 영상 본문 사건",
                "why_needed": "서사의 기준",
                "priority": "must_use",
                "expected_input_types": ["url"],
                "default_mode": "link_provide",
                "user_options": ["link_provide", "ai_delegate", "skip"],
                "ai_delegate_task": "공식 발표 수집",
                "risk_notice": None,
                "status": "pending",
            },
            {
                "item_id": "context_sources",
                "label": "맥락 출처",
                "description": "주변 맥락 자료",
                "why_needed": "배경 설명",
                "priority": "normal",
                "expected_input_types": ["url"],
                "default_mode": "ai_delegate",
                "user_options": ["ai_delegate", "skip"],
                "ai_delegate_task": "주변 보도 자동 수집",
                "risk_notice": None,
                "status": "pending",
            },
        ],
    },
    ensure_ascii=False,
)


class _IsolatedProjectsRoot(unittest.TestCase):
    """본 저장소의 실제 `projects/` 를 건드리지 않게 임시 디렉토리로 redirect.

    `orchestrator.config.REPO_ROOT` 를 monkeypatch 한다. project_manager 와
    BaseWorker 모두 본 REPO_ROOT 기준으로 path 를 계산하므로 한 군데만 바꾸면 됨...
    이 아니다. `workers.base_worker.REPO_ROOT` 는 별도로 정의되어 있다. 둘 다 패치.
    """

    def setUp(self) -> None:
        from workers import base_worker
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_repo_root_config = orch_config.REPO_ROOT
        self._orig_repo_root_worker = base_worker.REPO_ROOT
        orch_config.REPO_ROOT = self.root
        base_worker.REPO_ROOT = self.root
        # config 캐시가 없으므로 매 호출 load_config 가 새 REPO_ROOT 를 본다.
        self.projects_root = self.root / "projects"
        self._saved_env = {
            "OSINT_LLM_STUB": os.environ.get("OSINT_LLM_STUB"),
            "OSINT_LLM_STUB_RESPONSE": os.environ.get("OSINT_LLM_STUB_RESPONSE"),
        }

    def tearDown(self) -> None:
        from workers import base_worker
        orch_config.REPO_ROOT = self._orig_repo_root_config
        base_worker.REPO_ROOT = self._orig_repo_root_worker
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def _stub(self, response: str) -> None:
        os.environ["OSINT_LLM_STUB"] = "1"
        os.environ["OSINT_LLM_STUB_RESPONSE"] = response

    def _create_demo3(self) -> ProjectManifest:
        return ProjectManifest.model_validate_json(
            self._run_cli([
                "new-project", "demo3",
                "--title", "테스트 주제",
                "--category", "geopolitics",
                "--duration-min", "18",
                "--topic-summary", "스텁 요약",
            ], capture_manifest=True)
        )

    def _run_cli(self, argv: list[str], capture_manifest: bool = False) -> str:
        """orchestrator.main(argv) 호출. capture_manifest=True 면 호출 직후
        manifest 파일을 읽어 반환."""
        exit_code = cli_main(argv)
        self.assertEqual(exit_code, 0, f"CLI {argv} failed with exit={exit_code}")
        if capture_manifest:
            pid_idx = argv.index("new-project") + 1 if "new-project" in argv else 1
            pid = argv[pid_idx]
            return (self.projects_root / pid / "project_manifest.json").read_text(
                encoding="utf-8"
            )
        return ""

    def _load_manifest(self, pid: str) -> ProjectManifest:
        return ProjectManifest.model_validate_json(
            (self.projects_root / pid / "project_manifest.json").read_text(
                encoding="utf-8"
            )
        )


class TestPlanIntakeCLI(_IsolatedProjectsRoot):
    def test_plan_intake_creates_plan_and_advances_state(self) -> None:
        self._create_demo3()
        self.assertEqual(
            self._load_manifest("demo3").current_state, ProjectState.CREATED.value
        )

        self._stub(VALID_PLAN_JSON)
        exit_code = cli_main(["plan-intake", "demo3"])
        self.assertEqual(exit_code, 0)

        plan_path = self.projects_root / "demo3" / "01_intake" / "intake_plan.json"
        self.assertTrue(plan_path.exists())
        plan = IntakePlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan.project_id, "demo3")
        self.assertEqual(len(plan.required_items), 2)

        manifest = self._load_manifest("demo3")
        self.assertEqual(
            manifest.current_state, ProjectState.INTAKE_PENDING_USER.value
        )
        # state_history 에 두 전이가 모두 기록됐는지
        transitions = [
            (
                t.from_state if isinstance(t.from_state, str) else t.from_state.value,
                t.to_state if isinstance(t.to_state, str) else t.to_state.value,
            )
            for t in manifest.state_history
        ]
        self.assertIn(
            (ProjectState.CREATED.value, ProjectState.INTAKE_PLANNING.value),
            transitions,
        )
        self.assertIn(
            (ProjectState.INTAKE_PLANNING.value, ProjectState.INTAKE_PENDING_USER.value),
            transitions,
        )

    def test_plan_intake_fails_when_llm_validation_fails(self) -> None:
        self._create_demo3()
        # required field 누락 → IntakePlan 검증 실패
        self._stub(json.dumps({"schema_version": 1}))
        exit_code = cli_main(["plan-intake", "demo3"])
        self.assertEqual(exit_code, 1)
        # state 는 INTAKE_PLANNING 으로 멈춤 (PENDING_USER 까지 못 감)
        manifest = self._load_manifest("demo3")
        self.assertEqual(
            manifest.current_state, ProjectState.INTAKE_PLANNING.value
        )


class TestSubmitIntakeCLI(_IsolatedProjectsRoot):
    def _prepare_pending(self) -> None:
        self._create_demo3()
        self._stub(VALID_PLAN_JSON)
        self.assertEqual(cli_main(["plan-intake", "demo3"]), 0)

    def test_submit_intake_persists_and_advances_state(self) -> None:
        self._prepare_pending()

        intake = SourceIntake(
            project_id="demo3",
            user_decisions=[],
        )
        intake_file = self.root / "user_decisions.json"
        intake_file.write_text(intake.model_dump_json(indent=2), encoding="utf-8")

        exit_code = cli_main(
            ["submit-intake", "demo3", "--file", str(intake_file)]
        )
        self.assertEqual(exit_code, 0)
        out = self.projects_root / "demo3" / "01_intake" / "source_intake.json"
        self.assertTrue(out.exists())
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SOURCE_COLLECTING.value,
        )

    def test_submit_intake_rejects_mismatched_project_id(self) -> None:
        self._prepare_pending()
        intake = SourceIntake(project_id="other", user_decisions=[])
        intake_file = self.root / "bad.json"
        intake_file.write_text(intake.model_dump_json(indent=2), encoding="utf-8")
        exit_code = cli_main(
            ["submit-intake", "demo3", "--file", str(intake_file)]
        )
        self.assertEqual(exit_code, 1)


class TestWebSubmit(_IsolatedProjectsRoot):
    def test_post_submit_persists_source_intake_and_transitions(self) -> None:
        self._create_demo3()
        self._stub(VALID_PLAN_JSON)
        self.assertEqual(cli_main(["plan-intake", "demo3"]), 0)

        from web.intake_page_app import app

        client = TestClient(app)
        # form 제출: core_event 는 link_provide + URL 1개, context_sources 는 skip
        resp = client.post(
            "/intake/demo3/submit",
            data={
                "mode__core_event": "link_provide",
                "user_note__core_event": "공식 발표 링크 첨부",
                "provided_links__core_event": "https://example.org/news\nhttps://example.org/follow",
                "mode__context_sources": "skip",
            },
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        self.assertEqual(payload["decisions"], 2)
        self.assertEqual(payload["current_state"], ProjectState.SOURCE_COLLECTING.value)

        out = self.projects_root / "demo3" / "01_intake" / "source_intake.json"
        self.assertTrue(out.exists())
        intake = SourceIntake.model_validate_json(out.read_text(encoding="utf-8"))
        self.assertEqual(len(intake.user_decisions), 2)
        core = next(d for d in intake.user_decisions if d.item_id == "core_event")
        self.assertEqual(core.mode, IntakeMode.LINK_PROVIDE.value)
        self.assertEqual(len(core.provided_links), 2)
        skip = next(d for d in intake.user_decisions if d.item_id == "context_sources")
        self.assertEqual(skip.mode, IntakeMode.SKIP.value)

    def test_get_intake_page_renders_html(self) -> None:
        self._create_demo3()
        self._stub(VALID_PLAN_JSON)
        cli_main(["plan-intake", "demo3"])

        from web.intake_page_app import app

        client = TestClient(app)
        resp = client.get("/intake/demo3")
        self.assertEqual(resp.status_code, 200)
        body = resp.text
        self.assertIn("테스트 주제", body)
        self.assertIn("core_event", body)
        self.assertIn("영상 생성 착수", body)


if __name__ == "__main__":
    unittest.main()

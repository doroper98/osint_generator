"""Phase 6 Script 흐름 테스트 — build-script CLI + ScriptWorker.

research 까지 진행한 뒤 build-script(LLM stub)가 full_script.json 을
생성하고 state 를 research → blueprint_review → script_draft 으로
전이하는지 검증. LLM stub(OSINT_LLM_STUB=1)로 실 호출 우회.

실행: python -m unittest tests.test_script_flow
"""

from __future__ import annotations

import argparse
import json

from orchestrator.main import main as cli_main
from schemas.models import FullScript, ProjectState, TaskQueueItem
from tests.test_research_flow import VALID_DOSSIER_JSON, _ResearchHarness


VALID_SCRIPT_JSON = json.dumps(
    {
        "schema_version": 1,
        "project_id": "demo3",
        "title": "테스트 영상",
        "topic": "테스트 주제",
        "target_duration_min": 8,
        "chapters": [
            {"chapter_id": "ch_intro", "title": "도입", "summary": "왜 중요한가"},
            {"chapter_id": "ch_facts", "title": "핵심 사실", "summary": "확인된 사실"},
        ],
        "segments": [
            {
                "segment_id": "seg_01", "chapter_id": "ch_intro",
                "narration": "이 사건이 왜 중요한지 살펴봅니다.",
                "on_screen_caption": "왜 중요한가", "claim_refs": [],
                "label": None, "est_duration_sec": 6.0,
            },
            {
                "segment_id": "seg_02", "chapter_id": "ch_facts",
                "narration": "공식 기관 두 곳이 사건을 확인했습니다.",
                "on_screen_caption": "공식 확인", "claim_refs": ["claim_01"],
                "label": "<확인>", "est_duration_sec": 8.0,
            },
            {
                "segment_id": "seg_03", "chapter_id": "ch_facts",
                "narration": "추가 배후가 있다는 주장도 제기됐으나 아직 확인되지 않았습니다.",
                "on_screen_caption": "미확인 주장", "claim_refs": ["claim_02"],
                "label": "<주장>", "est_duration_sec": 9.0,
            },
        ],
        "total_est_duration_sec": 23.0,
    },
    ensure_ascii=False,
)


class _ScriptHarness(_ResearchHarness):
    def _advance_to_research_in_progress(self) -> None:
        self._advance_to_completeness_review()
        self._stub(VALID_DOSSIER_JSON)
        self.assertEqual(cli_main(["build-research-dossier", "demo3"]), 0)
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.RESEARCH.value,
        )


class TestBuildScriptCLI(_ScriptHarness):
    def test_creates_script_and_advances_state(self) -> None:
        self._advance_to_research_in_progress()
        self._stub(VALID_SCRIPT_JSON)
        rc = cli_main(["build-script", "demo3"])
        self.assertEqual(rc, 0)

        script_path = self.projects_root / "demo3" / "05_script" / "full_script.json"
        self.assertTrue(script_path.exists())
        script = FullScript.model_validate_json(script_path.read_text(encoding="utf-8"))
        self.assertEqual(script.project_id, "demo3")
        self.assertEqual(len(script.segments), 3)
        # 미검증 주장 세그먼트에 라벨 보존.
        self.assertEqual(script.segments[2].label, "<주장>")
        self.assertEqual(script.segments[2].claim_refs, ["claim_02"])

        # v3.0.0: research → script_draft 한 번(16 §2).
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SCRIPT_DRAFT.value,
        )
        transitions = [
            (t.from_state if isinstance(t.from_state, str) else t.from_state.value,
             t.to_state if isinstance(t.to_state, str) else t.to_state.value)
            for t in self._load_manifest("demo3").state_history
        ]
        self.assertIn(
            (ProjectState.RESEARCH.value, ProjectState.SCRIPT_DRAFT.value),
            transitions,
        )

    def test_fails_when_llm_validation_fails(self) -> None:
        self._advance_to_research_in_progress()
        self._stub(json.dumps({"schema_version": 1}))  # project_id 누락
        rc = cli_main(["build-script", "demo3"])
        self.assertEqual(rc, 1)
        # research 로 멈춤.
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.RESEARCH.value,
        )

    def test_rejected_outside_research_in_progress(self) -> None:
        self._create_demo3()  # created
        rc = cli_main(["build-script", "demo3"])
        self.assertEqual(rc, 2)

    def test_invalid_project_id_rejected(self) -> None:
        self.assertEqual(cli_main(["build-script", "../etc"]), 1)


class TestScriptWorkerPrompt(_ScriptHarness):
    def test_prompt_surfaces_claims_and_label_rule(self) -> None:
        self._advance_to_research_in_progress()
        from workers.script_worker import ScriptWorker

        worker = ScriptWorker()
        args = argparse.Namespace(project_id="demo3", task_id="t", projects_root="projects")
        task = TaskQueueItem(
            task_id="t", task_type="script", assigned_worker="script", description="d"
        )
        prompt = worker.build_user_prompt(args, task)
        # 도시어 claim 이 인용 가능하게 노출.
        self.assertIn("claim_id=claim_01", prompt)
        self.assertIn("claim_id=claim_02", prompt)
        # 라벨 규칙 노출 (미검증/주장 분리).
        self.assertIn("label", prompt)
        self.assertIn("target_duration_min", prompt)


if __name__ == "__main__":
    import unittest

    unittest.main()

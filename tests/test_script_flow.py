"""Phase 6 Script 흐름 테스트 — build-script CLI + ScriptWorker.

research 까지 진행한 뒤 build-script(LLM stub)가 script.yaml(Script)과 script_labels.json(코드 계산 라벨,
D-0043)을 만들고 state 를 research → script_draft 로 전이하는지 검증. LLM stub(OSINT_LLM_STUB=1)로 실 호출 우회.

실행: python -m unittest tests.test_script_flow
"""

from __future__ import annotations

import argparse
import json

from orchestrator.main import main as cli_main
import yaml

from schemas.models import ProjectState, TaskQueueItem
from script.labels import ScriptLabels
from script.schema import Script
from tests.test_research_flow import VALID_FACTS_JSON, _ResearchHarness


VALID_SCRIPT_JSON = json.dumps(
    {
        "schema_version": 1,
        "title": "테스트 영상",
        "subtitle": "테스트 주제",
        "date": "2026.09.18",
        "scenes": [
            {"id": "intro", "sentences": [
                {"date": "2026.09.18", "text": "이 사건이 왜 중요한지 살펴봅니다."},
            ]},
            {"id": "facts", "sentences": [
                {"date": "2026.09.18", "text": "공식 기관 두 곳이 사건을 확인했습니다.", "sources": ["clm_0001"]},
                {"date": "2026.09.18", "text": "그런데 한 매체는 배후가 따로 있다고 주장했습니다.",
                 "sources": ["clm_0002"]},
                {"date": "2026.09.18", "text": "따라서 두 기관의 확인과 배후 주장을 함께 봅니다.", "sources": ["clm_0001", "clm_0002"]},
            ]},
        ],
    },
    ensure_ascii=False,
)


class _ScriptHarness(_ResearchHarness):
    def _advance_to_research_in_progress(self) -> None:
        self._advance_to_source_verify()
        self._stub(VALID_FACTS_JSON)
        self.assertEqual(cli_main(["build-research", "demo3"]), 0)
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

        pdir = self.projects_root / "demo3"
        script = Script.model_validate(yaml.safe_load((pdir / "script.yaml").read_text(encoding="utf-8")))
        self.assertEqual([sc.id for sc in script.scenes], ["intro", "facts"])
        # 라벨은 코드가 claims.json status 로 계산한다(D42 → v3.2.0) — 가장 약한 status
        labels = ScriptLabels.model_validate_json((pdir / "script_labels.json").read_text(encoding="utf-8"))
        self.assertIsNone(labels.labels["intro_0"].status)
        self.assertEqual((labels.labels["facts_0"].status, labels.labels["facts_0"].label), ("verified", None))
        self.assertEqual((labels.labels["facts_1"].status, labels.labels["facts_1"].label), ("unverified", "<미검증>"))
        self.assertEqual(labels.labels["facts_2"].label, "<미검증>")
        self.assertEqual(labels.counts(), {"verified": 1, "corroborated": 0, "unverified": 2, "disputed": 0})

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
        self._stub(json.dumps({"schema_version": 1}))  # title·scenes 누락
        rc = cli_main(["build-script", "demo3"])
        self.assertEqual(rc, 1)
        # research 로 멈춤.
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.RESEARCH.value,
        )

    def test_unknown_claim_id_fails(self) -> None:
        self._advance_to_research_in_progress()
        bad = json.loads(VALID_SCRIPT_JSON)
        bad["scenes"][1]["sentences"][0]["sources"] = ["clm_0099"]
        self._stub(json.dumps(bad, ensure_ascii=False))
        self.assertEqual(cli_main(["build-script", "demo3"]), 1)
        self.assertFalse((self.projects_root / "demo3" / "script.yaml").exists())   # 출력 없음(15 P6)
        self.assertEqual(self._load_manifest("demo3").current_state, ProjectState.RESEARCH.value)

    def test_label_mismatch_is_lint_error(self) -> None:
        self._advance_to_research_in_progress()
        self._stub(VALID_SCRIPT_JSON)
        self.assertEqual(cli_main(["build-script", "demo3"]), 0)
        from script.lint import main as lint_main  # noqa: PLC0415
        pdir = self.projects_root / "demo3"
        self.assertEqual(lint_main([str(pdir)]), 0)
        lp = pdir / "script_labels.json"
        d = json.loads(lp.read_text(encoding="utf-8"))
        d["labels"]["facts_1"]["label"] = None      # 저장본을 손으로 바꾸면 재계산과 달라진다
        lp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(lint_main([str(pdir)]), 1)

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
        # 사실과 인용할 claim_id·status 노출(v3.2.0)
        self.assertIn("clm_0001(verified)", prompt)
        self.assertIn("clm_0002(unverified)", prompt)
        # 라벨은 쓰지 말라는 규칙 노출(D-0043) — status 는 보여 주되 라벨 문구 자체는 주지 않는다.
        self.assertIn("검증 라벨", prompt)
        self.assertIn("귀속", prompt)
        self.assertIn("target_duration_min", prompt)


if __name__ == "__main__":
    import unittest

    unittest.main()

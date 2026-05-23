"""Phase 6A 리서치 흐름 테스트 — build-research-dossier CLI + ResearchWorker.

검증 흐름
--------
1. 프로젝트를 source_completeness_review 상태까지 진행
   (create → plan-intake → submit-intake → build-source-registry).
2. `build-research-dossier demo3` 가 ResearchWorker(LLM stub)를 호출해
   `04_research/research_dossier.json` 을 생성하고 state 를
   `source_completeness_review → research_in_progress` 로 전이.
3. stub 검증 실패 / state precondition / 영속화 / 워커 프롬프트 회귀.

본 테스트는 LLM stub (`OSINT_LLM_STUB=1`) 모드로 실 CLI 호출을 우회한다.

실행:
    python -m unittest tests.test_research_flow
"""

from __future__ import annotations

import argparse
import json

from orchestrator.main import main as cli_main
from schemas.models import (
    ProjectState,
    ResearchDossier,
    SourceCollectionPartial,
    SourceEntry,
    SourceIntake,
    TaskQueueItem,
)
from tests.test_intake_flow import VALID_PLAN_JSON, _IsolatedProjectsRoot


VALID_DOSSIER_JSON = json.dumps(
    {
        "schema_version": 1,
        "project_id": "demo3",
        "topic": "테스트 주제",
        "summary": "핵심 발견과 미확인 영역 요약.",
        "seeds": [
            {
                "seed_id": "seed_1",
                "url": "https://report.example/analysis_1",
                "description": "사용자 제공 분석 리포트",
                "is_derivative": True,
                "requires_verification": True,
            }
        ],
        "claims": [
            {
                "claim_id": "claim_01",
                "statement": "공식 발표가 사건을 확인했다.",
                "status": "confirmed",
                "evidence": [
                    {
                        "source_id": "s1",
                        "seed_id": None,
                        "quote": "공식 성명 발췌",
                        "locator": None,
                        "stance": "supports",
                    }
                ],
                "cross_checked": True,
                "confidence": "high",
                "notes": "",
                "risk_flags": [],
            },
            {
                "claim_id": "claim_02",
                "statement": "시드 리포트가 추가 배후를 주장한다.",
                "status": "claim",
                "evidence": [
                    {
                        "source_id": None,
                        "seed_id": "seed_1",
                        "quote": "리포트 주장",
                        "locator": None,
                        "stance": "supports",
                    }
                ],
                "cross_checked": False,
                "confidence": "low",
                "notes": "1차 출처로 별도 검증 필요.",
                "risk_flags": [],
            },
        ],
        "open_questions": ["배후 주장의 1차 출처는?"],
    },
    ensure_ascii=False,
)


class _ResearchHarness(_IsolatedProjectsRoot):
    def _write_partial(self, partial: SourceCollectionPartial) -> None:
        pdir = self.projects_root / "demo3" / "02_sources" / "partials"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / f"{partial.task_id}.json").write_text(
            partial.model_dump_json(indent=2), encoding="utf-8"
        )

    def _advance_to_completeness_review(self, *, with_source: bool = True) -> None:
        """create → plan-intake → submit-intake → build-source-registry."""
        # 초기 링크를 하나 넣어 워커 프롬프트의 seed 노출을 검증 가능하게.
        self.assertEqual(
            cli_main([
                "new-project", "demo3",
                "--title", "테스트 주제", "--category", "geopolitics",
                "--topic-summary", "스텁 요약",
                "--link", "https://report.example/analysis_1",
            ]),
            0,
        )
        self._stub(VALID_PLAN_JSON)
        self.assertEqual(cli_main(["plan-intake", "demo3"]), 0)
        intake = SourceIntake(project_id="demo3", user_decisions=[])
        intake_file = self.root / "decisions.json"
        intake_file.write_text(intake.model_dump_json(indent=2), encoding="utf-8")
        self.assertEqual(
            cli_main(["submit-intake", "demo3", "--file", str(intake_file)]), 0
        )
        if with_source:
            self._write_partial(
                SourceCollectionPartial(
                    project_id="demo3",
                    task_id="src_collect__a",
                    input_item_id="i1",
                    collected_sources=[
                        SourceEntry(
                            source_id="s1",
                            platform="gov",
                            source_type="statement",
                            rights_status="rights_clear",
                        )
                    ],
                )
            )
        self.assertEqual(cli_main(["build-source-registry", "demo3"]), 0)
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SOURCE_COMPLETENESS_REVIEW.value,
        )


class TestBuildResearchDossierCLI(_ResearchHarness):
    def test_creates_dossier_and_advances_state(self) -> None:
        self._advance_to_completeness_review()
        self._stub(VALID_DOSSIER_JSON)
        rc = cli_main(["build-research-dossier", "demo3"])
        self.assertEqual(rc, 0)

        dossier_path = (
            self.projects_root / "demo3" / "04_research" / "research_dossier.json"
        )
        self.assertTrue(dossier_path.exists())
        dossier = ResearchDossier.model_validate_json(
            dossier_path.read_text(encoding="utf-8")
        )
        self.assertEqual(dossier.project_id, "demo3")
        self.assertEqual(len(dossier.claims), 2)
        # source_id 인용 + 파생 시드 인용 모두 보존.
        self.assertEqual(dossier.claims[0].evidence[0].source_id, "s1")
        self.assertEqual(dossier.claims[1].evidence[0].seed_id, "seed_1")
        # 미검증/주장 라벨 파생 동작.
        self.assertEqual(dossier.claims[1].display_label, "<주장>")

        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.RESEARCH_IN_PROGRESS.value,
        )

    def test_fails_when_llm_validation_fails(self) -> None:
        self._advance_to_completeness_review()
        # required field 누락 (project_id 없음) → ResearchDossier 검증 실패.
        self._stub(json.dumps({"schema_version": 1}))
        rc = cli_main(["build-research-dossier", "demo3"])
        self.assertEqual(rc, 1)
        # state 는 source_completeness_review 로 멈춤 (research_in_progress 까지 못 감).
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SOURCE_COMPLETENESS_REVIEW.value,
        )

    def test_rejected_outside_completeness_review(self) -> None:
        # created 상태에서 바로 호출 → exit 2 (precondition 위반).
        self._create_demo3()
        rc = cli_main(["build-research-dossier", "demo3"])
        self.assertEqual(rc, 2)

    def test_invalid_project_id_rejected(self) -> None:
        rc = cli_main(["build-research-dossier", "../etc"])
        self.assertEqual(rc, 1)

    def test_idempotent_skip_when_valid_dossier_exists(self) -> None:
        """유효한 research_dossier.json 이 이미 있고 force 미지정이면 worker 미호출."""
        import os

        from orchestrator.research_io import persist_research_dossier
        from orchestrator.research_service import run_research_worker

        self._advance_to_completeness_review()
        # 이전 실행 산출물 시뮬레이션 — 유효한 dossier 를 미리 디스크에 둔다.
        persist_research_dossier(
            "demo3", ResearchDossier.model_validate_json(VALID_DOSSIER_JSON)
        )
        # LLM stub 을 일부러 unset — worker 가 호출되면 실패해야 idempotency 가 의미.
        os.environ.pop("OSINT_LLM_STUB", None)
        os.environ.pop("OSINT_LLM_STUB_RESPONSE", None)

        # 이전 단계(plan-intake)의 llm_calls 가 이미 있으므로 before/after 스냅샷으로
        # research worker 의 추가 호출 여부만 본다.
        llm_dir = self.projects_root / "demo3" / "llm_calls"
        before = set(p.name for p in llm_dir.iterdir()) if llm_dir.exists() else set()

        _manifest, _outputs, skipped = run_research_worker("demo3", force=False)
        self.assertTrue(skipped)
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.RESEARCH_IN_PROGRESS.value,
        )
        # worker 가 안 돌았으면 llm_calls/ 에 새 record 가 생기지 않음.
        after = set(p.name for p in llm_dir.iterdir()) if llm_dir.exists() else set()
        self.assertEqual(
            before, after, "worker 가 재실행되어 llm_calls 가 누적됨 (idempotency 실패)"
        )


class TestResearchWorkerPrompt(_ResearchHarness):
    """ResearchWorker.build_user_prompt 회귀 — source_id / seed / 파생 검증 문구."""

    def test_prompt_surfaces_sources_seeds_and_verification_note(self) -> None:
        self._advance_to_completeness_review()
        from workers.research_worker import ResearchWorker

        worker = ResearchWorker()
        args = argparse.Namespace(
            project_id="demo3", task_id="t", projects_root="projects"
        )
        task = TaskQueueItem(
            task_id="t", task_type="research",
            assigned_worker="research", description="d",
        )
        prompt = worker.build_user_prompt(args, task)
        # registry 의 source_id 가 인용 가능하게 노출.
        self.assertIn("source_id=s1", prompt)
        # initial_links 가 리서치 시드로 노출.
        self.assertIn("https://report.example/analysis_1", prompt)
        self.assertIn("seed_id=seed_1", prompt)
        # 사용자 제공 리포트의 별도 검증 필요 명시 (C4 / docs/13 노트).
        self.assertIn("별도 검증", prompt)
        self.assertIn("2차/파생", prompt)


if __name__ == "__main__":
    import unittest

    unittest.main()

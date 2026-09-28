"""리서치 흐름 — build-research CLI + ResearchWorker(claims.json → facts.json) (v3.2.0, 17 §5.1, back_and_forth D-0051 작업 7).

프로젝트를 source_verify 까지 올리고 sources.json·claims.json 을 직접 둔 뒤(소스 인테이크·검증 워커는 따로 테스트),
build-research 가 ResearchWorker(LLM stub)로 facts.json 을 만들고 source_verify → research 로 전이하는지 본다.
실행: python -m unittest tests.test_research_flow
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime

from orchestrator.main import main as cli_main
from orchestrator import source_intake as si
from schemas.models import ProjectState, TaskQueueItem
from schemas.source_models import ClaimsFile
from script.schema import Facts
from tests.test_intake_flow import VALID_PLAN_JSON, _IsolatedProjectsRoot

CLAIMS = {"schema_version": 1, "claims": [
    {"claim_id": "clm_0001", "text": "공식 발표가 사건을 확인했다.", "source_ids": ["src_x_0001", "src_art_0001"], "status": "verified",
     "checks": ["official:src_x_0001"]},
    {"claim_id": "clm_0002", "text": "배후가 따로 있다는 주장이 나왔다.", "source_ids": ["src_art_0001"], "status": "unverified"},
]}
VALID_FACTS_JSON = json.dumps({"schema_version": 1, "facts": [
    {"id": "f_confirm", "text": "공식 기관이 9월 18일 사건을 확인했다.", "date": "2026.09.18", "source_ids": ["clm_0001"], "confidence": "high"},
    {"id": "f_claim", "text": "한 매체는 배후가 따로 있다고 주장했다.", "date": "2026.09.18", "source_ids": ["clm_0002"], "confidence": "low"},
]}, ensure_ascii=False)


class _ResearchHarness(_IsolatedProjectsRoot):
    def _advance_to_source_verify(self, *, with_claims: bool = True) -> None:
        """create → plan-intake → 소스 2건(확인) → source_verify → claims.json."""
        self.assertEqual(cli_main(["new-project", "demo3", "--title", "테스트 주제", "--category", "geopolitics",
                                   "--topic-summary", "스텁 요약"]), 0)
        self._stub(VALID_PLAN_JSON)
        self.assertEqual(cli_main(["plan-intake", "demo3"]), 0)
        pdir = self.projects_root / "demo3"
        x = si.add_x_text(pdir, account_name="Gov", handle="@gov_test", text="We confirm the incident.", lang="en",
                          posted_at=datetime(2026, 9, 18, 9, 0))
        a = si.add_article(pdir, publisher="테스트일보", headline="사건 확인", published_at=date(2026, 9, 18), body="사건이 확인됐다.")
        for s in (x, a):
            si.confirm(pdir, s.id, "tester")
        self.assertEqual(cli_main(["transition", "demo3", "--to", "source_verify"]), 0)
        if with_claims:
            (pdir / "intake" / "claims.json").write_text(json.dumps(CLAIMS, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self._load_manifest("demo3").current_state, ProjectState.SOURCE_VERIFY.value)


class TestBuildResearchCLI(_ResearchHarness):
    def test_creates_facts_and_advances_state(self) -> None:
        self._advance_to_source_verify()
        self._stub(VALID_FACTS_JSON)
        self.assertEqual(cli_main(["build-research", "demo3"]), 0)
        facts = Facts.model_validate_json((self.projects_root / "demo3" / "facts.json").read_text(encoding="utf-8"))
        self.assertEqual([f.source_ids for f in facts.facts], [["clm_0001"], ["clm_0002"]])
        self.assertEqual(self._load_manifest("demo3").current_state, ProjectState.RESEARCH.value)

    def test_fact_outside_claims_rejected(self) -> None:
        self._advance_to_source_verify()
        bad = json.loads(VALID_FACTS_JSON)
        bad["facts"][0]["source_ids"] = ["clm_0099"]
        self._stub(json.dumps(bad, ensure_ascii=False))
        self.assertEqual(cli_main(["build-research", "demo3"]), 1)
        self.assertFalse((self.projects_root / "demo3" / "facts.json").exists())
        self.assertEqual(self._load_manifest("demo3").current_state, ProjectState.SOURCE_VERIFY.value)

    def test_contested_claim_needs_contested_fact(self) -> None:
        from workers.research_worker import check_facts  # noqa: PLC0415

        c = ClaimsFile.model_validate({"claims": [{"claim_id": "clm_0001", "text": "t", "source_ids": ["src_x_0001"],
                                                   "status": "unverified", "contested": True}]})
        f = Facts.model_validate({"facts": [{"id": "f", "text": "t", "source_ids": ["clm_0001"], "confidence": "low"}]})
        self.assertTrue(check_facts(f, c))

    def test_requires_claims(self) -> None:
        self._advance_to_source_verify(with_claims=False)
        self.assertEqual(cli_main(["build-research", "demo3"]), 2)

    def test_rejected_outside_source_verify(self) -> None:
        self._create_demo3()
        self.assertEqual(cli_main(["build-research", "demo3"]), 2)

    def test_invalid_project_id_and_legacy_command(self) -> None:
        from orchestrator.errors import LegacyRemovedError  # noqa: PLC0415

        self.assertEqual(cli_main(["build-research", "../etc"]), 1)
        with self.assertRaises(LegacyRemovedError):
            cli_main(["build-research-dossier", "demo3"])
        self.assertEqual(cli_main(["import-bundle", "demo3", "--file", "x.json"]), 1)   # v3.5.0 복귀 — 없는 파일·프로젝트 = 명시 오류

    def test_idempotent_skip_when_valid_facts_exist(self) -> None:
        import os  # noqa: PLC0415

        from orchestrator.research_service import run_research_worker  # noqa: PLC0415

        self._advance_to_source_verify()
        (self.projects_root / "demo3" / "facts.json").write_text(VALID_FACTS_JSON, encoding="utf-8")
        os.environ.pop("OSINT_LLM_STUB", None)
        os.environ.pop("OSINT_LLM_STUB_RESPONSE", None)
        _m, _o, skipped = run_research_worker("demo3", force=False)
        self.assertTrue(skipped)
        self.assertEqual(self._load_manifest("demo3").current_state, ProjectState.RESEARCH.value)


class TestResearchWorkerPrompt(_ResearchHarness):
    def test_prompt_surfaces_claims_status_and_sources(self) -> None:
        self._advance_to_source_verify()
        from workers.research_worker import ResearchWorker  # noqa: PLC0415

        args = argparse.Namespace(project_id="demo3", task_id="t", projects_root="projects")
        task = TaskQueueItem(task_id="t", task_type="research", assigned_worker="research", description="d")
        prompt = ResearchWorker().build_user_prompt(args, task)
        self.assertIn("claim_id=clm_0001 | status=verified", prompt)
        self.assertIn("claim_id=clm_0002 | status=unverified", prompt)
        self.assertIn("src_x_0001 | X 게시물", prompt)
        self.assertIn("src_art_0001 | 기사 | 테스트일보", prompt)


if __name__ == "__main__":
    import unittest

    unittest.main()

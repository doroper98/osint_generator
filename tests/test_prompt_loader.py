"""workers/prompt_loader + 워커 프롬프트 파일 분리 (v2.0.0, docs/handoff/19 §5.5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rules import load_rules, rules_hash
from workers import prompt_loader
from workers.dummy_llm_worker import DummyLLMWorker
from workers.intake_planner_worker import CATEGORY_GUIDANCE
from workers.prompt_loader import PromptTemplateError, load_prompt, prompt_sha1
from workers.script_worker import ScriptWorker


class PromptLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = load_rules()
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self._patch = mock.patch.object(prompt_loader, "PROMPTS_DIR", self.dir)
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmp.cleanup()

    def test_header_stripped_and_rules_substituted(self) -> None:
        (self.dir / "x.md").write_text(
            "<!--\ntier: 2\n-->\n원칙:\n{{RULES.balance_principles}}\n{project_id}", encoding="utf-8"
        )
        out = load_prompt("x", self.rules)
        self.assertTrue(out.startswith("원칙:\n- 모든 수치에 출처"))
        self.assertTrue(out.endswith("{project_id}"))  # 워커 자리표시는 워커가 치환
        self.assertNotIn("tier:", out)

    def test_unknown_placeholder_fails_loud(self) -> None:
        (self.dir / "y.md").write_text("{{RULES.no_such_key}}", encoding="utf-8")
        with self.assertRaises(PromptTemplateError):
            load_prompt("y", self.rules)

    def test_missing_file_fails_loud(self) -> None:
        with self.assertRaises(PromptTemplateError):
            load_prompt("absent", self.rules)


class WorkerPromptFilesTest(unittest.TestCase):
    def test_script_prompt_has_no_fixed_length(self) -> None:
        # G4-13: 고정 길이(4~6분) 제한 문단 삭제 (docs/handoff/19 §5.5)
        text = ScriptWorker().system_prompt()
        self.assertNotIn("4~6분", text)
        self.assertIn("FullScript JSON 스키마", text)

    def test_category_guidance_from_yaml(self) -> None:
        self.assertIn("geopolitics", CATEGORY_GUIDANCE)
        self.assertTrue(CATEGORY_GUIDANCE["economy"].startswith("경제/금융/산업"))

    def test_worker_provenance(self) -> None:
        w = DummyLLMWorker()
        prov = w.worker_provenance()
        assert prov is not None
        self.assertEqual(prov.prompt_name, "dummy")
        self.assertEqual(prov.prompt_sha1, prompt_sha1(w.system_prompt()))
        self.assertEqual(prov.rules_hash, rules_hash())


if __name__ == "__main__":
    unittest.main()

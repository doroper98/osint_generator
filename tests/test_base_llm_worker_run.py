"""BaseLLMWorker.run() 통합 테스트 — parsed_status 도달성 + 영속화 (v0.2.5 M3).

stub mode 또는 monkeypatch 로 4 parsed_status 케이스를 모두 도달시킨다:
  - ok                  : 정상 stub JSON
  - parse_failed        : stub 이 JSON 이 아닌 텍스트
  - validation_failed   : stub 이 schema 위반 JSON
  - subprocess_error    : _invoke_llm 이 LLMSubprocessError raise

각 케이스에서 prompt.txt / raw.txt / record.json 3 파일이 항상 영속화되는지 확인.

실행:
    python -m unittest tests.test_base_llm_worker_run
"""

from __future__ import annotations

import argparse
import os
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar, Type

from pydantic import Field

from schemas.models import (
    LLMCallRecord,
    TaskQueueItem,
    TaskStatus,
    VersionedModel,
)
from workers.base_llm_worker import BaseLLMWorker, LLMSubprocessError


class FixtureResponse(VersionedModel):
    """테스트용 응답 모델."""

    echo: str = ""
    items: list[str] = Field(default_factory=list)


class FixtureLLMWorker(BaseLLMWorker):
    worker_name = "fixture_llm_worker"
    task_type = "fixture_llm"
    llm_backend: ClassVar[str] = "claude"
    llm_mode: ClassVar[str] = "response"
    response_model: ClassVar[Type[VersionedModel]] = FixtureResponse

    def system_prompt(self) -> str:  # 테스트 픽스처 — 실제 워커는 prompts/*.md (v2.0.0)
        return "fixture system prompt"

    def build_user_prompt(self, args, task):
        return f"fixture prompt for {task.task_id}"

    def output_path(self, args, task):
        return self.project_dir(args) / "_fixture" / f"{task.task_id}.json"


class AgentModeWorker(FixtureLLMWorker):
    """allow_agent_mode 가드 검증용."""

    worker_name = "agent_mode_worker"
    llm_mode: ClassVar[str] = "agent"
    # allow_agent_mode 는 기본 False — gate 가 막아야 함


class _BaseRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.project_id = "fixture_project"
        self.projects_root = self.root / "projects"
        (self.projects_root / self.project_id).mkdir(parents=True)
        self.task = TaskQueueItem(
            task_id="t-001",
            task_type="fixture_llm",
            assigned_worker="fixture_llm_worker",
            description="test task",
            depends_on=[],
            output_refs=[],
        )
        self.args = argparse.Namespace(
            project_id=self.project_id,
            task_id="t-001",
            projects_root=str(self.projects_root),
        )
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

    @property
    def llm_calls_dir(self) -> Path:
        return self.projects_root / self.project_id / "llm_calls"

    def _read_record(self) -> LLMCallRecord:
        records = list(self.llm_calls_dir.glob("*.json"))
        self.assertEqual(len(records), 1, f"expected 1 record, got {records}")
        return LLMCallRecord.model_validate_json(records[0].read_text(encoding="utf-8"))

    def _assert_three_files(self) -> None:
        prompts = list(self.llm_calls_dir.glob("*.prompt.txt"))
        raws = list(self.llm_calls_dir.glob("*.raw.txt"))
        records = list(self.llm_calls_dir.glob("*.json"))
        self.assertEqual(len(prompts), 1)
        self.assertEqual(len(raws), 1)
        self.assertEqual(len(records), 1)


class TestRunOk(_BaseRunTest):
    def test_ok_persists_all_files_and_output(self) -> None:
        self._stub('{"schema_version":1,"echo":"hi","items":["a","b"]}')
        result = FixtureLLMWorker().run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self._assert_three_files()
        record = self._read_record()
        self.assertEqual(record.parsed_status, "ok")
        # stub mode 는 exit_code=0 반환
        self.assertEqual(record.exit_code, 0)
        # output 파일 존재
        outp = self.projects_root / self.project_id / "_fixture" / "t-001.json"
        self.assertTrue(outp.exists())
        parsed = FixtureResponse.model_validate_json(outp.read_text(encoding="utf-8"))
        self.assertEqual(parsed.echo, "hi")


class TestRunParseFailed(_BaseRunTest):
    def test_invalid_json_yields_parse_failed(self) -> None:
        self._stub("not a json at all")
        result = FixtureLLMWorker().run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        self._assert_three_files()
        record = self._read_record()
        self.assertEqual(record.parsed_status, "parse_failed")
        self.assertIsNotNone(record.error_message)


class TestRunValidationFailed(_BaseRunTest):
    def test_schema_mismatch_yields_validation_failed(self) -> None:
        # JSON 으로는 valid 지만 FixtureResponse 의 extra="forbid" 위배
        self._stub('{"unknown_field":42}')
        result = FixtureLLMWorker().run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        record = self._read_record()
        self.assertEqual(record.parsed_status, "validation_failed")


class TestRunSubprocessError(_BaseRunTest):
    def test_subprocess_error_preserves_partial_stdout_and_exit_code(self) -> None:
        worker = FixtureLLMWorker()

        def fake_invoke(args, full_prompt):
            raise LLMSubprocessError(
                "fake CLI failure",
                stdout="partial-stdout-bytes",
                stderr="some stderr",
                exit_code=7,
            )

        worker._invoke_llm = fake_invoke  # type: ignore[method-assign]
        result = worker.run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        self._assert_three_files()
        record = self._read_record()
        self.assertEqual(record.parsed_status, "subprocess_error")
        self.assertEqual(record.exit_code, 7)
        # H1: 부분 stdout 이 raw.txt 에 저장됐는지
        raw_path = self.llm_calls_dir / Path(record.raw_response_path).name
        self.assertEqual(raw_path.read_text(encoding="utf-8"), "partial-stdout-bytes")

    def test_subprocess_error_with_none_exit_code(self) -> None:
        worker = FixtureLLMWorker()

        def fake_invoke(args, full_prompt):
            raise LLMSubprocessError(
                "CLI not found",
                stdout="",
                stderr="",
                exit_code=None,
            )

        worker._invoke_llm = fake_invoke  # type: ignore[method-assign]
        result = worker.run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        record = self._read_record()
        self.assertEqual(record.parsed_status, "subprocess_error")
        self.assertIsNone(record.exit_code)


class TestAgentModeGate(_BaseRunTest):
    def test_agent_mode_without_opt_in_fails_early(self) -> None:
        # AgentModeWorker 는 llm_mode="agent" + allow_agent_mode=False (기본)
        # → LLM 호출 전에 즉시 FAILED. record / output 파일 모두 생기지 않음.
        self._stub('{"schema_version":1,"echo":"should not run"}')
        result = AgentModeWorker().run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        # 가드는 LLM 호출 전에 동작하므로 llm_calls/ 자체가 생성되지 않음.
        self.assertFalse(self.llm_calls_dir.exists())
        self.assertTrue(any("LLM-AP-003" in e for e in (result.errors or [])))


class TestOutputPathValidation(_BaseRunTest):
    def test_output_path_outside_project_dir_is_rejected(self) -> None:
        worker = FixtureLLMWorker()
        outside = self.root / "elsewhere" / "stolen.json"

        def bad_output_path(args, task):
            return outside

        worker.output_path = bad_output_path  # type: ignore[method-assign]
        self._stub('{"schema_version":1,"echo":"x"}')
        result = worker.run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        record = self._read_record()
        # LLM 응답은 ok 였고 output 단계에서만 실패. parsed_status 는 ok.
        self.assertEqual(record.parsed_status, "ok")
        self.assertIsNotNone(record.error_message)
        self.assertIn("outside project_dir", record.error_message or "")
        # outside 파일은 생기지 않아야 함
        self.assertFalse(outside.exists())

    def test_output_path_not_in_output_refs_is_rejected(self) -> None:
        worker = FixtureLLMWorker()
        # task.output_refs 가 명시되어 있는데 worker 가 다른 경로에 쓰려고 함
        task = self.task.model_copy(
            update={"output_refs": ["_fixture/different.json"]}
        )
        self._stub('{"schema_version":1,"echo":"y"}')
        result = worker.run(self.args, task)
        self.assertEqual(result.status, TaskStatus.FAILED)
        record = self._read_record()
        self.assertIn("output_refs", record.error_message or "")


if __name__ == "__main__":
    unittest.main()


class VisionModeWorker(FixtureLLMWorker):
    """v3.1.0 시각 검수 — vision 모드 호출 기록이 LLMCallRecord 를 통과해야 한다(hormuz_ai 실측 버그)."""

    worker_name = "vision_mode_worker"
    llm_mode: ClassVar[str] = "vision"


class TestVisionModeRecord(_BaseRunTest):
    def test_vision_record_persists(self) -> None:
        self._stub('{"schema_version":1,"echo":"v"}')
        result = VisionModeWorker().run(self.args, self.task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(self._read_record().mode, "vision")

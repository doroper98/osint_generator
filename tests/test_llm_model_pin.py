"""v0.43.5 — 구독 LLM 브리지 모델 고정 회귀 테스트.

배경: v0.43.4 까지 `claude -p` 호출에 `--model` 이 없어 사용자 머신 CLI 의 기본 모델이
쓰였고 저장소 어디에도 기록되지 않았다. 이제 모델명은 config.yaml `llm.model` 한 곳
(SSOT)에서 오고, argv 와 LLMCallRecord.model 에 남는다.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from orchestrator.config import CONFIG_PATH, LLMConfig, load_config
from schemas.models import LLMCallRecord
from tests.test_base_llm_worker_sandbox import (
    _ResponseClaudeWorker,
    _ResponseCodexWorker,
    _ScratchTestBase,
)
from workers.base_llm_worker import CLI_INVOCATION


class TestLLMModelConfig(unittest.TestCase):
    def test_repo_config_pins_opus_5_5(self) -> None:
        cfg = load_config(Path(CONFIG_PATH))
        self.assertEqual(cfg.llm.model, "claude-opus-5-5")

    def test_default_when_config_missing(self) -> None:
        self.assertEqual(LLMConfig().model, "claude-opus-5-5")

    def test_claude_templates_carry_model_placeholder(self) -> None:
        for mode in ("response", "agent"):
            template = CLI_INVOCATION[("claude", mode)]
            self.assertIn("--model", template, mode)
            self.assertEqual(template[template.index("--model") + 1], "{model}", mode)
        for mode in ("response", "agent"):
            self.assertNotIn("--model", CLI_INVOCATION[("codex", mode)])


class TestInvocationCarriesModel(_ScratchTestBase):
    def test_claude_response_argv_has_model_from_config(self) -> None:
        w = _ResponseClaudeWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "PROMPT")
        self.assertIn("--model", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "claude-opus-5-5")
        self.assertNotIn("{model}", " ".join(cmd))

    def test_instance_override_wins(self) -> None:
        w = _ResponseClaudeWorker()
        w.llm_model = "claude-sonnet-5"
        cmd = w._build_invocation_cmd(self._args("t-001"), "PROMPT")
        self.assertEqual(cmd[cmd.index("--model") + 1], "claude-sonnet-5")

    def test_codex_argv_has_no_model_flag(self) -> None:
        w = _ResponseCodexWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "PROMPT")
        self.assertNotIn("--model", cmd)


class TestCallRecordModelField(unittest.TestCase):
    def test_model_field_is_optional_and_compatible(self) -> None:
        # 기존 llm_calls/*.json (model 없음) 도 그대로 파싱돼야 한다 (C3 호환 방향).
        base = dict(
            schema_version=1,
            call_id="llm_x",
            task_id="t",
            worker="w",
            backend="claude",
            mode="response",
            system_prompt_hash="h",
            user_prompt_path="p",
            raw_response_path="r",
            parsed_status="ok",
            started_at="2026-09-27T00:00:00Z",
            completed_at="2026-09-27T00:00:01Z",
        )
        self.assertIsNone(LLMCallRecord.model_validate(base).model)
        rec = LLMCallRecord.model_validate({**base, "model": "claude-opus-5-5"})
        self.assertEqual(rec.model, "claude-opus-5-5")


if __name__ == "__main__":
    unittest.main()

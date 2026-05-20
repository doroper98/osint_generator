"""BaseLLMWorker 의 wrapper unwrap 회귀 테스트 (LLM-AP-001).

실제 subprocess 는 호출하지 않습니다. 본 파일은 wrapper 처리 로직만 검증합니다.

실행:
    python -m unittest tests.test_base_llm_worker
"""

from __future__ import annotations

import json
import unittest

from workers.base_llm_worker import (
    LLMSubprocessError,
    _extract_json_block,
    _unwrap_claude_response,
    _unwrap_codex_response,
)


class TestExtractJsonBlock(unittest.TestCase):
    """markdown code fence 제거."""

    def test_plain_json_passthrough(self) -> None:
        s = '{"a": 1}'
        self.assertEqual(_extract_json_block(s), '{"a": 1}')

    def test_json_with_surrounding_whitespace(self) -> None:
        s = '\n  {"a": 1}\n  '
        self.assertEqual(_extract_json_block(s), '{"a": 1}')

    def test_markdown_json_fence(self) -> None:
        s = '```json\n{"a": 1}\n```'
        self.assertEqual(_extract_json_block(s), '{"a": 1}')

    def test_markdown_plain_fence(self) -> None:
        s = '```\n{"a": 1}\n```'
        self.assertEqual(_extract_json_block(s), '{"a": 1}')

    def test_fence_without_closing(self) -> None:
        s = '```json\n{"a": 1}'
        self.assertEqual(_extract_json_block(s), '{"a": 1}')


class TestUnwrapClaudeResponse(unittest.TestCase):
    """`claude -p --output-format json` wrapper 처리."""

    def test_wrapper_success_with_plain_json_result(self) -> None:
        wrapper = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": '{"schema_version":1,"echo":"hi"}',
            "session_id": "abc",
            "duration_ms": 100,
            "uuid": "u1",
        }
        out = _unwrap_claude_response(json.dumps(wrapper))
        self.assertEqual(json.loads(out), {"schema_version": 1, "echo": "hi"})

    def test_wrapper_success_with_markdown_fence(self) -> None:
        inner = '```json\n{"schema_version":1,"echo":"fenced"}\n```'
        wrapper = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": inner,
            "session_id": "abc",
            "uuid": "u2",
        }
        out = _unwrap_claude_response(json.dumps(wrapper))
        self.assertEqual(json.loads(out), {"schema_version": 1, "echo": "fenced"})

    def test_wrapper_error_raises(self) -> None:
        wrapper = {
            "type": "result",
            "subtype": "error",
            "is_error": True,
            "result": "something went wrong",
            "session_id": "abc",
            "uuid": "u3",
        }
        with self.assertRaises(LLMSubprocessError):
            _unwrap_claude_response(json.dumps(wrapper))

    def test_result_not_string_raises(self) -> None:
        wrapper = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": {"already": "dict"},
            "uuid": "u4",
        }
        with self.assertRaises(LLMSubprocessError):
            _unwrap_claude_response(json.dumps(wrapper))

    def test_passthrough_when_not_wrapper(self) -> None:
        # 도메인 JSON 이 그대로 들어온 경우 (stub mode 등)
        s = '{"schema_version":1,"echo":"direct"}'
        self.assertEqual(_unwrap_claude_response(s), s)

    def test_passthrough_when_not_json(self) -> None:
        s = "not json at all"
        self.assertEqual(_unwrap_claude_response(s), s)

    def test_passthrough_when_wrapper_type_unknown(self) -> None:
        wrapper = {"type": "stream", "data": "..."}
        s = json.dumps(wrapper)
        self.assertEqual(_unwrap_claude_response(s), s)


class TestUnwrapCodexResponse(unittest.TestCase):
    """codex 는 v0.2.3 시점에 pass-through."""

    def test_passthrough(self) -> None:
        s = '{"any": "thing"}'
        self.assertEqual(_unwrap_codex_response(s), s)


if __name__ == "__main__":
    unittest.main()

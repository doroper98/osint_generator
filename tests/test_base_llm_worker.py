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

    def test_preamble_then_fenced_block(self) -> None:
        # LLM-AP-005: 모델이 서두 설명 prose 를 붙이고 ```json 펜스로 감싼 경우.
        s = '설명 문장입니다.\n\n```json\n{"a": 1}\n```\n뒤따르는 설명.'
        self.assertEqual(_extract_json_block(s), '{"a": 1}')

    def test_preamble_then_bare_object(self) -> None:
        # 펜스 없이 서두 prose + 첫 균형 {...} (문자열 내 중괄호 포함).
        s = 'preamble {"x": "값 {중괄호}", "y": 2} trailing'
        self.assertEqual(_extract_json_block(s), '{"x": "값 {중괄호}", "y": 2}')


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

    def test_wrapper_subtype_not_success_raises(self) -> None:
        # v0.2.5 M1 엄격화: type=result + subtype != success 면 pass-through 가 아니라 raise
        wrapper = {
            "type": "result",
            "subtype": "partial",
            "is_error": False,
            "result": "incomplete...",
            "uuid": "u5",
        }
        with self.assertRaises(LLMSubprocessError) as ctx:
            _unwrap_claude_response(json.dumps(wrapper))
        self.assertIn("partial", str(ctx.exception))

    def test_wrapper_subtype_missing_raises(self) -> None:
        wrapper = {
            "type": "result",
            "is_error": False,
            "result": "no subtype",
            "uuid": "u6",
        }
        with self.assertRaises(LLMSubprocessError):
            _unwrap_claude_response(json.dumps(wrapper))


class TestUnwrapCodexResponse(unittest.TestCase):
    """`codex exec --json` JSONL stream 처리 (LLM-AP-002).

    fixture 는 codex-cli 0.130.0 의 실제 캡쳐 (Windows cmd).
    """

    REAL_CAPTURE: str = (
        '{"type":"thread.started","thread_id":"019e453e-0b10-77a3-a23d-2e37de112cd5"}\n'
        '{"type":"turn.started"}\n'
        '{"type":"item.completed","item":{"id":"item_0","type":"agent_message",'
        '"text":"{\\"schema_version\\":1,\\"echo\\":\\"hello\\",\\"items\\":[\\"a\\",\\"b\\"]}"}}\n'
        '{"type":"turn.completed","usage":{"input_tokens":26904,'
        '"cached_input_tokens":6528,"output_tokens":21,"reasoning_output_tokens":0}}\n'
    )

    def test_real_capture_extracts_domain_json(self) -> None:
        out = _unwrap_codex_response(self.REAL_CAPTURE)
        parsed = json.loads(out)
        self.assertEqual(
            parsed,
            {"schema_version": 1, "echo": "hello", "items": ["a", "b"]},
        )

    def test_agent_message_with_markdown_fence(self) -> None:
        # codex 가 markdown code fence 로 감싸서 답하는 경우
        inner = "```json\\n{\\\"schema_version\\\":1,\\\"echo\\\":\\\"fenced\\\"}\\n```"
        stream = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"item.completed","item":{"id":"i","type":"agent_message","text":"'
            + inner + '"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        out = _unwrap_codex_response(stream)
        self.assertEqual(
            json.loads(out), {"schema_version": 1, "echo": "fenced"}
        )

    def test_multiple_agent_messages_uses_last(self) -> None:
        stream = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"first"}}\n'
            '{"type":"item.completed","item":{"id":"i2","type":"agent_message","text":"last"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        self.assertEqual(_unwrap_codex_response(stream), "last")

    def test_no_agent_message_raises(self) -> None:
        # codex 이벤트는 있지만 agent_message 가 하나도 없는 경우 (모델이 응답 못 함 등)
        stream = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        with self.assertRaises(LLMSubprocessError):
            _unwrap_codex_response(stream)

    def test_ignores_unknown_item_types(self) -> None:
        # tool_call, reasoning 같은 미지의 item type 은 무시되고 agent_message 만 추출
        stream = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"item.completed","item":{"id":"i1","type":"tool_call","name":"sh"}}\n'
            '{"type":"item.completed","item":{"id":"i2","type":"agent_message","text":"final"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        self.assertEqual(_unwrap_codex_response(stream), "final")

    def test_passthrough_when_not_jsonl(self) -> None:
        # 단일 JSON 또는 자연어가 그대로 들어온 경우 (stub mode, 매핑 변경 등)
        s = '{"schema_version":1,"direct":true}'
        self.assertEqual(_unwrap_codex_response(s), s)

    def test_passthrough_when_first_line_not_json(self) -> None:
        s = "plain text\nmore text"
        self.assertEqual(_unwrap_codex_response(s), s)

    def test_empty_input(self) -> None:
        self.assertEqual(_unwrap_codex_response(""), "")
        self.assertEqual(_unwrap_codex_response("   \n  "), "   \n  ")


if __name__ == "__main__":
    unittest.main()

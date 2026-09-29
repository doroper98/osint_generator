"""v4.10.0 G9 — LLM 브리지 프롬프트 stdin 전달 (LLM-AP-009 구조 조치, back_and_forth D-0116 작업 2).

프롬프트를 argv 한 칸으로 넘기면 리눅스 단일 인자 한도(MAX_ARG_STRLEN 128KB)를 넘는 입력에서
subprocess 생성이 OSError 로 실패했다. 이제 프롬프트는 stdin 으로만 간다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_base_llm_worker_sandbox import (
    _AgentCodexWorker,
    _ResponseClaudeWorker,
    _ResponseCodexWorker,
    _ScratchTestBase,
)

BIG = 140 * 1024   # 128KB(MAX_ARG_STRLEN) 초과


class _AgentClaudeWorker(_ResponseClaudeWorker):
    worker_name = "_agent_claude"
    llm_mode = "agent"
    allow_agent_mode = True


class TestPromptNotInArgv(_ScratchTestBase):
    def test_claude_and_codex_argv_have_no_prompt(self) -> None:
        for w in (_ResponseClaudeWorker(), _AgentClaudeWorker(), _ResponseCodexWorker(), _AgentCodexWorker()):
            cmd = w._build_invocation_cmd(self._args("t-001"))
            self.assertNotIn("PROMPT", " ".join(cmd), w.worker_name)
            self.assertFalse(any("{" in seg for seg in cmd), (w.worker_name, cmd))

    def test_claude_print_flag_kept_without_positional(self) -> None:
        cmd = _ResponseClaudeWorker()._build_invocation_cmd(self._args("t-001"))
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertEqual(cmd[2], "--output-format")   # -p 뒤 위치 인자 없음 → stdin 을 프롬프트로 읽는다

    def test_codex_reads_stdin_marker(self) -> None:
        self.assertEqual(_ResponseCodexWorker()._build_invocation_cmd(self._args("t-001"))[-1], "-")


class TestInvokePassesStdin(_ScratchTestBase):
    def test_subprocess_gets_prompt_as_input(self) -> None:
        w = _ResponseClaudeWorker()
        seen: dict = {}

        def fake_run(cmd, **kw):  # noqa: ANN001, ANN003, ANN202
            seen.update(kw, cmd=cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")

        with mock.patch.dict(os.environ, {"OSINT_LLM_STUB": ""}), mock.patch("subprocess.run", fake_run):
            out, code = w._invoke_llm(self._args("t-001"), "본문 {\"schema_version\": 1}")
        self.assertEqual((out, code), ("{}", 0))
        self.assertEqual(seen["input"], "본문 {\"schema_version\": 1}")
        self.assertNotIn("stdin", seen)   # input= 과 stdin=DEVNULL 은 함께 쓸 수 없다
        self.assertNotIn("본문", " ".join(seen["cmd"]))


class TestLargePromptOver128KB(_ScratchTestBase):
    """가짜 `claude` 실행 파일(stdin 길이를 JSON 으로 돌려줌)을 PATH 앞에 두고 실제 subprocess 로 부른다."""

    def setUp(self) -> None:
        super().setUp()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake = self.bin / "claude"
        fake.write_text(f"#!{sys.executable}\nimport json, sys\n"
                        "data = sys.stdin.buffer.read()\n"
                        "print(json.dumps({'stdin_bytes': len(data), 'argv_max': max(len(a) for a in sys.argv)}))\n",
                        encoding="utf-8")
        fake.chmod(0o755)

    @unittest.skipUnless(sys.platform.startswith("linux"), "MAX_ARG_STRLEN 은 리눅스 한도")
    def test_argv_would_fail_but_stdin_passes(self) -> None:
        prompt = "가" * (BIG // 3 + 1) + "x" * 10
        self.assertGreater(len(prompt.encode("utf-8")), 128 * 1024)
        with self.assertRaises(OSError):   # 대조군: 예전 방식(argv 한 칸)은 subprocess 생성에서 실패한다
            subprocess.run(["true", prompt], check=False)   # noqa: S603, S607
        env = {"PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}", "OSINT_LLM_STUB": ""}
        with mock.patch.dict(os.environ, env):
            out, code = _ResponseClaudeWorker()._invoke_llm(self._args("t-001"), prompt)
        got = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(got["stdin_bytes"], len(prompt.encode("utf-8")))
        self.assertLess(got["argv_max"], 1024)


if __name__ == "__main__":
    unittest.main()

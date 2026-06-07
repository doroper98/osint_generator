"""BaseLLMWorker 의 v0.4.1 sandbox / scratch / placeholder 가드 회귀 테스트.

codex 1차 리뷰 (v0.4.0 → v0.4.1) 가 지적한 4 갈래:
  - C1: task_id path traversal 가드
  - C2: scratch 경로상 symlink preflight
  - H1: placeholder 미해결 fail-fast
  - H2: response 모드 template 이 {scratch_dir} 가지면 raise
  - M1: clean_scratch_on_start 의 ephemeral 보장

각 가드를 단위로 회귀 잠금.

실행:
    python -m unittest tests.test_base_llm_worker_sandbox
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar, Type
from unittest import mock

from pydantic import Field

import workers.base_llm_worker as blw
from schemas.models import TaskQueueItem, VersionedModel
from workers.base_llm_worker import (
    CLI_INVOCATION,
    BaseLLMWorker,
    LLMSubprocessError,
    _assert_no_symlinks_in_path,
    _is_safe_path_segment,
)


class _NullResponse(VersionedModel):
    pass


class _ResponseClaudeWorker(BaseLLMWorker):
    worker_name = "_resp_claude"
    task_type = "_resp"
    llm_backend: ClassVar[str] = "claude"
    llm_mode: ClassVar[str] = "response"
    system_prompt: ClassVar[str] = ""
    response_model: ClassVar[Type[VersionedModel]] = _NullResponse

    def build_user_prompt(self, args, task):
        return "user prompt"

    def output_path(self, args, task):
        return self.project_dir(args) / "_out.json"


class _ResponseCodexWorker(_ResponseClaudeWorker):
    worker_name = "_resp_codex"
    llm_backend: ClassVar[str] = "codex"


class _AgentCodexWorker(_ResponseClaudeWorker):
    worker_name = "_agent_codex"
    llm_backend: ClassVar[str] = "codex"
    llm_mode: ClassVar[str] = "agent"
    allow_agent_mode: ClassVar[bool] = True


class _AgentCodexWorkerNoClean(_AgentCodexWorker):
    worker_name = "_agent_codex_noclean"
    clean_scratch_on_start: ClassVar[bool] = False


# ---------------------------------------------------------------------------
# 1. _is_safe_path_segment
# ---------------------------------------------------------------------------


class TestPathSegmentSafety(unittest.TestCase):
    def test_safe_segments_accepted(self) -> None:
        for s in ("t-001", "task_42", "abc", "0123456789", "x" * 128):
            self.assertTrue(_is_safe_path_segment(s), f"should accept: {s!r}")

    def test_rejects_path_separators(self) -> None:
        for s in ("a/b", "a\\b", "/abs", "rel/", "a/b/c"):
            self.assertFalse(_is_safe_path_segment(s), f"should reject: {s!r}")

    def test_rejects_dot_components(self) -> None:
        for s in (".", "..", ".env", ".ssh", ".hidden"):
            self.assertFalse(_is_safe_path_segment(s), f"should reject: {s!r}")

    def test_rejects_empty_or_too_long(self) -> None:
        self.assertFalse(_is_safe_path_segment(""))
        self.assertFalse(_is_safe_path_segment("x" * 129))


# ---------------------------------------------------------------------------
# 2. _scratch_dir_for_task
# ---------------------------------------------------------------------------


class _ScratchTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.project_id = "pj"
        self.projects_root = self.root / "projects"
        (self.projects_root / self.project_id).mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _args(self, task_id: str = "t-001") -> argparse.Namespace:
        return argparse.Namespace(
            project_id=self.project_id,
            task_id=task_id,
            projects_root=str(self.projects_root),
        )


class TestScratchDirHelper(_ScratchTestBase):
    def test_creates_and_is_idempotent(self) -> None:
        w = _AgentCodexWorker()
        a = self._args("t-001")
        d1 = w._scratch_dir_for_task(a)
        self.assertTrue(d1.exists() and d1.is_dir())
        self.assertEqual(d1.name, "t-001")
        self.assertEqual(d1.parent.name, "scratch")
        # 두 번째 호출도 같은 경로 (멱등)
        d2 = w._scratch_dir_for_task(a)
        self.assertEqual(d1, d2)

    def test_rejects_unsafe_task_id(self) -> None:
        w = _AgentCodexWorker()
        for tid in ("a/b", "..", ".env", "", "with\\sep"):
            with self.assertRaises(LLMSubprocessError) as ctx:
                w._scratch_dir_for_task(self._args(tid))
            self.assertIn("unsafe task_id", str(ctx.exception))

    def test_clean_scratch_default_true_removes_existing(self) -> None:
        w = _AgentCodexWorker()
        a = self._args("t-001")
        d = w._scratch_dir_for_task(a)
        leftover = d / "old.txt"
        leftover.write_text("from previous run", encoding="utf-8")
        self.assertTrue(leftover.exists())

        # 두 번째 호출 — clean_scratch_on_start=True 라서 leftover 가 사라져야 함
        d2 = w._scratch_dir_for_task(a)
        self.assertEqual(d, d2)
        self.assertFalse(leftover.exists())

    def test_clean_scratch_false_preserves_existing(self) -> None:
        w = _AgentCodexWorkerNoClean()
        a = self._args("t-001")
        d = w._scratch_dir_for_task(a)
        leftover = d / "keep.txt"
        leftover.write_text("kept across runs", encoding="utf-8")
        # 두 번째 호출 — clean_scratch_on_start=False 라서 leftover 가 남아야 함
        w._scratch_dir_for_task(a)
        self.assertTrue(leftover.exists())

    def test_symlink_in_scratch_root_raises(self) -> None:
        # scratch_root (= projects/{pid}/scratch) 위치에 symlink 가 있으면 거부.
        if sys.platform == "win32":
            self.skipTest("Windows 의 symlink 권한 이슈로 본 테스트는 POSIX 한정.")
        w = _AgentCodexWorker()
        pid_dir = self.projects_root / self.project_id
        outside = self.root / "evil"
        outside.mkdir()
        (pid_dir / "scratch").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(LLMSubprocessError) as ctx:
            w._scratch_dir_for_task(self._args("t-001"))
        self.assertIn("symlink", str(ctx.exception))


class TestAssertNoSymlinks(_ScratchTestBase):
    def test_clean_path_passes(self) -> None:
        pid_dir = self.projects_root / self.project_id
        scratch = pid_dir / "scratch" / "t-001"
        scratch.mkdir(parents=True)
        # 예외 없이 정상 종료해야 함
        _assert_no_symlinks_in_path(scratch, stop_at=pid_dir)

    def test_path_not_under_stop_raises(self) -> None:
        unrelated = self.root / "outside" / "tree"
        unrelated.mkdir(parents=True)
        with self.assertRaises(LLMSubprocessError):
            _assert_no_symlinks_in_path(
                unrelated, stop_at=self.projects_root / self.project_id
            )


# ---------------------------------------------------------------------------
# 3. _build_invocation_cmd argv shape
# ---------------------------------------------------------------------------


class TestInvocationCmdShape(_ScratchTestBase):
    def test_codex_agent_includes_sandbox_and_scratch_cd(self) -> None:
        w = _AgentCodexWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "PROMPT")
        # sandbox 플래그 인접 확인
        self.assertIn("--sandbox", cmd)
        sb_idx = cmd.index("--sandbox")
        self.assertEqual(cmd[sb_idx + 1], "workspace-write")
        # --cd 인자가 scratch dir 로 향함
        self.assertIn("--cd", cmd)
        cd_idx = cmd.index("--cd")
        cd_target = Path(cmd[cd_idx + 1])
        expected_scratch = (
            self.projects_root / self.project_id / "scratch" / "t-001"
        )
        self.assertEqual(cd_target, expected_scratch)
        self.assertTrue(cd_target.exists(), "agent argv 빌드 시 scratch dir mkdir 까지 일어나야 함")
        # full_prompt 가 마지막 인자
        self.assertEqual(cmd[-1], "PROMPT")

    def test_codex_response_excludes_sandbox_and_scratch(self) -> None:
        w = _ResponseCodexWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "PROMPT")
        self.assertNotIn("--sandbox", cmd)
        self.assertNotIn("--cd", cmd)
        # scratch dir 자체가 생성되지 않아야 함 (template-driven)
        scratch = self.projects_root / self.project_id / "scratch"
        self.assertFalse(
            scratch.exists(),
            "response 모드 build 는 scratch 디렉토리를 생성하면 안 됨"
        )

    def test_claude_response_unchanged(self) -> None:
        w = _ResponseClaudeWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "PROMPT")
        self.assertEqual(cmd[0], "claude")
        self.assertIn("-p", cmd)
        self.assertNotIn("--sandbox", cmd)


# ---------------------------------------------------------------------------
# 4. placeholder fail-fast & template/mode 정합성
# ---------------------------------------------------------------------------


class TestPlaceholderFailFast(_ScratchTestBase):
    def test_response_template_with_scratch_dir_raises(self) -> None:
        # CLI_INVOCATION 을 직접 모킹 — response 모드 template 에 {scratch_dir} 끼움.
        w = _ResponseClaudeWorker()
        key = (w.llm_backend, w.llm_mode)
        saved = CLI_INVOCATION.get(key)
        CLI_INVOCATION[key] = [
            "claude", "-p", "{prompt}", "--cd", "{scratch_dir}",
        ]
        try:
            with self.assertRaises(LLMSubprocessError) as ctx:
                w._build_invocation_cmd(self._args("t-001"), "PROMPT")
            self.assertIn("scratch_dir", str(ctx.exception))
            self.assertIn("not 'agent'", str(ctx.exception))
        finally:
            if saved is not None:
                CLI_INVOCATION[key] = saved
            else:
                CLI_INVOCATION.pop(key, None)

    def test_unresolved_placeholder_raises(self) -> None:
        # template 에 미지의 placeholder {unknown_token} 끼움 — argv 에 그대로 남으면
        # fail-fast 가드가 잡아야 함.
        w = _ResponseClaudeWorker()
        key = (w.llm_backend, w.llm_mode)
        saved = CLI_INVOCATION.get(key)
        CLI_INVOCATION[key] = ["claude", "-p", "{prompt}", "--magic", "{unknown_token}"]
        try:
            with self.assertRaises(LLMSubprocessError) as ctx:
                w._build_invocation_cmd(self._args("t-001"), "PROMPT")
            self.assertIn("unresolved placeholder", str(ctx.exception))
            self.assertIn("{unknown_token}", str(ctx.exception))
        finally:
            if saved is not None:
                CLI_INVOCATION[key] = saved
            else:
                CLI_INVOCATION.pop(key, None)

    def test_prompt_body_with_braces_is_allowed(self) -> None:
        # 사용자 prompt 본문이 JSON `{...}` 같은 토큰을 포함해도 argv 의 {prompt}
        # 자리에 통째로 들어간 seg 는 fail-fast 검사에서 제외돼 통과해야 함.
        w = _ResponseClaudeWorker()
        body = 'please output {"schema_version": 1}'
        cmd = w._build_invocation_cmd(self._args("t-001"), body)
        self.assertIn(body, cmd)


# ---------------------------------------------------------------------------
# 5. LLM-AP-006: codex response 프롬프트 stdin 경유 + Windows .cmd 셈 실행 해석
# ---------------------------------------------------------------------------


class TestStdinPromptAndLauncher(_ScratchTestBase):
    def test_codex_response_argv_excludes_prompt(self) -> None:
        # codex response 템플릿엔 {prompt} 가 없어야 한다 (프롬프트는 stdin 으로 넘김).
        w = _ResponseCodexWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "THE_PROMPT_BODY")
        self.assertNotIn("THE_PROMPT_BODY", cmd)
        self.assertEqual(cmd[:2], ["codex", "exec"])
        template = CLI_INVOCATION[("codex", "response")]
        self.assertFalse(
            any("{prompt}" in seg for seg in template),
            "codex response 는 prompt 를 stdin 으로 넘기므로 argv 에 {prompt} 가 없어야 함",
        )

    def test_claude_response_keeps_prompt_in_argv(self) -> None:
        # claude response 는 여전히 argv 경유 (-p {prompt}) — 회귀 방지.
        w = _ResponseClaudeWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "THE_PROMPT_BODY")
        self.assertIn("THE_PROMPT_BODY", cmd)

    def test_codex_agent_keeps_prompt_in_argv(self) -> None:
        # agent 모드는 prompt 를 마지막 argv 로 유지 (stdin 전환 대상 아님).
        w = _AgentCodexWorker()
        cmd = w._build_invocation_cmd(self._args("t-001"), "THE_PROMPT_BODY")
        self.assertEqual(cmd[-1], "THE_PROMPT_BODY")

    def test_resolve_launcher_wraps_windows_cmd_shim(self) -> None:
        fake = r"C:\Users\x\.npm-global\codex.cmd"
        comspec = r"C:\Windows\System32\cmd.exe"
        with mock.patch.object(blw.shutil, "which", return_value=fake), \
             mock.patch.object(blw.os, "name", "nt"), \
             mock.patch.dict(blw.os.environ, {"COMSPEC": comspec}):
            out = BaseLLMWorker._resolve_launcher(["codex", "exec", "--json"])
        self.assertEqual(out, [comspec, "/c", fake, "exec", "--json"])

    def test_resolve_launcher_posix_uses_plain_path(self) -> None:
        fake = "/usr/local/bin/codex"
        with mock.patch.object(blw.shutil, "which", return_value=fake), \
             mock.patch.object(blw.os, "name", "posix"):
            out = BaseLLMWorker._resolve_launcher(["codex", "exec"])
        self.assertEqual(out, [fake, "exec"])

    def test_resolve_launcher_windows_exe_not_wrapped(self) -> None:
        # 실제 .exe 면 cmd /c 로 감싸지 않는다.
        fake = r"C:\tools\codex.exe"
        with mock.patch.object(blw.shutil, "which", return_value=fake), \
             mock.patch.object(blw.os, "name", "nt"):
            out = BaseLLMWorker._resolve_launcher(["codex", "exec"])
        self.assertEqual(out, [fake, "exec"])

    def test_resolve_launcher_missing_returns_original(self) -> None:
        # which 가 None (미설치) → 원본 그대로 둬 FileNotFoundError 로 설치 안내 유지.
        with mock.patch.object(blw.shutil, "which", return_value=None):
            out = BaseLLMWorker._resolve_launcher(["codex", "exec"])
        self.assertEqual(out, ["codex", "exec"])


# ---------------------------------------------------------------------------
# 6. LLM-AP-007: subprocess 인코딩 UTF-8 고정 (한국어 Windows cp949 회피)
# ---------------------------------------------------------------------------


class TestInvokeEncoding(_ScratchTestBase):
    def _fake_proc(self, stdout: str = "{}"):
        return blw.subprocess.CompletedProcess(
            args=[], returncode=0, stdout=stdout, stderr=""
        )

    def test_codex_response_uses_utf8_and_stdin(self) -> None:
        w = _ResponseCodexWorker()
        captured: dict = {}

        def fake_run(cmd, **kw):
            captured["cmd"] = cmd
            captured["kw"] = kw
            return self._fake_proc()

        prompt = "한글 시스템 프롬프트 — 20% 상승 \"인용\""
        with mock.patch.object(blw.shutil, "which", return_value="/usr/local/bin/codex"), \
             mock.patch.object(blw.subprocess, "run", side_effect=fake_run), \
             mock.patch.dict(blw.os.environ, {}, clear=False):
            blw.os.environ.pop("OSINT_LLM_STUB", None)
            out, rc = w._invoke_llm(self._args("t-001"), prompt)

        self.assertEqual(captured["kw"].get("encoding"), "utf-8")
        # codex response 는 프롬프트를 stdin 으로 (argv 엔 없음)
        self.assertEqual(captured["kw"].get("input"), prompt)
        self.assertNotIn(prompt, captured["cmd"])
        self.assertEqual(out, "{}")
        self.assertEqual(rc, 0)

    def test_claude_response_utf8_without_stdin(self) -> None:
        w = _ResponseClaudeWorker()
        captured: dict = {}

        def fake_run(cmd, **kw):
            captured["kw"] = kw
            return self._fake_proc()

        with mock.patch.object(blw.shutil, "which", return_value="/usr/local/bin/claude"), \
             mock.patch.object(blw.subprocess, "run", side_effect=fake_run), \
             mock.patch.dict(blw.os.environ, {}, clear=False):
            blw.os.environ.pop("OSINT_LLM_STUB", None)
            w._invoke_llm(self._args("t-001"), "PROMPT")

        self.assertEqual(captured["kw"].get("encoding"), "utf-8")
        # claude 는 argv 경유 → stdin input 없음
        self.assertIsNone(captured["kw"].get("input"))


if __name__ == "__main__":
    unittest.main()

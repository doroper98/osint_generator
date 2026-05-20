"""LLM 호출이 필요한 Worker 의 공통 베이스.

docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md 의 정식 코드 구현입니다.

원칙
----
- LLM API 키를 사용하지 않습니다.
- 모든 LLM 호출은 사용자 머신의 구독 인증된 CLI (`claude`, `codex`) 를 subprocess 로
  호출하는 방식으로만 수행합니다.
- 모든 호출은 `projects/{pid}/llm_calls/{call_id}.{json,prompt.txt,raw.txt}` 로 영속화됩니다.

하위 클래스가 구현하는 것
------------------------
- worker_name, task_type (BaseWorker 와 동일)
- llm_backend ∈ {"claude", "codex"}
- llm_mode    ∈ {"response", "agent"}
- system_prompt: str (한국어/영어 가능. `.replace()` 만 사용. `.format()` 금지)
- response_model: VersionedModel 의 하위 클래스. raw stdout 을 검증할 Pydantic 모델
- build_user_prompt(args, task) -> str
- output_path(args, task) -> Path  (parse_response 결과를 저장할 위치)

테스트
------
- 환경변수 `OSINT_LLM_STUB=1` 이면 실 CLI 호출을 건너뛰고
  `OSINT_LLM_STUB_RESPONSE` (기본값 `{}`) 를 stdout 으로 가장합니다.
  smoke test 및 단위 검증용입니다.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import subprocess
from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Literal, Optional, Type

from pydantic import ValidationError

from schemas.models import (
    LLMCallRecord,
    QAStatus,
    TaskQueueItem,
    TaskResult,
    TaskStatus,
    VersionedModel,
)
from workers.base_worker import BaseWorker, emit, utc_now


# ---------------------------------------------------------------------------
# CLI 호출 매핑 (ADDENDUM_04 §5)
# ---------------------------------------------------------------------------
# v0.2.2 시점의 가정. 사용자 머신 CLI 갱신 시 본 dict 만 수정하면 됩니다.
# placeholder: {prompt}, {project_dir}
CLI_INVOCATION: dict[tuple[str, str], list[str]] = {
    ("claude", "response"): ["claude", "-p", "{prompt}", "--output-format", "json"],
    ("claude", "agent"): ["claude", "--print", "--add-dir", "{project_dir}", "-p", "{prompt}"],
    ("codex", "response"): ["codex", "exec", "--json", "{prompt}"],
    ("codex", "agent"): ["codex", "exec", "--cd", "{project_dir}", "{prompt}"],
}


class LLMSubprocessError(Exception):
    """CLI 호출 실패. CLI 미설치 / 비정상 종료 / timeout 등."""


# ---------------------------------------------------------------------------
# BaseLLMWorker
# ---------------------------------------------------------------------------


class BaseLLMWorker(BaseWorker):
    """LLM 호출이 필요한 Worker 의 공통 베이스."""

    # 하위 클래스가 오버라이드해야 하는 클래스 변수
    llm_backend: ClassVar[Literal["claude", "codex"]] = "claude"
    llm_mode: ClassVar[Literal["response", "agent"]] = "response"
    system_prompt: ClassVar[str] = ""
    response_model: ClassVar[Type[VersionedModel]]
    invoke_timeout_sec: ClassVar[int] = 600

    # -----------------------------------------------------------------
    # 추상 메서드
    # -----------------------------------------------------------------

    @abstractmethod
    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """task 와 입력 데이터로 user prompt 를 구성합니다."""

    @abstractmethod
    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        """parse 결과를 저장할 경로 (절대경로 또는 project_dir 기준)."""

    # -----------------------------------------------------------------
    # run 오버라이드 (BaseWorker)
    # -----------------------------------------------------------------

    def run(self, args: argparse.Namespace, task: Optional[TaskQueueItem]) -> TaskResult:
        if task is None:
            return self._build_failure_result(args, "task 가 None 입니다", started=utc_now())

        started = utc_now()
        call_id = self._make_call_id()
        emit(
            "system",
            f"llm call_id={call_id} backend={self.llm_backend} mode={self.llm_mode}",
        )

        user_prompt = self.build_user_prompt(args, task)
        full_prompt = self._compose_full_prompt(user_prompt)
        prompt_path = self._dump_prompt(args, call_id, full_prompt)
        prompt_hash = self._hash(full_prompt)

        # subprocess 호출
        raw_text = ""
        exit_code = 0
        parsed_status: Literal[
            "ok", "parse_failed", "validation_failed", "subprocess_error"
        ] = "ok"
        error_message: Optional[str] = None
        completed: Optional[datetime] = None

        try:
            raw_text, exit_code = self._invoke_llm(args, full_prompt)
        except LLMSubprocessError as e:
            parsed_status = "subprocess_error"
            error_message = str(e)
            emit("stderr", f"llm subprocess error: {e}")

        raw_path = self._dump_raw(args, call_id, raw_text)

        # 검증
        parsed: Optional[VersionedModel] = None
        if parsed_status == "ok":
            try:
                parsed = self.response_model.model_validate_json(raw_text)
            except ValidationError as e:
                parsed_status = "validation_failed"
                error_message = f"Pydantic validation: {e}"
                emit("stderr", error_message)
            except ValueError as e:
                parsed_status = "parse_failed"
                error_message = f"JSON parse: {e}"
                emit("stderr", error_message)

        completed = utc_now()

        # 출력 저장 (성공한 경우만)
        output_rel_path: Optional[str] = None
        if parsed is not None:
            outp = self.output_path(args, task)
            outp.parent.mkdir(parents=True, exist_ok=True)
            outp.write_text(parsed.model_dump_json(indent=2), encoding="utf-8")
            output_rel_path = self._as_relative(args, outp)
            emit("system", f"output written: {output_rel_path}")

        # LLMCallRecord 영속화
        record = LLMCallRecord(
            call_id=call_id,
            task_id=args.task_id,
            worker=self.worker_name,
            backend=self.llm_backend,
            mode=self.llm_mode,
            system_prompt_hash=prompt_hash,
            user_prompt_path=self._as_relative(args, prompt_path),
            raw_response_path=self._as_relative(args, raw_path),
            parsed_status=parsed_status,
            started_at=started,
            completed_at=completed,
            exit_code=exit_code,
            error_message=error_message,
        )
        record_path = self._llm_calls_dir(args) / f"{call_id}.json"
        record_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

        # TaskResult 구성
        outputs: list[str] = [self._as_relative(args, record_path)]
        if output_rel_path is not None:
            outputs.insert(0, output_rel_path)

        if parsed is not None:
            return TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.COMPLETED,
                started_at=started,
                completed_at=completed,
                outputs=outputs,
                qa_status=QAStatus.PASS,
            )

        return TaskResult(
            project_id=args.project_id,
            task_id=args.task_id,
            worker=self.worker_name,
            status=TaskStatus.FAILED,
            started_at=started,
            completed_at=completed,
            outputs=outputs,
            errors=[error_message or "unknown LLM failure"],
            qa_status=QAStatus.FAIL,
        )

    # -----------------------------------------------------------------
    # CLI subprocess
    # -----------------------------------------------------------------

    def _invoke_llm(
        self, args: argparse.Namespace, full_prompt: str
    ) -> tuple[str, int]:
        """subprocess 로 backend CLI 호출.

        반환: (stdout_text, exit_code)
        실패: LLMSubprocessError
        """
        # stub 모드 (smoke test 전용)
        if os.environ.get("OSINT_LLM_STUB") == "1":
            stub = os.environ.get("OSINT_LLM_STUB_RESPONSE", "{}")
            emit("system", "OSINT_LLM_STUB=1: skipping real CLI invocation")
            return stub, 0

        key = (self.llm_backend, self.llm_mode)
        template = CLI_INVOCATION.get(key)
        if template is None:
            raise LLMSubprocessError(
                f"unsupported backend/mode combination: {key}"
            )

        cmd = [
            seg.replace("{prompt}", full_prompt).replace(
                "{project_dir}", str(self.project_dir(args))
            )
            for seg in template
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.invoke_timeout_sec,
                check=False,
            )
        except FileNotFoundError as e:
            raise LLMSubprocessError(
                f"{self.llm_backend} CLI not found: {e}. "
                f"ADDENDUM_04 §5 의 CLI 설치 확인 필요."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise LLMSubprocessError(
                f"{self.llm_backend} CLI timeout after {self.invoke_timeout_sec}s"
            ) from e

        if proc.returncode != 0:
            raise LLMSubprocessError(
                f"{self.llm_backend} exit {proc.returncode}: "
                f"{(proc.stderr or '').strip()[:500]}"
            )

        return proc.stdout, proc.returncode

    # -----------------------------------------------------------------
    # 내부 헬퍼
    # -----------------------------------------------------------------

    def _make_call_id(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"llm_{ts}_{secrets.token_hex(2)}"

    def _llm_calls_dir(self, args: argparse.Namespace) -> Path:
        d = self.project_dir(args) / "llm_calls"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _compose_full_prompt(self, user_prompt: str) -> str:
        """system + user prompt 결합. .replace() 만 사용 (CLAUDE.md C2)."""
        if self.system_prompt:
            return f"{self.system_prompt}\n\n---\n\n{user_prompt}"
        return user_prompt

    def _dump_prompt(self, args: argparse.Namespace, call_id: str, prompt: str) -> Path:
        p = self._llm_calls_dir(args) / f"{call_id}.prompt.txt"
        p.write_text(prompt, encoding="utf-8")
        return p

    def _dump_raw(self, args: argparse.Namespace, call_id: str, raw: str) -> Path:
        p = self._llm_calls_dir(args) / f"{call_id}.raw.txt"
        p.write_text(raw, encoding="utf-8")
        return p

    def _hash(self, text: str) -> str:
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _as_relative(self, args: argparse.Namespace, path: Path) -> str:
        """project_dir 기준 상대경로. 실패 시 절대경로 반환."""
        pdir = self.project_dir(args)
        try:
            return str(path.resolve().relative_to(pdir.resolve()))
        except ValueError:
            return str(path)

    def _build_failure_result(
        self, args: argparse.Namespace, message: str, started: datetime
    ) -> TaskResult:
        return TaskResult(
            project_id=args.project_id,
            task_id=args.task_id,
            worker=self.worker_name,
            status=TaskStatus.FAILED,
            started_at=started,
            completed_at=utc_now(),
            errors=[message],
            qa_status=QAStatus.FAIL,
        )

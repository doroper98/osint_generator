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
import json
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
    # codex 옵션 설명 (codex-cli 0.130.0 기준):
    #   --json: JSONL 이벤트 스트림 (마지막 agent_message 가 도메인 응답)
    #   --skip-git-repo-check: project_dir 이 git repo 아니어도 실행 허용
    #   --color never: ANSI 코드 끼지 않게 안전장치
    ("codex", "response"): [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "--color", "never", "{prompt}",
    ],
    ("codex", "agent"): [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "--color", "never", "--cd", "{project_dir}", "{prompt}",
    ],
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

        # 검증 (LLM-AP-001: backend 별 wrapper 를 먼저 벗긴 뒤 Pydantic 검증)
        parsed: Optional[VersionedModel] = None
        if parsed_status == "ok":
            try:
                domain_json = self._unwrap_response(raw_text)
                parsed = self.response_model.model_validate_json(domain_json)
            except LLMSubprocessError as e:
                parsed_status = "subprocess_error"
                error_message = f"wrapper unwrap: {e}"
                emit("stderr", error_message)
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
    # Backend 별 wrapper unwrap (LLM-AP-001)
    # -----------------------------------------------------------------

    def _unwrap_response(self, raw: str) -> str:
        """backend 별 wrapper 를 벗기고 도메인 JSON 문자열을 반환합니다.

        - raw 가 비어 있으면 그대로 (Pydantic 단계에서 ValueError 로 처리됨).
        - 알 수 없는 backend 는 pass-through.
        - 자세한 배경은 docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md LLM-AP-001 참고.
        """
        if not raw.strip():
            return raw
        if self.llm_backend == "claude":
            return _unwrap_claude_response(raw)
        if self.llm_backend == "codex":
            return _unwrap_codex_response(raw)
        return raw

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


# ---------------------------------------------------------------------------
# 모듈 레벨 unwrap 헬퍼 (LLM-AP-001)
# ---------------------------------------------------------------------------


def _unwrap_claude_response(raw: str) -> str:
    """`claude -p ... --output-format json` 의 wrapper 를 벗긴다.

    실제 wrapper 예 (LLM-AP-001):
        {
          "type": "result", "subtype": "success", "is_error": false,
          "result": "<도메인 응답 문자열>", "session_id": "...", ...
        }

    - wrapper 가 `type=result, subtype=success` 면 `result` 문자열을 꺼내고
      그 안에 markdown code fence 가 있으면 추가로 벗긴다.
    - wrapper 가 `is_error=True` 면 LLMSubprocessError.
    - JSON 이 아니거나 wrapper 형태가 아니면 pass-through (이미 도메인 JSON 가능성).
    """
    stripped = raw.strip()
    try:
        wrapper = json.loads(stripped)
    except json.JSONDecodeError:
        return raw
    if not isinstance(wrapper, dict):
        return raw
    if wrapper.get("type") != "result":
        return raw
    if wrapper.get("is_error") is True:
        inner = wrapper.get("result", "")
        snippet = inner[:300] if isinstance(inner, str) else str(inner)[:300]
        raise LLMSubprocessError(f"claude returned error wrapper: {snippet}")
    if wrapper.get("subtype") == "success":
        inner = wrapper.get("result", "")
        if not isinstance(inner, str):
            raise LLMSubprocessError(
                f"claude wrapper.result is not a string: {type(inner).__name__}"
            )
        return _extract_json_block(inner)
    return raw


def _unwrap_codex_response(raw: str) -> str:
    """`codex exec --json` 의 JSONL stream 에서 도메인 응답을 추출한다.

    codex-cli 0.130.0 의 실제 출력 (LLM-AP-002):
        {"type":"thread.started","thread_id":"..."}
        {"type":"turn.started"}
        {"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"<도메인>"}}
        {"type":"turn.completed","usage":{...}}

    규칙:
    - 마지막 `item.completed` 이벤트 중 `item.type=="agent_message"` 의 `text` 를 본문으로 채택.
    - 본문이 markdown code fence 로 감싸여 있으면 `_extract_json_block` 으로 한 번 더 벗긴다.
    - JSONL 형식이 아니면 (단일 JSON 또는 자연어) pass-through — 매핑 변경/stub 응답 보호.
    - codex 이벤트는 보이지만 `agent_message` 가 하나도 없으면 `LLMSubprocessError`.
    """
    stripped = raw.strip()
    if not stripped:
        return raw
    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if not lines:
        return raw

    last_agent_text: Optional[str] = None
    saw_codex_event = False
    for ln in lines:
        try:
            evt = json.loads(ln)
        except json.JSONDecodeError:
            # JSONL 이 아닌 라인이 섞이면 codex 응답으로 간주하지 않는다.
            return raw
        if not isinstance(evt, dict):
            return raw
        etype = evt.get("type")
        if isinstance(etype, str) and (
            etype.startswith("thread.")
            or etype.startswith("turn.")
            or etype == "item.completed"
        ):
            saw_codex_event = True
        if etype == "item.completed":
            item = evt.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    last_agent_text = text
        # 미지의 이벤트 타입은 호환성 차원에서 무시 (codex 가 새 이벤트 추가해도 깨지지 않음)

    if not saw_codex_event:
        return raw
    if last_agent_text is None:
        raise LLMSubprocessError(
            "codex JSONL stream had no agent_message item.completed event"
        )
    return _extract_json_block(last_agent_text)


def _extract_json_block(text: str) -> str:
    """markdown code fence 가 있으면 내부 본문만 반환, 없으면 strip 만."""
    s = text.strip()
    if not s.startswith("```"):
        return s
    nl = s.find("\n")
    if nl == -1:
        return s
    body = s[nl + 1:]
    end = body.rfind("```")
    if end != -1:
        body = body[:end]
    return body.strip()

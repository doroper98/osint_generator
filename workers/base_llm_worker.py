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
# 사용자 머신 CLI 갱신 시 본 dict 만 수정하면 됩니다.
# placeholder: {prompt}, {project_dir}, {scratch_dir}
#
# v0.4.0 변경 — LLM-AP-003 본격 mitigation:
#   - codex agent: `--sandbox workspace-write` 추가. codex 가 `--cd` 디렉토리 안에서만
#     write 하도록 강제 (자세한 옵션 의미는 `codex exec --help` 참고).
#   - codex agent 의 `--cd` 를 `{scratch_dir}` 로 변경. agent worker 는 자기 task 의
#     `projects/{pid}/scratch/{task_id}/` 안에서만 동작. project_dir 의 다른 산출물을
#     덮어쓸 수 없다. 필요한 prompt-time 자료는 build_user_prompt 에서 텍스트로
#     내장 (외부 자료는 `<untrusted_source>` envelope 으로 격리).
CLI_INVOCATION: dict[tuple[str, str], list[str]] = {
    ("claude", "response"): ["claude", "-p", "{prompt}", "--output-format", "json"],
    ("claude", "agent"): ["claude", "--print", "--add-dir", "{project_dir}", "-p", "{prompt}"],
    # codex 옵션 설명 (codex-cli 0.130.0 기준):
    #   --json: JSONL 이벤트 스트림 (마지막 agent_message 가 도메인 응답)
    #   --skip-git-repo-check: project_dir 이 git repo 아니어도 실행 허용
    #   --color never: ANSI 코드 끼지 않게 안전장치
    #   --sandbox workspace-write: --cd 디렉토리 안에서만 write 허용 (agent 모드 전용)
    ("codex", "response"): [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "--color", "never", "{prompt}",
    ],
    ("codex", "agent"): [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "--color", "never",
        "--sandbox", "workspace-write",
        "--cd", "{scratch_dir}",
        "{prompt}",
    ],
}


class LLMSubprocessError(Exception):
    """CLI 호출 실패. CLI 미설치 / 비정상 종료 / timeout 등.

    부가 정보:
    - stdout: 비0 종료/timeout 으로 인한 부분 출력 (있다면). raw.txt 영속화용.
    - stderr: stderr 부분 출력.
    - exit_code: 실제 종료코드. None = 미실행 (FileNotFoundError 등) 또는 timeout.
    """

    def __init__(
        self,
        message: str,
        *,
        stdout: str = "",
        stderr: str = "",
        exit_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


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

    # LLM-AP-003: agent 모드는 prompt injection 면적이 넓어 명시적 opt-in 강제.
    # 하위 클래스가 `llm_mode = "agent"` 를 쓰려면 동시에 `allow_agent_mode = True` 도 명시해야 함.
    allow_agent_mode: ClassVar[bool] = False

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

        # LLM-AP-003: agent 모드는 opt-in 강제.
        if self.llm_mode == "agent" and not self.allow_agent_mode:
            return self._build_failure_result(
                args,
                f"agent mode requires allow_agent_mode=True opt-in (LLM-AP-003). "
                f"worker={self.worker_name}",
                started=started,
            )

        user_prompt = self.build_user_prompt(args, task)
        full_prompt = self._compose_full_prompt(user_prompt)
        prompt_path = self._dump_prompt(args, call_id, full_prompt)
        prompt_hash = self._hash(full_prompt)

        raw_text = ""
        exit_code: Optional[int] = None
        parsed_status: Literal[
            "ok", "parse_failed", "validation_failed", "subprocess_error"
        ] = "ok"
        error_message: Optional[str] = None
        parsed: Optional[VersionedModel] = None
        output_rel_path: Optional[str] = None
        record_path = self._llm_calls_dir(args) / f"{call_id}.json"

        try:
            # subprocess 호출 (H1+H2: 부분 stdout / exit_code 복원)
            try:
                raw_text, exit_code = self._invoke_llm(args, full_prompt)
            except LLMSubprocessError as e:
                parsed_status = "subprocess_error"
                error_message = str(e)
                raw_text = e.stdout or ""
                exit_code = e.exit_code
                emit("stderr", f"llm subprocess error: {e}")

            # 검증 — H3: parse_failed 와 validation_failed 명확 분리.
            if parsed_status == "ok":
                try:
                    domain_json = self._unwrap_response(raw_text)
                except LLMSubprocessError as e:
                    parsed_status = "subprocess_error"
                    error_message = f"wrapper unwrap: {e}"
                    emit("stderr", error_message)

            parsed_obj = None
            if parsed_status == "ok":
                try:
                    parsed_obj = json.loads(domain_json)
                except json.JSONDecodeError as e:
                    parsed_status = "parse_failed"
                    error_message = f"JSON parse: {e}"
                    emit("stderr", error_message)

            if parsed_status == "ok" and parsed_obj is not None:
                try:
                    parsed = self.response_model.model_validate(parsed_obj)
                except ValidationError as e:
                    parsed_status = "validation_failed"
                    error_message = f"Pydantic validation: {e}"
                    emit("stderr", error_message)

            # H5: output 저장 (성공 + path 검증 통과 시만)
            if parsed is not None:
                try:
                    outp = self.output_path(args, task)
                    self._validate_output_path(args, task, outp)
                    outp.parent.mkdir(parents=True, exist_ok=True)
                    outp.write_text(
                        parsed.model_dump_json(indent=2), encoding="utf-8"
                    )
                    output_rel_path = self._as_relative(args, outp)
                    emit("system", f"output written: {output_rel_path}")
                except Exception as e:
                    # LLM 응답은 정상이었으나 output 단계에서 실패. parsed_status 는 ok 유지하되
                    # task 결과는 실패로. record 의 error_message 에 명시.
                    error_message = f"output write failed: {e}"
                    parsed = None
                    output_rel_path = None
                    emit("stderr", error_message)
        finally:
            # H4: 어떤 경로든 LLMCallRecord 와 raw.txt 는 항상 영속화.
            completed = utc_now()
            raw_path = self._dump_raw(args, call_id, raw_text)
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
            try:
                record_path.write_text(
                    record.model_dump_json(indent=2), encoding="utf-8"
                )
            except Exception as e:
                emit("stderr", f"record write failed: {e}")

        outputs: list[str] = [self._as_relative(args, record_path)]
        if output_rel_path is not None:
            outputs.insert(0, output_rel_path)

        if parsed is not None and parsed_status == "ok":
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

        # {scratch_dir} 는 agent 모드 templates 가 참조. agent 모드일 때만 미리 생성하고
        # response 모드에서는 placeholder 가 없으니 빈 문자열로 둬도 안전.
        scratch_value = ""
        if self.llm_mode == "agent":
            scratch_value = str(self._scratch_dir_for_task(args))

        cmd = [
            seg.replace("{prompt}", full_prompt)
               .replace("{project_dir}", str(self.project_dir(args)))
               .replace("{scratch_dir}", scratch_value)
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
                f"ADDENDUM_04 §5 의 CLI 설치 확인 필요.",
                exit_code=None,
            ) from e
        except subprocess.TimeoutExpired as e:
            # H2: partial stdout/stderr 를 보존해서 raw.txt 영속화에 사용
            partial_stdout = e.stdout if isinstance(e.stdout, str) else (
                e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
            )
            partial_stderr = e.stderr if isinstance(e.stderr, str) else (
                e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            )
            raise LLMSubprocessError(
                f"{self.llm_backend} CLI timeout after {self.invoke_timeout_sec}s",
                stdout=partial_stdout,
                stderr=partial_stderr,
                exit_code=None,
            ) from e

        if proc.returncode != 0:
            # H1: 비0 종료라도 stdout 을 LLMSubprocessError 에 실어 raw.txt 영속화
            raise LLMSubprocessError(
                f"{self.llm_backend} exit {proc.returncode}: "
                f"{(proc.stderr or '').strip()[:500]}",
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
                exit_code=proc.returncode,
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

    def _scratch_dir_for_task(self, args: argparse.Namespace) -> Path:
        """agent 모드 codex CLI 의 `--cd` 대상 디렉토리.

        `projects/{pid}/scratch/{task_id}/` 를 만들어 반환. agent 가 본 디렉토리
        밖으로 write 하지 못하도록 `--sandbox workspace-write` 와 함께 사용
        (LLM-AP-003 mitigation). 본 디렉토리 내용은 task 단위 일회용이며,
        영속 산출물은 worker 가 `output_refs` 로 따로 기록한다.
        """
        d = self.project_dir(args) / "scratch" / args.task_id
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

    def _validate_output_path(
        self, args: argparse.Namespace, task: TaskQueueItem, outp: Path
    ) -> None:
        """output_path 가 project_dir 안이고 task.output_refs 와 일치하는지 검증.

        CLAUDE.md C4 "Worker 는 자기 자신의 output_refs 만 쓴다" 의 코드 단 가드.
        - project_dir 밖이면 ValueError.
        - task.output_refs 가 비어 있지 않으면 outp 의 project_dir 상대경로가
          그중 하나와 일치해야 함 (path separator 차이 흡수).
        """
        pdir = self.project_dir(args).resolve()
        try:
            rel = outp.resolve().relative_to(pdir)
        except ValueError as e:
            raise ValueError(
                f"output_path {outp} is outside project_dir {pdir}"
            ) from e
        if task.output_refs:
            rel_str = str(rel).replace("\\", "/")
            allowed = {r.replace("\\", "/") for r in task.output_refs}
            if rel_str not in allowed:
                raise ValueError(
                    f"output_path {rel_str!r} not in task.output_refs "
                    f"{sorted(allowed)}"
                )

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

    규칙 (M1 엄격화):
    - JSON 이 아니거나 dict 가 아니면 pass-through (이미 도메인 JSON 가능성).
    - `type != "result"` 면 pass-through (stream 이벤트 등 다른 포맷).
    - `is_error == True` 면 `LLMSubprocessError`.
    - `type == "result"` 인데 `subtype != "success"` 면 `LLMSubprocessError`
      (이전 버전은 pass-through 였으나 validation_failed 로 흡수되어 원인 추적이 어려움).
    - 정상 케이스: `result` 문자열을 꺼내고 markdown code fence 가 있으면 추가로 벗긴다.
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

    subtype = wrapper.get("subtype")
    if subtype != "success":
        snippet = str(wrapper.get("result", ""))[:300]
        raise LLMSubprocessError(
            f"claude wrapper subtype={subtype!r} (expected 'success'): {snippet}"
        )

    inner = wrapper.get("result", "")
    if not isinstance(inner, str):
        raise LLMSubprocessError(
            f"claude wrapper.result is not a string: {type(inner).__name__}"
        )
    return _extract_json_block(inner)


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

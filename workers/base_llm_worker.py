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
- prompt_name: str → `prompts/{prompt_name}.md` (v2.0.0, 코드 상수 금지. `.replace()` 만 사용)
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
import re
import secrets
import shutil
import subprocess
import tempfile
from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Literal, Optional, Type

from pydantic import BaseModel, ValidationError

from schemas.models import (
    LLMCallRecord,
    QAStatus,
    TaskQueueItem,
    TaskResult,
    TaskStatus,
    VersionedModel,
    WorkerProvenance,
)
from orchestrator.config import load_config
from rules import load_rules, rules_hash
from schemas.genre_models import GenreProfile
from schemas.rules_models import VideoRules
from workers.base_worker import BaseWorker, emit, utc_now
from workers.prompt_loader import load_prompt, prompt_sha1


# ---------------------------------------------------------------------------
# CLI 호출 매핑 (ADDENDUM_04 §5)
# ---------------------------------------------------------------------------
# 사용자 머신 CLI 갱신 시 본 dict 만 수정하면 됩니다.
# placeholder: {project_dir}, {scratch_dir}, {model}, {attach_dir}. 프롬프트는 argv 가 아니라 stdin(v4.10.0 LLM-AP-009)
#
# v0.43.5 — claude 백엔드에 `--model {model}` 고정. 값은 config.yaml `llm.model` (SSOT).
#   이전에는 --model 이 없어 사용자 머신 claude CLI 기본 모델이 쓰였다(저장소 비고정).
#
# v0.4.0 변경 — LLM-AP-003 본격 mitigation:
#   - codex agent: `--sandbox workspace-write` 추가. codex 가 `--cd` 디렉토리 안에서만
#     write 하도록 강제 (자세한 옵션 의미는 `codex exec --help` 참고).
#   - codex agent 의 `--cd` 를 `{scratch_dir}` 로 변경. agent worker 는 자기 task 의
#     `projects/{pid}/scratch/{task_id}/` 안에서만 동작. project_dir 의 다른 산출물을
#     덮어쓸 수 없다. 필요한 prompt-time 자료는 build_user_prompt 에서 텍스트로
#     내장 (외부 자료는 `<untrusted_source>` envelope 으로 격리).
CLI_INVOCATION: dict[tuple[str, str], list[str]] = {
    # v4.10.0 (LLM-AP-009, back_and_forth D-0116): 프롬프트는 **stdin** 으로만 넘긴다. argv 한 칸에 넣으면
    # 리눅스 단일 인자 한도(MAX_ARG_STRLEN 128KB)를 넘는 입력에서 subprocess 생성이 OSError 로 실패했다.
    # 그래서 템플릿에 `{prompt}` 자리가 없다(있으면 _build_invocation_cmd 가 오류 — argv 경로 삭제, 15 P2).
    # `claude -p` 는 위치 인자가 없으면 stdin 을 프롬프트로 읽는다. `codex exec -` 도 같다.
    #
    # response 모드: 한 방 JSON 생성기로만 동작해야 한다. 그런데 `claude -p` 는 print
    # 모드여도 cwd 의 CLAUDE.md / .claude 훅 / 도구를 자동으로 물어 에이전트처럼 22턴씩
    # 돌며 git commit 까지 시도하는 사고가 있었다 (LLM-AP-004, v0.8.1 실제 run 에서 발견).
    #   - `--tools ""`            : 내장 도구 전체 비활성 → 파일 IO/Bash 불가, 순수 텍스트.
    #   - `--no-session-persistence`: 세션 파일을 디스크에 남기지 않음 (호출 격리).
    # 추가로 _invoke_llm 이 subprocess 를 **repo 밖 중립 cwd** 에서 실행해 CLAUDE.md
    # 자동 탐색을 차단한다 (도구만 꺼도 cwd 가 repo 면 CLAUDE.md 가 컨텍스트를 오염시킴).
    ("claude", "response"): [
        "claude", "-p", "--output-format", "json", "--model", "{model}",
        "--tools", "", "--no-session-persistence",
    ],
    # v3.1.0 vision 모드(시각 검수, 17 §4.1, D-0047 §0-3): 도구는 Read 하나만, 첨부 폴더만 읽기 허용.
    # 실측(2026-09-28): `claude -p` 가 Read 로 프리뷰 시트(jpg)를 열어 25칸·첫 라벨을 정확히 읽었다(2턴).
    ("claude", "vision"): [
        "claude", "-p", "--output-format", "json", "--model", "{model}",
        "--tools", "Read", "--allowedTools", "Read", "--add-dir", "{attach_dir}", "--no-session-persistence",
    ],
    ("claude", "agent"): [
        "claude", "--print", "--model", "{model}", "--add-dir", "{project_dir}",
    ],
    # codex 옵션 설명 (codex-cli 0.130.0 기준):
    #   --json: JSONL 이벤트 스트림 (마지막 agent_message 가 도메인 응답)
    #   --skip-git-repo-check: project_dir 이 git repo 아니어도 실행 허용
    #   --color never: ANSI 코드 끼지 않게 안전장치
    #   --sandbox workspace-write: --cd 디렉토리 안에서만 write 허용 (agent 모드 전용)
    #   마지막 `-`: 프롬프트를 stdin 에서 읽는다(v4.10.0 LLM-AP-009)
    ("codex", "response"): [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "--color", "never", "-",
    ],
    ("codex", "agent"): [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "--color", "never",
        "--sandbox", "workspace-write",
        "--cd", "{scratch_dir}",
        "-",
    ],
}


# ---------------------------------------------------------------------------
# Path safety helpers (v0.4.1 — LLM-AP-003 defense-in-depth)
# ---------------------------------------------------------------------------


def _is_safe_path_segment(s: str) -> bool:
    """`s` 가 단일 path 세그먼트로 안전한지.

    True 조건:
    - 비어 있지 않음
    - `/`, `\\` 미포함 (path separator)
    - `..` 와 `.` 자체가 아님
    - `.` 으로 시작하지 않음 (`.env`, `.ssh` 같은 hidden 자료 차단)
    - 길이 ≤ 128 (운영적 sanity)

    Path 객체로도 정합 확인 (`Path(s).name == s`) — Windows 의 `:` (드라이브)
    같은 OS-specific 케이스를 한 번 더 거른다.
    """
    if not s or len(s) > 128:
        return False
    if "/" in s or "\\" in s:
        return False
    if s in (".", ".."):
        return False
    if s.startswith("."):
        return False
    try:
        if Path(s).name != s:
            return False
    except (ValueError, OSError):
        return False
    return True


def _assert_no_symlinks_in_path(path: Path, *, stop_at: Path) -> None:
    """`path` 부터 `stop_at` 까지 위로 올라가며 symlink 가 없는지 확인.

    `stop_at` 자체는 검사 대상에서 제외 (project_dir 등 외부에서 관리되는 경계).
    중간에 symlink 가 있으면 `LLMSubprocessError`. codex `--sandbox` 경계의
    OS-level resolve 가 sandbox 밖으로 향하는 사고를 막기 위한 preflight.
    """
    path = path.absolute()
    stop = stop_at.absolute()
    current = path
    # 무한 루프 방어 (root 까지 doh 가도 stop 못 만나는 경우)
    for _ in range(64):
        if current == stop:
            return
        if current.is_symlink():
            raise LLMSubprocessError(
                f"symlink detected in scratch path: {current} → "
                f"{current.resolve()}. LLM-AP-003 sandbox boundary integrity "
                f"requires non-symlink path."
            )
        parent = current.parent
        if parent == current:
            # filesystem root 도달했는데 stop_at 못 찾음 — 경로가 stop_at 의 하위가 아님
            raise LLMSubprocessError(
                f"scratch path {path} is not under expected base {stop_at}. "
                f"refusing to proceed."
            )
        current = parent
    raise LLMSubprocessError(
        f"_assert_no_symlinks_in_path: depth > 64 from {path} to {stop_at}. "
        f"refusing to proceed."
    )


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

    # 하위 클래스가 오버라이드해야 하는 클래스 변수.
    # llm_backend 는 호출자가 인스턴스 단위로 override 할 수 있어야 하므로 (CLI/Web 의
    # --backend 선택) ClassVar 가 아닌 일반 속성으로 둔다. 값 검증은 입력 경계
    # (argparse choices / web 400) 와 CLI_INVOCATION 키 조회에서 수행.
    llm_backend: str = "claude"
    # v0.43.5: None 이면 config.yaml `llm.model` 을 쓴다. 인스턴스 단위 override 는
    # 테스트·일회성 실험용. 모듈/클래스 상수로 다른 모델명을 박지 않는다 (SSOT).
    llm_model: Optional[str] = None
    llm_mode: ClassVar[Literal["response", "agent", "vision"]] = "response"
    # v3.1.0: 계약(스키마·check_parsed) 위반 출력은 오류를 붙여 이 횟수만큼 다시 요청한 뒤 중단(16 §3). 기본 0(옛 워커 동작 유지)
    retry_on_invalid: ClassVar[int] = 0
    # v2.0.0: 프롬프트는 코드 상수가 아니라 `prompts/{prompt_name}.md` 파일에서 온다
    # (docs/handoff/15 P3, tests/anti_inertia/test_prompts_from_files). 빈 문자열이면 system
    # prompt 없음(테스트 픽스처 전용).
    prompt_name: ClassVar[str] = ""
    response_model: ClassVar[Type[BaseModel]]   # v3.0.0 — schema_version 을 가진 모델(VersionedModel 또는 script.schema:Script)
    # v2.0.0: 타임아웃 값은 config.yaml `llm.<키>` 한 곳에서 온다 (docs/handoff/15 P3).
    # 하위 클래스는 키 이름만 바꾼다 (예: ScriptWorker → "script_timeout_sec").
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "invoke_timeout_sec"

    # LLM-AP-003: agent 모드는 prompt injection 면적이 넓어 명시적 opt-in 강제.
    # 하위 클래스가 `llm_mode = "agent"` 를 쓰려면 동시에 `allow_agent_mode = True` 도 명시해야 함.
    allow_agent_mode: ClassVar[bool] = False

    # v0.4.1: scratch dir 의 task-단위 ephemeral 화 (codex 1차 리뷰 M1).
    # True 이면 _scratch_dir_for_task 진입 시 기존 디렉토리를 rmtree 후 재생성한다.
    # 같은 task_id 재실행 시 이전 잔존물이 LLM 에 노출되지 않는다.
    # 멱등 실행 worker (예: parse-on-resume) 가 잔존물을 활용해야 한다면 False 로 opt-out.
    clean_scratch_on_start: ClassVar[bool] = True

    # -----------------------------------------------------------------
    # 추상 메서드
    # -----------------------------------------------------------------

    @abstractmethod
    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """task 와 입력 데이터로 user prompt 를 구성합니다."""

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """스키마 검증 뒤 추가 계약 검사(v3.0.0). 위반은 ValueError — validation_failed 로 기록, 출력 없음(15 P6)."""

    def serialize(self, parsed: BaseModel) -> str:
        """출력 파일 직렬화(v3.0.0). 기본 JSON. 사람이 고치는 원고는 YAML(ScriptWorker)."""
        return parsed.model_dump_json(indent=2)

    def after_output(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """출력 저장 직후 파생 산출물 저장(v3.0.0, 자기 output_refs 안에서만 — C4.3)."""

    @abstractmethod
    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        """parse 결과를 저장할 경로 (절대경로 또는 project_dir 기준)."""

    # -----------------------------------------------------------------
    # run 오버라이드 (BaseWorker)
    # -----------------------------------------------------------------

    def attachments(self, args: argparse.Namespace, task: TaskQueueItem) -> list[Path]:
        """vision 모드 첨부 이미지(v3.1.0). 프롬프트에 경로로 넣고 Read 도구로 연다(17 §4.1)."""
        return []

    def run(self, args: argparse.Namespace, task: Optional[TaskQueueItem]) -> TaskResult:
        if task is None:
            return self._build_failure_result(args, "task 가 None 입니다", started=utc_now())
        self.bind_genre(args)
        feedback = ""
        for attempt in range(self.retry_on_invalid + 1):
            result, status, err = self._run_once(args, task, feedback)
            if status not in ("parse_failed", "validation_failed") or attempt == self.retry_on_invalid:
                return result
            emit("system", f"계약 위반 출력 — 재요청 {attempt + 1}/{self.retry_on_invalid} (16 §3): {str(err)[:200]}")
            feedback = (f"\n\n[직전 출력이 계약을 어겼다 — 고쳐서 같은 형식으로 다시 출력하라]\n{str(err)[:4000]}")
        return result

    def _run_once(self, args: argparse.Namespace, task: TaskQueueItem, feedback: str = "") -> tuple[TaskResult, str, Optional[str]]:
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
            ), "subprocess_error", "agent mode opt-in"

        self.__dict__["_attachments"] = self.attachments(args, task) if self.llm_mode == "vision" else []
        user_prompt = self.build_user_prompt(args, task) + feedback
        full_prompt = self._compose_full_prompt(user_prompt)
        prompt_path = self._dump_prompt(args, call_id, full_prompt)
        prompt_hash = self._hash(full_prompt)

        raw_text = ""
        exit_code: Optional[int] = None
        parsed_status: Literal[
            "ok", "parse_failed", "validation_failed", "subprocess_error"
        ] = "ok"
        error_message: Optional[str] = None
        parsed: Optional[BaseModel] = None
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
                else:
                    try:
                        self.check_parsed(args, task, parsed)   # v3.0.0 — 스키마 밖 계약(예: 원고 sources ⊂ 도시어)
                    except ValueError as e:
                        parsed = None
                        parsed_status = "validation_failed"
                        error_message = f"check_parsed: {e}"
                        emit("stderr", error_message)

            # H5: output 저장 (성공 + path 검증 통과 시만)
            if parsed is not None:
                try:
                    outp = self.output_path(args, task)
                    self._validate_output_path(args, task, outp)
                    outp.parent.mkdir(parents=True, exist_ok=True)
                    outp.write_text(self.serialize(parsed), encoding="utf-8")
                    self.after_output(args, task, parsed)
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
                model=self.resolve_model() if self.llm_backend == "claude" else None,
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
                worker_provenance=self.worker_provenance(),
            ), parsed_status, None

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
            worker_provenance=self.worker_provenance(),
        ), parsed_status, error_message

    # -----------------------------------------------------------------
    # CLI subprocess
    # -----------------------------------------------------------------

    @property
    def rules(self) -> VideoRules:
        """영상 규칙 SSOT (`rules/video_rules.yaml`). 인스턴스당 1회 로드."""
        cached = self.__dict__.get("_rules_cache")
        if cached is None:
            cached = load_rules()
            self.__dict__["_rules_cache"] = cached
        return cached

    def bind_genre(self, args: argparse.Namespace) -> None:
        """프로젝트 장르를 읽어 둔다(v4.4.0 D-0090 작업 1). 주문(order.yaml)이 없으면 기본 장르 — 프롬프트 추가 문단 0.
        주문이 있는데 장르 프로필이 없거나 형식 오류면 GenreError(조용히 기본 장르로 넘어가지 않는다, 15 P6)."""
        from genres.load import project_genre  # noqa: PLC0415

        pdir = self.project_dir(args)
        prof, declared = project_genre(pdir) if pdir.exists() else (None, False)
        self.__dict__["_genre"] = (prof, declared)

    @property
    def genre(self) -> "GenreProfile | None":
        return (self.__dict__.get("_genre") or (None, False))[0]

    def system_prompt(self) -> str:
        """`prompts/{prompt_name}.md` + 규칙 치환 결과(+ 장르 문단). prompt_name 이 비면 빈 문자열."""
        if not self.prompt_name:
            return ""
        return load_prompt(self.prompt_name, self.rules, self.genre)

    def worker_provenance(self) -> Optional[WorkerProvenance]:
        """task_result.json 에 남길 프롬프트·규칙 증명 (15 P5). 프롬프트가 없으면 None."""
        if not self.prompt_name:
            return None
        prof, declared = self.__dict__.get("_genre") or (None, False)
        layered = prof is not None and prof.genre != self.rules.genre_prompt.base_genre
        return WorkerProvenance(
            prompt_name=self.prompt_name,
            prompt_sha1=prompt_sha1(self.system_prompt()),
            rules_hash=rules_hash(),
            genre=prof.genre if layered else None,
            genre_declared=declared if layered else None,
        )

    def invoke_timeout_sec(self) -> int:
        """CLI 호출 타임아웃(초) — config.yaml `llm.{invoke_timeout_key}` (v2.0.0 SSOT)."""
        return int(getattr(load_config().llm, self.invoke_timeout_key))

    def resolve_model(self) -> str:
        """이번 호출이 쓸 모델명. 인스턴스 override → config.yaml `llm.model` (v0.43.5)."""
        if self.llm_model:
            return self.llm_model
        model = load_config().llm.model.strip()
        if not model:
            raise LLMSubprocessError("config.yaml llm.model 이 비어 있습니다 (SSOT).")
        return model

    def _build_invocation_cmd(self, args: argparse.Namespace) -> list[str]:
        """subprocess argv 만 빌드 (실 호출 없음). v0.4.1 refactor.

        분리 이유: argv shape 회귀 테스트가 subprocess 를 띄우지 않고 검증 가능하도록.
        본 메서드 안에 v0.4.1 가드들 (template-driven scratch / response 모드 충돌
        / placeholder fail-fast) 이 들어 있다. 프롬프트는 argv 에 넣지 않는다 — stdin 으로
        넘긴다(v4.10.0 LLM-AP-009). 템플릿에 `{prompt}` 가 있으면 오류다.
        """
        key = (self.llm_backend, self.llm_mode)
        template = CLI_INVOCATION.get(key)
        if template is None:
            raise LLMSubprocessError(
                f"unsupported backend/mode combination: {key}"
            )
        if any("{prompt}" in seg for seg in template):
            raise LLMSubprocessError(
                f"template for {key} puts {{prompt}} in argv. 프롬프트는 stdin 으로만 넘긴다 "
                f"(LLM-AP-009 — 단일 인자 128KB 한도). CLI_INVOCATION 에서 {{prompt}} 를 빼라."
            )

        # v0.4.1 (codex 1차 리뷰 H2): template-driven mkdir.
        # mode-driven 으로 가면 template 이 `{scratch_dir}` 를 참조하지 않아도
        # 매 호출마다 scratch 디렉토리를 만들게 되어 의도 drift. 또한 response 모드
        # 에서 누군가 실수로 `{scratch_dir}` 를 끼우면 빈 문자열로 silent corruption.
        # 두 문제 모두 "template 이 placeholder 를 가질 때만 활성, 모드와 정합 안 맞으면
        # 즉시 raise" 로 해결.
        template_uses_scratch = any("{scratch_dir}" in seg for seg in template)
        if template_uses_scratch and self.llm_mode != "agent":
            raise LLMSubprocessError(
                f"template for {key} references {{scratch_dir}} but llm_mode "
                f"is not 'agent'. scratch dir is only meaningful for agent-mode "
                f"sandbox (LLM-AP-003). fix CLI_INVOCATION or set llm_mode='agent'."
            )

        scratch_value = ""
        if template_uses_scratch:
            scratch_value = str(self._scratch_dir_for_task(args))

        model_value = ""
        if any("{model}" in seg for seg in template):
            model_value = self.resolve_model()

        attach_value = ""
        if any("{attach_dir}" in seg for seg in template):
            atts = self.__dict__.get("_attachments") or []
            if not atts:
                raise LLMSubprocessError(f"{key}: vision 모드인데 첨부 이미지가 없다 — attachments() 확인")
            attach_value = str(Path(os.path.commonpath([str(Path(a).resolve().parent) for a in atts])))

        cmd = [
            seg.replace("{project_dir}", str(self.project_dir(args)))
               .replace("{scratch_dir}", scratch_value)
               .replace("{model}", model_value)
               .replace("{attach_dir}", attach_value)
            for seg in template
        ]

        # v0.4.1 (codex 1차 리뷰 H1): 치환 후 남은 `{name}` 토큰이 있으면 즉시 실패.
        # 새 placeholder 가 도입됐는데 _build_invocation_cmd 의 치환 코드가 갱신되지
        # 않은 경우를 잡는다. 프롬프트 본문은 argv 에 없으므로(stdin) 모든 seg 를 검사한다.
        # JSON `{}` 와 충돌하지 않도록 `{` 직후 영문/숫자/언더스코어 만 잡는다.
        unresolved_pattern = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")
        for i, seg in enumerate(cmd):
            m = unresolved_pattern.search(seg)
            if m:
                raise LLMSubprocessError(
                    f"unresolved placeholder {m.group(0)} remains in argv[{i}]={seg!r} "
                    f"for {key}. _build_invocation_cmd substitution is out of sync "
                    f"with CLI_INVOCATION."
                )

        return cmd

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

        cmd = self._build_invocation_cmd(args)

        # LLM-AP-004: subprocess 를 repo 밖 중립 디렉토리에서 실행한다. `claude` 는 cwd
        # 에서 위로 올라가며 CLAUDE.md / .claude/settings (훅) 를 자동 탐색하는데, repo
        # cwd 면 그것들이 컨텍스트를 오염시켜 응답이 도메인 JSON 대신 repo 작업 지시로
        # 변질된다. codex 는 자체 `--cd`/`--skip-git-repo-check` 로 cwd 비의존이라 영향 없음.
        neutral_cwd = Path(tempfile.gettempdir()) / "osint_llm_neutral_cwd"
        neutral_cwd.mkdir(parents=True, exist_ok=True)

        timeout_sec = self.invoke_timeout_sec()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",   # v4.10.0 — stdin 프롬프트(한국어)를 로캘(cp949·POSIX)이 아니라 UTF-8 로 쓴다
                timeout=timeout_sec,
                check=False,
                cwd=str(neutral_cwd),
                input=full_prompt,   # v4.10.0 LLM-AP-009 — 프롬프트는 stdin 으로(argv 128KB 한도 없음). 쓰고 닫으니 기다림도 없다
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
                f"{self.llm_backend} CLI timeout after {timeout_sec}s",
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

        보안 (v0.4.1, codex 1차 리뷰 C1+C2):
        - args.task_id 는 단일 path 세그먼트여야 한다 (`/`, `\\`, `..`, leading `.`
          금지). 오케스트레이터 계약은 이미 단순 ID 를 보장하지만, 본 함수가
          최종 path join 의 안전 경계가 되도록 defense-in-depth.
        - `clean_scratch_on_start=True` 면 기존 scratch 를 rmtree 후 재생성 →
          이전 task_id 재실행 / 외부에서 미리 깔아둔 symlink 모두 제거.
        - 그래도 scratch dir 자체에 도달하는 경로상 (예: projects/{pid}/scratch)
          에 symlink 가 있으면 OS 레벨에서 escape 가능 → preflight 로 거부.
        """
        task_id = args.task_id
        if not _is_safe_path_segment(task_id):
            raise LLMSubprocessError(
                f"unsafe task_id={task_id!r}: must be a single path segment "
                f"(no '/', '\\\\', '..', leading '.'). LLM-AP-003 path traversal guard."
            )

        scratch_root = self.project_dir(args) / "scratch"
        d = scratch_root / task_id

        # cleanup: ephemeral 보장. rmtree 실패는 그냥 raise (호출자가 LLMSubprocessError 로 wrap).
        if self.clean_scratch_on_start and d.exists():
            shutil.rmtree(d)

        d.mkdir(parents=True, exist_ok=True)

        # preflight: scratch_root ~ d 까지의 경로상 symlink 검사.
        # codex `--sandbox workspace-write` 는 `--cd` 디렉토리 안에서만 write 를
        # 허용하지만, 경계 자체가 symlink 면 resolve 결과가 sandbox 밖으로 갈 수 있다.
        # codex 버전에 따른 차이를 최소화하기 위해 우리 쪽에서 한 번 더 확인.
        _assert_no_symlinks_in_path(d, stop_at=self.project_dir(args))

        return d

    def _compose_full_prompt(self, user_prompt: str) -> str:
        """system + user prompt 결합. .replace() 만 사용 (CLAUDE.md C2)."""
        system = self.system_prompt()
        if system:
            return f"{system}\n\n---\n\n{user_prompt}"
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
    """도메인 JSON 문자열을 추출한다 (LLM-AP-005).

    모델이 형식 지시를 어기고 (a) markdown code fence 로 감싸거나 (b) 서두 설명
    텍스트를 붙이는 경우를 견고하게 처리한다. 처리 순서:
    1. 선두 ```fence``` → 내부 본문.
    2. 이미 순수 JSON ({ 또는 [ 로 시작) → 그대로.
    3. 본문 어딘가의 첫 ```json ... ``` 블록 → 그 본문 (서두 prose 무시).
    4. 첫 균형 잡힌 {...} 객체 → 그 부분 (최후 폴백).
    그래도 못 찾으면 strip 만 반환 (Pydantic 단계에서 parse_failed 로 흡수).
    """
    s = text.strip()
    if not s:
        return s
    # 1) 선두 fence
    if s.startswith("```"):
        nl = s.find("\n")
        if nl != -1:
            body = s[nl + 1:]
            end = body.rfind("```")
            if end != -1:
                body = body[:end]
            return body.strip()
    # 2) 이미 순수 JSON
    if s[0] in "{[":
        return s
    # 3) 본문 중간의 첫 fenced 블록 (서두 prose 가 있는 경우)
    fence = re.search(r"```(?:json)?\s*\n(.*?)\n```", s, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    # 4) 첫 균형 {...} 객체 (문자열 내 중괄호/이스케이프 고려)
    start = s.find("{")
    if start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(s)):
            ch = s[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return s[start:i + 1]
    return s

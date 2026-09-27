"""SourceCollectorWorker — Phase 5 의 첫 agent 모드 LLM worker (v0.5.0).

`SourceIntake.user_decisions` 중 `mode ∈ {ai_delegate, mixed(ai_delegate_remaining=True)}`
한 항목에 대해 OSINT 1차 출처를 수집하고 `SourceCollectionPartial` 한 객체로 응답하는
agent 모드 worker. partial 들은 후속 PATCH 의 `SourceRegistryBuilder` 가 합쳐 정식
`SourceRegistry` 를 만든다.

원칙
----
- `BaseLLMWorker` 상속. `llm_backend="codex"`, `llm_mode="agent"`,
  `allow_agent_mode=True` (LLM-AP-003 opt-in).
- `response_model=SourceCollectionPartial`.
- sandbox 격리: codex agent 의 `--sandbox workspace-write` + `--cd {scratch_dir}` 가
  `BaseLLMWorker._scratch_dir_for_task` 와 `CLI_INVOCATION` 매핑에 이미 박혀 있다.
  본 worker 는 그 위에 system prompt 로 sandbox 의 verified side channels
  (`%TEMP%`, `~/.codex/memories`) 접근 금지를 명시한다.
- 외부 자료 (`user_note`, `provided_links`, `uploaded_files`, `google_drive_links`)
  는 `workers.prompt_safety.wrap_untrusted` 로 `<untrusted_source>` envelope 격리.
- output: `projects/{pid}/02_sources/partials/{task_id}.json`.

본 PATCH 범위 외
---------------
- task_queue.json 영속화 / CLI 노출 / state 전이: 후속 PATCH.
- 실 codex 프로세스를 띄우는 e2e smoke: 후속 PATCH (사용자 머신에서).
- `SourceRegistryBuilder` (partial → registry 합치기): 후속 PATCH.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import ClassVar, Optional, Type

from schemas.models import (
    IntakeMode,
    QAStatus,
    SourceCollectionPartial,
    SourceIntake,
    TaskQueueItem,
    TaskResult,
    TaskStatus,
    UserDecision,
    VersionedModel,
)
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import emit, run_worker, utc_now
from workers.prompt_loader import load_prompt
from workers.prompt_safety import wrap_untrusted


# ---------------------------------------------------------------------------
# system prompt — `.replace()` 만 (CLAUDE.md C2). 본 프롬프트 자체에 placeholder 는
# 없으나, JSON 스키마 예시의 `{...}` 가 `.format()` 으로 해석되면 KeyError/ValueError
# 가 나도록 의도 (회귀 테스트가 본 동작을 잠근다).
# ---------------------------------------------------------------------------
# system prompt: prompts/source_collector.md / user template: prompts/source_collector_user.md (v2.0.0, 15 P3)


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class SourceCollectorWorker(BaseLLMWorker):
    """codex agent 모드 자료 수집기. 단일 UserDecision → SourceCollectionPartial."""

    worker_name = "source_collector"
    task_type = "source_collection"

    llm_backend: str = "codex"
    llm_mode: ClassVar[str] = "agent"
    # LLM-AP-003: agent 모드 opt-in. BaseLLMWorker.run() 의 가드 통과 조건.
    allow_agent_mode: ClassVar[bool] = True
    prompt_name: ClassVar[str] = "source_collector"
    response_model: ClassVar[Type[VersionedModel]] = SourceCollectionPartial

    # SourceCollector 가 처리하는 mode 화이트리스트. 외부에서도 검증할 수 있게 노출.
    ACCEPTED_MODES: ClassVar[frozenset[str]] = frozenset(
        {IntakeMode.AI_DELEGATE.value, IntakeMode.MIXED.value}
    )

    # -----------------------------------------------------------------
    # BaseLLMWorker 추상 메서드
    # -----------------------------------------------------------------

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """source_intake.json 의 매칭 UserDecision 을 envelope 으로 격리해 prompt 구성.

        실 검증은 `_preflight_validate` 에 위임. 본 메서드는 prompt 텍스트 생성만 책임.
        run() override 가 LLM 호출 전 동일 검증을 먼저 돌려 raise 를 TaskResult(FAILED)
        로 변환한다.
        """
        decision, _intake = self._preflight_validate(args, task)
        # _preflight_validate 가 통과했으므로 item_id 비어 있지 않음.
        assert task.input_item_id is not None  # for type checker
        item_id = task.input_item_id
        mode_value = (
            decision.mode.value if isinstance(decision.mode, IntakeMode) else str(decision.mode)
        )

        untrusted_body = wrap_untrusted(
            self._format_user_payload(decision),
            source_label=f"UserDecision/{item_id}",
        )

        template = load_prompt("source_collector_user", self.rules)
        return (
            template
            .replace("{project_id}", args.project_id)
            .replace("{task_id}", args.task_id)
            .replace("{item_id}", item_id)
            .replace("{mode}", mode_value)
            .replace("{remaining}", str(decision.ai_delegate_remaining))
            .replace("{untrusted}", untrusted_body)
        )

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "02_sources" / "partials" / f"{args.task_id}.json"

    # -----------------------------------------------------------------
    # run override — preflight + post-parse identity invariant
    # -----------------------------------------------------------------

    def run(
        self, args: argparse.Namespace, task: Optional[TaskQueueItem]
    ) -> TaskResult:
        """BaseLLMWorker.run() 을 감싸 preflight + post-parse invariant 추가.

        - **Preflight (LLM 호출 전)**: `_preflight_validate` 가 raise 하면 LLM 호출
          비용 없이 즉시 `TaskResult(FAILED)`. 본 worker 의 build_user_prompt 도
          동일 검증을 다시 수행 — preflight 가 미리 통과시킨 입력만 prompt 단계로
          들어간다. (LLM 호출 전 catch 의 이유: codex 호출은 시간/요금 비용이 있고,
          입력 invariants 위반은 LLM 응답을 보기 전에 잡아야 디버깅 단순.)
        - **Post-parse identity invariant**: LLM 이 echo 해야 할 식별자
          (`project_id` / `task_id` / `input_item_id`) 가 task 와 일치하는지
          확인. Pydantic 은 well-typed 값을 통과시키지만 LLM 이 다른 task 의 값을
          섞어 응답하는 cross-task contamination 시나리오를 잡는다. 불일치 시
          FAILED 로 마킹 (output 파일 자체는 base 가 이미 영속화했지만 errors 와
          status 로 표시).
        """
        started = utc_now()

        # task 가 None 이면 base 가 즉시 FAILED 반환 — 그대로 위임.
        if task is None:
            return super().run(args, task)

        # preflight — LLM 호출 전 검증.
        try:
            self._preflight_validate(args, task)
        except (ValueError, FileNotFoundError) as e:
            emit("stderr", f"preflight failed: {type(e).__name__}: {e}")
            return TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.FAILED,
                started_at=started,
                completed_at=utc_now(),
                errors=[f"preflight: {type(e).__name__}: {e}"],
                qa_status=QAStatus.FAIL,
            )

        result = super().run(args, task)
        if result.status != TaskStatus.COMPLETED:
            return result

        # post-parse identity invariant — output 다시 읽어 검증.
        outp = self.output_path(args, task)
        try:
            partial = SourceCollectionPartial.model_validate_json(
                outp.read_text(encoding="utf-8")
            )
        except Exception as e:  # noqa: BLE001 — 파일/JSON/Pydantic 어떤 실패든 동일 처치
            emit("stderr", f"post-parse re-read failed: {e}")
            result.status = TaskStatus.FAILED
            result.errors.append(f"post_parse_reread: {type(e).__name__}: {e}")
            result.qa_status = QAStatus.FAIL
            return result

        identity_errors: list[str] = []
        if partial.project_id != args.project_id:
            identity_errors.append(
                f"identity_mismatch:project_id "
                f"partial={partial.project_id!r} expected={args.project_id!r}"
            )
        if partial.task_id != args.task_id:
            identity_errors.append(
                f"identity_mismatch:task_id "
                f"partial={partial.task_id!r} expected={args.task_id!r}"
            )
        if not partial.input_item_id or partial.input_item_id != task.input_item_id:
            identity_errors.append(
                f"identity_mismatch:input_item_id "
                f"partial={partial.input_item_id!r} expected={task.input_item_id!r}"
            )
        if identity_errors:
            for e_msg in identity_errors:
                emit("stderr", e_msg)
            result.status = TaskStatus.FAILED
            result.errors.extend(identity_errors)
            result.qa_status = QAStatus.FAIL

        return result

    # -----------------------------------------------------------------
    # 내부 헬퍼
    # -----------------------------------------------------------------

    def _preflight_validate(
        self, args: argparse.Namespace, task: TaskQueueItem
    ) -> tuple[UserDecision, SourceIntake]:
        """build_user_prompt + run() 양쪽이 호출하는 단일 검증 함수.

        raise:
          - ValueError: input_item_id 누락 / 매칭 결정 없음 / 중복 매칭 / 잘못된 mode /
            mixed-인데-ai_delegate_remaining=False.
          - FileNotFoundError: source_intake.json 부재.

        returns:
          (decision, intake) — caller 가 그대로 재사용. 같은 검증을 두 번 돌리지 않게.
        """
        item_id = task.input_item_id
        if not item_id:
            raise ValueError(
                "task.input_item_id 누락. SourceCollector 는 UserDecision 의 "
                "item_id 가 필요합니다 (한 task = 한 UserDecision)."
            )

        intake_path = self.project_dir(args) / "01_intake" / "source_intake.json"
        if not intake_path.exists():
            raise FileNotFoundError(
                f"source_intake.json 이 없습니다: {intake_path}"
            )
        intake = SourceIntake.model_validate_json(
            intake_path.read_text(encoding="utf-8")
        )

        decision = self._find_decision(intake, item_id)
        if decision is None:
            raise ValueError(
                f"UserDecision 매칭 실패: item_id={item_id!r} 가 source_intake.json 에 없습니다."
            )

        mode_value = (
            decision.mode.value if isinstance(decision.mode, IntakeMode) else str(decision.mode)
        )
        if mode_value not in self.ACCEPTED_MODES:
            raise ValueError(
                f"SourceCollector 는 mode ∈ {sorted(self.ACCEPTED_MODES)} 만 처리합니다. "
                f"item_id={item_id} mode={mode_value!r}"
            )

        # mixed 모드는 ai_delegate_remaining=True 인 경우에만 처리. planner 가 이미
        # 동일 필터링하지만 worker 단에서도 enforce — 수동/잘못된 task_queue 진입 차단.
        if mode_value == IntakeMode.MIXED.value and not decision.ai_delegate_remaining:
            raise ValueError(
                f"mixed 모드인데 ai_delegate_remaining=False 입니다. "
                f"item_id={item_id} — 사용자 제공 자료로 이미 완료된 항목이므로 "
                f"SourceCollector 처리 대상이 아닙니다."
            )

        return decision, intake

    @staticmethod
    def _find_decision(intake: SourceIntake, item_id: str) -> Optional[UserDecision]:
        """`item_id` 매칭 UserDecision 을 0/1/many 분기로 명시 처리.

        - 0 개: None 반환 (caller 가 ValueError 로 변환).
        - 1 개: 정상 반환.
        - 2 개 이상: ValueError. 동일 item_id 중복은 source_intake.json 의 데이터
          오류이며, 어느 것을 선택해도 의미가 모호하므로 명시적 실패.
        """
        matches = [d for d in intake.user_decisions if d.item_id == item_id]
        if not matches:
            return None
        if len(matches) > 1:
            raise ValueError(
                f"source_intake.json 에 item_id={item_id!r} 가 {len(matches)} 회 "
                f"중복 등장. UserDecision 은 item_id 당 단일이어야 합니다."
            )
        return matches[0]

    @staticmethod
    def _format_user_payload(decision: UserDecision) -> str:
        """envelope 안에 넣을 외부 자료 본문 정형화.

        링크/파일 이름은 prompt injection 표면을 줄이기 위해 한 줄씩 분리. uploaded_files
        는 실 내용 접근이 sandbox 로 차단됨을 LLM 에 명시.
        """
        parts: list[str] = []
        if decision.user_note:
            parts.append(f"user_note:\n{decision.user_note}")
        if decision.provided_links:
            parts.append("provided_links:\n" + "\n".join(decision.provided_links))
        if decision.google_drive_links:
            parts.append(
                "google_drive_links:\n" + "\n".join(decision.google_drive_links)
            )
        if decision.uploaded_files:
            parts.append(
                "uploaded_files (이름만 — 실 내용 접근은 sandbox 가 차단):\n"
                + "\n".join(decision.uploaded_files)
            )
        if not parts:
            parts.append(
                "(사용자 제공 자료 없음. 항목 자체의 의미에 기반해 자료 수집)"
            )
        return "\n\n".join(parts)


if __name__ == "__main__":
    run_worker(SourceCollectorWorker())

"""SourceIntake → TaskQueueItem 빌더 (Phase 5, v0.5.0).

`source_intake.json` 의 `UserDecision[]` 을 읽어, AI 수집이 필요한 항목에 대해
`source_collector_worker` 용 `TaskQueueItem` 을 생성합니다.

처리 대상:
- `mode == "ai_delegate"`            전적으로 AI 가 수집
- `mode == "mixed"` 이고 `ai_delegate_remaining == True`  사용자 제공 + AI 보완

제외:
- `mode ∈ {"direct_provide", "link_provide", "gdrive_provide", "file_upload",
   "skip", "must_use", "reference_only"}` — SourceCollector 의 책임 밖.
- `mixed` 이지만 `ai_delegate_remaining == False` — 사용자 자체 자료로 충분.

본 모듈은 **순수 함수만** 제공합니다. 디스크 / 네트워크 I/O 없음. `task_queue.json`
영속화는 후속 PATCH 의 CLI 또는 orchestrator 가 책임.
"""

from __future__ import annotations

from typing import Optional

from schemas.models import (
    IntakeMode,
    SourceIntake,
    TaskQueueItem,
    UserDecision,
)


SOURCE_COLLECTOR_WORKER = "source_collector"
SOURCE_COLLECTOR_TASK_TYPE = "source_collection"

# task_id prefix. `_is_safe_path_segment` (BaseLLMWorker) 통과 보장.
_TASK_ID_PREFIX = "src_collect__"


def task_id_for(item_id: str) -> str:
    """item_id 로부터 source_collector task_id 생성.

    단일 path 세그먼트로서 `BaseLLMWorker._is_safe_path_segment` 통과를 보장:
    - `/`, `\\` 미포함, `..` 아님, leading `.` 없음, 길이 ≤ 128.
    `item_id` 는 IntakePlannerWorker 의 system_prompt 가 영문 snake_case 만
    요구하지만, 빌더는 외부 입력 신뢰 없이도 호출되도록 분리 prefix 를 박는다.
    """
    return f"{_TASK_ID_PREFIX}{item_id}"


def needs_collection(decision: UserDecision) -> bool:
    """SourceCollector 가 처리해야 할 결정인가."""
    mode = decision.mode if isinstance(decision.mode, str) else decision.mode.value
    if mode == IntakeMode.AI_DELEGATE.value:
        return True
    if mode == IntakeMode.MIXED.value and decision.ai_delegate_remaining:
        return True
    return False


def build_source_collection_tasks(
    intake: SourceIntake,
    *,
    existing_task_ids: Optional[set[str]] = None,
) -> list[TaskQueueItem]:
    """SourceIntake 에서 source_collector task 만 생성.

    parameters
    ----------
    intake : SourceIntake
        제출된 SourceIntake (`01_intake/source_intake.json` 으로 영속화된 모델).
    existing_task_ids : set[str], optional
        이미 task_queue 에 들어 있는 task_id 집합. 중복 회피 (idempotency).

    returns
    -------
    list[TaskQueueItem]
        AI 수집이 필요한 항목만. 빈 리스트 반환 가능.
    """
    existing = existing_task_ids or set()
    tasks: list[TaskQueueItem] = []
    for decision in intake.user_decisions:
        if not needs_collection(decision):
            continue
        tid = task_id_for(decision.item_id)
        if tid in existing:
            continue
        tasks.append(
            TaskQueueItem(
                task_id=tid,
                input_item_id=decision.item_id,
                assigned_worker=SOURCE_COLLECTOR_WORKER,
                task_type=SOURCE_COLLECTOR_TASK_TYPE,
                description=f"AI 자료 수집: {decision.item_id}",
                output_refs=[f"02_sources/partials/{tid}.json"],
                parallelizable=True,
            )
        )
    return tasks

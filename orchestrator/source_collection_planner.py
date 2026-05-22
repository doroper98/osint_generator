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

from schemas.models import (
    IntakeMode,
    SourceIntake,
    TaskQueueItem,
    UserDecision,
)
from workers.base_llm_worker import _is_safe_path_segment


SOURCE_COLLECTOR_WORKER = "source_collector"
SOURCE_COLLECTOR_TASK_TYPE = "source_collection"

# task_id prefix. `_is_safe_path_segment` (BaseLLMWorker) 통과 보장.
_TASK_ID_PREFIX = "src_collect__"


def task_id_for(item_id: str) -> str:
    """item_id 로부터 source_collector task_id 생성.

    `BaseLLMWorker._is_safe_path_segment` 통과를 **함수 단에서 강제** (codex 1차
    리뷰 Critical 흡수, v0.5.2). 단순 prefix 조합만 하던 v0.5.0 구현은 buggy /
    malicious upstream 이 `/`, `..`, leading `.`, 매우 긴 문자열을 넘기면 task
    생성은 성공하고 worker 실행 시점 (`_scratch_dir_for_task`) 에서야 sandbox 가드
    가 raise 하는 contract drift 가 있었다. 본 함수는 planning boundary 에서 fail
    fast.

    raise:
      ValueError: 생성된 task_id 가 `_is_safe_path_segment` 를 통과하지 못할 때.
    """
    # item_id 자체에도 path-traversal 의도가 있는 토큰이 없는지 확인. prefix 가
    # 붙으면 candidate 가 `..` / `.` 자체는 아니게 되어 `_is_safe_path_segment`
    # 를 통과하지만, 의도적 traversal 시도일 가능성이 높으므로 명시적 거부.
    if "/" in item_id or "\\" in item_id:
        raise ValueError(
            f"unsafe item_id={item_id!r}: path separator (`/`, `\\\\`) 포함."
        )
    if ".." in item_id:
        raise ValueError(
            f"unsafe item_id={item_id!r}: '..' 토큰 포함 (path traversal 의도)."
        )

    candidate = f"{_TASK_ID_PREFIX}{item_id}"
    if not _is_safe_path_segment(candidate):
        raise ValueError(
            f"unsafe item_id={item_id!r}: derived task_id={candidate!r} 가 "
            f"_is_safe_path_segment 가드 (no '/', '\\\\', '..', leading '.', "
            f"length ≤ 128) 를 통과하지 못합니다. UserDecision 의 item_id 는 "
            f"영문 snake_case 만 허용해야 합니다."
        )
    return candidate


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
    existing_task_ids: set[str] | None = None,
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

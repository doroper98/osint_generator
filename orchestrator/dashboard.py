"""Job Dashboard 데이터 모델.

TUI 가 본 모듈의 dataclass 를 읽어 Job Dashboard Panel 을 그립니다.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional

from schemas.models import TaskQueue, TaskStatus


@dataclass
class DashboardSnapshot:
    project_id: str
    current_state: str
    queued: int
    running: int
    assigned: int
    completed: int
    failed: int
    needs_user_upload: int
    needs_user_confirmation: int
    rights_review_required: int
    skipped: int
    total: int
    current_gate: Optional[str] = None
    next_action: Optional[str] = None
    version: str = ""

    @classmethod
    def from_queue(
        cls,
        project_id: str,
        current_state: str,
        queue: TaskQueue,
        version: str = "",
        current_gate: Optional[str] = None,
        next_action: Optional[str] = None,
    ) -> "DashboardSnapshot":
        counter: Counter[str] = Counter(t.status for t in queue.tasks)
        # pydantic 의 use_enum_values=True 이므로 status 는 문자열입니다.
        return cls(
            project_id=project_id,
            current_state=current_state,
            queued=counter.get(TaskStatus.QUEUED.value, 0),
            running=counter.get(TaskStatus.RUNNING.value, 0),
            assigned=counter.get(TaskStatus.ASSIGNED.value, 0),
            completed=counter.get(TaskStatus.COMPLETED.value, 0),
            failed=counter.get(TaskStatus.FAILED.value, 0),
            needs_user_upload=counter.get(TaskStatus.NEEDS_USER_UPLOAD.value, 0),
            needs_user_confirmation=counter.get(TaskStatus.NEEDS_USER_CONFIRMATION.value, 0),
            rights_review_required=counter.get(TaskStatus.RIGHTS_REVIEW_REQUIRED.value, 0),
            skipped=counter.get(TaskStatus.SKIPPED.value, 0),
            total=len(queue.tasks),
            current_gate=current_gate,
            next_action=next_action,
            version=version,
        )

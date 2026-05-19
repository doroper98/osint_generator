"""Phase 1 MVP 검증용 Dummy Worker.

목적
----
- Worker Slot Manager 가 subprocess 로 띄울 수 있는가?
- stdout/stderr 가 Log Router 를 통해 Slot Panel 에 흐르는가?
- task_result.json 이 정상적으로 작성되는가?
- BaseWorker 의 종료 코드 매핑이 동작하는가?

동작
----
- task 의 input_refs[0] 에 작업 시뮬레이션 시간(초) 이 있으면 그만큼 sleep.
- 없으면 기본 5초.
- 1초마다 stdout 으로 heartbeat 한 줄.
- task.description 에 'fail' 포함 → 실패로 종료.
- task.description 에 'needs_user' 포함 → needs_user_confirmation 으로 종료.
- task.description 에 'rights' 포함 → rights_review_required 로 종료.
- 그 외 → completed.
"""

from __future__ import annotations

import argparse
import time
from typing import Optional

from workers.base_worker import BaseWorker, emit, run_worker, utc_now
from schemas.models import QAStatus, TaskQueueItem, TaskResult, TaskStatus


class DummyWorker(BaseWorker):
    worker_name = "dummy_worker"
    task_type = "dummy"

    def run(self, args: argparse.Namespace, task: Optional[TaskQueueItem]) -> TaskResult:
        assert task is not None
        emit("stdout", f"start dummy_worker for task {task.task_id}: {task.description}")

        duration_sec = 5
        if task.input_refs:
            try:
                duration_sec = max(1, int(task.input_refs[0]))
            except ValueError:
                duration_sec = 5

        for i in range(duration_sec):
            time.sleep(1)
            emit("stdout", f"tick {i + 1}/{duration_sec} task={task.task_id}")

        desc = (task.description or "").lower()
        if "fail" in desc:
            emit("stderr", "simulated failure (description contains 'fail')")
            return TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.FAILED,
                started_at=utc_now(),
                completed_at=utc_now(),
                errors=["simulated failure"],
                qa_status=QAStatus.FAIL,
            )
        if "needs_user" in desc:
            return TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.NEEDS_USER_CONFIRMATION,
                started_at=utc_now(),
                completed_at=utc_now(),
                warnings=["사용자 확인이 필요합니다 (simulated)"],
                qa_status=QAStatus.PENDING,
            )
        if "rights" in desc:
            return TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.RIGHTS_REVIEW_REQUIRED,
                started_at=utc_now(),
                completed_at=utc_now(),
                warnings=["권리 검토가 필요합니다 (simulated)"],
                qa_status=QAStatus.WARN,
                risk_flags=["graphic_content"],
            )

        emit("stdout", "done")
        return TaskResult(
            project_id=args.project_id,
            task_id=args.task_id,
            worker=self.worker_name,
            status=TaskStatus.COMPLETED,
            started_at=utc_now(),
            completed_at=utc_now(),
            outputs=[],
            qa_status=QAStatus.PASS,
        )


if __name__ == "__main__":
    run_worker(DummyWorker())

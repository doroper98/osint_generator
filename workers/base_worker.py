"""모든 Worker CLI 의 공통 베이스.

CLAUDE.md C4 의 규칙을 강제합니다.

- argparse 표준화 (--project-id / --task-id)
- task_queue.json 에서 자기 task 를 읽어옴
- 결과를 task_results/{task_id}_result.json 으로 저장
- stdout 은 1줄 1이벤트 원칙으로 emit
- 사용자에게 stdin 으로 질문하지 않는다 (PIPELINE-AP-001)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from schemas.models import (
    TaskQueue,
    TaskQueueItem,
    TaskResult,
    TaskStatus,
    QAStatus,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def emit(kind: str, message: str) -> None:
    """1줄 1이벤트 로그 출력. Log Router 가 파싱합니다."""
    line = f"[{kind}] {message}"
    print(line, flush=True)


class BaseWorker(ABC):
    """모든 Worker 의 베이스 클래스.

    하위 클래스는 worker_name, task_type, run 만 구현하면 됩니다.
    """

    worker_name: str = "base_worker"
    task_type: str = "base"

    # -----------------------------------------------------------------
    # 인자 파싱
    # -----------------------------------------------------------------

    def parse_args(self, argv: Optional[list[str]] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(prog=f"workers.{self.worker_name}")
        parser.add_argument("--project-id", required=True)
        parser.add_argument("--task-id", required=True)
        parser.add_argument("--projects-root", default="projects")
        return parser.parse_args(argv)

    # -----------------------------------------------------------------
    # 입출력 경로
    # -----------------------------------------------------------------

    def project_dir(self, args: argparse.Namespace) -> Path:
        return REPO_ROOT / args.projects_root / args.project_id

    def task_queue_path(self, args: argparse.Namespace) -> Path:
        return self.project_dir(args) / "03_tasks" / "task_queue.json"

    def result_path(self, args: argparse.Namespace) -> Path:
        return self.project_dir(args) / "03_tasks" / "task_results" / f"{args.task_id}_result.json"

    # -----------------------------------------------------------------
    # task 로드
    # -----------------------------------------------------------------

    def load_task(self, args: argparse.Namespace) -> Optional[TaskQueueItem]:
        path = self.task_queue_path(args)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        queue = TaskQueue.model_validate(raw)
        return queue.find(args.task_id)

    # -----------------------------------------------------------------
    # run (하위 클래스가 구현)
    # -----------------------------------------------------------------

    @abstractmethod
    def run(self, args: argparse.Namespace, task: Optional[TaskQueueItem]) -> TaskResult:
        ...

    # -----------------------------------------------------------------
    # 결과 기록
    # -----------------------------------------------------------------

    def write_result(self, args: argparse.Namespace, result: TaskResult) -> None:
        path = self.result_path(args)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    # -----------------------------------------------------------------
    # 진입점
    # -----------------------------------------------------------------

    def main(self, argv: Optional[list[str]] = None) -> int:
        args = self.parse_args(argv)
        emit("system", f"worker={self.worker_name} pid={os.getpid()} project={args.project_id} task={args.task_id}")
        task = self.load_task(args)
        if task is None:
            emit("stderr", "task not found in task_queue.json")
            result = TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.FAILED,
                started_at=utc_now(),
                completed_at=utc_now(),
                errors=["task not found in task_queue.json"],
                qa_status=QAStatus.FAIL,
            )
            self.write_result(args, result)
            return 1

        started = utc_now()
        try:
            result = self.run(args, task)
        except Exception as e:  # noqa: BLE001
            emit("stderr", f"unhandled exception: {e}")
            for line in traceback.format_exc().splitlines():
                emit("stderr", line)
            result = TaskResult(
                project_id=args.project_id,
                task_id=args.task_id,
                worker=self.worker_name,
                status=TaskStatus.FAILED,
                started_at=started,
                completed_at=utc_now(),
                errors=[f"{type(e).__name__}: {e}"],
                qa_status=QAStatus.FAIL,
            )

        # started_at / completed_at 보정
        if result.started_at is None:
            result.started_at = started
        if result.completed_at is None:
            result.completed_at = utc_now()

        self.write_result(args, result)
        emit("system", f"result_status={result.status if isinstance(result.status, str) else result.status.value}")

        # 종료 코드: BaseWorker 계약 (docs/03_AGENT_ARCHITECTURE.md §4)
        status_value = result.status if isinstance(result.status, str) else result.status.value
        if status_value == TaskStatus.COMPLETED.value:
            return 0
        if status_value in {
            TaskStatus.NEEDS_USER_UPLOAD.value,
            TaskStatus.NEEDS_USER_CONFIRMATION.value,
        }:
            return 2
        if status_value == TaskStatus.RIGHTS_REVIEW_REQUIRED.value:
            return 3
        return 1


def run_worker(worker: BaseWorker) -> None:
    """진입점 헬퍼. 하위 모듈의 __main__ 에서 호출."""
    sys.exit(worker.main())

"""Worker Slot Manager.

ADDENDUM_01 §2~3 의 책임을 담당합니다.

- task_queue.json 에서 실행 가능한 task 를 찾는다.
- depends_on 이 충족된 task 만 실행 가능.
- parallelizable=True 인 task 는 빈 Worker Slot 에 배정.
- parallelizable=False 는 다른 모든 Slot 이 비었을 때만 단독 실행.
- asyncio.create_subprocess_exec 로 worker CLI 를 띄우고
  stdout/stderr 를 Log Router 로 보낸다.
- worker_slots.json 을 단일 쓰기자로 동기화한다.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from orchestrator.config import AppConfig
from orchestrator.log_router import LogCallback, LogRouter
from schemas.models import (
    TaskPriority,
    TaskQueue,
    TaskQueueItem,
    TaskStatus,
    WorkerSlot,
    WorkerSlotStatus,
    WorkerSlotsSnapshot,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkerSlotManager:
    """단일 인스턴스. Orchestrator (TUI 메인 task) 가 소유합니다.

    state_listener 콜백은 (snapshot) 단위로 통보됩니다. TUI 는 이를 받아
    화면을 다시 그립니다.
    """

    def __init__(
        self,
        project_id: str,
        project_dir: Path,
        cfg: AppConfig,
        log_callback: Optional[LogCallback] = None,
        state_listener: Optional[Callable[[WorkerSlotsSnapshot], None]] = None,
    ) -> None:
        self.project_id = project_id
        self.project_dir = project_dir
        self.cfg = cfg
        self.log_callback = log_callback
        self.state_listener = state_listener

        self.task_queue_path: Path = project_dir / "03_tasks" / "task_queue.json"
        self.worker_slots_path: Path = project_dir / "03_tasks" / "worker_slots.json"
        self.task_results_dir: Path = project_dir / "03_tasks" / "task_results"
        self.worker_logs_dir: Path = project_dir / "logs" / "workers"

        self.task_queue: TaskQueue = self._load_queue()
        self.snapshot: WorkerSlotsSnapshot = self._init_slots()
        self._processes: dict[int, asyncio.subprocess.Process] = {}
        self._routers: dict[int, LogRouter] = {}
        self._tasks: dict[int, list[asyncio.Task[None]]] = {}

    # -----------------------------------------------------------------
    # 로딩 / 저장
    # -----------------------------------------------------------------

    def _load_queue(self) -> TaskQueue:
        if not self.task_queue_path.exists():
            return TaskQueue(project_id=self.project_id, tasks=[])
        raw = json.loads(self.task_queue_path.read_text(encoding="utf-8"))
        return TaskQueue.model_validate(raw)

    def reload_queue(self) -> None:
        self.task_queue = self._load_queue()

    def _init_slots(self) -> WorkerSlotsSnapshot:
        if self.worker_slots_path.exists():
            try:
                raw = json.loads(self.worker_slots_path.read_text(encoding="utf-8"))
                loaded = WorkerSlotsSnapshot.model_validate(raw)
                if len(loaded.slots) == self.cfg.command_center.worker_slot_count:
                    # idle 외 상태는 재진입 시 idle 로 리셋 (서브프로세스는 사라졌음)
                    for s in loaded.slots:
                        s.status = WorkerSlotStatus.IDLE
                        s.assigned_task_id = None
                        s.assigned_worker = None
                        s.started_at = None
                        s.last_heartbeat = None
                        s.progress = 0.0
                    return loaded
            except Exception:
                pass
        slots = [
            WorkerSlot(slot_id=i + 1, status=WorkerSlotStatus.IDLE)
            for i in range(self.cfg.command_center.worker_slot_count)
        ]
        return WorkerSlotsSnapshot(project_id=self.project_id, slots=slots)

    def save_snapshot(self) -> None:
        self.worker_slots_path.parent.mkdir(parents=True, exist_ok=True)
        self.worker_slots_path.write_text(
            self.snapshot.model_dump_json(indent=2),
            encoding="utf-8",
        )
        if self.state_listener:
            self.state_listener(self.snapshot)

    def save_queue(self) -> None:
        self.task_queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.task_queue_path.write_text(
            self.task_queue.model_dump_json(indent=2),
            encoding="utf-8",
        )

    # -----------------------------------------------------------------
    # 실행 가능한 task 탐색
    # -----------------------------------------------------------------

    def _is_runnable(self, task: TaskQueueItem) -> bool:
        if task.status != TaskStatus.QUEUED.value:
            return False
        for dep_id in task.depends_on:
            dep = self.task_queue.find(dep_id)
            if dep is None or dep.status != TaskStatus.COMPLETED.value:
                return False
        return True

    def _any_slot_running(self) -> bool:
        return any(s.status in {WorkerSlotStatus.RUNNING.value, WorkerSlotStatus.ASSIGNED.value} for s in self.snapshot.slots)

    def _find_idle_slot(self) -> Optional[WorkerSlot]:
        for s in self.snapshot.slots:
            if s.status == WorkerSlotStatus.IDLE.value:
                return s
        return None

    def _pick_next_task(self) -> Optional[TaskQueueItem]:
        """우선순위 / runnable / parallelizable 을 종합 판단."""
        runnable = [t for t in self.task_queue.tasks if self._is_runnable(t)]
        if not runnable:
            return None
        priority_order = {
            TaskPriority.MUST_USE.value: 0,
            TaskPriority.HIGH.value: 1,
            TaskPriority.NORMAL.value: 2,
            TaskPriority.LOW.value: 3,
        }
        runnable.sort(key=lambda t: (priority_order.get(t.priority, 99), t.task_id))
        # 직렬 task 는 다른 slot 이 모두 비었을 때만 실행
        for t in runnable:
            if t.parallelizable:
                return t
            if not self._any_slot_running():
                return t
        return None

    # -----------------------------------------------------------------
    # 배정 / 실행
    # -----------------------------------------------------------------

    async def tick(self) -> None:
        """주기적으로 호출되어 idle slot 에 task 를 배정합니다."""
        # subprocess 종료 감지
        for slot_id, proc in list(self._processes.items()):
            if proc.returncode is not None:
                await self._finalize_slot(slot_id, proc.returncode)

        # 새 task 배정
        while True:
            slot = self._find_idle_slot()
            if slot is None:
                break
            task = self._pick_next_task()
            if task is None:
                break
            await self._launch(slot, task)

        self.save_snapshot()

    async def _launch(self, slot: WorkerSlot, task: TaskQueueItem) -> None:
        # task / slot 상태 업데이트
        task.status = TaskStatus.ASSIGNED.value
        slot.status = WorkerSlotStatus.ASSIGNED.value
        slot.assigned_task_id = task.task_id
        slot.assigned_worker = task.assigned_worker
        slot.started_at = utc_now()
        slot.progress = 0.0
        slot.log_path = str((self.worker_logs_dir / f"{task.task_id}.log").relative_to(self.project_dir.parent.parent)) if False else str(self.worker_logs_dir / f"{task.task_id}.log")

        # Log Router 준비
        log_file = self.worker_logs_dir / f"{task.task_id}.log"
        router = LogRouter(
            slot_id=slot.slot_id,
            task_id=task.task_id,
            log_file=log_file,
            callback=self.log_callback,
            max_lines=self.cfg.command_center.log_panel_max_lines,
        )
        self._routers[slot.slot_id] = router

        router.emit("system", f"=== task {task.task_id} → slot {slot.slot_id} ({task.assigned_worker}) ===")

        # subprocess 실행
        cmd = [
            sys.executable,
            "-u",  # unbuffered stdout
            "-m",
            f"workers.{task.assigned_worker}",
            "--project-id",
            self.project_id,
            "--task-id",
            task.task_id,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,  # PIPELINE-AP-001 회피
                cwd=str(self.project_dir.parent.parent),  # repo root
            )
        except FileNotFoundError as e:
            router.emit("stderr", f"Worker 실행 실패 (FileNotFoundError): {e}")
            task.status = TaskStatus.FAILED.value
            task.error_message = str(e)
            slot.status = WorkerSlotStatus.FAILED.value
            return

        self._processes[slot.slot_id] = proc
        slot.status = WorkerSlotStatus.RUNNING.value
        task.status = TaskStatus.RUNNING.value

        # stdout / stderr 비동기 소비 task 등록
        self._tasks[slot.slot_id] = [
            asyncio.create_task(router.consume_stream(proc.stdout, "stdout")),
            asyncio.create_task(router.consume_stream(proc.stderr, "stderr")),
        ]

    async def _finalize_slot(self, slot_id: int, returncode: int) -> None:
        slot = next((s for s in self.snapshot.slots if s.slot_id == slot_id), None)
        if slot is None:
            return
        task = self.task_queue.find(slot.assigned_task_id) if slot.assigned_task_id else None
        router = self._routers.pop(slot_id, None)

        # stream 소비 task 가 끝날 때까지 잠깐 대기
        for t in self._tasks.pop(slot_id, []):
            try:
                await asyncio.wait_for(t, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        if router:
            router.emit("system", f"=== exit {returncode} ===")
            router.close()

        # task_result.json 읽어 상태 확정 (있다면)
        new_status = self._infer_task_status(slot.assigned_task_id, returncode)
        if task is not None:
            task.status = new_status

        # PIPELINE-AP-006 회피: terminal 상태를 slot 에 남기면 다음 tick 에서
        # idle slot 을 찾지 못해 후속 task 가 영영 queued 로 남는다.
        # worker_slots.json 은 "지금 누가 일하는가" 의 SSOT 일 뿐이며,
        # "누가 무엇을 끝냈는가" 의 SSOT 는 task_queue.json 이므로
        # finalize 직후 즉시 IDLE 로 환원한다.
        slot.status = WorkerSlotStatus.IDLE.value
        slot.assigned_task_id = None
        slot.assigned_worker = None
        slot.started_at = None
        slot.last_heartbeat = None
        slot.progress = 0.0

        self._processes.pop(slot_id, None)
        self.save_queue()
        self.save_snapshot()

    def _infer_task_status(self, task_id: Optional[str], returncode: int) -> str:
        if task_id is None:
            return TaskStatus.FAILED.value
        result_path = self.task_results_dir / f"{task_id}_result.json"
        if result_path.exists():
            try:
                raw = json.loads(result_path.read_text(encoding="utf-8"))
                status = raw.get("status")
                if status:
                    return status
            except Exception:
                pass
        if returncode == 0:
            return TaskStatus.COMPLETED.value
        if returncode == 2:
            return TaskStatus.NEEDS_USER_CONFIRMATION.value
        if returncode == 3:
            return TaskStatus.RIGHTS_REVIEW_REQUIRED.value
        return TaskStatus.FAILED.value

    # -----------------------------------------------------------------
    # 종료
    # -----------------------------------------------------------------

    async def shutdown(self) -> None:
        for slot_id, proc in list(self._processes.items()):
            if proc.returncode is None:
                try:
                    proc.terminate()
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except (asyncio.TimeoutError, ProcessLookupError):
                    try:
                        proc.kill()
                    except Exception:
                        pass
            await self._finalize_slot(slot_id, proc.returncode if proc.returncode is not None else -1)

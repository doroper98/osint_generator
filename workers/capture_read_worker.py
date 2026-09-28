"""CaptureReadWorker — X 게시물 화면 캡처 판독 (v3.2.0, docs/handoff/18 §1·§7, back_and_forth D-0051 작업 5).

입력: `intake/screenshots/{source_id}.png`(vision 첨부 — `claude -p` Read 로 연다) + 사용자 메모(task.description, untrusted).
출력: `intake/drafts/{source_id}.json`(`CaptureDraft`). 소스 레코드로 합치는 것은 `orchestrator.source_intake` 몫이고,
사용자 확인(`confirmed_by`) 전에는 검증 단계로 가지 않는다. x.com 을 열지 않는다(18 §1).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import ClassVar, Type

from pydantic import BaseModel

from schemas.models import TaskQueueItem
from schemas.source_models import CaptureDraft
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt
from workers.prompt_safety import wrap_untrusted

SCREENSHOTS = Path("intake") / "screenshots"
DRAFTS = Path("intake") / "drafts"


class CaptureReadWorker(BaseLLMWorker):
    worker_name = "capture_read"
    task_type = "capture_read"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "vision"
    prompt_name: ClassVar[str] = "capture_read"
    response_model: ClassVar[Type[BaseModel]] = CaptureDraft
    retry_on_invalid: ClassVar[int] = 1

    def _source_id(self, task: TaskQueueItem) -> str:
        if not task.input_item_id:
            raise ValueError("capture_read: task.input_item_id(소스 id) 없음")
        return task.input_item_id

    def attachments(self, args: argparse.Namespace, task: TaskQueueItem) -> list[Path]:
        img = self.project_dir(args) / SCREENSHOTS / f"{self._source_id(task)}.png"
        if not img.exists():
            raise FileNotFoundError(f"캡처 없음: {img}")
        return [img]

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        imgs = "\n".join(f"- {p.resolve()}  (Read 도구로 연다)" for p in self.attachments(args, task))
        note = wrap_untrusted(task.description or "(없음)", source_label="user_note")
        return (load_prompt("capture_read_user", self.rules)
                .replace("{images}", imgs)
                .replace("{source_id}", self._source_id(task))
                .replace("{user_note}", note))

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / DRAFTS / f"{self._source_id(task)}.json"


if __name__ == "__main__":
    run_worker(CaptureReadWorker())

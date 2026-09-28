"""VisualQAWorker — 시각 검수 (v3.1.0, docs/handoff/17 §4, back_and_forth D-0047 작업 8).

입력: `prev/sheet.jpg`(이미지 — `claude -p` Read 로 연다, D-0047 §0-3) + `prev/frames.json` + `prev/checks.json` 요약.
출력: `prev/qa_verdict.v{n}.json`(QAVerdict). 검수자는 연출 파일을 고치지 않는다(AP-V6-11).
판정·코멘트는 프롬프트·규칙에 자동 반영하지 않는다(15 P11).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from engine.qa import QAVerdict
from schemas.models import TaskQueueItem
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.direction_io import next_version
from workers.prompt_loader import load_prompt


def checks_summary(pdir: Path) -> str:
    c = json.loads((pdir / "prev" / "checks.json").read_text(encoding="utf-8"))
    rows = [f"- {i['id']} ({i['severity']}): {i['count']}" + (f" — {i['details'][:3]}" if i["count"] else "") for i in c["items"]]
    return f"hard {c['hard']} · warning {c['warnings']}\n" + "\n".join(rows)


class VisualQAWorker(BaseLLMWorker):
    worker_name = "visual_qa"
    task_type = "visual_qa"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "vision"
    prompt_name: ClassVar[str] = "visual_qa"
    response_model: ClassVar[Type[BaseModel]] = QAVerdict
    retry_on_invalid: ClassVar[int] = 1
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def attachments(self, args: argparse.Namespace, task: TaskQueueItem) -> list[Path]:
        return [self.project_dir(args) / "prev" / "sheet.jpg"]

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        pdir = self.project_dir(args)
        imgs = "\n".join(f"- {p.resolve()}  (Read 도구로 연다)" for p in self.attachments(args, task))
        frames = json.loads((pdir / "prev" / "frames.json").read_text(encoding="utf-8"))
        return (load_prompt("visual_qa_user", self.rules)
                .replace("{images}", imgs)
                .replace("{frames}", json.dumps(frames["frames"], ensure_ascii=False))
                .replace("{checks}", checks_summary(pdir)))

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        pdir = self.project_dir(args)
        return pdir / "prev" / f"qa_verdict.v{next_version(pdir / 'prev', 'qa_verdict', '.json')}.json"


if __name__ == "__main__":
    run_worker(VisualQAWorker())

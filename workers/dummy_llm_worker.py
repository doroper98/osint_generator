"""Stub LLM worker for v0.2.2 smoke test.

실 LLM 호출은 하지 않습니다. `OSINT_LLM_STUB=1` 환경변수를 활용해 BaseLLMWorker 의
전체 흐름 (prompt 빌드 → subprocess 건너뛰기 → Pydantic 검증 → output 저장 → LLMCallRecord 영속화)
이 정상 동작하는지 확인하는 용도입니다.

실 환경에서 실행하지 마십시오. Phase 3 의 IntakePlannerWorker 가 본 worker 를 참조해
실 worker 를 만듭니다.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import ClassVar, Type

from pydantic import Field

from schemas.models import TaskQueueItem, VersionedModel
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker


class DummyLLMResponse(VersionedModel):
    """더미 응답 모델. stub_response 에서 받은 JSON 을 검증."""

    echo: str = ""
    note: str = ""
    items: list[str] = Field(default_factory=list)


class DummyLLMWorker(BaseLLMWorker):
    worker_name = "dummy_llm_worker"
    task_type = "dummy_llm"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    system_prompt: ClassVar[str] = (
        "You are a stub. Echo back the user input as JSON: "
        '{"schema_version":1,"echo":"...","note":"...","items":[...]}'
    )
    response_model: ClassVar[Type[VersionedModel]] = DummyLLMResponse

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        return f"task_id={task.task_id} task_type={task.task_type} desc={task.description}"

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "_dummy_llm" / f"{task.task_id}.json"


if __name__ == "__main__":
    run_worker(DummyLLMWorker())

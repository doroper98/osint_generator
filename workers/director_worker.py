"""DirectorWorker — AI 연출가 (v3.1.0, docs/handoff/17 §2·§5.3, back_and_forth D-0047 작업 8).

입력: `script.yaml` + `plan.json` + 엔티티·미디어 레지스트리 + 지오 역량 + 이벤트 필드 표(15 P9 — 자기 몫만)
+ (있으면) 카메라 제안값 `prev/camera_suggest.json`(v3.3.0, 옵션 — 따를지는 연출가가 정한다, P8).
출력: `projects/{pid}/direction.yaml`(Direction, YAML) + `direction.v{n}.yaml` 보관(16 §6) + `direction.meta.json`
(origin=ai, 모델·프롬프트 sha1 — provenance `ai_direction`).
검증: 스키마 → 앵커·레지스트리·엔티티(check_parsed) 위반이면 오류를 붙여 1회 재요청 후 중단(16 §3).
사용자에게 묻지 않는다(C4).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from engine.direction import Direction
from schemas.models import TaskQueueItem
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.direction_io import (
    bundle_materials_text,
    camera_suggest_text,
    check_direction,
    music_list_text,
    dump_direction_yaml,
    entities_text,
    event_fields_table,
    geo_text,
    load_plan,
    media_text,
    next_version,
    plan_table,
)
from workers.prompt_loader import load_prompt, prompt_sha1

HEADER = "# direction.yaml — AI 연출(DirectorWorker, v3.1.0, 17 §5.3). 사람 검토 전 초안 — 승인 게이트 ②에서 판정.\n"


class DirectorWorker(BaseLLMWorker):
    worker_name = "director"
    task_type = "direction"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "director"
    response_model: ClassVar[Type[BaseModel]] = Direction
    retry_on_invalid: ClassVar[int] = 1
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        pdir = self.project_dir(args)
        return (load_prompt("director_user", self.rules)
                .replace("{script_yaml}", (pdir / "script.yaml").read_text(encoding="utf-8"))
                .replace("{plan_table}", plan_table(load_plan(pdir)))
                .replace("{entities}", entities_text(pdir))
                .replace("{media}", media_text(pdir))
                .replace("{geo}", geo_text(pdir))
                .replace("{event_fields}", event_fields_table())
                .replace("{music_list}", music_list_text(pdir))
                .replace("{camera_suggest}", camera_suggest_text(pdir)[0])
                .replace("{bundle_materials}", bundle_materials_text(pdir)[0]))

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "direction.yaml"

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        assert isinstance(parsed, Direction)
        check_direction(parsed, self.project_dir(args))

    def serialize(self, parsed: BaseModel) -> str:
        assert isinstance(parsed, Direction)
        return dump_direction_yaml(parsed, HEADER)

    def after_output(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        pdir = self.project_dir(args)
        n = next_version(pdir, "direction", ".yaml")
        for rel in (f"direction.v{n}.yaml", "direction.meta.json"):
            self._validate_output_path(args, task, pdir / rel)
        shutil.copyfile(pdir / "direction.yaml", pdir / f"direction.v{n}.yaml")
        (pdir / "direction.meta.json").write_text(json.dumps({
            "schema_version": 1, "origin": "ai", "worker": self.worker_name, "version": n,
            "model": self.resolve_model() if self.llm_backend == "claude" else self.llm_backend,
            "prompt_sha1": prompt_sha1(self.system_prompt()),
            "camera_suggest_sha1": camera_suggest_text(pdir)[1],
            "bundle_materials_sha1": bundle_materials_text(pdir)[1]}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    run_worker(DirectorWorker())

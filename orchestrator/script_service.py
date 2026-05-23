"""build-script 오케스트레이션 (Phase 6 Script, v0.9.0).

`ScriptWorker` 1회 호출 + 상태 전이를 묶는 thin orchestration (research_service 와
동형). 수직 슬라이스에서 별도 Blueprint 단계를 만들지 않으므로, 상태는
`research_in_progress → blueprint_review → script_writing` 으로 **blueprint_review 를
통과만** 하고 script_writing 에 안착한다 (대본 산출 완료, script_review 게이트 직전).
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from orchestrator.config import AppConfig, load_config
from orchestrator.project_manager import resume_project, transition_state
from orchestrator.script_io import full_script_path, load_full_script
from schemas.models import FullScript, ProjectManifest, ProjectState, TaskQueueItem


class ScriptError(RuntimeError):
    """build-script 흐름 실패. kind: "state" / "worker" / "persist"."""

    def __init__(
        self, message: str, *, kind: str, errors: Optional[list[str]] = None
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.errors = errors or []


def _state_str(state) -> str:
    return state.value if hasattr(state, "value") else str(state)


def run_script_worker(
    project_id: str,
    *,
    backend: str = "claude",
    force: bool = False,
    cfg: Optional[AppConfig] = None,
) -> tuple[ProjectManifest, list[str], bool]:
    """build-script 전체 흐름.

    1. precondition: research_in_progress.
    2. 유효한 기존 full_script.json + force 미지정이면 worker skip.
    3. 합성 TaskQueueItem + worker.run() + write_result.
    4. worker 성공 시 디스크 full_script 검증(전이 게이트).
    5. research_in_progress → blueprint_review → script_writing 전이 (blueprint 흡수).

    returns: (manifest, outputs, skipped). raises: FileNotFoundError / ScriptError / ValueError.
    """
    from workers.script_worker import ScriptWorker

    cfg = cfg or load_config()

    manifest = resume_project(project_id, cfg)
    current = _state_str(manifest.current_state)
    if current != ProjectState.RESEARCH_IN_PROGRESS.value:
        raise ScriptError(
            f"현재 상태 '{current}' 에서는 build-script 를 실행할 수 없습니다. "
            f"(허용: research_in_progress)",
            kind="state",
        )

    script_path = full_script_path(project_id, cfg)

    skipped = False
    if script_path.exists() and not force:
        try:
            FullScript.model_validate_json(script_path.read_text(encoding="utf-8"))
            skipped = True
        except (json.JSONDecodeError, ValueError):
            skipped = False

    if skipped:
        outputs = [str(script_path)]
    else:
        task_id = f"script-{project_id}"
        task = TaskQueueItem(
            task_id=task_id,
            task_type="script",
            assigned_worker="script",
            description="ScriptWorker 1회 실행",
            input_refs=["04_research/research_dossier.json", "project_manifest.json"],
            output_refs=["05_script/full_script.json"],
        )
        worker = ScriptWorker()
        worker.llm_backend = backend

        worker_args = argparse.Namespace(
            project_id=project_id, task_id=task_id, projects_root="projects"
        )
        result = worker.run(worker_args, task)
        try:
            worker.write_result(worker_args, result)
        except OSError:
            pass

        if _state_str(result.status) != "completed":
            raise ScriptError(
                f"ScriptWorker 실패: status={_state_str(result.status)}",
                kind="worker",
                errors=list(result.errors),
            )
        outputs = list(result.outputs)

        try:
            load_full_script(project_id, cfg)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            raise ScriptError(
                f"full_script.json 영속화 검증 실패: {e}", kind="persist"
            ) from e

    # blueprint_review 를 통과만 하고 script_writing 에 안착 (수직 슬라이스: blueprint 흡수).
    manifest = transition_state(
        manifest,
        ProjectState.BLUEPRINT_REVIEW,
        reason="blueprint 단계 흡수 (수직 슬라이스, v0.9.0)",
        cfg=cfg,
    )
    manifest = transition_state(
        manifest,
        ProjectState.SCRIPT_WRITING,
        reason="ScriptWorker 성공" if not skipped else "기존 full_script.json 재사용",
        cfg=cfg,
    )
    return manifest, outputs, skipped


__all__ = ["run_script_worker", "ScriptError"]

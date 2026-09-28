"""build-script 오케스트레이션 (Phase 6 Script, v0.9.0).

`ScriptWorker` 1회 호출 + 상태 전이를 묶는 thin orchestration (research_service 와
동형). 상태는 `research → script_draft` (v3.0.0, 16 §2 — 다음은 script_approval 게이트).
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

import yaml

from orchestrator.config import AppConfig, load_config
from orchestrator.project_manager import resume_project, transition_state
from orchestrator.config import project_dir
from orchestrator.script_io import load_script, script_path
from schemas.models import ProjectManifest, ProjectState, TaskQueueItem
from script.labels import check_project_labels


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

    1. precondition: research.
    2. 유효한 기존 script.yaml(+ 라벨 일치) + force 미지정이면 worker skip.
    3. 합성 TaskQueueItem + worker.run() + write_result.
    4. worker 성공 시 디스크 script.yaml·script_labels.json 검증(전이 게이트).
    5. research → script_draft 전이.

    returns: (manifest, outputs, skipped). raises: FileNotFoundError / ScriptError / ValueError.
    """
    from workers.script_worker import ScriptWorker

    cfg = cfg or load_config()

    manifest = resume_project(project_id, cfg)
    current = _state_str(manifest.current_state)
    if current != ProjectState.RESEARCH.value:
        raise ScriptError(
            f"현재 상태 '{current}' 에서는 build-script 를 실행할 수 없습니다. "
            f"(허용: research)",
            kind="state",
        )

    spath = script_path(project_id, cfg)

    skipped = False
    if spath.exists() and not force:
        try:   # 유효한 원고 + 라벨이 도시어와 일치할 때만 재사용(D-0043 §3)
            check_project_labels(project_dir(project_id, cfg), load_script(project_id, cfg))
            skipped = True
        except (json.JSONDecodeError, ValueError, yaml.YAMLError):
            skipped = False

    if skipped:
        outputs = [str(spath)]
    else:
        task_id = f"script-{project_id}"
        task = TaskQueueItem(
            task_id=task_id,
            task_type="script",
            assigned_worker="script",
            description="ScriptWorker 1회 실행",
            input_refs=["04_research/research_dossier.json", "project_manifest.json"],
            output_refs=["script.yaml", "script_labels.json"],
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
            check_project_labels(project_dir(project_id, cfg), load_script(project_id, cfg))
        except (FileNotFoundError, json.JSONDecodeError, ValueError, yaml.YAMLError) as e:
            raise ScriptError(
                f"script.yaml·script_labels.json 영속화 검증 실패: {e}", kind="persist"
            ) from e

    manifest = transition_state(
        manifest,
        ProjectState.SCRIPT_DRAFT,
        reason="ScriptWorker 성공" if not skipped else "기존 script.yaml 재사용",
        cfg=cfg,
    )
    return manifest, outputs, skipped


__all__ = ["run_script_worker", "ScriptError"]

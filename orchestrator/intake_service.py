"""plan-intake 오케스트레이션 — CLI 와 Web 진입점이 공유하는 단일 출처 (v0.7.0).

`IntakePlannerWorker` 1회 호출 + 상태 전이 (`created`/`intake_planning` →
`intake_pending_user`) 를 한 함수로 묶는다. CLI (`orchestrator.main._cmd_plan_intake`)
와 Web (`web.intake_page_app` 의 프로젝트 생성 라우트) 가 동일 로직을 쓰도록 하여
전이 순서·idempotency 가 두 곳에서 어긋나지 않게 한다.

순수 함수는 아니다 (worker 실행 + manifest 영속화). 다만 사용자 입출력 (print) 은
호출자 (CLI / Web) 가 담당하고, 본 모듈은 결과/예외로만 소통한다.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import resume_project, transition_state
from schemas.models import IntakePlan, ProjectManifest, ProjectState, TaskQueueItem


class IntakePlanningError(RuntimeError):
    """plan-intake 흐름 실패.

    kind:
    - "state"  : state precondition 위반 (created/intake_planning 이 아님).
    - "worker" : IntakePlannerWorker 가 completed 가 아닌 상태로 종료.
    """

    def __init__(self, message: str, *, kind: str, errors: Optional[list[str]] = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.errors = errors or []


def _state_str(state) -> str:
    return state.value if hasattr(state, "value") else str(state)


def run_intake_planner(
    project_id: str,
    *,
    backend: str = "claude",
    force: bool = False,
    projects_root: str = "projects",
    cfg: Optional[AppConfig] = None,
) -> tuple[ProjectManifest, list[str], bool]:
    """plan-intake 전체 흐름 실행.

    1. manifest 로딩 + state precondition.
    2. created → intake_planning 전이 (이미 planning 이면 skip).
    3. 유효한 기존 `intake_plan.json` 이 있고 force 미지정이면 worker skip.
    4. 합성 TaskQueueItem + worker.run() + write_result.
    5. intake_planning → intake_pending_user 전이.

    parameters
    ----------
    backend : "claude" | "codex"
        IntakePlannerWorker.llm_backend.
    force : bool
        True 면 기존 intake_plan.json 이 유효해도 worker 재실행.

    returns
    -------
    (ProjectManifest, list[str], bool)
        전이 완료된 manifest, outputs 요약, worker skip 여부.

    raises
    ------
    FileNotFoundError
        manifest 없음.
    IntakePlanningError
        state 위반 (kind="state") 또는 worker 실패 (kind="worker").
    ValueError
        전이 자체 실패 (드묾).
    """
    # 지연 import: worker 의존성이 없는 다른 진입점에 영향 주지 않도록.
    from workers.intake_planner_worker import IntakePlannerWorker

    cfg = cfg or load_config()

    manifest = resume_project(project_id, cfg)
    current = _state_str(manifest.current_state)
    if current == ProjectState.CREATED.value:
        manifest = transition_state(
            manifest, ProjectState.INTAKE_PLANNING, reason="plan-intake 시작", cfg=cfg
        )
    elif current != ProjectState.INTAKE_PLANNING.value:
        raise IntakePlanningError(
            f"현재 상태 '{current}' 에서는 plan-intake 를 실행할 수 없습니다. "
            f"(허용: created 또는 intake_planning)",
            kind="state",
        )

    plan_path = project_dir(project_id, cfg) / "01_intake" / "intake_plan.json"

    skipped = False
    if plan_path.exists() and not force:
        try:
            IntakePlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
            skipped = True
        except (json.JSONDecodeError, ValueError):
            # 손상된 기존 plan 은 무시하고 재실행.
            skipped = False

    if skipped:
        outputs = [str(plan_path)]
    else:
        task_id = f"intake-plan-{project_id}"
        task = TaskQueueItem(
            task_id=task_id,
            task_type="intake_planning",
            assigned_worker="intake_planner",
            description="IntakePlannerWorker 1회 실행",
            input_refs=["project_manifest.json"],
            output_refs=["01_intake/intake_plan.json"],
        )
        worker = IntakePlannerWorker()
        worker.llm_backend = backend  # type: ignore[misc]

        worker_args = argparse.Namespace(
            project_id=project_id,
            task_id=task_id,
            projects_root=projects_root,
        )
        result = worker.run(worker_args, task)
        try:
            worker.write_result(worker_args, result)
        except OSError:
            # task_result.json 영속화 실패는 치명적이지 않음 — 진행.
            pass

        result_status = _state_str(result.status)
        if result_status != "completed":
            raise IntakePlanningError(
                f"IntakePlannerWorker 실패: status={result_status}",
                kind="worker",
                errors=list(result.errors),
            )
        outputs = list(result.outputs)

    manifest = transition_state(
        resume_project(project_id, cfg),
        ProjectState.INTAKE_PENDING_USER,
        reason="IntakePlannerWorker 성공" if not skipped else "기존 intake_plan.json 재사용",
        cfg=cfg,
    )
    return manifest, outputs, skipped


__all__ = ["run_intake_planner", "IntakePlanningError"]

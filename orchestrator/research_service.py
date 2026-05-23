"""build-research-dossier 오케스트레이션 (Phase 6A, v0.8.0).

`ResearchWorker` 1회 호출 + 상태 전이(`source_completeness_review` →
`research_in_progress`)를 한 함수로 묶는다. `intake_service.run_intake_planner` 와
동일한 형태의 thin orchestration — 사용자 입출력(print)은 호출자(CLI)가 담당하고,
본 모듈은 결과/예외로만 소통한다. 디스크 영속화는 ResearchWorker(output_path) 와
research_io 가 담당하며, 본 모듈은 precondition·worker 실행·전이 게이트만 책임진다.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from orchestrator.config import AppConfig, load_config
from orchestrator.project_manager import resume_project, transition_state
from orchestrator.research_io import load_research_dossier, research_dossier_path
from schemas.models import ProjectManifest, ProjectState, ResearchDossier, TaskQueueItem


class ResearchError(RuntimeError):
    """build-research-dossier 흐름 실패.

    kind:
    - "state"  : state precondition 위반 (source_completeness_review 가 아님).
    - "worker" : ResearchWorker 가 completed 가 아닌 상태로 종료.
    - "persist": worker 는 성공했으나 디스크 dossier 검증/로딩 실패.
    """

    def __init__(
        self, message: str, *, kind: str, errors: Optional[list[str]] = None
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.errors = errors or []


def _state_str(state) -> str:
    return state.value if hasattr(state, "value") else str(state)


def run_research_worker(
    project_id: str,
    *,
    backend: str = "claude",
    force: bool = False,
    cfg: Optional[AppConfig] = None,
) -> tuple[ProjectManifest, list[str], bool]:
    """build-research-dossier 전체 흐름 실행.

    1. manifest 로딩 + state precondition (source_completeness_review 에서만).
    2. 유효한 기존 research_dossier.json 이 있고 force 미지정이면 worker skip.
    3. 합성 TaskQueueItem + worker.run() + write_result.
    4. worker 성공 시 디스크 dossier 를 load 로 검증 (전이 게이트).
    5. source_completeness_review → research_in_progress 전이.

    returns
    -------
    (ProjectManifest, list[str], bool)
        전이 완료된 manifest, outputs 요약, worker skip 여부.

    raises
    ------
    FileNotFoundError
        manifest 없음.
    ResearchError
        state 위반(kind="state") / worker 실패(kind="worker") / 영속화 검증 실패(kind="persist").
    ValueError
        전이 자체 실패 (드묾).
    """
    # 지연 import: worker 의존성이 없는 다른 진입점에 영향 주지 않도록.
    from workers.research_worker import ResearchWorker

    cfg = cfg or load_config()

    manifest = resume_project(project_id, cfg)
    current = _state_str(manifest.current_state)
    if current != ProjectState.SOURCE_COMPLETENESS_REVIEW.value:
        raise ResearchError(
            f"현재 상태 '{current}' 에서는 build-research-dossier 를 실행할 수 없습니다. "
            f"(허용: source_completeness_review)",
            kind="state",
        )

    dossier_path = research_dossier_path(project_id, cfg)

    skipped = False
    if dossier_path.exists() and not force:
        try:
            ResearchDossier.model_validate_json(
                dossier_path.read_text(encoding="utf-8")
            )
            skipped = True
        except (json.JSONDecodeError, ValueError):
            # 손상된 기존 dossier 는 무시하고 재실행.
            skipped = False

    if skipped:
        outputs = [str(dossier_path)]
    else:
        task_id = f"research-{project_id}"
        task = TaskQueueItem(
            task_id=task_id,
            task_type="research",
            assigned_worker="research",
            description="ResearchWorker 1회 실행",
            input_refs=["02_sources/source_registry.json", "project_manifest.json"],
            output_refs=["04_research/research_dossier.json"],
        )
        worker = ResearchWorker()
        worker.llm_backend = backend

        worker_args = argparse.Namespace(
            project_id=project_id,
            task_id=task_id,
            projects_root="projects",
        )
        result = worker.run(worker_args, task)
        try:
            worker.write_result(worker_args, result)
        except OSError:
            # task_result.json 영속화 실패는 치명적이지 않음 — 진행.
            pass

        result_status = _state_str(result.status)
        if result_status != "completed":
            raise ResearchError(
                f"ResearchWorker 실패: status={result_status}",
                kind="worker",
                errors=list(result.errors),
            )
        outputs = list(result.outputs)

        # 전이 게이트: dossier 가 디스크에 유효하게 영속화됐는지 확인 후에만 전진.
        try:
            load_research_dossier(project_id, cfg)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            raise ResearchError(
                f"research_dossier.json 영속화 검증 실패: {e}",
                kind="persist",
            ) from e

    # planner worker 와 마찬가지로 ResearchWorker 는 manifest 를 건드리지 않으므로
    # in-memory manifest 를 그대로 전이 (resume 재호출의 race window 제거).
    manifest = transition_state(
        manifest,
        ProjectState.RESEARCH_IN_PROGRESS,
        reason="ResearchWorker 성공" if not skipped else "기존 research_dossier.json 재사용",
        cfg=cfg,
    )
    return manifest, outputs, skipped


__all__ = ["run_research_worker", "ResearchError"]

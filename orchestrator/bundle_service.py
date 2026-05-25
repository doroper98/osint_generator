"""import-bundle 오케스트레이션 (외부 연동, 계약 v1).

agents_reviewer report_bundle → research_dossier 로 변환·영속화하고 상태를
`research_in_progress` 로 전이한다. `build-research-dossier`(LLM ResearchWorker)의
드롭인 대체 — 둘 다 `source_completeness_review → research_in_progress` 이고
`research_dossier.json` 을 산출하므로, 이후 build-script → build-scene → build-audio →
render-debug 가 그대로 동작한다. research_service 와 동형의 thin orchestration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from orchestrator.bundle_io import bundle_to_research_dossier, load_report_bundle
from orchestrator.config import AppConfig, load_config
from orchestrator.project_manager import resume_project, transition_state
from orchestrator.research_io import (
    load_research_dossier,
    persist_research_dossier,
    research_dossier_path,
)
from schemas.models import ProjectManifest, ProjectState


class BundleImportError(RuntimeError):
    """import-bundle 흐름 실패.

    kind:
    - "state"  : state precondition 위반 (source_completeness_review 가 아님).
    - "bundle" : report_bundle 로드/검증 실패 (JSON 손상·스키마 위반).
    - "persist": 변환은 됐으나 디스크 dossier 검증/로딩 실패.
    """

    def __init__(self, message: str, *, kind: str) -> None:
        super().__init__(message)
        self.kind = kind


def _state_str(state) -> str:
    return state.value if hasattr(state, "value") else str(state)


def import_report_bundle(
    project_id: str,
    bundle_path: Path,
    *,
    cfg: Optional[AppConfig] = None,
) -> tuple[ProjectManifest, list[str]]:
    """import-bundle 전체 흐름.

    1. precondition: source_completeness_review.
    2. report_bundle 로드·검증 (ReportBundle, extra="forbid").
    3. research_dossier 로 변환·영속화.
    4. 디스크 dossier 검증 (전이 게이트).
    5. source_completeness_review → research_in_progress 전이.

    returns: (manifest, outputs). raises: FileNotFoundError / BundleImportError / ValueError.
    """
    cfg = cfg or load_config()

    manifest = resume_project(project_id, cfg)
    current = _state_str(manifest.current_state)
    if current != ProjectState.SOURCE_COMPLETENESS_REVIEW.value:
        raise BundleImportError(
            f"현재 상태 '{current}' 에서는 import-bundle 를 실행할 수 없습니다. "
            f"(허용: source_completeness_review)",
            kind="state",
        )

    try:
        bundle = load_report_bundle(bundle_path)
    except FileNotFoundError:
        raise
    except (json.JSONDecodeError, ValueError) as e:
        raise BundleImportError(f"report_bundle 검증 실패: {e}", kind="bundle") from e

    dossier = bundle_to_research_dossier(bundle, project_id)
    persist_research_dossier(project_id, dossier, cfg)

    # 전이 게이트: dossier 가 디스크에 유효하게 영속화됐는지 확인 후에만 전진.
    try:
        load_research_dossier(project_id, cfg)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        raise BundleImportError(
            f"research_dossier.json 영속화 검증 실패: {e}", kind="persist"
        ) from e

    manifest = transition_state(
        manifest,
        ProjectState.RESEARCH_IN_PROGRESS,
        reason=(
            f"report_bundle 흡수 (producer={bundle.producer.system} "
            f"{bundle.producer.version})"
        ),
        cfg=cfg,
    )
    return manifest, [str(research_dossier_path(project_id, cfg))]


__all__ = ["import_report_bundle", "BundleImportError"]

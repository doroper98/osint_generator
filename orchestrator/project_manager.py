"""Project Manager — ProjectManifest 의 생성·재개·상태 전이를 담당.

본 모듈이 `projects/{project_id}/project_manifest.json` 의 유일한 쓰기자입니다.
다른 모듈은 `load_manifest` 로 읽기만 합니다.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.state_machine import validate_transition
from schemas.models import (
    Category,
    ProjectManifest,
    ProjectState,
    StateHistoryEntry,
    utc_now,
)


MANIFEST_FILENAME = "project_manifest.json"


# 새 프로젝트 디렉토리에 만들어두는 표준 하위 폴더.
# command_center.run_command_center 와 일치시킵니다.
_STANDARD_SUBDIRS: tuple[str, ...] = (
    "03_tasks",
    "03_tasks/task_results",
    "logs/workers",
)


class ProjectExistsError(RuntimeError):
    """동일 project_id 의 manifest 가 이미 존재."""


class ProjectNotFoundError(RuntimeError):
    """resume 대상 manifest 가 없음."""


def manifest_path(project_id: str, cfg: AppConfig | None = None) -> Path:
    return project_dir(project_id, cfg) / MANIFEST_FILENAME


def _ensure_subdirs(base: Path, subdirs: Iterable[str] = _STANDARD_SUBDIRS) -> None:
    base.mkdir(parents=True, exist_ok=True)
    for rel in subdirs:
        (base / rel).mkdir(parents=True, exist_ok=True)


def _serialize(manifest: ProjectManifest) -> str:
    # use_enum_values=True 라서 enum 은 자동으로 문자열화됨.
    return manifest.model_dump_json(indent=2)


def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def save_manifest(manifest: ProjectManifest, cfg: AppConfig | None = None) -> Path:
    """디스크에 직렬화. updated_at 은 호출자가 갱신해야 합니다."""
    cfg = cfg or load_config()
    path = manifest_path(manifest.project_id, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, _serialize(manifest))
    return path


def load_manifest(project_id: str, cfg: AppConfig | None = None) -> ProjectManifest:
    cfg = cfg or load_config()
    path = manifest_path(project_id, cfg)
    if not path.exists():
        raise ProjectNotFoundError(
            f"project_manifest.json 이 없습니다: {path}. "
            f"먼저 `new-project {project_id}` 로 생성하세요."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ProjectManifest.model_validate(raw)


def new_project(
    project_id: str,
    title: str,
    category: Category | str,
    target_duration_min: int = 18,
    topic_summary: str = "",
    cfg: AppConfig | None = None,
    overwrite: bool = False,
) -> ProjectManifest:
    """새 프로젝트 매니페스트를 생성하고 디스크에 저장."""
    cfg = cfg or load_config()
    path = manifest_path(project_id, cfg)
    if path.exists() and not overwrite:
        raise ProjectExistsError(
            f"이미 존재하는 프로젝트입니다: {path}. "
            f"재개하려면 `resume {project_id}` 를 사용하세요."
        )

    if isinstance(category, str):
        category = Category(category)

    now = utc_now()
    manifest = ProjectManifest(
        project_id=project_id,
        title=title,
        category=category,
        created_at=now,
        updated_at=now,
        current_state=ProjectState.CREATED,
        target_duration_min=target_duration_min,
        topic_summary=topic_summary,
        state_history=[
            StateHistoryEntry(
                from_state=None,
                to_state=ProjectState.CREATED,
                at=now,
                reason="project created",
            )
        ],
    )

    _ensure_subdirs(project_dir(project_id, cfg))
    save_manifest(manifest, cfg)
    return manifest


def resume_project(project_id: str, cfg: AppConfig | None = None) -> ProjectManifest:
    """기존 매니페스트를 로드. 표준 하위 폴더가 빠져 있으면 보충."""
    cfg = cfg or load_config()
    manifest = load_manifest(project_id, cfg)
    _ensure_subdirs(project_dir(project_id, cfg))
    return manifest


def transition_state(
    project_id: str,
    next_state: ProjectState | str,
    reason: str = "",
    cfg: AppConfig | None = None,
) -> ProjectManifest:
    """상태 전이 + 감사 로그 + 디스크 저장.

    허용되지 않은 전이는 `InvalidTransitionError`(ValueError 하위) 로 거부됩니다.
    """
    cfg = cfg or load_config()
    manifest = load_manifest(project_id, cfg)

    cur = manifest.current_state
    # use_enum_values=True 영향으로 cur 는 문자열일 수 있음. enum 으로 정규화.
    cur_enum = cur if isinstance(cur, ProjectState) else ProjectState(cur)

    nxt = next_state if isinstance(next_state, ProjectState) else ProjectState(next_state)

    validate_transition(cur_enum, nxt)

    now = utc_now()
    manifest.current_state = nxt
    manifest.updated_at = now
    manifest.state_history.append(
        StateHistoryEntry(
            from_state=cur_enum,
            to_state=nxt,
            at=now,
            reason=reason,
        )
    )
    save_manifest(manifest, cfg)
    return manifest

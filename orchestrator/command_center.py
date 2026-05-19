"""Command Center 진입 모듈.

`orchestrator.main command-center --project {pid}` 의 본체.
TUI 실행만 담당하며 라우팅은 main.py 가 합니다.

Phase 2 부터: project_manager 가 manifest 의 단일 쓰기자이므로
본 모듈은 read-only 로 manifest 를 로드해 TUI 에 current_state 를 전달합니다.
"""

from __future__ import annotations

from pathlib import Path

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import (
    MANIFEST_FILENAME,
    load_manifest,
)
from orchestrator.tui_app import CommandCenterApp
from schemas.models import ProjectState


def run_command_center(project_id: str, cfg: AppConfig | None = None) -> None:
    cfg = cfg or load_config()
    pdir = project_dir(project_id, cfg)
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks").mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks" / "task_results").mkdir(parents=True, exist_ok=True)
    (pdir / "logs" / "workers").mkdir(parents=True, exist_ok=True)

    # manifest 가 있으면 current_state 를 읽고, 없으면 created 로 가정.
    current_state: str = ProjectState.CREATED.value
    manifest_file: Path = pdir / MANIFEST_FILENAME
    if manifest_file.exists():
        try:
            manifest = load_manifest(project_id, cfg)
            state = manifest.current_state
            current_state = state.value if hasattr(state, "value") else str(state)
        except Exception:
            # manifest 가 손상된 경우 TUI 진입은 막지 않되 created 로 fallback.
            current_state = ProjectState.CREATED.value

    app = CommandCenterApp(
        project_id=project_id,
        project_dir=pdir,
        cfg=cfg,
        current_state=current_state,
    )
    app.run()

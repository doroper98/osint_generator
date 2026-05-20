"""Command Center 진입 모듈.

`orchestrator.main command-center --project {pid}` 의 본체.
TUI 실행만 담당하며 라우팅은 main.py 가 합니다.

Phase 2 부터 ProjectManifest 로딩은 `project_manager` 가 SSOT 입니다.
manifest 가 없으면 Command Center 는 진입을 거부합니다 — 먼저
`new-project {pid}` 로 생성하세요.
"""

from __future__ import annotations

import sys

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import ProjectNotFoundError, resume_project
from orchestrator.tui_app import CommandCenterApp


def run_command_center(project_id: str, cfg: AppConfig | None = None) -> None:
    cfg = cfg or load_config()
    try:
        manifest = resume_project(project_id, cfg)
    except ProjectNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    pdir = project_dir(project_id, cfg)
    current_state = manifest.current_state
    if hasattr(current_state, "value"):
        current_state = current_state.value

    app = CommandCenterApp(
        project_id=project_id,
        project_dir=pdir,
        cfg=cfg,
        current_state=current_state,
    )
    app.run()

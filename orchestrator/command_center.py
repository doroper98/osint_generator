"""Command Center 진입 모듈.

`orchestrator.main command-center --project {pid}` 의 본체.
TUI 실행만 담당하며 라우팅은 main.py 가 합니다.
"""

from __future__ import annotations

from pathlib import Path

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.tui_app import CommandCenterApp


def run_command_center(project_id: str, cfg: AppConfig | None = None) -> None:
    cfg = cfg or load_config()
    pdir = project_dir(project_id, cfg)
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks").mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks" / "task_results").mkdir(parents=True, exist_ok=True)
    (pdir / "logs" / "workers").mkdir(parents=True, exist_ok=True)

    # project_manifest.json 이 있으면 current_state 읽기 (Phase 2 에서 본격화)
    current_state = "created"
    manifest_path: Path = pdir / "project_manifest.json"
    if manifest_path.exists():
        try:
            import json

            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            current_state = raw.get("current_state", "created")
        except Exception:
            pass

    app = CommandCenterApp(
        project_id=project_id,
        project_dir=pdir,
        cfg=cfg,
        current_state=current_state,
    )
    app.run()

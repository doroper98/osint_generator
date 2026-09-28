"""Command Center 진입 모듈.

`orchestrator.main command-center --project {pid}` 의 본체.
TUI 실행만 담당하며 라우팅은 main.py 가 합니다.

Phase 2 부터: project_manager 가 manifest 의 단일 쓰기자이므로
본 모듈은 read-only 로 manifest 를 로드해 TUI 에 current_state 를 전달합니다.

v3.0.0 (16 §3, 15 P6): 손상·옛 버전 manifest 는 'created' 로 폴백하지 않고 오류다.
manifest 가 없는 프로젝트도 오류다 — `new-project` 로 먼저 만든다.
"""

from __future__ import annotations

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import MANIFEST_FILENAME, load_manifest
from orchestrator.state_machine import coerce


def load_project_state(project_id: str, cfg: AppConfig | None = None) -> str:
    """manifest 의 current_state 값.

    raises
    ------
    FileNotFoundError : manifest 없음.
    orchestrator.errors.ManifestCorruptError : JSON·스키마 손상.
    orchestrator.errors.ManifestVersionError : schema_version ≠ 2 (재생성 필요).
    """
    cfg = cfg or load_config()
    return coerce(load_manifest(project_id, cfg).current_state).value


def run_command_center(project_id: str, cfg: AppConfig | None = None) -> None:
    # 지연 import: textual 없이도 load_project_state 를 쓸 수 있게.
    from orchestrator.tui_app import CommandCenterApp  # noqa: PLC0415

    cfg = cfg or load_config()
    pdir = project_dir(project_id, cfg)
    if not (pdir / MANIFEST_FILENAME).exists():
        raise FileNotFoundError(
            f"{pdir / MANIFEST_FILENAME} 없음 — `python -m orchestrator.main new-project` 로 먼저 만든다"
        )
    current_state = load_project_state(project_id, cfg)
    (pdir / "03_tasks" / "task_results").mkdir(parents=True, exist_ok=True)
    (pdir / "logs" / "workers").mkdir(parents=True, exist_ok=True)

    app = CommandCenterApp(
        project_id=project_id,
        project_dir=pdir,
        cfg=cfg,
        current_state=current_state,
    )
    app.run()

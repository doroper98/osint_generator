"""config.yaml 로더.

본 모듈은 운영 파라미터의 유일한 진입점입니다.
도메인 데이터(프로젝트 상태 등)는 여기에 두지 않습니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONFIG_PATH: Path = REPO_ROOT / "config.yaml"


class CommandCenterConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    worker_slot_count: int = 4
    heartbeat_timeout_sec: int = 60
    log_panel_max_lines: int = 500
    log_router_read_chunk: int = 1024
    tui_refresh_interval_sec: float = 0.5


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    level: str = "INFO"
    file: str = "logs/orchestrator.log"
    rotate_daily: bool = True
    retention_days: int = 30


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    projects_root: str = "projects"
    remotion_root: str = "remotion"
    python_bin: str = "python"


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    command_center: CommandCenterConfig = Field(default_factory=CommandCenterConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    render: dict[str, Any] = Field(default_factory=dict)
    tts: dict[str, Any] = Field(default_factory=dict)
    review_gates: dict[str, Any] = Field(default_factory=dict)


def load_config(path: Path | None = None) -> AppConfig:
    """config.yaml 을 읽어 AppConfig 로 검증해 반환합니다.

    파일이 없으면 기본값으로 동작합니다.
    """
    target = path or CONFIG_PATH
    if not target.exists():
        return AppConfig()
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(raw)


def project_dir(project_id: str, cfg: AppConfig | None = None) -> Path:
    """프로젝트 디렉토리 절대경로."""
    cfg = cfg or load_config()
    return REPO_ROOT / cfg.paths.projects_root / project_id

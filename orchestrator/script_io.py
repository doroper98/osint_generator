"""full_script.json 영속화 + 로딩 (Phase 6 Script, v0.9.0).

`research_io.py` 와 동일한 I/O 경계 패턴. 도메인 생성 로직(LLM 호출)은 ScriptWorker
가 책임지고, 본 모듈은 full_script.json 의 경로 SSOT · atomic 영속화 · 타입 로딩만
담당한다. ScriptWorker 는 `BaseLLMWorker.output_path` 로 동일 경로에 직접 write 하며,
`load_full_script` 는 CLI 가 전이 전 디스크 검증 게이트로 쓰고 다음 단계(Scene Planner)
의 입력 로더로도 재사용된다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from schemas.models import FullScript


SCRIPT_DIRNAME = "05_script"
FULL_SCRIPT_FILENAME = "full_script.json"


def script_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/05_script/` 디렉토리."""
    return project_dir(project_id, cfg) / SCRIPT_DIRNAME


def full_script_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/05_script/full_script.json` 경로."""
    return script_dir(project_id, cfg) / FULL_SCRIPT_FILENAME


def _atomic_write_text(path: Path, data: str) -> None:
    """tmp write → fsync → atomic rename. research_io._atomic_write_text 와 동일 정책."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise
    try:
        dir_fd = os.open(path.parent, getattr(os, "O_DIRECTORY", os.O_RDONLY))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass


def persist_full_script(
    project_id: str, script: FullScript, cfg: Optional[AppConfig] = None
) -> Path:
    """`FullScript` 를 `05_script/full_script.json` 으로 atomic 영속화."""
    cfg = cfg or load_config()
    path = full_script_path(project_id, cfg)
    _atomic_write_text(path, script.model_dump_json(indent=2))
    return path


def load_full_script(
    project_id: str, cfg: Optional[AppConfig] = None
) -> FullScript:
    """`05_script/full_script.json` 을 로드 → `FullScript`. 없으면 FileNotFoundError."""
    cfg = cfg or load_config()
    path = full_script_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"full_script.json 이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return FullScript.model_validate(raw)


__all__ = [
    "script_dir",
    "full_script_path",
    "persist_full_script",
    "load_full_script",
]

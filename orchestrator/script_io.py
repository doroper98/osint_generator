"""원고 script.yaml 영속화 + 로딩 (v3.0.0, 16 §6, back_and_forth D-0040 작업 5).

원고의 정본은 `projects/{pid}/script.yaml`(`script.schema:Script`, 사람이 고치는 YAML)이다.
옛 `05_script/full_script.json`(FullScript)은 삭제했다(15 P2). ScriptWorker 는 `output_path` 로
같은 경로에 쓰고, 검증 라벨 파생값은 `script_labels.json`(script/labels, D-0043).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from orchestrator.config import AppConfig, load_config, project_dir
from script.labels import LABELS_FILENAME
from script.schema import Script

SCRIPT_FILENAME = "script.yaml"


def script_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/script.yaml` 경로."""
    return project_dir(project_id, cfg) / SCRIPT_FILENAME


def labels_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/script_labels.json` 경로."""
    return project_dir(project_id, cfg) / LABELS_FILENAME


def dump_script_yaml(script: Script) -> str:
    """사람이 고치기 쉬운 YAML(키 순서 유지, 한글 그대로). 빈 선택 필드는 뺀다."""
    return yaml.safe_dump(script.model_dump(mode="json", exclude_none=True), allow_unicode=True,
                          sort_keys=False, width=1000)


def _atomic_write_text(path: Path, data: str) -> None:
    """tmp write → fsync → atomic rename. source_intake.save_sources 와 같은 정책."""
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


def persist_script(project_id: str, script: Script, cfg: Optional[AppConfig] = None) -> Path:
    """`Script` 를 script.yaml 로 atomic 영속화."""
    cfg = cfg or load_config()
    path = script_path(project_id, cfg)
    _atomic_write_text(path, dump_script_yaml(script))
    return path


def load_script(project_id: str, cfg: Optional[AppConfig] = None) -> Script:
    """script.yaml → `Script`. 없으면 FileNotFoundError."""
    cfg = cfg or load_config()
    path = script_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"script.yaml 이 없습니다: {path}")
    return Script.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


__all__ = ["SCRIPT_FILENAME", "dump_script_yaml", "labels_path", "load_script", "persist_script", "script_path"]

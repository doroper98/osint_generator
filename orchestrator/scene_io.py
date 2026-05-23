"""scene_manifest.json 영속화 + 로딩 + build wiring (수직 슬라이스 V2, v0.10.0).

`scene_builder.build_scene_manifest` 는 순수 함수(I/O 없음). 본 모듈이 그 I/O 경계 —
full_script 로딩, scene_manifest.json 의 경로 SSOT · atomic 영속화 · 타입 로딩.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.scene_builder import build_scene_manifest
from orchestrator.script_io import load_full_script
from schemas.models import SceneManifest


SCENE_DIRNAME = "06_scene"
SCENE_MANIFEST_FILENAME = "scene_manifest.json"


def scene_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/06_scene/` 디렉토리."""
    return project_dir(project_id, cfg) / SCENE_DIRNAME


def scene_manifest_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/06_scene/scene_manifest.json` 경로."""
    return scene_dir(project_id, cfg) / SCENE_MANIFEST_FILENAME


def _atomic_write_text(path: Path, data: str) -> None:
    """tmp write → fsync → atomic rename. script_io._atomic_write_text 와 동일 정책."""
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


def persist_scene_manifest(
    project_id: str, manifest: SceneManifest, cfg: Optional[AppConfig] = None
) -> Path:
    """`SceneManifest` 를 `06_scene/scene_manifest.json` 으로 atomic 영속화."""
    cfg = cfg or load_config()
    path = scene_manifest_path(project_id, cfg)
    _atomic_write_text(path, manifest.model_dump_json(indent=2))
    return path


def load_scene_manifest(
    project_id: str, cfg: Optional[AppConfig] = None
) -> SceneManifest:
    """`06_scene/scene_manifest.json` 로드. 없으면 FileNotFoundError."""
    cfg = cfg or load_config()
    path = scene_manifest_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"scene_manifest.json 이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SceneManifest.model_validate(raw)


def build_and_persist_scene_manifest(
    project_id: str, cfg: Optional[AppConfig] = None
) -> SceneManifest:
    """full_script 로딩 → build_scene_manifest(순수) → scene_manifest.json 영속화.

    raises
    ------
    FileNotFoundError : full_script.json 없음.
    json.JSONDecodeError / pydantic.ValidationError : full_script 손상.
    """
    cfg = cfg or load_config()
    script = load_full_script(project_id, cfg)
    manifest = build_scene_manifest(script)
    persist_scene_manifest(project_id, manifest, cfg)
    return manifest


__all__ = [
    "scene_dir",
    "scene_manifest_path",
    "persist_scene_manifest",
    "load_scene_manifest",
    "build_and_persist_scene_manifest",
]

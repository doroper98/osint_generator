"""audio_manifest.json 영속화 + 로딩 + 경로 (수직 슬라이스 V4, v0.12.0).

나레이션 wav 는 `08_audio/narration/{segment_id}.wav` (gitignore), manifest 는
`08_audio/audio_manifest.json` (추적). 합성 로직(백엔드 호출)은 audio_service 에.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from schemas.models import AudioManifest


AUDIO_DIRNAME = "08_audio"
NARRATION_DIRNAME = "narration"
AUDIO_MANIFEST_FILENAME = "audio_manifest.json"


def audio_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return project_dir(project_id, cfg) / AUDIO_DIRNAME


def narration_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return audio_dir(project_id, cfg) / NARRATION_DIRNAME


def audio_manifest_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return audio_dir(project_id, cfg) / AUDIO_MANIFEST_FILENAME


def _atomic_write_text(path: Path, data: str) -> None:
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


def persist_audio_manifest(
    project_id: str, manifest: AudioManifest, cfg: Optional[AppConfig] = None
) -> Path:
    cfg = cfg or load_config()
    path = audio_manifest_path(project_id, cfg)
    _atomic_write_text(path, manifest.model_dump_json(indent=2))
    return path


def load_audio_manifest(
    project_id: str, cfg: Optional[AppConfig] = None
) -> AudioManifest:
    cfg = cfg or load_config()
    path = audio_manifest_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"audio_manifest.json 이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return AudioManifest.model_validate(raw)


__all__ = [
    "audio_dir",
    "narration_dir",
    "audio_manifest_path",
    "persist_audio_manifest",
    "load_audio_manifest",
]

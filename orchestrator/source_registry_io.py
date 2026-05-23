"""partials 로딩 + source_registry.json 영속화 (Phase 5, v0.5.5).

`orchestrator/source_registry_builder.py` 는 의도적으로 **순수 함수만** 제공합니다
(디스크 I/O 없음). 본 모듈은 그 builder 의 **I/O 경계** 입니다 — partial 파일
로딩과 `source_registry.json` 영속화를 담당하여 builder 의 순수성을 유지합니다.

결정론적 순서 (builder 계약)
----------------------------

`build_source_registry` 의 docstring 은 호출자가 **결정론적 순서** (recommended:
`task_id` 오름차순) 로 partial 을 넘길 것을 계약으로 요구합니다. `os.listdir` /
`Path.glob` 의 순서는 OS·파일시스템 의존적이므로, 본 모듈의 `load_partials` 는
파싱 후 `(task_id, 파일명)` 기준으로 정렬하여 builder 에 넘깁니다. 같은 입력
디렉토리에서 항상 같은 registry 가 나오도록 보장합니다.

fail-fast
---------

손상된 JSON / 스키마 위반 partial 은 조용히 건너뛰지 않고 예외를 전파합니다
(builder 의 fail-fast 철학과 동일). 호출자 (CLI) 가 잡아 사용자에게 보고합니다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.source_registry_builder import build_source_registry, partial_counter
from schemas.models import SourceCollectionPartial, SourceRegistry


SOURCES_DIRNAME = "02_sources"
PARTIALS_DIRNAME = "partials"
SOURCE_REGISTRY_FILENAME = "source_registry.json"


# ---------------------------------------------------------------------------
# 경로 헬퍼
# ---------------------------------------------------------------------------


def partials_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/02_sources/partials/` 디렉토리."""
    return project_dir(project_id, cfg) / SOURCES_DIRNAME / PARTIALS_DIRNAME


def source_registry_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/02_sources/source_registry.json` 경로."""
    return project_dir(project_id, cfg) / SOURCES_DIRNAME / SOURCE_REGISTRY_FILENAME


# ---------------------------------------------------------------------------
# atomic write
# ---------------------------------------------------------------------------


def _atomic_write_text(path: Path, data: str) -> None:
    """tmp write → fsync → atomic rename. project_manager._write_manifest 와 동일 정책.

    - Visibility: tmp 에 먼저 쓰고 `Path.replace` 로 교체 (동시 reader 가 half-written
      상태를 보지 못함).
    - Durability: flush + fsync 후 rename, 부모 디렉토리도 best-effort fsync.
    - 예외 안전: 실패 시 tmp 를 best-effort cleanup 하고 원본 예외 전파.
    """
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
        # Windows 등에서 directory fd fsync 미지원 — best-effort skip.
        pass


# ---------------------------------------------------------------------------
# 로딩 / 영속화
# ---------------------------------------------------------------------------


def load_partials(
    project_id: str, cfg: Optional[AppConfig] = None
) -> list[SourceCollectionPartial]:
    """`02_sources/partials/*.json` 을 로드 → `SourceCollectionPartial[]`.

    반환 순서는 **결정론적** — 파싱 후 `(task_id, 파일명)` 오름차순. builder 의
    caller-ordering 계약 (`task_id` asc) 을 충족합니다.

    partials 디렉토리가 없으면 빈 리스트 (collector 가 아직 실행되지 않은 상태).

    raise
    -----
    json.JSONDecodeError / pydantic.ValidationError
        손상된 partial 파일은 건너뛰지 않고 전파 (fail-fast).
    """
    cfg = cfg or load_config()
    pdir = partials_dir(project_id, cfg)
    if not pdir.exists():
        return []

    loaded: list[tuple[str, str, SourceCollectionPartial]] = []
    for path in pdir.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        partial = SourceCollectionPartial.model_validate(raw)
        loaded.append((partial.task_id, path.name, partial))

    # 결정론적 정렬: parsed task_id asc, tie-break 파일명. os.listdir/glob 의
    # OS 의존적 순서를 builder 에 그대로 넘기지 않는다.
    loaded.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in loaded]


def persist_source_registry(
    project_id: str, registry: SourceRegistry, cfg: Optional[AppConfig] = None
) -> Path:
    """`SourceRegistry` 를 `02_sources/source_registry.json` 으로 atomic 영속화.

    returns
    -------
    Path
        쓰여진 파일 경로.
    """
    cfg = cfg or load_config()
    path = source_registry_path(project_id, cfg)
    _atomic_write_text(path, registry.model_dump_json(indent=2))
    return path


def build_and_persist_source_registry(
    project_id: str,
    *,
    strict_input_item_id: bool = True,
    cfg: Optional[AppConfig] = None,
) -> tuple[SourceRegistry, dict[str, int]]:
    """partials 로딩 → build_source_registry → source_registry.json 영속화.

    builder 의 순수성을 깨지 않는 thin orchestration. I/O (로딩·쓰기) 는 본 모듈,
    병합·검증 로직은 builder 에 둡니다.

    parameters
    ----------
    strict_input_item_id : bool, default True
        builder 로 그대로 전달. pipeline production path 는 strict (None 거부).

    returns
    -------
    (SourceRegistry, dict[str, int])
        영속화된 registry 와 `partial_counter` 통계 (로그·검증용).

    raise
    -----
    ValueError
        builder 의 fail-fast invariant 위반 (충돌·정규화·버전 불일치 등).
    json.JSONDecodeError / pydantic.ValidationError
        partial 파일 손상.
    """
    cfg = cfg or load_config()
    partials = load_partials(project_id, cfg)
    registry = build_source_registry(
        project_id, partials, strict_input_item_id=strict_input_item_id
    )
    persist_source_registry(project_id, registry, cfg)
    return registry, partial_counter(partials)


__all__ = [
    "partials_dir",
    "source_registry_path",
    "load_partials",
    "persist_source_registry",
    "build_and_persist_source_registry",
]

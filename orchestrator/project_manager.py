"""Project Manager — ProjectManifest 의 생성·재개·전이 책임.

본 모듈은 `projects/{project_id}/project_manifest.json` 의 유일한 쓰기자입니다.
TUI / CLI 는 본 모듈을 통해서만 manifest 를 갱신합니다.

원칙
----
- `state_history` 는 append-only 입니다. 기존 항목 수정 금지.
- 모든 전이는 `state_machine.validate_transition` 을 통과해야 합니다.
- 디스크 쓰기는 항상 `updated_at` 을 갱신합니다.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.state_machine import validate_transition
from schemas.models import (
    Category,
    ProjectManifest,
    ProjectState,
    StateTransition,
)


logger = logging.getLogger(__name__)


MANIFEST_FILENAME = "project_manifest.json"

# project_id slug 정규식. 영문 소문자·숫자·하이픈·언더스코어를 허용하며,
# 첫 글자는 영문 소문자 또는 숫자여야 한다 (선두 `-` / `_` 차단).
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]*$")


def validate_project_id(project_id: str) -> str:
    """project_id slug 정책을 외부 호출 지점에서 강제하는 공개 가드.

    `new_project` 의 내부 검증을 web/CLI/외부 통합 코드에서 재사용할 수 있게 분리.
    v0.3.1: codex 4차 리뷰 C1 (web {project_id} path traversal) 의 구조적 조치.

    raises
    ------
    ValueError : project_id 가 _SLUG_RE 패턴에 맞지 않으면. 메시지에 사용자 입력 자체는
                 노출하지 않고 정책만 명시 (정찰 가치를 낮춤).
    """
    if not isinstance(project_id, str) or not _SLUG_RE.match(project_id):
        raise ValueError(
            "잘못된 project_id 입니다. "
            "영문 소문자·숫자·하이픈·언더스코어만 허용되며 첫 글자는 영숫자입니다."
        )
    return project_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 경로 헬퍼
# ---------------------------------------------------------------------------


def manifest_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return project_dir(project_id, cfg) / MANIFEST_FILENAME


def _ensure_project_layout(project_id: str, cfg: AppConfig) -> Path:
    """프로젝트 디렉토리 골격을 만듭니다. 이미 존재하면 그대로 둡니다."""
    pdir = project_dir(project_id, cfg)
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks").mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks" / "task_results").mkdir(parents=True, exist_ok=True)
    (pdir / "logs" / "workers").mkdir(parents=True, exist_ok=True)
    return pdir


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _write_manifest(manifest: ProjectManifest, cfg: AppConfig) -> Path:
    """manifest 를 디스크에 직렬화. 항상 updated_at 을 현재시간으로 갱신.

    Atomic **visibility** vs **durability** 를 분리해 보장:

    - Visibility (외부 reader 가 half-written 상태를 보지 못함):
      tmp 파일에 먼저 write 한 뒤 `Path.replace` 로 교체. POSIX `rename(2)`
      와 Windows `os.replace` 는 동일한 inode/path 교체 의미에서 atomic.
      이 단계까지만 보장하면 TUI 의 라이브 manifest reload 같은 동시 reader
      가 깨진 JSON 을 잠깐도 볼 수 없다.

    - Durability (전원장애·강제종료에도 마지막 write 가 살아남음):
      tmp write 직후 `flush()` + `os.fsync()` 로 데이터가 디스크 매체에 도달함을
      보장한 뒤 rename. 추가로 부모 디렉토리도 fsync (POSIX 한정, Windows 는
      `O_DIRECTORY` 미지원이라 best-effort skip) 해 rename 사실 자체도 durable.

    - 예외 안전: write 중간 실패 시 tmp 파일을 best-effort cleanup. `replace`
      이후의 tmp 는 이미 path 로 옮겨졌으므로 잔존 없음.
    """
    manifest.updated_at = utc_now()
    path = manifest_path(manifest.project_id, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = manifest.model_dump_json(indent=2)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        # 실패 시 leftover tmp 정리 (best-effort, 실패해도 원본 예외만 전파).
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise
    # 부모 디렉토리 fsync — rename 사실 자체를 durable 하게 만든다 (POSIX).
    # Windows 는 directory fd open 이 막혀있어 best-effort skip.
    # 실패는 흡수하되 (rename 자체는 이미 visible) 운영자에게 신호하기 위해
    # platform · errno 를 포함해 warning 로그를 남긴다. docstring 의 durability
    # 보장 문구와 runtime 현실의 어긋남을 가시화.
    try:
        dir_fd = os.open(path.parent, getattr(os, "O_DIRECTORY", os.O_RDONLY))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as e:
        logger.warning(
            "dir fsync 실패 (rename durability 약화 가능): "
            "path=%s platform=%s errno=%s msg=%s",
            path.parent,
            os.name,
            e.errno,
            e,
        )
    return path


def load_manifest(project_id: str, cfg: Optional[AppConfig] = None) -> ProjectManifest:
    """디스크의 project_manifest.json 을 읽어 ProjectManifest 로 검증."""
    cfg = cfg or load_config()
    path = manifest_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"project_manifest.json 이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ProjectManifest.model_validate(raw)


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


def new_project(
    project_id: str,
    title: str,
    category: Category | str,
    target_duration_min: int = 18,
    topic_summary: str = "",
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """새 프로젝트 manifest 를 생성·저장하고 반환합니다.

    - 이미 동일 project_id 가 존재하면 FileExistsError.
    - project_id 는 영문 소문자/숫자/하이픈/언더스코어만 허용.
    """
    cfg = cfg or load_config()

    validate_project_id(project_id)

    path = manifest_path(project_id, cfg)
    if path.exists():
        raise FileExistsError(
            f"이미 존재하는 프로젝트입니다: {project_id} (manifest: {path})"
        )

    cat = category if isinstance(category, Category) else Category(category)

    manifest = ProjectManifest(
        project_id=project_id,
        title=title,
        category=cat,
        target_duration_min=target_duration_min,
        topic_summary=topic_summary,
        current_state=ProjectState.CREATED,
        state_history=[],
    )

    _ensure_project_layout(project_id, cfg)
    _write_manifest(manifest, cfg)
    return manifest


def resume_project(
    project_id: str,
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """기존 프로젝트를 로드. manifest 가 없으면 FileNotFoundError.

    manifest 검증을 먼저 수행한 뒤 누락된 하위 폴더만 보강합니다
    (미존재 프로젝트로 resume 호출 시 빈 폴더가 생기는 것을 막기 위해).
    """
    cfg = cfg or load_config()
    manifest = load_manifest(project_id, cfg)
    _ensure_project_layout(project_id, cfg)
    return manifest


def transition_state(
    manifest: ProjectManifest,
    next_state: ProjectState | str,
    reason: str = "",
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """current_state 를 next_state 로 전이.

    잘못된 전이는 ValueError. state_history 에 append-only 로 기록 후 디스크 저장.
    """
    cfg = cfg or load_config()
    target = next_state if isinstance(next_state, ProjectState) else ProjectState(next_state)

    validate_transition(manifest.current_state, target)

    transition = StateTransition(
        from_state=manifest.current_state if isinstance(manifest.current_state, ProjectState)
        else ProjectState(manifest.current_state),
        to_state=target,
        transitioned_at=utc_now(),
        reason=reason,
    )

    manifest.state_history.append(transition)
    manifest.current_state = target

    _write_manifest(manifest, cfg)
    return manifest

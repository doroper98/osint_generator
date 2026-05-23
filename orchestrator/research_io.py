"""research_dossier.json 영속화 + 로딩 (Phase 6A, v0.8.0).

`source_registry_io.py` 의 I/O 경계 패턴을 답습한다. 도메인 판정/생성 로직은 두지
않고 (그것은 ResearchWorker 의 LLM 호출 책임), 본 모듈은 research_dossier.json 의
경로 SSOT · atomic 영속화 · 타입 로딩만 담당한다.

ResearchWorker 는 `BaseLLMWorker.output_path` 로 동일 경로(`research_dossier_path`)에
LLM 검증된 산출물을 직접 write 한다 (intake_planner 패턴). 본 모듈의
`persist_research_dossier` 는 비-LLM/프로그램적 생산자 및 테스트용 atomic writer 이고,
`load_research_dossier` 는 CLI 가 전이 전 디스크 검증 게이트로 쓰며 6B Evidence Guard
의 입력 로더로도 재사용된다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from schemas.models import ResearchDossier


RESEARCH_DIRNAME = "04_research"
RESEARCH_DOSSIER_FILENAME = "research_dossier.json"


# ---------------------------------------------------------------------------
# 경로 헬퍼
# ---------------------------------------------------------------------------


def research_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/04_research/` 디렉토리."""
    return project_dir(project_id, cfg) / RESEARCH_DIRNAME


def research_dossier_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/04_research/research_dossier.json` 경로."""
    return research_dir(project_id, cfg) / RESEARCH_DOSSIER_FILENAME


# ---------------------------------------------------------------------------
# atomic write (source_registry_io._atomic_write_text 와 동일 정책)
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


def persist_research_dossier(
    project_id: str, dossier: ResearchDossier, cfg: Optional[AppConfig] = None
) -> Path:
    """`ResearchDossier` 를 `04_research/research_dossier.json` 으로 atomic 영속화.

    returns
    -------
    Path
        쓰여진 파일 경로.
    """
    cfg = cfg or load_config()
    path = research_dossier_path(project_id, cfg)
    _atomic_write_text(path, dossier.model_dump_json(indent=2))
    return path


def load_research_dossier(
    project_id: str, cfg: Optional[AppConfig] = None
) -> ResearchDossier:
    """`04_research/research_dossier.json` 을 로드 → `ResearchDossier`.

    raise
    -----
    FileNotFoundError
        dossier 파일이 아직 없음 (ResearchWorker 미실행).
    json.JSONDecodeError / pydantic.ValidationError
        손상된 dossier 파일은 건너뛰지 않고 전파 (fail-fast).
    """
    cfg = cfg or load_config()
    path = research_dossier_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"research_dossier.json 이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ResearchDossier.model_validate(raw)


__all__ = [
    "research_dir",
    "research_dossier_path",
    "persist_research_dossier",
    "load_research_dossier",
]

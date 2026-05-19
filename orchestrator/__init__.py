"""Orchestrator 패키지.

본 패키지의 __version__ 은 저장소 root 의 VERSION 파일을 SSOT 로 따릅니다.
커밋 메시지 prefix (vX.Y.Z:) 와 일치해야 합니다 (.githooks/commit-msg).
"""

from __future__ import annotations

from pathlib import Path


def _read_version() -> str:
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "0.0.0"


__version__: str = _read_version()

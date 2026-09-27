"""영상 규칙 SSOT 로더 (v2.0.0, docs/handoff/15 §3 P3).

코드·프롬프트·린트·검증기가 모두 `rules/video_rules.yaml` 한 파일을 읽는다.
규칙 값을 모듈 상수로 다시 적지 않는다 (tests/anti_inertia/test_single_config).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from schemas.rules_models import VideoRules

RULES_PATH: Path = Path(__file__).resolve().parent / "video_rules.yaml"


def load_rules(path: Path | None = None) -> VideoRules:
    """규칙 파일을 읽어 `VideoRules`(extra=forbid)로 검증해 반환한다.

    파일이 없거나 모르는 키가 있으면 예외 — 기본값으로 조용히 폴백하지 않는다 (15 P6).
    """
    target = path or RULES_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    return VideoRules.model_validate(raw)


def rules_hash(path: Path | None = None) -> str:
    """규칙 파일 바이트의 sha1 (provenance `rules_hash`, 15 P5)."""
    target = path or RULES_PATH
    return hashlib.sha1(target.read_bytes()).hexdigest()

"""미디어 레지스트리 로더 (v2.5.5, D-0036 작업 2) — `rules media_beats.registry` 한 파일을 `MediaAsset` 로 검증한다.

필드 누락·자료사진 표기 없음·사상자 체크 불일치 등 스키마 위반은 RightsError(C9, 15 P6). 조용히 빼지 않는다.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from engine.credits import RightsError
from rules import load_rules
from schemas.media_models import MediaAsset, MediaRegistryFile

REPO = Path(__file__).resolve().parent.parent


def registry_path() -> Path:
    return REPO / load_rules().media_beats.registry


def load_media_registry(path: Path | None = None) -> dict[str, MediaAsset]:
    p = path or registry_path()
    if not p.exists():
        raise RightsError(f"미디어 레지스트리 없음: {p}")
    try:
        return MediaRegistryFile.model_validate(json.loads(p.read_text(encoding="utf-8"))).assets
    except ValidationError as ex:
        raise RightsError(f"미디어 레지스트리 권리·필드 오류({p.name}):\n{ex}") from ex


@lru_cache(maxsize=None)
def cached_registry() -> dict[str, MediaAsset]:
    """기본 레지스트리 1회 로드 — 카드 영역 계산처럼 자산 객체 없이 문구가 필요한 곳(RESERVED)."""
    return load_media_registry()


def credit_line(asset: MediaAsset) -> str:
    return asset.credit_line(load_rules().media_beats.credit_formats[asset.kind])

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


# ── v7.4.0 전쟁사 W2(D-0600 §2-2) — 작품(period_art) 캡션: 당대/후대 라벨 줄·"…로 추정되는" (코드 조판) ──
_DATE_AT: list = [None]   # 시각 t → 그 시각 문장 날짜 문자열. engine.project.load_project 가 정한다(없으면 라벨 없음 → [period-art-label-missing])


def configure_sentence_dates(date_at) -> None:  # noqa: ANN001 — Callable[[float], str | None]
    _DATE_AT[0] = date_at


def media_caption_text(asset: MediaAsset) -> str:
    """화면 캡션 — 작품 동정이 불확실하면 '…로 추정되는' 을 앞에(schemas.war_history.probable_caption)."""
    from schemas.war_history import probable_caption  # noqa: PLC0415

    return probable_caption(asset.caption, getattr(asset, "identification", None), getattr(asset, "identified_as", None))


def era_label(asset: MediaAsset, e: dict | None) -> str | None:
    """작품 비트의 당대/후대 라벨(작품 아니면 None)."""
    if getattr(asset, "kind", None) != "period_art" or e is None or _DATE_AT[0] is None:
        return None
    from schemas.era_date import is_era_date, parse_era_date  # noqa: PLC0415
    from schemas.war_history import period_art_label  # noqa: PLC0415

    raw = _DATE_AT[0](float(e.get("t0", 0.0)))
    return period_art_label(asset.created, parse_era_date(raw) if raw and is_era_date(raw) else None)


def media_credit(asset: MediaAsset, e: dict | None = None) -> str:
    """화면 출처 줄 — 작품이면 앞에 당대/후대 라벨(rules war_history.period_art.labels.sep 로 잇는다). 그 밖은 credit_line 그대로."""
    lab = era_label(asset, e)
    base = credit_line(asset)
    return base if lab is None else lab + load_rules().war_history.period_art.labels.sep + base

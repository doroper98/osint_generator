"""구성 레코드 로더 (v7.4.0, back_and_forth D-1003 §2·§3).

`data/categorical/<record_id>.yaml` → `schemas.data_models.CategoricalRecord`. 폴더는 `rules data.categorical_dir`.
원본 파일(`raw/<source_file.path>`)이 있으면 sha1 을 다시 재고 다르면 오류(15 P6). 원본이 저장소에 없으면
(용량 — artifacts 보관) `raw_checked False` 로 돌려준다 — provenance 에 그대로 남긴다(조용히 통과로 적지 않는다).
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from rules import load_rules
from schemas.data_models import CategoricalRecord

REPO = Path(__file__).resolve().parent.parent


class CategoricalError(ValueError):
    """레코드 없음·형식 오류·원본 지문 불일치(15 P6)."""


def categorical_dir() -> Path:
    return REPO / load_rules().data.categorical_dir


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()  # noqa: S324 — 무결성 지문(보안 용도 아님)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_categorical(raw: object, where: str = "<memory>") -> CategoricalRecord:
    try:
        return CategoricalRecord.model_validate(raw)
    except ValidationError as ex:
        raise CategoricalError(f"{where}: {ex}") from ex


@lru_cache(maxsize=None)
def _load(record_id: str, folder: str) -> tuple[CategoricalRecord, Optional[bool]]:
    d = Path(folder)
    p = d / f"{record_id}.yaml"
    if not p.exists():
        raise CategoricalError(f"구성 레코드 없음: {p}")
    rec = parse_categorical(yaml.safe_load(p.read_text(encoding="utf-8")), str(p))
    if rec.record_id != record_id:
        raise CategoricalError(f"{p}: record_id {rec.record_id!r} ≠ 파일 이름 {record_id!r}")
    raw = d / "raw" / rec.source_file.path
    checked: Optional[bool] = None
    if raw.exists():
        got = sha1_of(raw)
        if got != rec.source_file.sha1:
            raise CategoricalError(f"{p}: 원본 {raw.name} sha1 {got} ≠ 레코드 {rec.source_file.sha1}(원본이 바뀌었다, P6)")
        checked = True
    return rec, checked


def load_categorical(record_id: str, folder: Optional[Path] = None) -> CategoricalRecord:
    return _load(record_id, str(folder or categorical_dir()))[0]


def raw_checked(record_id: str, folder: Optional[Path] = None) -> Optional[bool]:
    """원본 sha1 대조 결과 — True = 대조 통과, None = 원본이 저장소에 없음(provenance 에 그대로)."""
    return _load(record_id, str(folder or categorical_dir()))[1]


__all__ = ["CategoricalError", "categorical_dir", "load_categorical", "parse_categorical", "raw_checked", "sha1_of"]

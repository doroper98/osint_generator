"""장르 프로필 로더 (v4.2.0, docs/handoff/20 §3, back_and_forth D-0081 작업 1).

`genres/<genre>.yaml` → `schemas.genre_models.GenreProfile`. 파일이 없거나, 파일 이름과 `genre` 가 다르거나,
미등록 무대·요소·검사를 참조하면 오류다 — 기본 프로필로 조용히 넘어가지 않는다(15 P6·P10).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from schemas.genre_models import GenreProfile

GENRES_DIR: Path = Path(__file__).resolve().parent
DEFAULT_GENRE = "geopolitics"   # direction.yaml 에 genre 가 없을 때(v3 원본 direction 무수정 원칙 D-0056). provenance 에 declared false


class GenreError(ValueError):
    """장르 프로필 없음·형식 오류·미등록 참조(15 P6·P10)."""


def genre_path(name: str, root: Path | None = None) -> Path:
    return (root or GENRES_DIR) / f"{name}.yaml"


def load_genre_file(path: Path) -> GenreProfile:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as ex:
        raise GenreError(f"{path}: {ex}") from ex
    try:
        prof = GenreProfile.model_validate(raw)
    except ValidationError as ex:
        raise GenreError(f"{path}: {ex}") from ex
    if prof.genre != path.stem:
        raise GenreError(f"{path}: genre {prof.genre!r} ≠ 파일 이름 {path.stem!r}")
    return prof


@lru_cache(maxsize=None)
def load_genre(name: str) -> GenreProfile:
    """이름 → 프로필(genres/<name>.yaml). 없는 장르 = GenreError."""
    p = genre_path(name)
    if not p.exists():
        have = sorted(x.stem for x in GENRES_DIR.glob("*.yaml"))
        raise GenreError(f"장르 프로필 없음 {name!r} — genres/: {have}")
    return load_genre_file(p)


def genre_names() -> list[str]:
    return sorted(p.stem for p in GENRES_DIR.glob("*.yaml"))


__all__ = ["DEFAULT_GENRE", "GENRES_DIR", "GenreError", "genre_names", "genre_path", "load_genre", "load_genre_file"]

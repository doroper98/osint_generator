"""장르 프로필 로더 (v4.2.0, docs/handoff/20 §3, back_and_forth D-0081 작업 1).

`genres/<genre>.yaml` → `schemas.genre_models.GenreProfile`. 파일이 없거나, 파일 이름과 `genre` 가 다르거나,
미등록 무대·요소·검사를 참조하면 오류다 — 기본 프로필로 조용히 넘어가지 않는다(15 P6·P10).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

from schemas.genre_models import GenreProfile

if TYPE_CHECKING:
    from schemas.order_models import Order

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


ORDER_FILE = "order.yaml"   # v4.4.0 — 주문(docs/handoff/20 §11, schemas/order_models.py)


def load_order(pdir: Path) -> "Order | None":
    """프로젝트 주문 파일 → Order. 파일이 없으면 None(지정학 기존 프로젝트). 형식 오류 = GenreError."""
    from schemas.order_models import Order  # noqa: PLC0415

    p = pdir / ORDER_FILE
    if not p.exists():
        return None
    try:
        return Order.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
    except (yaml.YAMLError, ValidationError) as ex:
        raise GenreError(f"{p}: {ex}") from ex


def project_genre(pdir: Path) -> tuple[GenreProfile, bool]:
    """프로젝트 장르(v4.4.0 D-0090 작업 1) — (프로필, 주문에 선언했는가). 주문이 없으면 DEFAULT_GENRE·False.
    원고·리서치 단계는 direction 이 아직 없으므로 주문이 장르의 단일 출처다."""
    order = load_order(pdir)
    if order is None:
        return load_genre(DEFAULT_GENRE), False
    return load_genre(order.genre), True


def genre_names() -> list[str]:
    return sorted(p.stem for p in GENRES_DIR.glob("*.yaml"))


__all__ = ["DEFAULT_GENRE", "GENRES_DIR", "ORDER_FILE", "GenreError", "genre_names", "genre_path", "load_genre", "load_genre_file",
           "load_order", "project_genre"]

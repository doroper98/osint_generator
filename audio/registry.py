"""BGM 레지스트리 (v3.4.0, back_and_forth D-0060 작업 1, 10 §7-1).

`assets/audio/bgm/registry.yaml` 이 음악 권리·표기의 SSOT 다. 엔딩 카드·설명란 음악 문구, 권리 레지스트리 `music` 절,
direction `sound.bgm` id → 파일 해석이 모두 여기서 나온다. 없는 id·쓸 수 없는 곡(available false)·sha1 불일치 = 오류(P6·P10).
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

REPO = Path(__file__).resolve().parent.parent
BGM_DIR = REPO / "assets" / "audio" / "bgm"
REGISTRY = BGM_DIR / "registry.yaml"
PREFIX = "music."


class BgmError(ValueError):
    pass


class BgmTrack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str
    sha1: Optional[str] = None
    duration_sec: Optional[float] = None
    name: str
    author: str
    license: str
    url: str
    attribution: str                       # 작가 표준 표기(RIGHTS.md 그대로)
    source: str
    mood: list[str] = Field(default_factory=list)
    bpm: Optional[float] = None
    available: bool

    @model_validator(mode="after")
    def _measured(self) -> "BgmTrack":
        if self.available and (self.sha1 is None or self.duration_sec is None):
            raise ValueError(f"{self.file}: available 인 곡은 sha1·duration_sec 실측값이 있어야 한다")
        return self


class BgmRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    tracks: dict[str, BgmTrack] = Field(min_length=1)

    @model_validator(mode="after")
    def _ids(self) -> "BgmRegistry":
        bad = [k for k in self.tracks if not k.startswith(PREFIX)]
        if bad:
            raise ValueError(f"BGM id 는 '{PREFIX}<이름>' 형식(credits 권리 키와 같음): {bad}")
        return self


@lru_cache(maxsize=None)
def load_registry(path: Path = REGISTRY) -> BgmRegistry:
    return BgmRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def track(bgm_id: str) -> BgmTrack:
    reg = load_registry()
    if bgm_id not in reg.tracks:
        raise BgmError(f"BGM 레지스트리에 없는 id: {bgm_id!r} — 등재: {sorted(reg.tracks)} (assets/audio/bgm/registry.yaml)")
    return reg.tracks[bgm_id]


def bgm_path(bgm_id: str, verify: bool = True) -> Path:
    """id → 파일. 쓸 수 없는 곡·파일 없음·sha1 불일치 = 오류(조용히 다른 곡을 쓰지 않는다)."""
    t = track(bgm_id)
    if not t.available:
        raise BgmError(f"{bgm_id}: 레지스트리에 있으나 파일이 없는 곡(available: false)")
    p = BGM_DIR / t.file
    if not p.exists():
        raise BgmError(f"{bgm_id}: 파일 없음 {p} — `python tools/fetch_data.py bgm`")
    if verify and hashlib.sha1(p.read_bytes()).hexdigest() != t.sha1:
        raise BgmError(f"{bgm_id}: sha1 불일치 — {p}")
    return p


def rights_music() -> dict[str, dict]:
    """권리 레지스트리 `music` 절(키 = id 에서 'music.' 을 뗀 이름) — 프로젝트 rights_registry.json 의 music 절 대신 쓴다."""
    return {k[len(PREFIX):]: {"name": t.name, "license": t.license, "author": t.author, "url": t.url}
            for k, t in load_registry().tracks.items()}


def card_line(bgm_id: str, fmt: str) -> tuple[str, str]:
    """엔딩 카드 (제목, 라이선스 줄). fmt 는 rules credits.music_card_license(.replace 자리표시 {author}·{license})."""
    t = track(bgm_id)
    return t.name, fmt.replace("{author}", t.author).replace("{license}", t.license)


def description_line(bgm_id: str, fmt: str) -> str:
    """설명란 음악 문구. fmt 는 rules credits.music_description(자리표시 {name}·{author}·{license})."""
    t = track(bgm_id)
    return fmt.replace("{name}", t.name).replace("{author}", t.author).replace("{license}", t.license)


__all__ = ["BGM_DIR", "BgmError", "BgmRegistry", "BgmTrack", "bgm_path", "card_line", "description_line", "load_registry",
           "rights_music", "track"]

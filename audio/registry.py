"""BGM 레지스트리 (v3.4.0, back_and_forth D-0060 작업 1, 10 §7-1).

`assets/audio/bgm/registry.yaml` 이 음악 권리·표기의 SSOT 다. 엔딩 카드·설명란 음악 문구, 권리 레지스트리 `music` 절,
direction `sound.bgm` id → 파일 해석이 모두 여기서 나온다. 없는 id·쓸 수 없는 곡(available false)·sha1 불일치 = 오류(P6·P10).
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from audio.bgm_measure import BgmMeasure, floor_failures

REPO = Path(__file__).resolve().parent.parent
BGM_DIR = REPO / "assets" / "audio" / "bgm"
REGISTRY = BGM_DIR / "registry.yaml"
PREFIX = "music."
# v5.22.2 UF-16·30·93(D-0205 §3) — 음악 없음(sound.bgm null)의 결정 번호. 연출(engine.direction.Sound)과 믹서(audio.mix.Sound)가
# 같은 정의를 쓴다(한 곳, P3) — 믹서 쪽에 칸이 없어 음악 없는 영상이 audio.mix 에서 extra_forbidden 으로 실패했다(UF-207 렌더 중 발견).
NoMusicDecision = Annotated[Optional[str], Field(pattern=r"^D-?\d{2,4}")]


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
    measured: Optional[BgmMeasure] = None          # v7.2.0 UF-100 D-0222 — audio.bgm_measure 실측(0~360초). available 곡 필수·하한 통과
    source_url: Optional[str] = None               # 파일을 받은 곳(fetch_data bgm 이 sha1 대조로 복원)
    unavailable_reason: Optional[str] = None       # available false 인 사유(사용 금지 등)
    # v7.4.0 UF-910(D923) — 사용자 제공 곡. floor_waiver = 등록 하한을 면제한 사용자 결정(사유 글), bed_gain_scale = 이 곡만 음악 베드 음량 배율(0 < x ≤ 1),
    # noncommercial = 비상업 이용만 되는 곡(연출 sound.noncommercial_ok 결정 번호 없이는 못 쓴다 — require_noncommercial_ok)
    floor_waiver: Optional[str] = Field(default=None, min_length=1)
    bed_gain_scale: Optional[float] = Field(default=None, gt=0, le=1)
    noncommercial: bool = False

    @model_validator(mode="after")
    def _measured(self) -> "BgmTrack":
        if self.available and (self.sha1 is None or self.duration_sec is None):
            raise ValueError(f"{self.file}: available 인 곡은 sha1·duration_sec 실측값이 있어야 한다")
        if self.available and self.measured is None:
            raise ValueError(f"{self.file}: available 인 곡은 measured(audio.bgm_measure 실측)가 있어야 한다 — UF-100 등록 하한")
        if self.available and self.floor_waiver is None and (bad := floor_failures(self.measured)):   # type: ignore[arg-type]
            raise ValueError(f"{self.file}: BGM 등록 하한 미달 {bad} — rules audio.bgm_floor(UF-100). 사용자가 직접 고른 곡이면 floor_waiver 에 결정을 적는다")
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


def bed_scale(bgm_id: str) -> float:
    """이 곡의 음악 베드 음량 배율(없으면 1.0) — audio.mix 가 곡을 읽을 때 곱한다(v7.4.0 UF-910 D923)."""
    s = track(bgm_id).bed_gain_scale
    return 1.0 if s is None else s


def require_noncommercial_ok(bgm_ids: list[str], ok: Optional[str]) -> None:
    """비상업 이용만 되는 곡(noncommercial)을 쓰려면 연출 sound.noncommercial_ok 에 "이 영상은 수익화하지 않는다"는 사용자 결정 번호가
    있어야 한다. 없으면 오류(조용히 쓰지 않는다 — C9·P6). 연출(engine.direction.Sound)과 믹서(audio.mix.Sound)가 같이 부른다."""
    bad = [i for i in bgm_ids if track(i).noncommercial]
    if bad and not ok:
        raise BgmError(f"비상업 전용 곡 {bad} — 수익화 영상에는 쓸 수 없다. 수익화하지 않는 영상이면 direction sound.noncommercial_ok 에 "
                       "사용자 결정 번호를 적는다(assets/audio/bgm/RIGHTS.md)")


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


__all__ = ["BGM_DIR", "BgmError", "BgmRegistry", "BgmTrack", "bed_scale", "bgm_path", "card_line", "description_line", "load_registry",
           "require_noncommercial_ok", "rights_music", "track"]

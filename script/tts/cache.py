"""TTS 캐시 키 (v2.1.0, plan3 build 의 sha1). 같은 발음 텍스트·같은 목소리 = 같은 파일(결정성).

v5.11.0(D-0152 D147 §5): Supertonic 은 `script.tts.supertonic.cache_salt`(`|st|스타일|속도|단계|…`).
v5.23.0 V4(D-0212): edge 백엔드 삭제 — `|edge|` 키 갈래도 지웠다(Supertonic·ElevenLabs 키는 그대로).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def cache_key(tts: str, eleven_voice_id: str | None, supertonic_salt: str | None = None) -> str:
    if supertonic_salt is not None:
        salt = supertonic_salt
    elif eleven_voice_id is not None:
        salt = "|el|" + eleven_voice_id
    else:
        salt = ""
    return hashlib.sha1((tts + salt).encode()).hexdigest()[:10]


def mp3_path(tts_dir: Path, sid: str, key: str) -> Path:
    return tts_dir / f"{sid}_{key}.mp3"


def cached(p: Path) -> bool:
    return p.exists() and os.path.getsize(p) > 1000

"""TTS 캐시 키 (v2.1.0, plan3 build 의 sha1). 같은 발음 텍스트·같은 목소리 = 같은 파일(결정성)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def cache_key(tts: str, eleven_voice_id: str | None) -> str:
    salt = "|el|" + eleven_voice_id if eleven_voice_id is not None else ""
    return hashlib.sha1((tts + salt).encode()).hexdigest()[:10]


def mp3_path(tts_dir: Path, sid: str, key: str) -> Path:
    return tts_dir / f"{sid}_{key}.mp3"


def cached(p: Path) -> bool:
    return p.exists() and os.path.getsize(p) > 1000

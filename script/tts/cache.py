"""TTS 캐시 키 (v2.1.0, plan3 build 의 sha1). 같은 발음 텍스트·같은 목소리 = 같은 파일(결정성).

v2.3.0: config 기본이 아닌 edge 목소리는 `|edge|{voice}`로 구분한다. 기본 목소리 키는 v3 와 같다(sha1(tts)) —
이전에는 edge 목소리를 바꿔도 같은 키라 옛 목소리 mp3 를 조용히 재사용했다(15 P6).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def cache_key(tts: str, eleven_voice_id: str | None, edge_voice: str | None = None) -> str:
    if eleven_voice_id is not None:
        salt = "|el|" + eleven_voice_id
    elif edge_voice is not None:
        salt = "|edge|" + edge_voice
    else:
        salt = ""
    return hashlib.sha1((tts + salt).encode()).hexdigest()[:10]


def mp3_path(tts_dir: Path, sid: str, key: str) -> Path:
    return tts_dir / f"{sid}_{key}.mp3"


def cached(p: Path) -> bool:
    return p.exists() and os.path.getsize(p) > 1000

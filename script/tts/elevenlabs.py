"""ElevenLabs with-timestamps 백엔드 (v2.1.0, plan3 `eleven_one`). 구조만 — 정렬 사용·trim_offset 은 Phase 4.

API 키·voice id 는 .env(환경 변수)로만 받는다(C9). 모델·voice_settings 는 config.yaml tts.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from orchestrator.config import load_config


def available() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY") and os.environ.get("ELEVENLABS_VOICE_ID"))


def voice_id() -> str:
    return os.environ["ELEVENLABS_VOICE_ID"]


def eleven_one(text: str, path: Path, prev_text: str | None, next_text: str | None) -> None:
    import requests  # noqa: PLC0415

    cfg = load_config().tts
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id()}/with-timestamps",
                      headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}, timeout=120,
                      json=dict(text=text, model_id=os.environ.get(cfg.eleven_model_env, cfg.eleven_model_default),
                                previous_text=prev_text, next_text=next_text,
                                voice_settings=cfg.voice_settings.model_dump()))
    r.raise_for_status()
    d = r.json()
    path.write_bytes(base64.b64decode(d["audio_base64"]))
    Path(str(path) + ".align.json").write_text(json.dumps(d.get("alignment")), encoding="utf-8")

"""ElevenLabs with-timestamps 백엔드 (v2.3.0, plan3 `eleven_one`, 03 §6, back_and_forth D-0021 작업 3).

- `/v1/text-to-speech/{voice_id}/with-timestamps` 로 음성과 글자별 정렬을 함께 받는다.
- 앞뒤 문장을 `previous_text`/`next_text`로 보내 문장 사이 억양을 잇는다.
- `voice_settings`·모델은 config.yaml `tts`(15 P3). 캐시 키는 `sha1(tts + '|el|' + voice_id)`(script/tts/cache).
- 정렬은 `{mp3}.align.json`(script/tts/align 공통 형식, 출처 elevenlabs_timestamps)에 **alignment 만** 저장한다 — audio_base64·요청 헤더·voice_id 는 쓰지 않는다(D-0022, C9).

API 키·voice id 는 환경 변수로만 받는다(C9). 어떤 파일에도 쓰지 않는다.

v5.13.0(D-0153 Q0, 가이드 23 §19 P0): 유료 호출 차단은 `require_allowed()` 한 곳 — plan·`eleven_one`·`tools/tts_align_probe.py` 가
요청·키 접근·파일 생성 전에 부른다. 키가 있어도 `config tts.elevenlabs_allowed: false` 면 호출하지 않는다(사용자 결정 D127, PIPELINE-AP-020).
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from orchestrator.config import load_config
from script.tts import align

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"


class ElevenLabsRefused(ValueError):
    pass


def require_allowed() -> None:
    """유료 TTS(ElevenLabs) 차단 — 허용이 아니면 오류. 다른 백엔드로 자동 전환하지 않는다(P6)."""
    if not load_config().tts.elevenlabs_allowed:
        raise ElevenLabsRefused("--tts elevenlabs 거부 — 사용자 결정(2026-10-05): ElevenLabs 음성을 쓰지 않는다"
                                "(config tts.elevenlabs_allowed: false). 콘티 판·본편 모두 기본 백엔드(config tts.backend_default)")


def available() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY") and os.environ.get("ELEVENLABS_VOICE_ID"))


def voice_id() -> str:
    return os.environ["ELEVENLABS_VOICE_ID"]


def voice_label() -> str:
    """plan.voice·provenance 용. voice_id 는 앞 4자만(D-0022)."""
    return f"elevenlabs:{voice_id()[:4]}…"


def request_body(text: str, prev_text: str | None, next_text: str | None) -> dict:
    cfg = load_config().tts
    body: dict = dict(text=text, model_id=os.environ.get(cfg.eleven_model_env, cfg.eleven_model_default),
                      voice_settings=cfg.voice_settings.model_dump())
    if prev_text:
        body["previous_text"] = prev_text
    if next_text:
        body["next_text"] = next_text
    return body


def eleven_one(text: str, path: Path, prev_text: str | None, next_text: str | None) -> None:
    require_allowed()   # 요청·키 접근 전(유료 호출 차단, D-0153 Q0)
    import requests  # noqa: PLC0415

    r = requests.post(API.format(voice=voice_id()), headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                      timeout=120, json=request_body(text, prev_text, next_text))
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs HTTP {r.status_code}: {r.text[:200]}")
    d = r.json()
    alignment = d.get("alignment")
    if not alignment or not alignment.get("characters"):
        raise RuntimeError("ElevenLabs 응답에 alignment 가 없다(with-timestamps)")
    path.write_bytes(base64.b64decode(d["audio_base64"]))
    align.write(path, align.from_elevenlabs(alignment))

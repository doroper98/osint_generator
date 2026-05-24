"""교체 가능한 TTS 백엔드 (수직 슬라이스 V4, v0.12.0).

`BaseLLMWorker` 가 claude/codex 를 `llm_backend` 로 바꾸듯, TTS 도 백엔드를 갈아끼운다.

- `stub`       : 무음 wav 를 텍스트 길이 기반 추정 길이로 생성. 엔진/네트워크 불필요 →
                 단위테스트·CI 전용. (`OSINT_TTS_STUB=1` 와 동일 목적의 명시 백엔드.)
- `local`      : 사용자 머신의 로컬 음성복제 TTS CLI 를 subprocess 로 호출 (프라이버시·
                 무료·기본 권장). 명령 템플릿은 `OSINT_TTS_CMD` 환경변수
                 (placeholder: {text} {out} {voice}). wav 산출 가정.
- `elevenlabs` : ElevenLabs HTTP API (고품질·외부 전송 — 로컬 보장 깨짐, opt-in).
                 `ELEVENLABS_API_KEY` (필수), `ELEVENLABS_VOICE_ID` 환경변수.

모든 백엔드의 계약: `synthesize(text, out_path, voice) -> duration_sec`. out_path 는
wav 로 쓰며 길이(초)를 반환한다. 길이는 scene/render 타이밍의 권위 소스가 된다.

C9/ADDENDUM_04 관계: 본 모듈은 LLM 호출이 아니라 TTS 다. 기본값 `local` 은 외부 전송이
없어 프라이버시 원칙과 합치한다. `elevenlabs` 는 사용자가 명시적으로 선택할 때만 외부
API 를 쓰며 키는 환경변수로만 읽고 커밋하지 않는다 (C9).
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import wave
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


# 한국어 나레이션 대략 분당 320자 (script_worker 프롬프트 가정과 동일) → 초당 ≈ 5.33자.
CHARS_PER_SEC: float = 320.0 / 60.0
STUB_SAMPLE_RATE: int = 16000


class TTSError(RuntimeError):
    """TTS 백엔드 실패 (미설정/네트워크/엔진 오류)."""


class TTSBackend(ABC):
    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str, out_path: Path, voice: Optional[str]) -> float:
        """text 를 음성으로 합성해 out_path(wav)에 쓰고 길이(초)를 반환."""


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------


def _wav_duration_sec(path: Path) -> float:
    """wav 파일 길이(초). wav 가 아니면 TTSError."""
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as w:
            frames = w.getnframes()
            rate = w.getframerate() or 1
            return frames / float(rate)
    except (wave.Error, EOFError) as e:
        raise TTSError(f"wav 길이 측정 실패: {path} ({e})") from e


def _estimate_duration_sec(text: str) -> float:
    """텍스트 길이 기반 추정 길이 (stub 용)."""
    n = len((text or "").strip())
    return max(0.8, round(n / CHARS_PER_SEC, 3))


def _write_silent_wav(path: Path, duration_sec: float, sample_rate: int = STUB_SAMPLE_RATE) -> None:
    """duration_sec 길이의 무음 mono 16-bit wav 작성."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = max(1, int(duration_sec * sample_rate))
    with contextlib.closing(wave.open(str(path), "wb")) as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00" * n_frames)


def _write_pcm16_as_wav(path: Path, pcm: bytes, sample_rate: int) -> float:
    """16-bit mono PCM 바이트를 wav 로 감싸 쓰고 길이(초) 반환."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.closing(wave.open(str(path), "wb")) as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return len(pcm) / float(2 * sample_rate)


# ---------------------------------------------------------------------------
# 백엔드 구현
# ---------------------------------------------------------------------------


class StubTTSBackend(TTSBackend):
    """무음 wav (테스트 전용). 엔진/네트워크 불필요."""

    name = "stub"

    def synthesize(self, text: str, out_path: Path, voice: Optional[str]) -> float:
        duration = _estimate_duration_sec(text)
        _write_silent_wav(out_path, duration)
        return duration


class LocalTTSBackend(TTSBackend):
    """로컬 음성복제 TTS CLI subprocess (기본 권장 — 프라이버시·무료).

    명령은 `OSINT_TTS_CMD` 환경변수의 템플릿으로 정의 (예:
    `mytts --text {text} --speaker ref.wav --out {out}`). placeholder: {text}/{out}/{voice}.
    엔진이 wav 를 out 경로에 쓴다고 가정하고, 그 길이를 측정해 반환한다.
    """

    name = "local"
    invoke_timeout_sec = 600

    def synthesize(self, text: str, out_path: Path, voice: Optional[str]) -> float:
        template = os.environ.get("OSINT_TTS_CMD")
        if not template:
            raise TTSError(
                "local TTS 백엔드는 OSINT_TTS_CMD 환경변수가 필요합니다 "
                "(예: 'mytts --text {text} --out {out}'). "
                "또는 --backend stub/elevenlabs 를 사용하십시오."
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # shlex 로 토큰화한 뒤 placeholder 치환 (.replace() — C2 정신, 셸 인젝션 회피).
        import shlex

        cmd = [
            tok.replace("{text}", text)
            .replace("{out}", str(out_path))
            .replace("{voice}", voice or "")
            for tok in shlex.split(template)
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.invoke_timeout_sec, check=False,
            )
        except FileNotFoundError as e:
            raise TTSError(f"local TTS 명령 실행 불가: {e}") from e
        except subprocess.TimeoutExpired as e:
            raise TTSError(f"local TTS 타임아웃: {e}") from e
        if proc.returncode != 0:
            raise TTSError(
                f"local TTS 실패 (exit {proc.returncode}): {(proc.stderr or '')[:300]}"
            )
        if not out_path.exists():
            raise TTSError(f"local TTS 가 출력 파일을 만들지 않음: {out_path}")
        return _wav_duration_sec(out_path)


class ElevenLabsTTSBackend(TTSBackend):
    """ElevenLabs HTTP API (고품질·외부 전송 — opt-in, 로컬 보장 깨짐).

    PCM 16kHz 로 받아 wav 로 감싼다(길이 측정 가능). 키는 환경변수에서만 읽고 커밋 금지(C9).
    """

    name = "elevenlabs"
    sample_rate = 16000
    timeout_sec = 120

    def synthesize(self, text: str, out_path: Path, voice: Optional[str]) -> float:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise TTSError(
                "elevenlabs 백엔드는 ELEVENLABS_API_KEY 환경변수가 필요합니다 "
                "(외부 API — opt-in). 키를 커밋하지 마십시오 (C9)."
            )
        voice_id = voice or os.environ.get("ELEVENLABS_VOICE_ID")
        if not voice_id:
            raise TTSError("elevenlabs 백엔드는 voice(또는 ELEVENLABS_VOICE_ID)가 필요합니다.")

        import httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        params = {"output_format": f"pcm_{self.sample_rate}"}
        headers = {"xi-api-key": api_key, "content-type": "application/json"}
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}
        try:
            resp = httpx.post(
                url, params=params, headers=headers, json=payload, timeout=self.timeout_sec
            )
        except httpx.HTTPError as e:
            raise TTSError(f"elevenlabs 요청 실패: {e}") from e
        if resp.status_code != 200:
            raise TTSError(
                f"elevenlabs 응답 {resp.status_code}: {resp.text[:300]}"
            )
        return _write_pcm16_as_wav(out_path, resp.content, self.sample_rate)


_BACKENDS: dict[str, type[TTSBackend]] = {
    "stub": StubTTSBackend,
    "local": LocalTTSBackend,
    "elevenlabs": ElevenLabsTTSBackend,
}

BACKEND_CHOICES = tuple(_BACKENDS.keys())


def get_backend(name: str) -> TTSBackend:
    """백엔드 이름 → 인스턴스. 알 수 없으면 TTSError."""
    cls = _BACKENDS.get(name)
    if cls is None:
        raise TTSError(f"알 수 없는 TTS backend: {name!r} (가능: {', '.join(BACKEND_CHOICES)})")
    return cls()


__all__ = [
    "TTSBackend",
    "TTSError",
    "StubTTSBackend",
    "LocalTTSBackend",
    "ElevenLabsTTSBackend",
    "get_backend",
    "BACKEND_CHOICES",
    "CHARS_PER_SEC",
]

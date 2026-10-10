"""Supertonic 3 백엔드(v5.11.0 back_and_forth D-0152 V1, 사용자 결정 D146·설계 D147 §1·§4·§5).

edge 와 같은 계약: `synth_all([(발음 텍스트, mp3 경로), …])` → mp3. 값은 config.yaml tts.supertonic 에서만(15 P3).
- 자산이 없거나 sha1 이 다르면 오류(받는 명령 안내). 다른 목소리로 넘어가지 않는다(P6).
- 결정성: 문장 시드 = sha1(발음 텍스트 · 스타일 · 속도 · 단계 · seed_salt) 앞 8바이트 → numpy Generator. 같은 입력 = 같은 wav.
- mp3 는 ffmpeg 고정 옵션(bitexact, 메타데이터 없음)으로 만든다.
- 단어 시각을 내지 않는다(duration 은 문장 총길이뿐) → `.align.json` 은 V2 강제 정렬이 쓴다. V1 은 쓰지 않는다.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from orchestrator.config import SupertonicConfig, load_config
from script.tts import supertonic_assets
from script.tts.supertonic_runtime import Style, TextToSpeech, chunk_text, load_style

SEED_BYTES = 8
MP3_ARGS = ("-ac", "1", "-codec:a", "libmp3lame", "-b:a", "128k", "-map_metadata", "-1",
            "-fflags", "+bitexact", "-flags:a", "+bitexact", "-id3v2_version", "0", "-write_xing", "0")


def config() -> SupertonicConfig:
    cfg = load_config().tts.supertonic
    if cfg is None:
        raise supertonic_assets.SupertonicAssetError("config.yaml tts.supertonic 이 없다(D-0152)")
    return cfg


def voice_label(cfg: SupertonicConfig | None = None) -> str:
    c = cfg or config()
    return f"supertonic-3 {c.voice_style} ×{c.speed}"


def cache_salt(cfg: SupertonicConfig) -> str:
    """캐시 키 소금 — 소리를 바꾸는 값 전부. edge 키(`|edge|…`·소금 없음)와 겹치지 않는다(조용한 재사용 금지, P6)."""
    return (f"|st|{cfg.voice_style}|{cfg.speed}|{cfg.total_step}|{cfg.silence_sec}|{cfg.max_chunk_len}"
            f"|{cfg.seed_salt}|{cfg.revision[:8]}")


def seed(tts: str, cfg: SupertonicConfig) -> int:
    h = hashlib.sha1(f"{tts}|{cfg.voice_style}|{cfg.speed}|{cfg.total_step}|{cfg.seed_salt}".encode()).digest()
    return int.from_bytes(h[:SEED_BYTES], "big")


def chunks(tts: str, cfg: SupertonicConfig) -> list[str]:
    """합성 때 나뉠 조각(합성 없이 같은 규칙) — plan 이 문장마다 기록한다."""
    return chunk_text(tts, cfg.max_chunk_len)


@lru_cache(maxsize=1)
def _engine(asset_dir: str, style_name: str) -> tuple[TextToSpeech, Style]:
    base = Path(asset_dir)
    return TextToSpeech(base / "onnx"), load_style(base / "voice_styles" / f"{style_name}.json")


def engine(cfg: SupertonicConfig) -> tuple[TextToSpeech, Style]:
    """ONNX 세션은 프로세스당 한 번(D147 §1). 자산 대조를 먼저 한다."""
    base = supertonic_assets.require_assets(cfg)
    return _engine(str(base), cfg.voice_style)


def synth_wav(tts: str, cfg: SupertonicConfig) -> tuple[np.ndarray, int, list[str]]:
    """발음 텍스트 → (wav float32, 표본율, 조각)."""
    eng, style = engine(cfg)
    wav, parts = eng.synth(tts, style, cfg.total_step, cfg.speed, cfg.silence_sec, cfg.max_chunk_len,
                           np.random.default_rng(seed(tts, cfg)))
    return wav, eng.sample_rate, parts


def write_mp3(wav: np.ndarray, sr: int, path: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        w = Path(d) / "a.wav"
        wavfile.write(w, sr, np.clip(wav, -1.0, 1.0).astype(np.float32))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), *MP3_ARGS, str(path)], check=True)


def synth_one(tts: str, path: Path, cfg: SupertonicConfig | None = None) -> list[str]:
    c = cfg or config()
    wav, sr, parts = synth_wav(tts, c)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_mp3(wav, sr, path)
    return parts


def synth_all(jobs: list[tuple[str, Path]], cfg: SupertonicConfig | None = None) -> None:
    c = cfg or config()
    for k, (tts, path) in enumerate(jobs):
        synth_one(tts, path, c)
        print(f"supertonic {k + 1}/{len(jobs)} {path.name}", flush=True)

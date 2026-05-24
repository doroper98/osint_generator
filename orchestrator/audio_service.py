"""build-audio 오케스트레이션 (수직 슬라이스 V4, v0.12.0).

full_script 의 각 ScriptSegment 를 선택된 TTS 백엔드로 합성해 wav + AudioManifest 를
만든다. 백엔드는 교체 가능 (local/elevenlabs/stub — workers/tts_backends.py).

render-debug 와 마찬가지로 state 전이 없는 산출물 생성 단계 (현재 full_script 로부터
언제든 재생성 가능). full_script 가 있어야 한다 (script_writing 이상).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from orchestrator.audio_io import audio_manifest_path, narration_dir, persist_audio_manifest
from orchestrator.config import AppConfig, load_config
from orchestrator.script_io import load_full_script
from schemas.models import AudioManifest, AudioSegment
from workers.tts_backends import TTSError, get_backend


def _rel(project_id: str, path: Path, cfg: AppConfig) -> str:
    """project_dir 기준 상대경로 문자열 (manifest 저장용, OS 무관 '/')."""
    from orchestrator.config import project_dir

    try:
        return str(path.resolve().relative_to(project_dir(project_id, cfg).resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def build_audio(
    project_id: str,
    *,
    backend: str = "local",
    voice: Optional[str] = None,
    cfg: Optional[AppConfig] = None,
) -> AudioManifest:
    """full_script → 세그먼트별 wav + audio_manifest.json.

    raises
    ------
    FileNotFoundError : full_script.json 없음.
    TTSError          : 백엔드 미설정/실패.
    """
    cfg = cfg or load_config()
    script = load_full_script(project_id, cfg)
    engine = get_backend(backend)

    ndir = narration_dir(project_id, cfg)
    ndir.mkdir(parents=True, exist_ok=True)

    segments: list[AudioSegment] = []
    total = 0.0
    for seg in script.segments:
        out_path = ndir / f"{seg.segment_id}.wav"
        duration = engine.synthesize(seg.narration, out_path, voice)
        total += duration
        segments.append(
            AudioSegment(
                segment_id=seg.segment_id,
                audio_path=_rel(project_id, out_path, cfg),
                duration_sec=round(duration, 3),
                text=seg.narration,
                backend=backend,
                voice=voice,
            )
        )

    manifest = AudioManifest(
        project_id=project_id,
        backend=backend,
        total_duration_sec=round(total, 3),
        segments=segments,
    )
    persist_audio_manifest(project_id, manifest, cfg)
    return manifest


__all__ = ["build_audio"]

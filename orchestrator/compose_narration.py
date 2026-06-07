"""compose_narration — ComposedScene[] → 실 음성(TTS) + 자막/씬 sync 데이터.

compose-hyperframes 경로에 음성 나레이션을 얹는 계층. codex(또는 stub) 가 각 씬에 써 준
`narration` 스크립트를 문장 단위로 쪼개 TTS 백엔드로 합성하고, **실 음성 길이**로 자막 큐
타이밍과 씬 길이를 다시 깐다 — 음성·자막·비주얼 drift 사고(build_narration.py 도입 배경) 회피.

설계(C0 영상미 / C2):
- 타임라인 계산(`plan_narration_timeline`)·문장 분할(`split_sentences`)은 **순수 함수** — ffmpeg/
  TTS 없이 단위테스트 가능. 실 합성·ffmpeg concat 은 `build_scene_narration` 에 격리.
- 자막 텍스트는 **원본 문장**(시청자 가독성). 합성에는 발음 사전(tts_pronounce) 적용한 변형을
  쓰되 자막엔 노출하지 않는다 (build_narration.py 의 text/narration 분리 정신).
- 모든 함수 타입 힌트. 도메인 결과는 Pydantic v2 모델.
"""

from __future__ import annotations

import contextlib
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from orchestrator.tts_pronounce import apply_pronunciation


# ---------------------------------------------------------------------------
# 도메인 모델
# ---------------------------------------------------------------------------


class NarrationCue(BaseModel):
    """한 문장의 자막 큐 — 절대 타임라인 시작 시점(at_sec)과 실 음성 길이(duration_sec)."""

    model_config = ConfigDict(extra="forbid")

    scene_id: str
    text: str            # 자막용 원본 문장(발음 변형 아님)
    at_sec: float        # 컴포지션 절대 타임라인 기준 시작(초)
    duration_sec: float  # 이 문장의 실 음성 길이(초)


class NarrationResult(BaseModel):
    """나레이션 합성 결과 — 큐·씬별 길이·총 길이·오디오 경로."""

    model_config = ConfigDict(extra="forbid")

    cues: list[NarrationCue] = Field(default_factory=list)
    scene_durations: dict[str, float] = Field(default_factory=dict)  # scene_id → 총 초(말미 pause 포함)
    total_sec: float = 0.0
    audio_path: Optional[str] = None


# ---------------------------------------------------------------------------
# 순수 함수 — 타임라인 / 문장 분할
# ---------------------------------------------------------------------------


def plan_narration_timeline(
    units: list[tuple[str, str, float]],
    *,
    lead_sec: float = 0.5,
    pause_sec: float = 0.5,
    tail_sec: float = 0.8,
) -> NarrationResult:
    """(scene_id, text, audio_dur_sec) 재생 순서 목록 → 큐·씬길이·총길이 (ffmpeg/TTS 무관).

    누적 규칙:
    - cursor = lead_sec 로 시작. 각 unit 은 cursor 시점에 시작하고 길이만큼 진행한 뒤
      문장 사이 pause_sec 만큼 무음을 둔다.
    - total_sec = 마지막 pause 를 빼고(말미 무음은 tail 로 대체) tail_sec 을 더한 값.
      unit 이 없으면 lead+tail.
    - scene_durations[scene_id] 는 그 씬의 모든 unit 에 대해 (dur + pause_sec) 합.
      즉 **각 문장 뒤 pause 를 그 씬 안에 포함**해 둔다(말미 tail 은 별도). 그래서
      sum(scene_durations) == cursor_end - lead_sec (= total - lead - tail + pause) 가 되며,
      호출자는 lead_sec 만큼 오프셋한 뒤 scene_durations 를 누적해 씬 start/duration 을
      다시 깔면 음성 구간과 비주얼이 정확히 정렬된다.
    """
    cues: list[NarrationCue] = []
    scene_durations: dict[str, float] = {}
    cursor = lead_sec
    for scene_id, text, dur in units:
        cues.append(NarrationCue(
            scene_id=scene_id, text=text,
            at_sec=round(cursor, 3), duration_sec=round(dur, 3),
        ))
        scene_durations[scene_id] = round(scene_durations.get(scene_id, 0.0) + dur + pause_sec, 3)
        cursor += dur
        cursor += pause_sec

    if units:
        total_sec = round(cursor - pause_sec + tail_sec, 3)
    else:
        total_sec = round(lead_sec + tail_sec, 3)

    return NarrationResult(cues=cues, scene_durations=scene_durations, total_sec=total_sec)


def split_sentences(text: str) -> list[str]:
    """한국어/영어 산문을 문장 경계로 분할. 종결부호(`. ! ? 。 …`) + 공백/끝 기준.

    각 문장은 strip 하고 빈 문장은 버린다. 종결부호가 전혀 없으면 전체를 한 문장으로.
    """
    t = (text or "").strip()
    if not t:
        return []
    # 종결부호 뒤(공백 또는 끝)에서 끊는다. 종결부호는 문장에 포함.
    parts = re.split(r"(?<=[.!?。…])\s+", t)
    out: list[str] = []
    for p in parts:
        s = p.strip()
        if s:
            out.append(s)
    return out


# ---------------------------------------------------------------------------
# ffmpeg 헬퍼 (오디오 조립)
# ---------------------------------------------------------------------------


def _resolve_ffmpeg() -> str:
    """ffmpeg 실행 파일 경로 — imageio-ffmpeg(portable) 우선, 그다음 PATH."""
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError(
        "ffmpeg 가 없습니다. pip install imageio-ffmpeg 또는 시스템에 ffmpeg 설치 필요."
    )


def _run_ffmpeg(args: list[str]) -> None:
    """ffmpeg subprocess 실행 — 실패 시 stderr 발췌를 담아 RuntimeError."""
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패 (exit {proc.returncode}): {(proc.stderr or '')[:400]}")


# 드리프트 회피(사용자 보고: 음성·자막 누적 drift): 파트별 mp3 재인코딩은 프레임 패딩이
# 누적돼 실 길이가 sum 보다 길어진다. → **PCM WAV(샘플 정확)로 조립**하고 cue 타이밍은
# WAV 실측 길이로 계산한 뒤, 마지막에 **한 번만** mp3 인코딩한다(패딩 1회로 무시 가능).
_WAV_RATE = 44100


def _write_silence_wav(ffmpeg: str, path: Path, sec: float) -> None:
    """정확한 길이의 무음 PCM WAV (mono, 16-bit, 44.1kHz)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg([
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"anullsrc=r={_WAV_RATE}:cl=mono",
        "-t", f"{max(0.001, sec):.3f}",
        "-ar", str(_WAV_RATE), "-ac", "1", "-c:a", "pcm_s16le",
        str(path),
    ])


def _normalize_to_wav(ffmpeg: str, src: Path, dst: Path) -> None:
    """임의 입력(wav/mp3)을 표준 PCM WAV(mono/16-bit/44.1kHz)로 디코딩 — concat 이 샘플 정확."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg([
        ffmpeg, "-y", "-i", str(src),
        "-ar", str(_WAV_RATE), "-ac", "1", "-c:a", "pcm_s16le",
        str(dst),
    ])


def _wav_duration_sec(path: Path) -> float:
    """WAV 실 길이(초) — stdlib wave 로 프레임 수/레이트 (ffprobe/mutagen 불요, 포터블)."""
    with contextlib.closing(wave.open(str(path), "rb")) as w:
        return w.getnframes() / float(w.getframerate())


def _concat_wav(ffmpeg: str, parts: list[Path], out: Path) -> None:
    """동일 포맷 PCM WAV 조각들을 concat demuxer 로 이어붙임 (-c copy → 샘플 정확)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    listfile = out.parent / "_concat_list.txt"
    listfile.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in parts) + "\n", encoding="utf-8"
    )
    try:
        _run_ffmpeg([
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", str(listfile), "-c", "copy", str(out),
        ])
    finally:
        try:
            listfile.unlink()
        except OSError:
            pass


def _encode_mp3(ffmpeg: str, src: Path, dst: Path) -> None:
    """최종 WAV → mp3 (단일 인코딩, 패딩 1회)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg([
        ffmpeg, "-y", "-i", str(src),
        "-c:a", "libmp3lame", "-q:a", "4",
        str(dst),
    ])


# ---------------------------------------------------------------------------
# 조립 — 실 TTS + ffmpeg (백엔드/ffmpeg 있는 환경에서 실행)
# ---------------------------------------------------------------------------


def build_scene_narration(
    scenes: list[Any],
    *,
    backend: Any,
    voice: Optional[str],
    audio_out: Path,
    ffmpeg_bin: str,
    pronounce_dict: Optional[dict[str, str]] = None,
    lead_sec: float = 0.5,
    pause_sec: float = 0.5,
    tail_sec: float = 0.8,
) -> NarrationResult:
    """ComposedScene[] → 합성 음성(audio_out, mp3) + sync 결과.

    각 씬의 나레이션 텍스트(narration ▷ body ▷ heading 순 폴백)를 문장으로 쪼개 TTS 합성,
    실 음성 길이로 큐/씬길이/총길이를 계산한다. 자막 텍스트는 원본 문장, 합성 텍스트는
    발음 사전 적용본(분리).

    backend 가 던지거나 ffmpeg 가 없으면 예외를 그대로 올린다 — 호출자가 잡아 무음성 폴백.
    """
    audio_out = Path(audio_out)

    with tempfile.TemporaryDirectory(prefix="osint_narration_") as tmp:
        tmpdir = Path(tmp)

        # 1) 씬→문장 unit 합성 → 표준 WAV 로 정규화 → **WAV 실측 길이**로 unit 길이 확정.
        #    실측을 쓰기에 cue at_sec 이 조립된 오디오의 실제 위치와 정확히 일치(drift 0).
        units: list[tuple[str, str, float]] = []
        norm_parts: list[Path] = []
        idx = 0
        for sc in scenes:
            narration_text = (
                getattr(sc, "narration", "") or getattr(sc, "body", "")
                or getattr(sc, "heading", "")
            )
            for sentence in split_sentences(narration_text):
                tts_text = (
                    apply_pronunciation(sentence, pronounce_dict)
                    if pronounce_dict else sentence
                )
                ext = getattr(backend, "file_ext", ".wav")
                raw = tmpdir / f"raw_{idx:04d}{ext}"
                backend.synthesize(tts_text, raw, voice)
                norm = tmpdir / f"norm_{idx:04d}.wav"
                _normalize_to_wav(ffmpeg_bin, raw, norm)
                dur = _wav_duration_sec(norm)
                units.append((sc.scene_id, sentence, dur))
                norm_parts.append(norm)
                idx += 1

        # 2) unit 이 없으면 빈 결과 — 짧은 무음 mp3 를 써 둔다(렌더가 src 를 가리켜도 무사).
        if not units:
            result = plan_narration_timeline(
                [], lead_sec=lead_sec, pause_sec=pause_sec, tail_sec=tail_sec
            )
            sil = tmpdir / "_empty.wav"
            _write_silence_wav(ffmpeg_bin, sil, result.total_sec)
            audio_out.parent.mkdir(parents=True, exist_ok=True)
            _encode_mp3(ffmpeg_bin, sil, audio_out)
            return result.model_copy(update={"audio_path": str(audio_out)})

        # 3) lead/pause/tail 무음 WAV + 파트 WAV 를 순서대로 concat → 최종 WAV → mp3 1회 인코딩.
        lead_path = tmpdir / "_lead.wav"
        _write_silence_wav(ffmpeg_bin, lead_path, lead_sec)
        tail_path = tmpdir / "_tail.wav"
        _write_silence_wav(ffmpeg_bin, tail_path, tail_sec)

        concat_parts: list[Path] = [lead_path]
        for i, norm in enumerate(norm_parts):
            concat_parts.append(norm)
            if i < len(norm_parts) - 1:
                pause_path = tmpdir / f"_pause_{i:04d}.wav"
                _write_silence_wav(ffmpeg_bin, pause_path, pause_sec)
                concat_parts.append(pause_path)
        concat_parts.append(tail_path)

        final_wav = tmpdir / "_final.wav"
        _concat_wav(ffmpeg_bin, concat_parts, final_wav)
        audio_out.parent.mkdir(parents=True, exist_ok=True)
        _encode_mp3(ffmpeg_bin, final_wav, audio_out)

    # 4) 타임라인 산출(WAV 실측 길이 기반) + 오디오 경로 부착.
    result = plan_narration_timeline(
        units, lead_sec=lead_sec, pause_sec=pause_sec, tail_sec=tail_sec
    )
    return result.model_copy(update={"audio_path": str(audio_out)})


__all__ = [
    "NarrationCue",
    "NarrationResult",
    "plan_narration_timeline",
    "split_sentences",
    "build_scene_narration",
]

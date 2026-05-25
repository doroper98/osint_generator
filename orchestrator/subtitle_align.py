"""자막 큐 forced-alignment (교체형 백엔드 + 비례 폴백).

자막 큐(SubtitleCue)의 타이밍을 **실제 TTS 음성에 맞춰 정밀화**한다. 지금 기본은
`render_io.split_subtitle_cues` 의 글자수 비례 추정인데, 음성이 있으면 정렬기로 문장별
실측 [start, dur] 로 교체한다(영상미 C0 — 자막이 음성과 딱 맞게).

백엔드는 환경변수 `OSINT_ALIGN_BACKEND` 로 선택한다 (TTS 백엔드 패턴과 동형):
- (unset / "none"): 정렬 안 함 → 호출자가 비례 큐 유지. **이 클라우드의 기본**
  (음성=stub 무음 + huggingface 차단이라 정렬 불가).
- "whisper": openai-whisper 로 단어 타임스탬프 추출 → 큐에 매핑. **모델 가중치 + 실제
  음성이 필요하므로 사용자 머신 전용**. 모델은 `OSINT_ALIGN_WHISPER_MODEL`(기본 base).

설계 원칙: `align_cues` 는 정밀 큐 또는 **None(폴백 신호)** 을 반환한다. 어떤 실패(미설치/
모델 다운로드 차단/무음/예외)도 None 으로 흡수해 파이프라인을 절대 깨지 않는다
(graceful degradation). 정밀 정렬은 사용자 머신에서만 동작하며, 본 클라우드에서는 항상
None → 비례 폴백이라 기존 동작과 동일하다.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from schemas.models import SubtitleCue

logger = logging.getLogger(__name__)

ALIGN_BACKEND_ENV = "OSINT_ALIGN_BACKEND"
WHISPER_MODEL_ENV = "OSINT_ALIGN_WHISPER_MODEL"


def align_backend() -> str:
    """현재 정렬 백엔드 ('none' / 'whisper'). env 미설정이면 'none'."""
    return (os.environ.get(ALIGN_BACKEND_ENV) or "none").strip().lower()


def alignment_enabled() -> bool:
    return align_backend() not in ("", "none")


def align_cues(
    base_cues: list[SubtitleCue],
    audio_path: Path,
) -> Optional[list[SubtitleCue]]:
    """음성에 맞춰 정밀 큐를 반환. 불가하면 None(호출자가 base_cues 비례 폴백 유지).

    base_cues 는 비례로 쪼갠 큐(=텍스트 줄 분할 기준). 정렬기는 그 **텍스트 경계의
    시작/길이만 음성 실측으로 교체**한다(텍스트 분할 자체는 그대로 신뢰).
    """
    backend = align_backend()
    if backend in ("", "none"):
        return None
    if not base_cues:
        return None
    p = Path(audio_path)
    if not p.exists() or p.stat().st_size == 0:
        return None  # 무음/stub/없음 → 폴백
    try:
        if backend == "whisper":
            return _align_whisper(p, base_cues)
        logger.warning("알 수 없는 OSINT_ALIGN_BACKEND=%r — 비례 폴백.", backend)
        return None
    except Exception as e:  # 정렬 실패는 절대 파이프라인을 깨지 않는다.
        logger.warning("forced-alignment 실패(%s) — 비례 폴백: %s", backend, e)
        return None


def _align_whisper(audio_path: Path, base_cues: list[SubtitleCue]) -> Optional[list[SubtitleCue]]:
    """openai-whisper 단어 타임스탬프 → base_cues 글자수만큼 단어를 소비하며 [start,dur] 할당.

    사용자 머신 전용(모델 가중치 필요). 단어가 안 나오면 None(폴백).
    """
    import whisper  # 미설치면 ImportError → 상위 except 가 None 으로 흡수.

    model = whisper.load_model(os.environ.get(WHISPER_MODEL_ENV) or "base")
    result = model.transcribe(str(audio_path), word_timestamps=True, language="ko")
    words = [
        w
        for seg in result.get("segments", [])
        for w in seg.get("words", [])
        if "start" in w and "end" in w
    ]
    if not words:
        return None

    cues: list[SubtitleCue] = []
    wi = 0
    for c in base_cues:
        target = max(1, len(c.text.replace(" ", "")))
        if wi >= len(words):
            # 단어 소진 — 남은 큐는 마지막 시점에 0 길이로(드묾).
            last = words[-1]["end"]
            cues.append(SubtitleCue(text=c.text, startSec=round(last, 3), durationSec=0.0))
            continue
        start = words[wi]["start"]
        end = words[wi]["end"]
        acc = 0
        while wi < len(words) and acc < target:
            acc += len(str(words[wi].get("word", "")).strip())
            end = words[wi]["end"]
            wi += 1
        cues.append(
            SubtitleCue(text=c.text, startSec=round(start, 3), durationSec=round(max(0.1, end - start), 3))
        )
    return cues


__all__ = ["align_backend", "alignment_enabled", "align_cues", "ALIGN_BACKEND_ENV"]

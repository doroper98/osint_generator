"""문장 끝 억양 보정 (v5.20.0, back_and_forth D-0175, 사용자 결정 D169 시안 C).

사용자 청취(2026-10-11): "~ㅆ습니다 의 '습니다' 높낮이가 너무 중간톤 — '~니다' 로 가면서 아래로 내리는 형태로."
Fable 시안 6개 중 C = **끝 3글자("습니다"·"입니다") 구간에 걸쳐 끝까지 4반음 선형 하강**, 그 앞은 원음 그대로.

    final_fall(audio, align, pron_text, cfg) -> (audio', FinalFallRecord)

- 시각은 **원본 mp3 기준**(정렬 `.align.json` 과 같은 축). plan 은 mp3 디코드 → final_fall → 트림 → npy 순서라
  mp3 캐시·정렬 파일은 바뀌지 않고, 합성이 프레임 시각을 보존하므로 정렬 시각은 그대로 유효하다(길이 = 원본).
- WORLD 보코더(pyworld, MIT): harvest(f0_floor~f0_ceil, frame_ms) + stonemask → cheaptrick·d4c → 구간 f0 만 바꿔 synthesize.
  구간 시작 = 끝 span_chars 글자의 첫 글자 시작 − pre_sec, 끝 = 마지막 유성 프레임. 반음 0 → −semitones 선형(프레임 비율).
- 구간 앞 샘플은 원음 그대로(바이트 동일), 구간 시작에서 crossfade_sec 로 합성음에 넘어가고, 합성 부분의 피크를 원음 같은 부분 피크에 맞춘다.
- 발음 텍스트가 suffix(+문장부호)로 끝나지 않거나 유성 프레임이 없으면 원음 그대로 + `applied: false, reason`.
- 값은 rules `tts_rules.prosody.final_fall` 하나(P3). pyworld 가 없으면 오류(폴백 금지, P6).
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from pydantic import BaseModel, ConfigDict

from schemas.rules_models import FinalFallRules

SR = 44100          # script.tts.trim.SR 와 같은 표본율(디코드 결과)
TAIL_PUNCT = " .,!?…\"'”’)」』"   # 끝 문장부호 — 이것을 뗀 뒤 suffix 로 끝나는지 본다
MIN_FRAMES = 4      # 구간 최소 프레임 수(시제품 e − 4)


class ProsodyError(RuntimeError):
    """보정에 필요한 것이 없다(pyworld 미설치·정렬 글자 불일치)."""


class FinalFallRecord(BaseModel):
    """plan row `prosody.final_fall` — 적용 여부·구간·반음·구간 시작/끝 f0(원음 기준 시작, 보정 뒤 끝)."""

    model_config = ConfigDict(extra="forbid")

    applied: bool
    reason: Optional[str] = None
    region_sec: Optional[tuple[float, float]] = None
    semitones: Optional[float] = None
    f0_start_hz: Optional[float] = None
    f0_end_hz: Optional[float] = None


def _pyworld():  # noqa: ANN202 — module
    try:
        import pyworld  # noqa: PLC0415
    except ImportError as ex:   # 폴백 금지(P6) — 보정 없는 음성으로 조용히 넘어가지 않는다
        raise ProsodyError("pyworld 가 없다 — `pip install -r requirements-engine.txt`(pyworld>=0.3, MIT)") from ex
    return pyworld


def span_start_index(pron_text: str, cfg: FinalFallRules) -> Optional[int]:
    """끝 문장부호를 뗀 발음 텍스트가 suffix 로 끝나면 끝 span_chars 글자의 첫 글자 위치, 아니면 None."""
    body = pron_text.rstrip(TAIL_PUNCT)
    if not body.endswith(cfg.suffix) or len(body) < cfg.span_chars:
        return None
    return len(body) - cfg.span_chars


def final_fall(audio: np.ndarray, align: dict, pron_text: str, cfg: FinalFallRules) -> tuple[np.ndarray, FinalFallRecord]:
    """끝 억양 보정. audio = 원본 mp3 디코드(float32, SR mono). 반환 음성은 같은 길이·같은 dtype."""
    if not cfg.enabled:
        return audio, FinalFallRecord(applied=False, reason="disabled")
    i = span_start_index(pron_text, cfg)
    if i is None:
        return audio, FinalFallRecord(applied=False, reason=f"'{cfg.suffix}' 로 끝나지 않는다")
    chars = align.get("characters") or []
    if "".join(chars) != pron_text:
        raise ProsodyError(f"정렬 글자 ≠ 발음 텍스트 — {''.join(chars)[:30]!r} vs {pron_text[:30]!r}")
    pw = _pyworld()
    x = audio.astype(np.float64)
    fp = cfg.frame_ms
    f0, t = pw.harvest(x, SR, f0_floor=cfg.f0_floor_hz, f0_ceil=cfg.f0_ceil_hz, frame_period=fp)
    f0 = pw.stonemask(x, f0, t, SR)
    voiced = np.flatnonzero(f0 > 0)
    if len(voiced) == 0:
        return audio, FinalFallRecord(applied=False, reason="유성 프레임 없음")
    e = int(voiced[-1])
    t_start = float(align["character_start_times_seconds"][i]) - cfg.pre_sec
    s0 = min(int(np.searchsorted(t, t_start)), e - MIN_FRAMES)
    if s0 < 0:
        return audio, FinalFallRecord(applied=False, reason="구간이 너무 짧다")
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    f0n = f0.copy()
    span = max(e - s0, 1)
    for k in range(s0, e + 1):
        if f0[k] > 0:
            f0n[k] = f0[k] * 2.0 ** (-cfg.semitones * ((k - s0) / span) / 12.0)
    y = pw.synthesize(f0n, sp, ap, SR, fp)
    y = np.pad(y, (0, max(0, len(x) - len(y))))[: len(x)]
    cs = int(round(t[s0] * SR))
    cf = max(1, int(round(cfg.crossfade_sec * SR)))
    tail_peak, syn_peak = float(np.max(np.abs(x[cs:]))), float(np.max(np.abs(y[cs:])))
    if syn_peak > 0:
        y = y * (tail_peak / syn_peak)
    out = audio.copy()   # 구간 앞 = 원음 바이트 그대로
    w = np.clip(np.arange(len(x) - cs, dtype=np.float64) / cf, 0.0, 1.0)
    out[cs:] = (x[cs:] * (1.0 - w) + y[cs:] * w).astype(audio.dtype)
    s_hz = next((float(f0[k]) for k in range(s0, e + 1) if f0[k] > 0), None)
    return out, FinalFallRecord(applied=True, region_sec=(round(float(t[s0]), 4), round(float(t[e]), 4)), semitones=cfg.semitones,
                                f0_start_hz=round(s_hz, 2) if s_hz else None, f0_end_hz=round(float(f0n[e]), 2))


__all__ = ["FinalFallRecord", "ProsodyError", "final_fall", "span_start_index"]

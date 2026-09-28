"""오디오 QA — 측정 코드 경로 하나 (v3.4.0, back_and_forth D-0060 작업 6, 10 §7-5, 13 Phase 8).

engine.checks(check_audio)·engine.mux(provenance audio)·tools/audio_report.py(얇은 CLI)가 모두 이 모듈을 부른다.
- 최종 mp4: ffmpeg loudnorm 측정 I·TP·LRA — 목표 rules audio.loudnorm.I ± audio.qa.i_tol_lu, TP ≤ loudnorm.TP
- mix.f32: 내레이션 스템을 plan npy 로 재구성(믹서와 같은 narration_peak 정규화·배치)해 최소제곱 스케일로 맞추고,
  나머지를 음악+효과음 스템으로 본다. 내레이션 구간 RMS 차(음악 − 내레이션, dB)가 audio.qa.music_under_narration_db 안.
- mix 피크 ≤ audio.master_peak.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel, ConfigDict

from rules import load_rules

SR = 44100                     # 코덱 상수(audio.mix.SR 과 같음 — test_audio_rules)
AU = load_rules().audio


class Loudness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    I: float  # noqa: E741, N815
    TP: float  # noqa: N815
    LRA: float  # noqa: N815


class AudioQA(BaseModel):
    """오디오 QA 한 벌. 판정(*_ok)은 규칙 값으로만 한다."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    final_loudness: Optional[Loudness] = None       # final.mp4 가 있을 때만
    mix_peak: float
    narration_rms_db: float
    music_rms_in_narration_db: float
    music_under_narration_db: float                  # 음악 − 내레이션(음수 = 음악이 낮다)
    narration_seconds: float
    loudness_ok: Optional[bool] = None
    true_peak_ok: Optional[bool] = None
    music_level_ok: bool
    peak_ok: bool
    method: str = "내레이션 스템 = plan npy 재배치(믹서 규칙) × 최소제곱 스케일, 음악 = mix − 내레이션(모노 평균)"

    def issues(self) -> list[str]:
        ln, q = AU.loudnorm, AU.qa
        out = []
        if self.final_loudness is not None and not self.loudness_ok:
            out.append(f"최종 음량 {self.final_loudness.I:.2f} LUFS — 목표 {ln.I:g} ± {q.i_tol_lu:g}")
        if self.final_loudness is not None and not self.true_peak_ok:
            out.append(f"트루 피크 {self.final_loudness.TP:.2f} dBTP > {ln.TP:g}")
        if not self.music_level_ok:
            lo, hi = q.music_under_narration_db
            out.append(f"내레이션 구간 음악 {self.music_under_narration_db:+.2f} dB — 범위 [{lo:g}, {hi:g}]")
        if not self.peak_ok:
            out.append(f"mix 피크 {self.mix_peak:.4f} > master_peak {AU.master_peak}")
        return out


def db(x: float) -> float:
    return 20 * math.log10(max(x, AU.norm_eps ** 2))


def measure_loudnorm(path: Path) -> Loudness:
    ln = AU.loudnorm
    af = f"loudnorm=I={ln.I:g}:TP={ln.TP:g}:LRA={ln.LRA:g}:print_format=json"
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", af, "-f", "null", "-"],
                         capture_output=True, text=True, check=True).stderr
    blob = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return Loudness(I=float(blob["input_i"]), TP=float(blob["input_tp"]), LRA=float(blob["input_lra"]))


def stems(mix_f32: Path, sentences: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:  # noqa: ANN001 — plan 문장(npy·t0·t1)
    """(mix 모노, 내레이션 스템(스케일 적용), 내레이션 구간 마스크). 문장은 속성 또는 dict."""
    mix = np.fromfile(mix_f32, np.float32).reshape(-1, 2).mean(1)
    n = len(mix)
    vo = np.zeros(n, np.float32)
    mask = np.zeros(n, bool)
    for x in sentences:
        g = (lambda k: x[k]) if isinstance(x, dict) else (lambda k: getattr(x, k))  # noqa: E731
        a = np.load(g("npy")).astype(np.float32)
        a = a / (np.abs(a).max() + AU.norm_eps) * AU.narration_peak
        i0 = int(g("t0") * SR)
        k = min(len(a), n - i0)
        vo[i0:i0 + k] += a[:k]
        mask[i0:int(g("t1") * SR)] = True
    scale = float((mix[mask] @ vo[mask]) / max(float(vo[mask] @ vo[mask]), AU.norm_eps))
    return mix, vo * scale, mask


def audio_qa(out_dir: Path, sentences: list) -> AudioQA:  # noqa: ANN001
    """out_dir = 프로젝트 out/(mix.f32 필수, final.mp4 있으면 음량 측정)."""
    mix, vo, mask = stems(out_dir / "mix.f32", sentences)
    music = mix - vo
    vo_db = db(float(np.sqrt(np.mean(vo[mask] ** 2))))
    mu_db = db(float(np.sqrt(np.mean(music[mask] ** 2))))
    lo, hi = AU.qa.music_under_narration_db
    final = out_dir / "final.mp4"
    loud = measure_loudnorm(final) if final.exists() else None
    peak = float(np.abs(mix).max())
    return AudioQA(final_loudness=loud, mix_peak=round(peak, 4), narration_rms_db=round(vo_db, 2),
                   music_rms_in_narration_db=round(mu_db, 2), music_under_narration_db=round(mu_db - vo_db, 2),
                   narration_seconds=round(float(mask.sum()) / SR, 1),
                   loudness_ok=None if loud is None else abs(loud.I - AU.loudnorm.I) <= AU.qa.i_tol_lu,
                   true_peak_ok=None if loud is None else loud.TP <= AU.loudnorm.TP,
                   music_level_ok=lo <= mu_db - vo_db <= hi, peak_ok=peak <= AU.master_peak)


__all__ = ["AudioQA", "Loudness", "audio_qa", "measure_loudnorm", "stems"]

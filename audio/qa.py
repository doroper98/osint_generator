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
    music_level_ok: Optional[bool]                   # None = 음악 없음(sound.bgm null) — 판정 대상 아님
    peak_ok: bool
    sentence_rms_db: dict[str, float] = {}            # 문장 id → 무음 제외 RMS(피크 정규화 뒤)
    sentence_rms_outliers: list[str] = []             # 평균에서 sentence_rms_dev_db 넘게 벗어난 문장(warning)
    method: str = "내레이션 스템 = plan npy 재배치(믹서 규칙) × 최소제곱 스케일, 음악 = mix − 내레이션(모노 평균)"

    def issues(self) -> list[str]:
        ln, q = AU.loudnorm, AU.qa
        out = []
        if self.final_loudness is not None and not self.loudness_ok:
            out.append(f"최종 음량 {self.final_loudness.I:.2f} LUFS — 목표 {ln.I:g} ± {q.i_tol_lu:g}")
        if self.final_loudness is not None and not self.true_peak_ok:
            out.append(f"트루 피크 {self.final_loudness.TP:.2f} dBTP > {ln.TP:g} + 코덱 여유 {q.tp_codec_margin_db:g}")
        if self.music_level_ok is False:
            lo, hi = q.music_under_narration_db
            out.append(f"내레이션 구간 음악 {self.music_under_narration_db:+.2f} dB — 범위 [{lo:g}, {hi:g}]")
        if not self.peak_ok:
            out.append(f"mix 피크 {self.mix_peak:.4f} > master_peak {AU.master_peak}")
        return out

    def warnings(self) -> list[str]:
        """warning 등급(D-0061 쟁점 2) — 문장 음량 편차. hard 는 issues()."""
        return [f"문장 {s} RMS 가 평균에서 {AU.qa.sentence_rms_dev_db:g}dB 넘게 벗어남" for s in self.sentence_rms_outliers]


def db(x: float) -> float:
    return 20 * math.log10(max(x, AU.norm_eps ** 2))


def _target() -> str:
    ln = AU.loudnorm
    return f"loudnorm=I={ln.I:g}:TP={ln.TP:g}:LRA={ln.LRA:g}"


def _loudnorm_json(inputs: list[str], af: str) -> dict:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *inputs, "-af", af + ":print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, check=True).stderr
    return json.loads(err[err.rindex("{"):err.rindex("}") + 1])


def measure_loudnorm(path: Path) -> Loudness:
    blob = _loudnorm_json(["-i", str(path)], _target())
    return Loudness(I=float(blob["input_i"]), TP=float(blob["input_tp"]), LRA=float(blob["input_lra"]))


def mix_inputs(mix_f32: Path, total: float) -> list[str]:
    return ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-t", f"{total:.3f}", "-i", str(mix_f32)]


def loudnorm_two_pass(mix_f32: Path, total: float) -> tuple[str, dict]:
    """2패스 loudnorm(v3.4.0 D-0061 쟁점 1 C): 1패스 측정 → 2패스 measured_* + linear=true 필터 문자열과 기록.
    linear 로 목표 TP 를 지킬 수 없으면 ffmpeg 가 dynamic 으로 처리한다 — 그 사실을 기록에 남긴다(숨기지 않음, P5·P6)."""
    ins = mix_inputs(mix_f32, total)
    p1 = _loudnorm_json(ins, _target())
    af = (f"{_target()}:measured_I={p1['input_i']}:measured_TP={p1['input_tp']}:measured_LRA={p1['input_lra']}"
          f":measured_thresh={p1['input_thresh']}:offset={p1['target_offset']}:linear=true")
    p2 = _loudnorm_json(ins, af)
    rec = {"pass1": {k: float(p1[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")},
           "pass2": {"output_i": float(p2["output_i"]), "output_tp": float(p2["output_tp"]),
                     "normalization_type": p2["normalization_type"]},
           "post_limiter_dbfs": AU.post_limiter_dbfs}
    # RENDER-AP-004 — loudnorm 뒤 샘플 피크 리미터(AAC 인코딩이 트루 피크를 올리는 만큼 미리 낮춘다). 값은 rules audio.post_limiter_dbfs
    af += f",alimiter=limit={10 ** (AU.post_limiter_dbfs / 20):.4f}:level=false:attack=1:release=50"
    return af, rec


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


def sentence_rms(sentences: list) -> dict[str, float]:  # noqa: ANN001
    """문장 npy 를 믹서처럼 피크 정규화(narration_peak)한 뒤, 창 RMS 중 무음(최대 대비 floor 이하)을 뺀 RMS(dB)."""
    q = AU.qa
    out: dict[str, float] = {}
    for i, x in enumerate(sentences):
        g = (lambda k: x.get(k)) if isinstance(x, dict) else (lambda k: getattr(x, k, None))  # noqa: E731
        a = np.load(g("npy")).astype(np.float32)
        a = a / (np.abs(a).max() + AU.norm_eps) * AU.narration_peak
        w = int(q.sentence_rms_window_sec * SR)
        k = len(a) // w
        fr = np.sqrt(np.mean(a[: k * w].reshape(k, w) ** 2, 1))
        act = fr[fr > fr.max() * 10 ** (q.sentence_rms_floor_db / 20)]
        out[str(g("sid") or i)] = round(db(float(np.sqrt(np.mean(act ** 2)))), 2)
    return out


def rms_outliers(srms: dict[str, float]) -> list[str]:
    """평균에서 audio.qa.sentence_rms_dev_db 넘게 벗어난 문장(warning 대상)."""
    if not srms:
        return []
    mean = float(np.mean(list(srms.values())))
    return [s for s, v in srms.items() if abs(v - mean) > AU.qa.sentence_rms_dev_db]


def audio_qa(out_dir: Path, sentences: list, has_music: bool = True) -> AudioQA:  # noqa: ANN001
    """out_dir = 프로젝트 out/(mix.f32 필수, final.mp4 있으면 음량 측정). has_music False(bgm null)면 음악 레벨 판정 없음."""
    mix, vo, mask = stems(out_dir / "mix.f32", sentences)
    srms = sentence_rms(sentences)
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
                   true_peak_ok=None if loud is None else round(loud.TP, 2) <= round(AU.loudnorm.TP + AU.qa.tp_codec_margin_db, 2),
                   music_level_ok=(lo <= mu_db - vo_db <= hi) if has_music else None, peak_ok=peak <= AU.master_peak,
                   sentence_rms_db=srms, sentence_rms_outliers=rms_outliers(srms))


__all__ = ["AudioQA", "Loudness", "audio_qa", "loudnorm_two_pass", "measure_loudnorm", "stems"]

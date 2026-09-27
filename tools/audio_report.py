"""오디오 리포트 (v2.0.1, back_and_forth D-0006 §2) — loudnorm 측정 + 내레이션 대비 음악 레벨.

- `out/final.mp4`(먹싱 후)의 ffmpeg loudnorm 측정값 I·TP·LRA (목표 −14 LUFS ±1, rules audio.loudnorm)
- `mix.f32`(먹싱 전)에서 내레이션 스템을 plan.json 의 npy 로 재구성(mix3 와 같은 0.8 피크 정규화·배치)하고,
  최소제곱으로 스케일을 맞춰 뺀 나머지를 음악+효과음 스템으로 본다. 내레이션 구간에서 두 스템의 RMS 차(dB).
  목표: 음악이 내레이션보다 14~18 dB 낮다(13 Phase 8, docs/handoff/10).
- 피크, 총 길이.

사용법: python tools/audio_report.py [--out docs/handoff/reports/phase1/audio_report.json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SR = 44100
LOUDNORM_MEASURE = "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json"


def measure_loudnorm(path: Path) -> dict[str, float]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", LOUDNORM_MEASURE,
                          "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    blob = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return {"I": float(blob["input_i"]), "TP": float(blob["input_tp"]), "LRA": float(blob["input_lra"])}


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def db(x: float) -> float:
    import math

    return 20 * math.log10(max(x, 1e-12))


def stems(root: Path, plan: dict) -> "tuple[object, object, object]":
    """(mix 모노, 내레이션 스템(스케일 적용), 내레이션 구간 마스크)."""
    import numpy as np

    mix = np.fromfile(root / "mix.f32", np.float32).reshape(-1, 2).mean(1)
    n = len(mix)
    vo = np.zeros(n, np.float32)
    mask = np.zeros(n, bool)
    for x in plan["sentences"]:
        a = np.load(x["npy"]).astype(np.float32)
        a = a / (np.abs(a).max() + 1e-6) * 0.8
        i0 = int(x["t0"] * SR)
        k = min(len(a), n - i0)
        vo[i0:i0 + k] += a[:k]
        mask[i0:int(x["t1"] * SR)] = True
    scale = float((mix[mask] @ vo[mask]) / max(float(vo[mask] @ vo[mask]), 1e-9))
    return mix, vo * scale, mask


def audio_report(root: Path, plan: dict) -> dict:
    import numpy as np

    rep: dict = {"schema_version": 1, "target": {"I": -14, "I_tol": 1, "music_below_narration_db": [14, 18]}}
    final = root / "out" / "final.mp4"
    if final.exists():
        rep["final_loudnorm"] = measure_loudnorm(final)
        rep["final_duration_sec"] = round(duration(final), 3)
    mix, vo, mask = stems(root, plan)
    music = mix - vo
    vo_rms = float(np.sqrt(np.mean(vo[mask] ** 2)))
    mu_rms = float(np.sqrt(np.mean(music[mask] ** 2)))
    gap = ~mask
    gap[: int(1.2 * SR)] = False  # 페이드 인 제외
    rep.update(
        mix_peak=round(float(np.abs(mix).max()), 4),
        mix_duration_sec=round(len(mix) / SR, 3),
        narration_rms_db=round(db(vo_rms), 2),
        music_rms_in_narration_db=round(db(mu_rms), 2),
        music_below_narration_db=round(db(vo_rms) - db(mu_rms), 2),
        music_rms_in_gaps_db=round(db(float(np.sqrt(np.mean(music[gap] ** 2)))), 2) if gap.any() else None,
        narration_seconds=round(mask.sum() / SR, 1),
        method="내레이션 스템 = plan npy 재배치(mix3 규칙) × 최소제곱 스케일, 음악 = mix − 내레이션",
    )
    lo, hi = rep["target"]["music_below_narration_db"]
    rep["music_level_ok"] = lo <= rep["music_below_narration_db"] <= hi
    if "final_loudnorm" in rep:
        rep["loudness_ok"] = abs(rep["final_loudnorm"]["I"] - (-14)) <= 1
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="오디오 리포트")
    ap.add_argument("--out", type=Path, default=REPO / "docs/handoff/reports/phase1/audio_report.json")
    args = ap.parse_args(argv)
    root = (REPO / os.environ.get("V3_ROOT", "projects/hormuz_korea_legacy")).resolve()
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    rep = audio_report(root, plan)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

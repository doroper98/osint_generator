"""음성 무음 트림·페이드 (v2.1.0, plan3 build 중반). 44.1k mono float32 npy 로 저장."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

SR = 44100
THRESH = 0.012      # 무음 판정 진폭
PRE_SEC = 0.03      # 첫 소리 앞 여유
POST_SEC = 0.12     # 끝 소리 뒤 여유
FADE_SEC = 0.01


def decode(mp3: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def trim(a: np.ndarray) -> np.ndarray:
    idx = np.where(np.abs(a) > THRESH)[0]
    if len(idx) == 0:
        raise ValueError("음성에 소리가 없다")
    a = a[max(0, idx[0] - int(PRE_SEC * SR)): min(len(a), idx[-1] + int(POST_SEC * SR))].copy()
    f = int(FADE_SEC * SR)
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    return a


def trim_to_npy(mp3: Path) -> tuple[Path, float]:
    a = trim(decode(mp3))
    npy = mp3.with_suffix(".npy")
    np.save(npy, a)
    return npy, len(a) / SR

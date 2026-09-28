"""음성 무음 트림·페이드 (v2.1.0, plan3 build 중반). 44.1k mono float32 npy 로 저장.

v2.3.0: 앞에서 잘라낸 길이(trim_offset, 초)를 돌려준다. 정렬 타임스탬프(원본 mp3 기준)를
트림된 음성 시각으로 옮길 때 뺀다(engine/timebase `at_word`, 03 §6.3).
"""

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


def trim(a: np.ndarray) -> tuple[np.ndarray, int]:
    """(트림·페이드된 음성, 앞에서 잘라낸 샘플 수)."""
    idx = np.where(np.abs(a) > THRESH)[0]
    if len(idx) == 0:
        raise ValueError("음성에 소리가 없다")
    start = max(0, idx[0] - int(PRE_SEC * SR))
    a = a[start: min(len(a), idx[-1] + int(POST_SEC * SR))].copy()
    f = int(FADE_SEC * SR)
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    return a, int(start)


def trim_to_npy(mp3: Path) -> tuple[Path, float, float]:
    """→ (npy 경로, 트림 후 길이 초, trim_offset 초)."""
    a, start = trim(decode(mp3))
    npy = mp3.with_suffix(".npy")
    np.save(npy, a)
    return npy, len(a) / SR, start / SR

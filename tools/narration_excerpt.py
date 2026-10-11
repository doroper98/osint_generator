"""내레이션만 발췌 (v5.20.0, back_and_forth D-0175 §2-9 — 끝 억양 보정 전/후 청취 자료).

    python tools/narration_excerpt.py <plan.json> <out.mp3> [--npy-dir DIR] [--t0 0] [--t1 60]

plan 의 문장 음성(npy, 44.1k mono)을 각 문장 t0 자리에 놓아 [t0, t1] 구간만 mp3 로 낸다(음악·효과음 없음).
--npy-dir 를 주면 npy 를 그 폴더에서 같은 파일 이름으로 찾는다(보정 전 사본과 비교할 때).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 44100


def excerpt(plan: dict, t0: float, t1: float, npy_dir: Path | None = None) -> np.ndarray:
    out = np.zeros(int(round((t1 - t0) * SR)), np.float32)
    for s in plan["sentences"]:
        if s["t1"] <= t0 or s["t0"] >= t1:
            continue
        p = Path(s["npy"]) if npy_dir is None else npy_dir / Path(s["npy"]).name
        a = np.load(p)
        k = int(round((s["t0"] - t0) * SR))
        lo, hi = max(k, 0), min(k + len(a), len(out))
        if hi > lo:
            out[lo:hi] += a[lo - k: hi - k]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plan", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--npy-dir", type=Path, default=None)
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--t1", type=float, default=60.0)
    a = ap.parse_args(argv)
    x = excerpt(json.loads(a.plan.read_text(encoding="utf-8")), a.t0, a.t1, a.npy_dir)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "128k", str(a.out)],
                   input=pcm, check=True)
    print(json.dumps({"out": str(a.out), "sec": round(len(x) / SR, 2)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

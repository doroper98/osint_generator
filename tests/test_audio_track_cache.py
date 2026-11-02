"""v7.4.0 back_and_forth D-1000 S2-9·D-1002 §4 — 인코딩된 오디오 트랙 재사용(engine.mux.audio_track·mux_av).

같은 mix·필터 → 트랙 재사용(reused), 묶은 mp4 의 오디오 스트림 바이트가 새로 인코딩한 것과 같다. mix 1샘플 변경 → 다시 인코딩(encoded).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from engine.mux import SR, audio_track, mux_av

TOTAL = 4.0


def _mix(p: Path) -> None:
    t = np.arange(int(TOTAL * SR) + SR) / SR
    x = (0.2 * np.sin(2 * np.pi * 330 * t)).astype(np.float32)
    np.repeat(x[:, None], 2, 1).tofile(p)


def _audio_md5(mp4: Path) -> str:
    return subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-map", "0:a", "-c", "copy", "-f", "md5", "-"],
                          capture_output=True, text=True, check=True).stdout.strip()


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg 없음")
class AudioTrackCacheTest(unittest.TestCase):
    def test_reuse_identical_and_invalidate(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            mix = d / "mix.f32"
            _mix(mix)
            video = d / "v.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s=64x36:r=24:d={TOTAL}", "-pix_fmt", "yuv420p",
                            str(video)], check=True)
            t1, r1 = audio_track(mix, TOTAL)
            self.assertEqual(r1["audio"], "encoded")
            mux_av(video, t1, TOTAL, d / "a.mp4", "표식")
            t2, r2 = audio_track(mix, TOTAL)
            self.assertEqual((r2["audio"], t2), ("reused", t1))
            mux_av(video, t2, TOTAL, d / "b.mp4")
            self.assertEqual(_audio_md5(d / "a.mp4"), _audio_md5(d / "b.mp4"))
            first = t1.read_bytes()
            t1.unlink()   # 캐시를 지우고 새로 인코딩해도 같은 바이트(인코더 결정적) — 재사용이 결과를 바꾸지 않는다
            t3, r3 = audio_track(mix, TOTAL)
            self.assertEqual((r3["audio"], t3.read_bytes()), ("encoded", first))
            x = np.fromfile(mix, np.float32)
            x[100] += 0.01
            x.tofile(mix)
            t4, r4 = audio_track(mix, TOTAL)
            self.assertEqual(r4["audio"], "encoded")
            self.assertNotEqual(t4, t3)
            self.assertEqual(sorted(p.name for p in (d / "audio_cache").glob("*.m4a")), [t4.name])   # 한 벌만


if __name__ == "__main__":
    unittest.main()

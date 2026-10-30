"""v7.4.0 back_and_forth D-0251 §1.3 — 쇼케이스 결합본 도구(tools/showcase_concat.py): concat·조건 불일치 거부·카탈로그 거부."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.showcase_concat import concat


def _clip(p: Path, w: int = 320, comment: str = "") -> Path:
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=gray:s={w}x180:r=24:d=1", "-f", "lavfi", "-i",
           "sine=frequency=440:sample_rate=48000:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", "2", "-shortest"]
    if comment:
        cmd += ["-metadata", f"comment={comment}"]
    subprocess.run([*cmd, str(p)], check=True)
    return p


class ConcatTest(unittest.TestCase):
    def test_concat_and_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a, b = _clip(Path(d) / "a.mp4"), _clip(Path(d) / "b.mp4")
            rows = concat([a, b], Path(d) / "showcase.mp4")
            self.assertEqual(len(rows), 3)
            self.assertIn("재인코딩 없음", rows[-1])
            with self.assertRaises(ValueError):
                concat([a, _clip(Path(d) / "c.mp4", w=480)], Path(d) / "x.mp4")
            with self.assertRaises(ValueError):
                concat([a, _clip(Path(d) / "k.mp4", comment="catalog — 카탈로그 판")], Path(d) / "y.mp4")


if __name__ == "__main__":
    unittest.main()

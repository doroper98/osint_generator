"""NB28 — 1080p 클립은 원본에서 뽑은 media/res_<프로파일>/{file}.npy 를 읽는다, 없으면 오류 (v4.0.0, back_and_forth D-0074).

기본 프로파일(480p) 경로는 그대로 `{file}_480.npy` 다(480p 결과 불변). 480p 클립을 늘려 쓰는 폴백은 없다(15 P6).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from pydantic import ValidationError

from engine.assets import AssetError, Assets
from orchestrator.config import OutputProfile, load_config

REPO = Path(__file__).resolve().parent.parent


def _bare(root: Path, res: str | None) -> Assets:
    """load_clip 만 쓰는 최소 객체(지형 티어 없이)."""
    a = Assets.__new__(Assets)
    a.root, a.res, a.clips = root, res, {}
    return a


class ClipPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "media" / "res_1080p").mkdir(parents=True)
        np.save(self.root / "media" / "c_480.npy", np.zeros((2, 270, 480, 3), np.uint8))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_default_profile_reads_480(self) -> None:
        a = _bare(self.root, None)
        a.load_clip("c")
        self.assertEqual(a.clips["c"].shape[2], 480)

    def test_other_profile_missing_is_error_not_fallback(self) -> None:
        with self.assertRaises(AssetError) as cm:
            _bare(self.root, "1080p").load_clip("c")
        self.assertIn("media_fetch.py", str(cm.exception))
        self.assertIn("--res 1080p", str(cm.exception))

    def test_other_profile_reads_res_dir(self) -> None:
        np.save(self.root / "media" / "res_1080p" / "c.npy", np.zeros((2, 576, 1024, 3), np.uint8))
        a = _bare(self.root, "1080p")
        a.load_clip("c")
        self.assertEqual(a.clips["c"].shape[1:], (576, 1024, 3))


class ClipConfigTest(unittest.TestCase):
    def test_1080p_clip_is_1024x576(self) -> None:
        _, p = load_config().engine.profile("1080p")   # v5.5.1 — final 은 720p(클립 null), 1080p 는 이름으로
        self.assertEqual(p.clip, (1024, 576))
        _, t = load_config().engine.profile("trial")
        self.assertIsNone(t.clip)

    def test_clip_must_be_16_9(self) -> None:
        with self.assertRaises(ValidationError):
            OutputProfile(width=1920, height=1080, fps=24, crf=19, preset="faster", mem_per_job_mb=1, clip=(1080, 608))

    def test_media_fetch_rejects_default_profile(self) -> None:
        from tools.media_fetch import MediaFetchError, run  # noqa: PLC0415
        with tempfile.TemporaryDirectory() as d, self.assertRaises(MediaFetchError):
            run(Path(d), registry={}, res="480p")


@unittest.skipUnless((REPO / "projects/hormuz_korea/media/res_1080p/strikes.npy").exists(), "환경: 1080p 클립 없음(media_fetch --res 1080p)")
class HormuzClipTest(unittest.TestCase):
    def test_hormuz_1080_clips_shape(self) -> None:
        for k in ("strikes", "niovi"):
            a = np.load(REPO / f"projects/hormuz_korea/media/res_1080p/{k}.npy", mmap_mode="r")
            b = np.load(REPO / f"projects/hormuz_korea/media/{k}_480.npy", mmap_mode="r")
            self.assertEqual(a.shape, (b.shape[0], 576, 1024, 3))


if __name__ == "__main__":
    unittest.main()

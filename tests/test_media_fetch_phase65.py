"""tools/media_fetch — 검수 시트·실패 집계·NB4 설정 (D-0036 작업 4·5·8)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.media_registry import load_media_registry  # noqa: E402
from orchestrator.config import load_config  # noqa: E402
from tools import commons_fetch, media_fetch  # noqa: E402


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg 없음 — run_log §0 apt-get install ffmpeg (D-0039 NB7)")
class ThumbSheetTest(unittest.TestCase):
    def test_twelve_frames(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "t.webm"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=6:size=320x180:rate=24",
                            "-c:v", "libvpx-vp9", "-b:v", "200k", str(src)], check=True)
            out = Path(d) / "sheet.jpg"
            times = media_fetch.thumbsheet(src, out, "t", (1.0, 3.0))
            self.assertEqual(len(times), media_fetch.SHEET_N)
            self.assertEqual(media_fetch.SHEET_N, 12)   # 14 §10.3-3
            im = Image.open(out)
            self.assertEqual(im.width, media_fetch.SHEET_TILE[0] * media_fetch.SHEET_COLS)


class FailureReportTest(unittest.TestCase):
    def test_changed_source_is_loud_with_rerun_command(self) -> None:
        reg = load_media_registry()
        a = reg["hormuz_transit"]
        fake = a.model_copy(update={"tool": a.tool.model_copy(update={"params": {**a.tool.params, "source": "x.jpg"}})})
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "media").mkdir()
            Image.new("RGB", (64, 40), (10, 20, 30)).save(Path(d) / "media" / "x.jpg")   # 원본과 다른 바이트
            with self.assertRaises(media_fetch.MediaFetchError) as cm:
                media_fetch.run(Path(d), registry={"hormuz_transit": fake}, sheets=False)
            msg = str(cm.exception)
            self.assertIn("남은 항목", msg)
            self.assertIn("--only hormuz_transit", msg)
            self.assertIn("source_hash", msg)

    def test_articles_have_no_files(self) -> None:
        reg = {k: v for k, v in load_media_registry().items() if v.kind == "article"}
        with tempfile.TemporaryDirectory() as d:
            rep = media_fetch.run(Path(d), registry=reg)
        self.assertEqual({v["kind"] for v in rep["assets"].values()}, {"article"})


class CommonsConfigTest(unittest.TestCase):
    def test_nb4_values_from_config(self) -> None:
        c = load_config().commons
        self.assertEqual(commons_fetch.TRIES, c.tries)
        self.assertEqual(commons_fetch.COMMONS_GAP_SEC, c.gap_sec)
        self.assertEqual(commons_fetch.backoff_sec(10), c.backoff_max_sec)
        self.assertEqual(commons_fetch.STANDARD_WIDTHS, tuple(c.standard_widths))


if __name__ == "__main__":
    unittest.main()

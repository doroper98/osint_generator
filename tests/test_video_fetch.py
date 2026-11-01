"""영상 받기 골격(v7.4.0, 사용자 의견 UF-141 준비) — tools/media_fetch.video_fetch_command. 네트워크 없이 검사한다.

허용 도메인 밖 주소·버전 다른 yt-dlp 는 오류. 봇 검사 우회 옵션(쿠키·클라이언트 위장·추출기 인자)은 명령에 없다.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from orchestrator.config import load_config
from tools import media_fetch

VF = load_config().media.video_fetch
BYPASS = re.compile(r"cookie|impersonat|extractor-args|user-agent|add-header|geo-bypass|proxy", re.I)


def _ver(v: str) -> mock.MagicMock:
    return mock.MagicMock(return_value=subprocess.CompletedProcess(["yt-dlp", "--version"], 0, stdout=v + "\n", stderr=""))


class VideoFetchTest(unittest.TestCase):
    def test_config_pinned(self) -> None:
        self.assertIsNotNone(VF)
        req = Path(media_fetch.REPO / "requirements-engine.txt").read_text(encoding="utf-8")
        self.assertIn(f"yt-dlp=={VF.yt_dlp_version}", req)
        self.assertNotIn("youtube.com", VF.allowed_domains)

    def test_allowed_domain_command(self) -> None:
        with mock.patch.object(media_fetch.subprocess, "run", _ver(VF.yt_dlp_version)):
            cmd = media_fetch.video_fetch_command("https://www.federalreserve.gov/videos/x", Path("/tmp/x.mp4"))
        self.assertEqual(cmd[0], "yt-dlp")
        self.assertIn(f"height<={VF.max_height}", " ".join(cmd))
        self.assertFalse(any(BYPASS.search(c) for c in cmd), cmd)

    def test_refuses_other_domain(self) -> None:
        with mock.patch.object(media_fetch.subprocess, "run", _ver(VF.yt_dlp_version)):
            for url in ("https://www.youtube.com/watch?v=x", "https://evilfederalreserve.gov/x"):
                with self.assertRaises(media_fetch.MediaFetchError):
                    media_fetch.video_fetch_command(url, Path("/tmp/x.mp4"))

    def test_refuses_version_mismatch(self) -> None:
        with mock.patch.object(media_fetch.subprocess, "run", _ver("2020.01.01")):
            with self.assertRaises(media_fetch.MediaFetchError):
                media_fetch.video_fetch_command("https://www.c-span.org/video/x", Path("/tmp/x.mp4"))


if __name__ == "__main__":
    unittest.main()

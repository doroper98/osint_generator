"""tools/youtube_upload.py 단위 시험 (v7.4.0 D-1200) — 비밀값·네트워크 없이 돈다(가짜 전송)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import youtube_upload as yu  # noqa: E402

DESC = "제품은 팔고 · 시험 영상\n\n요약 문장입니다.\n\n챕터\n0:00 시작\n0:30 끝"
SRT = "1\n00:00:01,200 --> 00:00:02,000\n자막입니다.\n"


def _proj(tmp: Path, desc: str = DESC) -> Path:
    out = tmp / "out"
    out.mkdir(parents=True)
    (out / "final.mp4").write_bytes(b"\0" * 1000)
    (out / "description.txt").write_text(desc, encoding="utf-8")
    (out / "final.srt").write_text(SRT, encoding="utf-8")
    return tmp


class MetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = yu.youtube_cfg()

    def test_config_is_private_only(self) -> None:
        self.assertEqual(self.cfg.privacy_status, "private")

    def test_parse_title_and_body(self) -> None:
        title, body = yu.parse_description(DESC)
        self.assertEqual(title, "제품은 팔고 · 시험 영상")
        self.assertTrue(body.startswith("요약 문장입니다."))

    def test_body_fields(self) -> None:
        m = yu.build_metadata(DESC, ["중국"], True, self.cfg)
        b = m.body()
        self.assertEqual(b["status"]["privacyStatus"], "private")
        self.assertIs(b["status"]["containsSyntheticMedia"], True)
        self.assertEqual(b["snippet"]["categoryId"], self.cfg.category_id)
        self.assertEqual(yu.validate_metadata(m, self.cfg), [])

    def test_description_byte_limit_is_error_not_trim(self) -> None:
        long = "제목\n\n" + "가" * 2000   # 6000 바이트
        m = yu.build_metadata(long, [], False, self.cfg)
        errs = yu.validate_metadata(m, self.cfg)
        self.assertTrue(any("바이트" in e for e in errs))
        self.assertEqual(len(m.description), 2000)   # 몰래 자르지 않는다

    def test_title_limit_and_forbidden_chars(self) -> None:
        m = yu.build_metadata("가" * 101 + "<\n\n본문>", [], False, self.cfg)
        errs = yu.validate_metadata(m, self.cfg)
        self.assertEqual(len(errs), 3)

    def test_missing_secrets_error(self) -> None:
        with self.assertRaises(yu.UploadError) as cm:
            yu.read_secrets({"YT_CLIENT_ID": "x"})
        self.assertIn("YT_REFRESH_TOKEN", str(cm.exception))


class CliTest(unittest.TestCase):
    def test_dry_run_needs_no_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d))
            self.assertEqual(yu.main([str(proj), "--synthetic-media", "yes", "--dry-run"]), 0)
            self.assertFalse((proj / "out" / "youtube_upload.json").exists())

    def test_dry_run_fails_on_long_description(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d), "제목\n\n" + "가" * 2000)
            self.assertEqual(yu.main([str(proj), "--synthetic-media", "no", "--dry-run"]), 1)

    def test_missing_video_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d))
            (proj / "out" / "final.mp4").unlink()
            self.assertEqual(yu.main([str(proj), "--synthetic-media", "yes", "--dry-run"]), 1)

    def test_synthetic_flag_required(self) -> None:
        with tempfile.TemporaryDirectory() as d, self.assertRaises(SystemExit):
            yu.main([str(_proj(Path(d))), "--dry-run"])


class FlowTest(unittest.TestCase):
    """가짜 전송으로 토큰 갱신 → 재개 가능 업로드(308 한 번) → 자막 흐름."""

    def setUp(self) -> None:
        self.cfg = yu.youtube_cfg().model_copy(update={"chunk_mb": 1})

    def test_invalid_grant_message(self) -> None:
        def h(req: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "invalid_grant"})
        with httpx.Client(transport=httpx.MockTransport(h)) as c, self.assertRaises(yu.UploadError) as cm:
            yu.access_token(c, self.cfg, ("a", "b", "c"))
        self.assertIn("토큰 만료", str(cm.exception))

    def test_resumable_upload_and_caption(self) -> None:
        size = 1024 * 1024 + 10
        seen: list[str] = []

        def h(req: httpx.Request) -> httpx.Response:
            if req.url.host == "upload.session":
                cr = req.headers["content-range"]
                seen.append(cr)
                if cr.endswith(f"-{size - 1}/{size}"):
                    return httpx.Response(200, json={"id": "VID123"})
                return httpx.Response(308, headers={"range": f"bytes=0-{1024 * 1024 - 1}"})
            if "captions" in req.url.path:
                self.assertIn(b"VID123", req.content)
                return httpx.Response(200, json={"id": "CAP1"})
            body = json.loads(req.content)
            self.assertEqual(body["status"]["privacyStatus"], "private")
            return httpx.Response(200, headers={"location": "https://upload.session/s"})

        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "v.mp4"
            v.write_bytes(b"\0" * size)
            s = Path(d) / "s.srt"
            s.write_text(SRT, encoding="utf-8")
            meta = yu.build_metadata(DESC, [], True, self.cfg)
            with httpx.Client(transport=httpx.MockTransport(h)) as c:
                self.assertEqual(yu.upload_video(c, self.cfg, "tok", v, meta), "VID123")
                self.assertEqual(yu.upload_caption(c, self.cfg, "tok", "VID123", s), "CAP1")
        self.assertEqual(len(seen), 2)

    def test_quota_error_hint(self) -> None:
        def h(req: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"error": {"message": "q", "errors": [{"reason": "quotaExceeded"}]}})
        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "v.mp4"
            v.write_bytes(b"\0")
            meta = yu.build_metadata(DESC, [], True, self.cfg)
            with httpx.Client(transport=httpx.MockTransport(h)) as c, self.assertRaises(yu.UploadError) as cm:
                yu.upload_video(c, self.cfg, "tok", v, meta)
        self.assertIn("할당량", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

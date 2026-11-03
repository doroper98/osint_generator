"""publish.youtube 단위 시험 (v7.4.0 D-1200) — 비밀값·네트워크 없이 돈다(가짜 전송)."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import httpx

from orchestrator import engine_service as es
from publish import youtube as yu
from schemas.models import ProjectState

DESC = "제품은 팔고 · 시험 영상\n\n요약 문장입니다.\n\n챕터\n0:00 시작\n0:30 끝"
SRT = "1\n00:00:01,200 --> 00:00:02,000\n자막입니다.\n"
ENV = {"YT_CLIENT_ID": "id", "YT_CLIENT_SECRET": "sec", "YT_REFRESH_TOKEN": "rt"}


def _sources_desc(n: int, title_len: int) -> str:
    lines = [f"매체{i} “{'제' * title_len}” — https://example.com/{'a' * 60}/{i}" for i in range(n)]
    return DESC + "\n\n출처 원문 (보도 · 자료 · X 게시물)\n" + "\n".join(lines)


def _proj(tmp: Path, desc: str = DESC, video: bytes = b"\0" * 1000) -> Path:
    out = tmp / "out"
    out.mkdir(parents=True)
    (out / "final.mp4").write_bytes(video)
    (out / "description.txt").write_text(desc, encoding="utf-8")
    (out / "final.srt").write_text(SRT, encoding="utf-8")
    return tmp


def _fake_api(size: int, calls: list[str]) -> httpx.MockTransport:
    def h(req: httpx.Request) -> httpx.Response:
        if req.url.host == "oauth2.googleapis.com":
            calls.append("token")
            return httpx.Response(200, json={"access_token": "AT"})
        if req.url.host == "upload.session":
            calls.append("put")
            return httpx.Response(200, json={"id": "VID123"})
        if "captions" in req.url.path:
            calls.append("caption")
            return httpx.Response(200, json={"id": "CAP1"})
        calls.append("start")
        assert json.loads(req.content)["status"]["privacyStatus"] == "private"
        return httpx.Response(200, headers={"location": "https://upload.session/s"})
    return httpx.MockTransport(h)


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
        m, trims = yu.build_metadata(DESC, ["중국"], True, self.cfg)
        b = m.body()
        self.assertEqual(trims, [])
        self.assertEqual(b["status"]["privacyStatus"], "private")
        self.assertIs(b["status"]["containsSyntheticMedia"], True)
        self.assertEqual(b["snippet"]["categoryId"], self.cfg.category_id)
        self.assertEqual(yu.validate_metadata(m, self.cfg), [])

    def test_fit_step1_drops_quoted_titles_keeps_links(self) -> None:
        _, body = yu.parse_description(_sources_desc(20, 80))   # 제목이 길어 넘침, 제목만 빼면 들어감
        self.assertGreater(len(body.encode()), 5000)
        out, trims = yu.fit_description(body, 5000)
        self.assertLessEqual(len(out.encode()), 5000)
        self.assertEqual(out.count("https://"), 20)
        self.assertNotIn("“", out)
        self.assertEqual(len(trims), 1)

    def test_fit_step2_drops_tail_links_and_says_so(self) -> None:
        _, body = yu.parse_description(_sources_desc(60, 5))
        out, trims = yu.fit_description(body, 5000)
        self.assertLessEqual(len(out.encode()), 5000)
        self.assertIn("링크 생략", out)
        self.assertTrue(out.split("\n")[-2].startswith("매체59"))   # 출처 이름은 모두 남는다
        self.assertTrue(any("링크 생략" in t for t in trims))

    def test_fit_without_sources_section_is_error(self) -> None:
        with self.assertRaises(yu.UploadError):
            yu.fit_description("가" * 2000, 5000)

    def test_title_limit_and_forbidden_chars(self) -> None:
        m, _ = yu.build_metadata("가" * 101 + "<\n\n본문>", [], False, self.cfg)
        self.assertEqual(len(yu.validate_metadata(m, self.cfg)), 3)

    def test_missing_secrets_error(self) -> None:
        with self.assertRaises(yu.UploadError) as cm:
            yu.read_secrets({"YT_CLIENT_ID": "x"})
        self.assertIn("YT_REFRESH_TOKEN", str(cm.exception))


class StageTest(unittest.TestCase):
    def _main(self, argv: list[str]) -> tuple[int, dict]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = yu.main(argv)
        return rc, json.loads(out.getvalue().strip().splitlines()[-1])

    def test_pipeline_wiring(self) -> None:
        self.assertEqual(es.STATE_STAGES[ProjectState.DELIVER], ("deliver", "upload"))
        self.assertEqual(es.STAGE_COMMANDS["upload"], ("publish.youtube", "upload"))

    def test_dry_run_stage_result(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d))
            rc, res = self._main([str(proj), "--dry-run"])
            self.assertEqual((rc, res["ok"], res["stage"]), (0, True, "upload"))
            self.assertFalse((proj / "out" / "youtube_upload.json").exists())
            self.assertEqual(es.parse_result("upload", rc, json.dumps(res), "").ok, True)

    def test_missing_secrets_stage_fails(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d))
            with self.assertRaises(yu.UploadError):
                yu.run(proj, env={})

    def test_missing_video_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d))
            (proj / "out" / "final.mp4").unlink()
            rc, res = self._main([str(proj), "--dry-run"])
            self.assertEqual((rc, res["ok"]), (1, False))

    def test_full_flow_records_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = _proj(Path(d))
            calls: list[str] = []
            res = yu.run(proj, transport=_fake_api(1000, calls), env=ENV)
            self.assertTrue(res.ok)
            self.assertEqual(calls, ["token", "start", "put", "caption"])
            rec = yu.UploadRecord.model_validate_json((proj / "out" / "youtube_upload.json").read_text(encoding="utf-8"))
            self.assertEqual((rec.video_id, rec.caption_id, rec.privacy_status), ("VID123", "CAP1", "private"))
            again = yu.run(proj, transport=_fake_api(1000, calls), env=ENV)   # 같은 영상 → 다시 안 올림
            self.assertTrue(again.ok)
            self.assertEqual(len(calls), 4)
            self.assertIn("다시 올리지 않음", again.warnings[0])


class FlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = yu.youtube_cfg().model_copy(update={"chunk_mb": 1})
        self.meta, _ = yu.build_metadata(DESC, [], True, self.cfg)

    def test_invalid_grant_message(self) -> None:
        t = httpx.MockTransport(lambda r: httpx.Response(400, json={"error": "invalid_grant"}))
        with httpx.Client(transport=t) as c, self.assertRaises(yu.UploadError) as cm:
            yu.access_token(c, self.cfg, ("a", "b", "c"))
        self.assertIn("invalid_grant", str(cm.exception))

    def test_resumable_308_then_done(self) -> None:
        size = 1024 * 1024 + 10
        seen: list[str] = []

        def h(req: httpx.Request) -> httpx.Response:
            if req.url.host == "upload.session":
                cr = req.headers["content-range"]
                seen.append(cr)
                if cr.endswith(f"-{size - 1}/{size}"):
                    return httpx.Response(200, json={"id": "VID123"})
                return httpx.Response(308, headers={"range": f"bytes=0-{1024 * 1024 - 1}"})
            return httpx.Response(200, headers={"location": "https://upload.session/s"})

        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "v.mp4"
            v.write_bytes(b"\0" * size)
            with httpx.Client(transport=httpx.MockTransport(h)) as c:
                self.assertEqual(yu.upload_video(c, self.cfg, "tok", v, self.meta), "VID123")
        self.assertEqual(len(seen), 2)

    def test_5xx_retry_then_resume(self) -> None:
        state = {"n": 0}

        def h(req: httpx.Request) -> httpx.Response:
            if req.url.host == "upload.session":
                state["n"] += 1
                if state["n"] == 1:
                    return httpx.Response(503)
                if req.headers["content-range"].startswith("bytes */"):
                    return httpx.Response(308)          # 받은 것 없음 → 처음부터
                return httpx.Response(201, json={"id": "V2"})
            return httpx.Response(200, headers={"location": "https://upload.session/s"})

        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "v.mp4"
            v.write_bytes(b"\0" * 10)
            with httpx.Client(transport=httpx.MockTransport(h)) as c:
                self.assertEqual(yu.upload_video(c, self.cfg, "tok", v, self.meta, sleep=lambda s: None), "V2")

    def test_quota_error_hint(self) -> None:
        t = httpx.MockTransport(lambda r: httpx.Response(403, json={"error": {"message": "q", "errors": [{"reason": "quotaExceeded"}]}}))
        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "v.mp4"
            v.write_bytes(b"\0")
            with httpx.Client(transport=t) as c, self.assertRaises(yu.UploadError) as cm:
                yu.upload_video(c, self.cfg, "tok", v, self.meta)
        self.assertIn("할당량", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

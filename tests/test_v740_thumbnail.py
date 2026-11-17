"""썸네일 = 제목 카드 프레임 + 안쪽 액자선, 완성본과 함께 나온다 (v7.4.0 사용자 의견 UF-923·UF-924, D938).

사용자 원문(2026-11-17): "썸네일 이미지도 같이 줘. 제목이 표시 되는 이미지있지? 그거면 될거 같아. 그리고 내가 옅은 테두리를 썸네일로 하기로 규약을 정한거 같은데."
· "저 이미지 외곽 테두리가 아니라 이미지 외곽에서 몇 px 들어와서 그려지는 고급진 테두리를 말하느거잖아"
1차 전달본은 선을 이미지 맨 가장자리에 붙여 그렸다(UF-924) — 가장자리 화소가 바뀌면 이 시험이 실패한다.
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import cairo
import numpy as np
from pydantic import ValidationError

from engine import thumbnail
from rules import load_rules
from schemas.rules_models import ThumbnailBorder

T = load_rules().thumbnail
W, H = 1280, 720


def _white() -> cairo.ImageSurface:
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    c.set_source_rgb(1, 1, 1)
    c.paint()
    return s


def _px(s: cairo.ImageSurface) -> np.ndarray:
    """밝기(0~1) H×W."""
    a = np.ndarray((H, W, 4), np.uint8, s.get_data())
    return a[:, :, :3].mean(axis=2) / 255


class FrameLineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.s = _white()
        self.inset, self.lw = thumbnail.draw_border(self.s)
        self.px = _px(self.s)

    def test_line_is_inset_from_the_image_edge(self) -> None:
        """UF-924 — 이미지 맨 가장자리에는 아무것도 그리지 않는다. 선은 가장자리에서 inset 만큼 안쪽에 있다."""
        m = int(self.inset) - 1
        self.assertGreaterEqual(m, 8, "선이 가장자리에 너무 붙었다")
        for band in (self.px[:m, :], self.px[-m:, :], self.px[:, :m], self.px[:, -m:]):
            self.assertEqual(float(band.min()), 1.0, "가장자리 띠에 선이 그려졌다(가장자리 테두리 — UF-924)")

    def test_line_runs_on_all_four_sides(self) -> None:
        c = int(round(self.inset + self.lw / 2 - 0.5))
        for name, v in {"위": self.px[c, W // 2], "아래": self.px[H - 1 - c, W // 2], "왼": self.px[H // 2, c], "오른": self.px[H // 2, W - 1 - c]}.items():
            self.assertLess(float(v), 0.97, f"{name}쪽 선이 없다")

    def test_line_is_fine_and_faint(self) -> None:
        col = self.px[:, W // 2]
        dark = np.flatnonzero(col[:H // 2] < 0.999)
        self.assertLessEqual(len(dark), 4, "선이 굵다(가는 선 한 줄)")
        self.assertGreater(float(col.min()), 0.55, "선이 진하다(옅은 선)")
        self.assertEqual(float(self.px[H // 2, W // 2]), 1.0, "선 안쪽 화면을 건드렸다")

    def test_schema_refuses_an_edge_border(self) -> None:
        ok = T.border.model_dump()
        for bad in ({"inset": 0}, {"inset": 4}, {"w": 4.0}, {"alpha": 0.8}):
            with self.assertRaises(ValidationError, msg=str(bad)):
                ThumbnailBorder.model_validate({**ok, **bad})


class TitleFrameTest(unittest.TestCase):
    def test_time_is_inside_the_title_card(self) -> None:
        cards = [NS(kind="title", t0=31.27, t1=36.87), NS(kind="end", t0=486.9, t1=497.9)]
        t = thumbnail.title_time(cards)
        self.assertTrue(31.27 + 1.0 < t < 36.87 - 1.0, "등장·퇴장 구간을 피한 가운데 시각이어야 한다")
        self.assertIsNone(thumbnail.title_time(cards[1:]))

    def test_make_writes_the_title_frame_with_the_line(self) -> None:
        import engine.project as ep  # noqa: PLC0415
        import engine.render as er  # noqa: PLC0415

        seen: dict = {}

        def fake_frame(P, i):  # noqa: ANN001, ANN202, N803
            seen["i"] = i
            return _white(), bytearray()

        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            plan = NS(cards=[NS(kind="title", t0=10.0, t1=15.0)])
            P = NS(n_frames=24 * 60, R=NS(out=NS(name="720p")))  # noqa: N806
            with mock.patch.object(ep, "load_plan", return_value=plan), mock.patch.object(ep, "load_project", return_value=P) as lp, \
                    mock.patch.object(er, "render_frame", side_effect=fake_frame):
                rec = thumbnail.make(proj)
            self.assertTrue(rec["written"] and (proj / "out" / thumbnail.FILE).exists())
            self.assertEqual(seen["i"], int((10.0 + 5.0 * T.title_at) * 24))
            self.assertEqual(lp.call_args.kwargs["out"].name, "720p", "완성본 해상도로 그린다")
            self.assertEqual(rec["size"], [W, H])
            self.assertGreaterEqual(rec["border"]["inset_px"], 8)
            got = cairo.ImageSurface.create_from_png(str(proj / "out" / thumbnail.FILE))
            self.assertLess(float(_px(got).min()), 0.97, "저장한 파일에 액자선이 없다")

    def test_no_title_card_is_reported_not_skipped_silently(self) -> None:
        import engine.project as ep  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            (proj / "out").mkdir()
            (proj / "out" / thumbnail.FILE).write_bytes(b"old")
            with mock.patch.object(ep, "load_plan", return_value=NS(cards=[])):
                rec = thumbnail.make(proj)
            self.assertFalse(rec["written"])
            self.assertIn("제목 카드 없음", rec["reason"])
            self.assertFalse((proj / "out" / thumbnail.FILE).exists(), "지난 실행의 썸네일이 남았다")


class DeliveryWiringTest(unittest.TestCase):
    def test_mux_makes_the_thumbnail_with_the_final_video(self) -> None:
        """UF-923 — 썸네일은 완성본을 만드는 단계(engine.mux)가 같이 만든다. 따로 부르는 것을 잊어 전달물에서 빠지지 않게."""
        from engine import mux  # noqa: PLC0415

        src = inspect.getsource(mux.main)
        self.assertIn("make_thumbnail(proj)", src)
        self.assertIn('prov["thumbnail"]', src)
        self.assertIn("[thumbnail-skipped]", src)
        self.assertIn('"thumbnail": str(outd / THUMB_FILE)', src)

    def test_workflow_lists_the_thumbnail_as_a_deliverable(self) -> None:
        wf = (Path(__file__).resolve().parents[1] / "WORKFLOWS.md").read_text(encoding="utf-8")
        self.assertIn("out/thumbnail.png", wf)


if __name__ == "__main__":
    unittest.main()

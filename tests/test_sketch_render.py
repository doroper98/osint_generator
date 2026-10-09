"""스케치 렌더 루프·공통 그리기 연기 테스트 — D-0140 §5 S0.

가짜 장면(단색 프레임 + 라벨·태그·사선)으로 mp4·시트·provenance 가 끝까지 나오는지, 시트 시각이 영상 밖이면 실패하는지 본다.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import cairo

from engine.style import H_OUT, W_OUT, output_profile
from sketch.common.draw import Overlay, hatch
from sketch.common.render import base_provenance, render_video, write_frames, write_provenance
from sketch.common.spec import SketchProvenance

SPEC_TEXT = "schema_version: 1\nkind: test\n"


class _Scene:
    def __init__(self) -> None:
        self.out = output_profile("trial")

    def frame(self, t: float) -> bytes:
        OP = self.out
        buf = bytearray(OP.width * OP.height * 4)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * 4)
        ctx = cairo.Context(surf)
        ctx.translate(OP.pad_x, 0)
        ctx.scale(OP.k, OP.k)
        ctx.set_source_rgb(0.1, 0.1, 0.1 + t)
        ctx.paint()
        ctx.save()
        ctx.rectangle(100, 100, 200, 120)
        ctx.clip()
        hatch(ctx, [(1, 0.8, 0.4), (1, 0.3, 0.4)], 0.75, 5.0, 1.6)
        ctx.restore()
        ov = Overlay(ctx)
        box = ov.label2(W_OUT - 4, 200, 1.0, "화면 끝 라벨", "부제", anchor="l")
        ov.tag("개념도", 120, 300, (1, 0.7, 0.3), 1.0)
        ov.flush()
        surf.flush()
        self.box = box
        return bytes(buf)


class RenderLoopTest(unittest.TestCase):
    def test_video_sheet_provenance(self) -> None:
        sc = _Scene()
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            spec = out / "sketch.yaml"
            spec.write_text(SPEC_TEXT, encoding="utf-8")
            mp4, sheet, rec = render_video(sc, 0.5, [0.0, 0.25], out, "sketch_test")
            self.assertGreater(mp4.stat().st_size, 0)
            self.assertTrue(sheet.is_file())
            self.assertEqual(rec.frames, int(0.5 * sc.out.fps))
            self.assertEqual(rec.profile, sc.out.name)
            prov = base_provenance("test", spec)
            prov.render = rec
            p = write_provenance(prov, out)
            back = SketchProvenance.model_validate(json.loads(p.read_text(encoding="utf-8")))
            self.assertEqual(back.render.frames, rec.frames)
            self.assertEqual(len(back.spec_sha1), 40)
            pngs = write_frames(sc, [0.1], out, "frame")
            self.assertTrue(pngs[0].is_file())
            with self.assertRaises(RuntimeError):
                render_video(sc, 0.5, [3.0], out, "sketch_bad")      # 시트 시각이 영상 밖 = 실패(조용히 빠지지 않는다)

    def test_label_pushed_inside_screen(self) -> None:
        sc = _Scene()
        sc.frame(0.0)
        x0, _, x1, _ = sc.box
        self.assertLessEqual(x1, W_OUT)        # 오른쪽 끝 라벨은 화면 안으로 밀린다
        self.assertGreater(x1 - x0, 0)
        self.assertLess(sc.box[1], H_OUT)


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 back_and_forth D-0630 장치 — 진형 마감 배율(UF-260)·곡 하이라이트 배치(UF-263)·곡 편집 크레딧.

- 3D 마감: rules sketch.war.terrain3d.finish.supersample ≥ supersample_min(2) 이 아니면 규칙 오류. render.js 가 그 배율로 찍고
  engine.stage_terrain3d.downsample_frames 가 LANCZOS 로 줄인다(정수배가 아니면 오류).
- 곡 이어 붙이기: sound.bgm [{id, from, src}] — 영상 시각 → 원곡 시각, 곡 끝을 넘으면 오류(곡 처음으로 몰래 돌아가지 않음).
- [bgm-highlight](warning): 원곡 세기 상위 대목이 전투 구간에 드는 비율. [bgm-edit-credit](hard): src 를 쓰면 크레딧 music 행에 edit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
from PIL import Image
from pydantic import ValidationError

from engine import checks as C
from engine.credits import CreditItem
from engine.stage_terrain3d import Terrain3DError, downsample_frames
from rules import load_rules
from schemas.rules_models import T3Finish

REPO = Path(__file__).resolve().parents[1]
FIN = load_rules().sketch.war.terrain3d.finish


class FinishTest(unittest.TestCase):
    def test_supersample_floor(self) -> None:
        self.assertIsNotNone(FIN)
        self.assertGreaterEqual(FIN.supersample, FIN.supersample_min)
        self.assertGreaterEqual(FIN.supersample_min, 2)
        with self.assertRaises(ValidationError):
            T3Finish.model_validate({**FIN.model_dump(), "supersample": 1})   # 하한 아래 = 규칙 오류(UF-260)

    def test_tools_read_supersample(self) -> None:
        js = (REPO / "tools" / "terrain3d" / "render.js").read_text(encoding="utf-8")
        html = (REPO / "tools" / "terrain3d" / "view.html").read_text(encoding="utf-8")
        self.assertIn("deviceScaleFactor: ss", js)
        self.assertIn("scene.finish.supersample", js)
        self.assertIn("setPixelRatio(F.supersample)", html)
        self.assertIn("sunDir.x + nz * sunDir.z > 0", html)   # 모서리 빛은 해를 보는 변만

    def test_downsample(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f_0000.png"
            Image.new("RGB", (40, 20), (200, 10, 10)).save(f)
            self.assertEqual(downsample_frames(Path(d), (20, 10)), 1)
            self.assertEqual(Image.open(f).size, (20, 10))
            self.assertEqual(downsample_frames(Path(d), (20, 10)), 0)   # 이미 그 크기
            Image.new("RGB", (30, 20)).save(f)
            with self.assertRaises(Terrain3DError):
                downsample_frames(Path(d), (20, 10))


class BgmHighlightTest(unittest.TestCase):
    SEGS = [{"t": 0.0, "src": 0.0}, {"t": 173.1, "src": 328.25}, {"t": 216.2, "src": 400.0}, {"t": 254.6, "src": 182.0}, {"t": 319.6, "src": 439.5}]

    def test_source_times(self) -> None:
        got = C.bgm_source_times(self.SEGS, np.array([10.0, 173.1, 200.0, 216.2, 260.0, 330.0]))
        np.testing.assert_allclose(got, [10.0, 328.25, 355.15, 400.0, 187.4, 449.9])

    def test_overlap(self) -> None:
        src_db = -35.0 + np.random.default_rng(1).uniform(-5, 5, 500)   # 실제 녹음처럼 같은 값이 없다(분위수 동률 방지)
        src_db[330:360] = -17.0
        src_db[400:440] = -18.0
        battle = [(178.0, 256.0)]
        frac, _ = C.bgm_highlight_overlap(src_db, self.SEGS, 372.0, battle)
        self.assertGreaterEqual(frac, load_rules().audio.qa.bgm_highlight.min_overlap)
        frac0, _ = C.bgm_highlight_overlap(src_db, [{"t": 0.0, "src": 0.0}], 372.0, battle)   # 옮기기 전(v2): 하이라이트가 전투 밖
        self.assertLess(frac0, load_rules().audio.qa.bgm_highlight.min_overlap)

    def test_edit_credit(self) -> None:
        cr = NS(sections=[NS(items=[CreditItem.model_validate({"music": "music.beethoven_coriolan"})])])
        P = NS(R=NS(cache={"bgm_list": [{"id": "music.beethoven_coriolan", "t": 0.0}, {"id": "music.beethoven_coriolan", "t": 173.1, "src": 328.25}]}, credits=cr))  # noqa: N806
        self.assertEqual(len(C.check_bgm_edit_credit(P)), 1)
        cr.sections[0].items[0] = CreditItem.model_validate({"music": "music.beethoven_coriolan", "edit": "악구 이어 붙임"})
        self.assertEqual(C.check_bgm_edit_credit(P), [])
        with self.assertRaises(ValidationError):
            CreditItem.model_validate({"main": "x", "edit": "y"})   # edit 는 music 행만

    def test_severity(self) -> None:
        self.assertIn("bgm_highlight", C.WARN)
        self.assertIn("bgm_edit_credit", C.HARD)


class BgmSpliceLengthTest(unittest.TestCase):
    def test_past_end_is_error(self) -> None:
        from audio import mix as M  # noqa: PLC0415

        snd = M.Sound.model_validate({"bgm": [{"id": "music.beethoven_coriolan", "t": 0.0}, {"id": "music.beethoven_coriolan", "t": 100.0, "src": 480.0}],
                                      "intensity": [[0, 0.5], [1, 0.5]]})
        with self.assertRaises(ValueError):
            M.bgm_segments(NS(total=372.0), snd)


if __name__ == "__main__":
    unittest.main()

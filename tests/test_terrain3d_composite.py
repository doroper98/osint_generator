"""terrain3d 합성 골든(v7.4.0 back_and_forth D-0614 ② — 엔진 컷 md5) — 빠름.

고정 3D 프레임(tests/fixtures/terrain3d/expected, 재렌더 재현성은 test_terrain3d_render 가 MAD 로 잰다) 위에 엔진 구간 레이어
(engine.layers.terrain3d.draw_base + draw_labels — 병종 픽토그램·부대 이름·지명·'개략' 출처 줄)를 427×240(k = 0.5) 표면에 그려
프레임마다 화소 바이트 md5 를 고정한다. 3D 쪽은 브라우저 GPU 차가 있어 MAD, 글자·그림은 엔진(cairo)이라 바이트 고정으로 나눈다.
의도한 변경이면 md5 를 고치고 커밋 메시지에 사유를 적는다(골든 갱신 = 사람이 본 뒤).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import cairo

from engine import typography
from engine.layers import terrain3d as t3l
from engine.style import FPS, Output
from schemas.war_units import WarForces

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "tests" / "fixtures" / "terrain3d"
SOURCE = "폴리비오스 『역사』 III.113~116(Paton 영역 1922)"

COMPOSITE_MD5 = {
    0: "f3e8d4b826acba6d55e768e7b46515f1",
    1: "3d7ed6e3ef42095322815f15151c712d",
    2: "c6874afe65b0e40e1a9ab5e6e523eb2f",
}


def _project() -> SimpleNamespace:
    forces = WarForces(approximate=True, sources=[SOURCE],
                       factions={"a": {"token": "ru", "name": "A"}, "b": {"token": "us", "name": "B"}})
    out = Output("fixture", 427, 240, FPS, 23, "medium", 512)   # k = 0.5, pad_x = 0
    return SimpleNamespace(R=SimpleNamespace(out=out, cache={"terrain3d_forces": forces, "terrain3d_emblems": {}}))


class Terrain3DCompositeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(FIX / "expected", cls.tmp / "frames")   # draw_base 는 <구간>/frames/f_NNNN.png 를 읽는다
        cls.labels = json.loads((FIX / "expected" / "labels.json").read_text(encoding="utf-8"))["frames"]
        cls.prev_fix = typography.CONTRAST_FIX
        typography.CONTRAST_FIX = None

    @classmethod
    def tearDownClass(cls) -> None:
        typography.CONTRAST_FIX = cls.prev_fix
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _compose(self, P: SimpleNamespace, seg: t3l.SegFrames, i: int) -> str:  # noqa: N803
        out = P.R.out
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, out.width, out.height)
        ctx = cairo.Context(surf)
        ctx.translate(out.pad_x, 0)
        ctx.scale(out.k, out.k)   # render_frame 과 같은 변환
        t3l.draw_base(ctx, seg, i)
        t3l.draw_labels(ctx, P, seg, i, i / FPS)
        surf.flush()
        return hashlib.md5(bytes(surf.get_data())).hexdigest()

    def test_composite_md5(self) -> None:
        P = _project()  # noqa: N806
        seg = t3l.SegFrames("seg00", 0, len(self.labels), 0.0, len(self.labels) / FPS, self.tmp, self.labels)
        got = {i: self._compose(P, seg, i) for i in range(len(self.labels))}
        self.assertEqual(got, COMPOSITE_MD5)
        drawn = P.R.cache["terrain3d_approx_drawn"]["seg00"]   # [war-units-approx] 가 재는 기록
        self.assertEqual(drawn["frames"], len(self.labels))
        self.assertIn(SOURCE, drawn["line"])

    def test_behind_label_not_drawn(self) -> None:
        """가려진 점(behind)은 그리지 않는다 — 모든 라벨을 behind 로 바꾸면 이름·그림이 사라져 md5 가 달라진다."""
        hidden = [[{**x, "behind": True} for x in f] for f in self.labels]
        P = _project()  # noqa: N806
        seg = t3l.SegFrames("seg00", 0, len(hidden), 0.0, len(hidden) / FPS, self.tmp, hidden)
        self.assertNotEqual(self._compose(P, seg, 0), COMPOSITE_MD5[0])


if __name__ == "__main__":
    unittest.main()

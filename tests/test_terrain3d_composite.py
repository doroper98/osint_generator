"""terrain3d 합성 골든(v7.4.0 back_and_forth D-0614 ② — 엔진 컷 md5) — 빠름.

고정 3D 프레임(tests/fixtures/terrain3d/expected, 재렌더 재현성은 test_terrain3d_render 가 MAD 로 잰다) 위에 엔진 구간 레이어
(engine.layers.terrain3d.draw_base + draw_labels — 병종 픽토그램·부대 이름·지명·'개략' 출처 줄)를 427×240(k = 0.5) 표면에 그려
프레임마다 화소 바이트 md5 를 고정한다. 3D 쪽은 브라우저 GPU 차가 있어 MAD, 글자·그림은 엔진(cairo)이라 바이트 고정으로 나눈다.
의도한 변경이면 md5 를 고치고 커밋 메시지에 사유를 적는다(골든 갱신 = 사람이 본 뒤).
md5 는 표준 FONTCONFIG(/etc/fonts/fonts.conf 사본, conf.d 에서 12-unhinted-grayscale 뺌 — R-0310 §3·D-0623)에서 고정했다. 이 설정 없이 돌리면 글자 힌팅 차로 실패한다.
v7.4.0 D-0627(UF-257) — 부대 이름이 블록 바깥 자리(layout_labels)로 옮겨 md5 다시 고정(fixture labels.json 에 block 상자 추가, 3D 프레임 PNG 는 같음).
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
    0: "501dbe3f3afdeeb2ed4c3093c45481f4",
    1: "fcc6c04a0b583c7b3fef0deb5d1b3725",
    2: "66b87f51ec33dafc5bed6e01d95370df",
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


class Terrain3DSeamTest(unittest.TestCase):
    """구간 이음(D-0619 ①) — 경계에서 3D 알파 0(mercator 그대로), seam_sec 뒤 1, 나옴 앞 seam_sec 동안 다시 0 으로. 0 이면 바탕을 건드리지 않는다."""

    def test_seam_alpha_ramps(self) -> None:
        from rules import load_rules  # noqa: PLC0415

        sec = load_rules().stage_terrain3d.seam_sec
        seg = t3l.SegFrames("s", 0, 10, 10.0, 30.0, Path("."), [])
        self.assertEqual(t3l.seam_alpha(seg, 10.0), 0.0)
        self.assertEqual(t3l.seam_alpha(seg, 30.0), 0.0)
        self.assertEqual(t3l.seam_alpha(seg, 10.0 + sec), 1.0)
        self.assertEqual(t3l.seam_alpha(seg, 30.0 - sec), 1.0)
        ramp = [t3l.seam_alpha(seg, 10.0 + sec * k / 8) for k in range(9)]
        self.assertEqual(ramp, sorted(ramp))
        self.assertTrue(all(0 < a < 1 for a in ramp[1:-1]))

    def test_alpha_zero_leaves_base(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(FIX / "expected", tmp / "frames")
            seg = t3l.SegFrames("s", 0, 3, 0.0, 1.0, tmp, [])
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, 427, 240)
            ctx = cairo.Context(surf)
            ctx.set_source_rgb(0.3, 0.5, 0.7)
            ctx.paint()
            before = bytes(surf.get_data())
            t3l.draw_base(ctx, seg, 0, 0.0)
            surf.flush()
            self.assertEqual(bytes(surf.get_data()), before)
            t3l.draw_base(ctx, seg, 0, 0.5)
            surf.flush()
            self.assertNotEqual(bytes(surf.get_data()), before)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Terrain3DLabelBoxTest(unittest.TestCase):
    """카드 덮음·진형 가운데 검사가 쓰는 부대 상자 — 라벨 점을 품고(아래 변), 병종 그림 위까지 올라간다."""

    def test_box_contains_point(self) -> None:
        P = _project()  # noqa: N806
        rec = {"k": "unit", "name": "로마 중무장보병", "glyph": "heavy_inf", "x": 200.0, "y": 120.0}
        x0, y0, x1, y1 = t3l.label_box(P, rec)
        x, y = 200.0 / P.R.out.k, 120.0 / P.R.out.k
        self.assertTrue(x0 < x < x1 and y0 < y <= y1)   # D-0627 — 부대 상자 = 병종 그림(점 위) ∪ 블록. 이름 자리는 layout_labels
        px0, py0, px1, py1 = t3l.label_box(P, {**rec, "k": "place", "name": "칸나이"})
        self.assertGreater(py0, y0)   # 지명 상자는 병종 그림 자리가 없다


if __name__ == "__main__":
    unittest.main()

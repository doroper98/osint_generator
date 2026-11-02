"""terrain3d 3D 렌더 재현성(v7.4.0 back_and_forth D-0614 ②) — slow.

고정 scene(tests/fixtures/terrain3d/scene)을 tools/terrain3d/render.js 로 다시 렌더해 고정 프레임(expected/)과
평균 절대 화소 차(0~255) ≤ rules qa_checks.terrain3d_render_mad_max. 라벨 화면 좌표(labels.json, 본편 경로 — 글자는 엔진이 그린다)는
같은 개수·같은 이름·좌표 차 ≤ 1 px. 합성 골든(엔진 컷 md5)은 이 fixture 의 고정 프레임을 쓰는 별도 시험이다.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from rules import load_rules

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "tests" / "fixtures" / "terrain3d"
TOOL = REPO / "tools" / "terrain3d"
LABEL_TOL_PX = 1.0


def _render(dst: Path) -> None:
    import os  # noqa: PLC0415

    npm_root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["node", str(TOOL / "render.js"), str(dst)], check=True, cwd=TOOL, env={**os.environ, "NODE_PATH": npm_root},
                   capture_output=True, text=True, timeout=900)


@pytest.mark.slow
class Terrain3DRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("node") is None:
            raise unittest.SkipTest("node 없음 — terrain3d 렌더 도구(tools/terrain3d)는 node + playwright 가 필요하다")
        cls.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(FIX / "scene", cls.tmp / "scene")
        _render(cls.tmp / "scene")
        cls.got = cls.tmp / "scene" / "frames"

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_frames_within_mad(self) -> None:
        lim = load_rules().qa_checks.terrain3d_render_mad_max
        exp = sorted((FIX / "expected").glob("f_*.png"))
        self.assertEqual([p.name for p in exp], sorted(p.name for p in self.got.glob("f_*.png")))
        for p in exp:
            with self.subTest(frame=p.name):
                a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
                b = np.asarray(Image.open(self.got / p.name).convert("RGB"), dtype=np.float32)
                self.assertEqual(a.shape, b.shape)
                self.assertLessEqual(float(np.abs(a - b).mean()), lim)

    def test_labels_match(self) -> None:
        exp = json.loads((FIX / "expected" / "labels.json").read_text(encoding="utf-8"))["frames"]
        got = json.loads((self.got / "labels.json").read_text(encoding="utf-8"))["frames"]
        self.assertEqual(len(exp), len(got))
        for i, (fe, fg) in enumerate(zip(exp, got)):
            self.assertEqual([(x["k"], x["name"]) for x in fe], [(x["k"], x["name"]) for x in fg], i)
            for x, y in zip(fe, fg):
                self.assertLessEqual(max(abs(x["x"] - y["x"]), abs(x["y"] - y["y"])), LABEL_TOL_PX, (i, x["name"]))


class Terrain3DFixtureTest(unittest.TestCase):
    """fixture 자체(빠름) — 본편 경로(text_in_engine)·내려다보기 90° 첫 프레임·라벨 기록이 있는지."""

    def test_fixture_shape(self) -> None:
        s = json.loads((FIX / "scene" / "scene.json").read_text(encoding="utf-8"))
        self.assertTrue(s["text_in_engine"])
        self.assertEqual(s["frames"][0]["elev"], 90.0)
        self.assertTrue(all("glyph" not in u for u in s["units"]))   # 병종 그림은 엔진이 그린다
        lab = json.loads((FIX / "expected" / "labels.json").read_text(encoding="utf-8"))
        self.assertEqual(lab["schema_version"], 1)
        self.assertEqual(len(lab["frames"]), len(s["frames"]))
        self.assertTrue(all(x["k"] in ("unit", "place") for f in lab["frames"] for x in f))


if __name__ == "__main__":
    unittest.main()

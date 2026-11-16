"""고정 격자 조각 캐시 정확성(v7.4.0 back_and_forth D-1000 S2-6, 15 P6).

짧은 합성 픽스처(fed_timeline_demo, 64초·조각 7개)를 전체 렌더 → 가운데 조각 하나에만 걸리는 마커 하나를 바꾼다 →
캐시 렌더(바뀐 조각만 rendered) → 같은 입력을 --no-cache 로 렌더 → 두 결과를 디코드해 프레임별 md5 가 같아야 한다.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pytest


def framemd5(mp4: Path) -> list[str]:
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-map", "0:v", "-f", "framemd5", "-"],
                         capture_output=True, text=True, check=True).stdout
    return [ln.rsplit(",", 1)[1].strip() for ln in out.splitlines() if ln and not ln.startswith("#")]


@pytest.mark.slow   # C8.3(D187) — 렌더 3회
class ChunkCacheCorrectnessTest(unittest.TestCase):
    MARKER = "label: 금리 월평균 5.33%, sub: 2023년 8월, side: right}"   # high_0 30.06~34.05초 = 조각 3 [30, 40) 안

    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project
        from engine.render import render_animatic
        from tests.test_g8_animatic import synthetic_project

        cls.tmp = tempfile.TemporaryDirectory()
        proj = synthetic_project("fed_timeline_demo", Path(cls.tmp.name) / "demo")
        P = load_project(proj, animatic=True)  # noqa: N806
        (proj / "out").mkdir()
        n = int(P.plan.total * 44100) + 44100
        tone = (0.05 * np.sin(np.arange(n) * 2 * np.pi * 220 / 44100)).astype(np.float32)
        np.repeat(tone[:, None], 2, 1).tofile(proj / "out" / "mix.f32")
        cls.proj = proj
        render_animatic(P, 4)
        cls.first = cls.chunks()
        d = proj / "direction.yaml"
        src = d.read_text(encoding="utf-8")
        assert src.count(cls.MARKER) == 1
        d.write_text(src.replace(cls.MARKER, cls.MARKER.replace("side: right", "side: left")), encoding="utf-8")
        render_animatic(load_project(proj, animatic=True), 4)
        cls.cached = cls.chunks()
        cls.cached_md5 = framemd5(proj / "out" / "animatic_noaudio.mp4")
        render_animatic(load_project(proj, animatic=True), 4, no_cache=True)
        cls.fresh = cls.chunks()
        cls.fresh_md5 = framemd5(proj / "out" / "animatic_noaudio.mp4")

    @classmethod
    def chunks(cls) -> list[dict]:
        return json.loads((cls.proj / "out" / "animatic_render.json").read_text(encoding="utf-8"))["chunks"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_fixed_grid_independent_of_jobs(self) -> None:
        from engine.chunk_cache import chunk_frames
        from engine.style import FPS

        step = chunk_frames(FPS)
        self.assertEqual([(c["s"], c["e"]) for c in self.first][:3], [(0, step), (step, 2 * step), (2 * step, 3 * step)])
        self.assertEqual({c["status"] for c in self.first}, {"rendered"})

    def test_only_changed_chunk_rendered(self) -> None:
        st = {c["idx"]: c["status"] for c in self.cached}
        self.assertEqual(st[3], "rendered")
        self.assertEqual({k for k, v in st.items() if v == "rendered"}, {3}, st)
        self.assertNotEqual(self.first[3]["key"], self.cached[3]["key"])
        self.assertEqual([c["key"] for k, c in enumerate(self.first) if k != 3], [c["key"] for k, c in enumerate(self.cached) if k != 3])

    def test_cached_equals_no_cache(self) -> None:
        self.assertEqual({c["status"] for c in self.fresh}, {"rendered"})
        self.assertEqual([c["key"] for c in self.fresh], [c["key"] for c in self.cached])
        self.assertEqual(len(self.cached_md5), len(self.fresh_md5))
        bad = [i for i, (a, b) in enumerate(zip(self.cached_md5, self.fresh_md5)) if a != b]
        self.assertEqual(bad, [], f"프레임 md5 다름 {len(bad)}개")


if __name__ == "__main__":
    unittest.main()

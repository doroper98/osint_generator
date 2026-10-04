"""출력 프로파일 (v3.6.0, back_and_forth D-0066 작업 1 · D-0067 요건 2).

config `engine.output`(프로파일 이름 → 장치 크기·fps·인코딩), 별칭 trial·final, CLI `--res`, provenance `render.resolution`.
설계 좌표(854×480)는 프로파일과 무관하다.
"""

from __future__ import annotations

import unittest

from orchestrator.config import EngineConfig, OutputConfig, OutputProfile, load_config
from engine.style import FPS, H_OUT, W_OUT, Output, output_profile


class ProfileConfigTest(unittest.TestCase):
    def test_aliases(self) -> None:
        eng = load_config().engine
        self.assertEqual(eng.profile("trial")[0], "480p")
        self.assertEqual(eng.profile("final")[0], "720p")   # v5.5.1 사용자 결정 2026-10-04 — 기준 해상도 720p
        self.assertEqual(eng.profile(None)[0], eng.output.default)
        _, p = eng.profile("1080p")
        self.assertEqual((p.width, p.height, p.fps), (1920, 1080, 24))

    def test_unknown_profile_loud(self) -> None:
        with self.assertRaises(ValueError):
            load_config().engine.profile("4k")
        with self.assertRaises(ValueError):
            EngineConfig(trial="720p")
        with self.assertRaises(ValueError):
            OutputConfig(default="720p")

    def test_480p_encode_unchanged(self) -> None:
        """480p 인코딩 값은 Phase 9 까지와 같다(crf 19, preset faster) — 480p 무변경."""
        o = output_profile("480p")
        self.assertEqual((o.crf, o.preset), (19, "faster"))

    def test_fps_must_match_design(self) -> None:
        eng = EngineConfig(output=OutputConfig(profiles={"480p": OutputProfile(width=854, height=480, fps=30, crf=19, preset="faster", mem_per_job_mb=600),
                                                           "1080p": OutputProfile(width=1920, height=1080, fps=24, crf=19, preset="faster", mem_per_job_mb=1500)}))
        from unittest import mock  # noqa: PLC0415

        from engine import style  # noqa: PLC0415

        with mock.patch.object(style, "_CFG", mock.Mock(engine=eng)):
            with self.assertRaises(ValueError):
                style.output_profile("480p")


class OutputTest(unittest.TestCase):
    def test_design_space_fixed(self) -> None:
        self.assertEqual((W_OUT, H_OUT, FPS), (854, 480, 24))

    def test_k_identity(self) -> None:
        o = output_profile("480p")
        self.assertEqual((o.k, o.pad_x), (1.0, 0.0))
        self.assertEqual(o.px(10.5), 10.5)     # k=1 항등 — 반올림하지 않는다(round(10.5)=10 이면 480p 가 바뀐다)
        self.assertEqual(o.px(9.5), 9.5)

    def test_k_1080(self) -> None:
        o = output_profile("1080p")
        self.assertEqual(o.k, 2.25)
        self.assertEqual(o.pad_x, -0.75)       # 854 × 2.25 = 1921.5 → 1920: 양옆 0.75px
        self.assertEqual(o.px(0.2), 0.45)      # 가는 선이 0 으로 사라지지 않는다
        self.assertEqual(o.px_i(300), 675)     # 정수는 표면·래스터 폭만
        self.assertEqual(o.px_i(0.1), 1)

    def test_record(self) -> None:
        r = output_profile("1080p").record()
        self.assertEqual({k: r[k] for k in ("profile", "width", "height", "k", "pad_x")},
                         {"profile": "1080p", "width": 1920, "height": 1080, "k": 2.25, "pad_x": -0.75})

    def test_frozen(self) -> None:
        self.assertIsInstance(output_profile(), Output)
        with self.assertRaises(Exception):
            output_profile().width = 1  # type: ignore[misc]


class JobsTest(unittest.TestCase):
    """청크 병렬 수(D-0066 작업 6): --jobs → config engine.render.jobs → cpu, 메모리 상한."""

    def test_order_and_mem(self) -> None:
        from unittest import mock  # noqa: PLC0415

        from engine.render import plan_jobs  # noqa: PLC0415

        o = output_profile("1080p")
        self.assertEqual(plan_jobs(3, o, cpu=8, mem_mb=100000), (3, "--jobs"))
        with mock.patch("orchestrator.config.load_config") as lc:
            lc.return_value.engine.render.jobs = None
            self.assertEqual(plan_jobs(None, o, cpu=8, mem_mb=100000), (8, "cpu"))
            lc.return_value.engine.render.jobs = 2
            self.assertEqual(plan_jobs(None, o, cpu=8, mem_mb=100000), (2, "config"))
        j, why = plan_jobs(8, o, cpu=8, mem_mb=o.mem_per_job_mb * 3 + 10)
        self.assertEqual(j, 3)
        self.assertIn("mem", why)
        self.assertEqual(plan_jobs(8, o, cpu=8, mem_mb=10)[0], 1)

    def test_config_default_cpu(self) -> None:
        self.assertIsNone(load_config().engine.render.jobs)


class CliTest(unittest.TestCase):
    def test_render_cli_unknown_res(self) -> None:
        import io  # noqa: PLC0415
        import json  # noqa: PLC0415
        from contextlib import redirect_stdout  # noqa: PLC0415
        from pathlib import Path  # noqa: PLC0415

        from engine import render  # noqa: PLC0415

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = render.main([str(Path("projects/hormuz_korea")), "--preview", "1", "--res", "4k"])
        self.assertEqual(rc, 1)
        self.assertIn("4k", json.loads(buf.getvalue().strip().splitlines()[-1])["errors"][0])


if __name__ == "__main__":
    unittest.main()

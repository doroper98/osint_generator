"""단계별 시간 기록(v7.4.0 back_and_forth D-1000 S0, 사용자 UF-300).

① 감쌀 지점 함수가 `stage_timer` 를 실제로 쓰는지(소스 검사 — 만들었지만 연결되지 않음, 15 §1 A).
② 짧은 픽스처 콘티 판 렌더 뒤 `out/timings.jsonl` 에 render 세 칸(그리기·검사·인코딩)이 있고, provenance `timings` 가 같은 합계인지.
"""

from __future__ import annotations

import ast
import inspect
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]

# (모듈, 함수, 그 함수 소스에 있어야 하는 단계 이름 조각)
WRAPPED: list[tuple[str, str, tuple[str, ...]]] = [
    ("script.plan", "build", ('"script.lint"', '"script.tts"', '"script.align"')),
    ("audio.mix", "main", ('"audio.mix"',)),
    ("orchestrator.ai_direction", "run_worker", ('f"llm.{name}"',)),
    ("engine.render", "preview", ('"render.preview.frames"', '"render.preview.checks"', '"render.preview.sheet"')),
    ("engine.render", "render_full", ('f"render.{kind}.frames"', 'f"render.{kind}.encode"')),
    ("engine.render", "render_animatic", ('"render.animatic.checks"', '"render.animatic.encode"')),
    ("engine.render", "render_catalog", ('"render.catalog.checks"', '"render.catalog.encode"')),
    ("engine.mux", "main", ('"mux.final.encode"',)),
]


def _calls_stage_timer(fn) -> bool:  # noqa: ANN001
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    return any(isinstance(n, ast.Call) and getattr(n.func, "id", None) == "stage_timer" for n in ast.walk(tree))


class StageTimerWiredTest(unittest.TestCase):
    def test_wrapped_points(self) -> None:
        import importlib

        for mod, name, stages in WRAPPED:
            fn = getattr(importlib.import_module(mod), name)
            src = inspect.getsource(fn)
            with self.subTest(f"{mod}.{name}"):
                self.assertTrue(_calls_stage_timer(fn), f"{mod}.{name} 가 stage_timer 를 부르지 않는다")
                for s in stages:
                    self.assertIn(s, src, f"{mod}.{name} 단계 이름 {s} 없음")

    def test_timer_records_and_failure(self) -> None:
        from engine.timing import read_timings, stage_timer, summarize

        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            with stage_timer(p, "x.ok", a=1) as extra:
                extra["b"] = 2
            with self.assertRaises(ValueError), stage_timer(p, "x.fail"):
                raise ValueError("boom")   # 실패도 기록하고 예외는 그대로 올린다(P6)
            with stage_timer(None, "x.none"):
                pass   # 프로젝트 밖 = 기록 없음
            rows = read_timings(p)
            self.assertEqual([(r.stage, r.ok) for r in rows], [("x.ok", True), ("x.fail", False)])
            self.assertEqual(rows[0].args, {"a": 1, "b": 2})
            self.assertEqual(rows[0].schema_version, 1)
            self.assertEqual(set(summarize(p)), {"x.ok", "x.fail"})
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(summarize(Path(d)))   # 돈 단계 없음 = None(P5)


@pytest.mark.slow   # C8.3(D187) — 렌더(빠른 묶음 밖)
class AnimaticTimingsTest(unittest.TestCase):
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
        cls.final, cls.prov = render_animatic(P, 2)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_three_render_stages(self) -> None:
        from engine.timing import read_timings

        stages = {r.stage for r in read_timings(self.proj)}
        for s in ("render.animatic.frames", "render.animatic.checks", "render.animatic.encode"):
            self.assertIn(s, stages)
        tm = json.loads((self.proj / "out" / "animatic_provenance.json").read_text(encoding="utf-8"))["timings"]
        self.assertGreater(tm["render.animatic.frames"]["sec"], 0)
        self.assertEqual(tm["render.animatic.checks"]["n"], 1)


if __name__ == "__main__":
    unittest.main()

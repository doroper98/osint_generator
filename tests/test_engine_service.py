"""orchestrator/engine_service — 엔진 CLI 어댑터 (v3.0.0, 16 §4, 15 P1·P6, D-0040 작업 4)."""

from __future__ import annotations

import ast
import json
import subprocess
import unittest
from pathlib import Path

from orchestrator import engine_service as es
from schemas.models import ProjectState
from tests._fonts import NO_FONTS_REASON, fonts_ready

REPO = Path(__file__).resolve().parent.parent
HORMUZ = REPO / "projects" / "hormuz_korea"


def _ok(stage: str, **kw: object) -> str:
    return json.dumps({"ok": True, "stage": stage, "artifacts": {}, "provenance": None, "drops": [],
                       "errors": [], "warnings": [], **kw})


class FakeRunner:
    def __init__(self, rc: int, stdout: str, stderr: str = "") -> None:
        self.rc, self.stdout, self.stderr = rc, stdout, stderr
        self.calls: list[list[str]] = []

    def __call__(self, cmd: list[str], **kw: object) -> subprocess.CompletedProcess:
        self.calls.append(cmd)
        assert kw["cwd"] == es.REPO and kw["check"] is False
        return subprocess.CompletedProcess(cmd, self.rc, self.stdout, self.stderr)


class CommandTest(unittest.TestCase):
    def test_commands_match_16_s4(self) -> None:
        p = Path("/p")
        self.assertEqual(es.build_command(p, "plan")[2:], ["script.plan", "/p"])
        self.assertEqual(es.build_command(p, "assets")[2:], ["geo.prep", "/p"])
        self.assertEqual(es.build_command(p, "direction_validate")[2:], ["script.lint", "/p"])
        self.assertEqual(es.build_command(p, "preview")[2:], ["engine.render", "/p", "--preview", "auto"])
        self.assertEqual(es.build_command(p, "render", jobs=4)[2:], ["engine.render", "/p", "--jobs", "4"])
        self.assertEqual(es.build_command(p, "mix")[2:], ["audio.mix", "/p"])
        self.assertEqual(es.build_command(p, "deliver")[2:], ["engine.mux", "/p"])
        self.assertEqual(es.build_command(p, "validate")[2:], ["engine.validate", "/p"])   # v3.1.0 17 §1

    def test_unknown_stage_is_error(self) -> None:
        with self.assertRaises(ValueError):
            es.build_command(Path("/p"), "lint")

    def test_state_stages_cover_engine_states(self) -> None:
        self.assertEqual(set(es.STATE_STAGES), {
            ProjectState.VOICE_TIMELINE, ProjectState.ASSETS, ProjectState.DIRECTION, ProjectState.PREVIEW_QA,
            ProjectState.RENDER, ProjectState.AUDIO_MIX, ProjectState.DELIVER})
        for stages in es.STATE_STAGES.values():
            for s in stages:
                self.assertIn(s, es.STAGE_COMMANDS)
        self.assertEqual(es.stages_for("script_approval"), ())


class ParseTest(unittest.TestCase):
    def test_ok(self) -> None:
        r = es.parse_result("mix", 0, "log line\n" + _ok("mix", artifacts={"mix": "out/mix.f32"}) + "\n", "")
        self.assertTrue(r.ok)
        self.assertEqual(r.artifacts, {"mix": "out/mix.f32"})

    def test_no_json(self) -> None:
        r = es.parse_result("plan", 1, "", "Traceback\nboom")
        self.assertFalse(r.ok)
        self.assertIn("StageResult JSON 없음", r.errors[0])
        self.assertIn("boom", r.errors)

    def test_bad_json(self) -> None:
        r = es.parse_result("plan", 0, "{not json", "")
        self.assertFalse(r.ok)

    def test_stage_mismatch(self) -> None:
        r = es.parse_result("deliver", 0, _ok("render"), "")
        self.assertFalse(r.ok)
        self.assertIn("stage='render'", r.errors[-1])

    def test_exit_code_contradiction(self) -> None:
        self.assertFalse(es.parse_result("mix", 1, _ok("mix"), "").ok)
        bad = json.dumps({"ok": False, "stage": "mix", "errors": ["x"]})
        r = es.parse_result("mix", 0, bad, "")
        self.assertFalse(r.ok)
        self.assertIn("종료 코드 0", r.errors[-1])

    def test_drops_propagate_as_failure(self) -> None:
        out = json.dumps({"ok": False, "stage": "geo", "drops": [{"stage": "geo", "tier": "W"}]})
        r = es.parse_result("assets", 1, out, "")
        self.assertFalse(r.ok)
        self.assertEqual(r.drops, [{"stage": "geo", "tier": "W"}])


class RunStageTest(unittest.TestCase):
    def test_fake_runner(self) -> None:
        fr = FakeRunner(0, _ok("preview", artifacts={"prev/p_0001.00.png": "x"}))
        r = es.run_stage(Path("/p"), "preview", runner=fr)
        self.assertTrue(r.ok)
        self.assertEqual(fr.calls[0][2:], ["engine.render", "/p", "--preview", "auto"])

    @unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)   # 린트가 자막 줄 수를 글자 폭으로 잰다(script/lint.py) — NB27
    def test_real_cli_direction_validate(self) -> None:
        r = es.run_stage(HORMUZ, "direction_validate")
        # v5.5.0 script_grammar(LLM-AP-013) — v3 골든 원고는 미확인 마무리·연결어 부족 오류 2개를 그대로 갖는다(원고 재작성 대상 아님)
        self.assertFalse(r.ok)
        self.assertEqual(sorted(x.split("]")[0] + "]" for x in r.errors), ["[flow-sparse]", "[uncertain-phrase]"])
        self.assertEqual(r.stage, "lint")
        # v3.2.0 — v3 원고가 claims 로 이관돼(D51) sources 경고가 사라졌다. 라벨 집계는 artifacts 로
        self.assertEqual([w for w in r.warnings if "source" in w], [])
        self.assertIn("label_counts", r.artifacts)


class NoInputWritesTest(unittest.TestCase):
    """15 P1 — 어댑터는 엔진 입력 파일을 쓰지 않는다: 파일 쓰기·삭제 호출이 없어야 한다."""

    def test_engine_service_does_not_write_files(self) -> None:
        tree = ast.parse((REPO / "orchestrator" / "engine_service.py").read_text(encoding="utf-8"))
        banned = {"write_text", "write_bytes", "mkdir", "unlink", "rmtree", "copy", "copyfile", "move", "rename", "replace", "touch"}
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
                if name in banned or name == "open":
                    hits.append(f"{name}@{node.lineno}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()

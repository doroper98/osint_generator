"""승인 게이트·진행(pipeline)·게이트 화면·Command Center 키 (v3.0.0, 16 §2·§4·§5, D-0040 작업 6·9)."""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from orchestrator.config import AppConfig, PathsConfig, ReviewGatesConfig
from orchestrator.main import main as cli_main
from orchestrator.pipeline import PipelineError, advance, next_action
from orchestrator.project_manager import (
    approve_gate,
    load_manifest,
    new_project,
    reject_gate,
    transition_state,
)
from schemas.models import ProjectState

S = ProjectState
REPO = Path(__file__).resolve().parent.parent
PRE_GATE = [S.INTAKE, S.SOURCE_VERIFY, S.RESEARCH, S.SCRIPT_DRAFT, S.SCRIPT_APPROVAL]
STAGE_NAME = {"script.plan": "plan", "geo.prep": "geo", "script.lint": "lint", "audio.mix": "mix", "engine.mux": "mux"}


def fake_runner(fail: str | None = None, drops: bool = False, log: list | None = None):  # noqa: ANN201
    def run(cmd: list[str], **kw: object) -> subprocess.CompletedProcess:
        mod = cmd[2]
        stage = STAGE_NAME.get(mod) or ("preview" if "--preview" in cmd else "render")
        if log is not None:
            log.append(stage)
        if stage == fail:
            body = {"ok": False, "stage": stage, "drops": [{"stage": stage}] if drops else [], "errors": [] if drops else ["boom"]}
            return subprocess.CompletedProcess(cmd, 1, json.dumps(body), "")
        return subprocess.CompletedProcess(cmd, 0, json.dumps({"ok": True, "stage": stage, "artifacts": {stage: "x"}}), "")
    return run


class _Proj(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cfg = AppConfig(paths=PathsConfig(projects_root=str(self.root)))
        self.m = new_project("p", "t", "geopolitics", cfg=self.cfg)
        shutil.copy(REPO / "projects" / "hormuz_korea" / "script.yaml", self.root / "p" / "script.yaml")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def to(self, *states: ProjectState) -> None:
        for s in states:
            self.m = transition_state(self.m, s, reason="test", cfg=self.cfg)

    def to_gate1(self) -> None:
        self.to(*PRE_GATE)


class GateTest(_Proj):
    def test_gate_blocks_plain_transition(self) -> None:
        self.to_gate1()
        with self.assertRaises(ValueError) as ctx:
            transition_state(self.m, S.VOICE_TIMELINE, cfg=self.cfg)
        self.assertIn("승인 게이트", str(ctx.exception))

    def test_approve_records_and_advances(self) -> None:
        self.to_gate1()
        m = approve_gate(self.m, "script_approval", by="tester", comment="좋다", shown={"lint_errors": "0"}, cfg=self.cfg)
        self.assertEqual(m.current_state, "voice_timeline")
        d = load_manifest("p", self.cfg).gate_decisions[-1]
        self.assertEqual((d.gate, d.decision, d.by, d.comment, d.shown), ("script_approval", "approved", "tester", "좋다", {"lint_errors": "0"}))

    def test_reject_script_rolls_back_with_comment(self) -> None:
        self.to_gate1()
        m = reject_gate(self.m, "script_approval", "script_draft", by="tester", comment="3장면 사실 확인", cfg=self.cfg)
        self.assertEqual(m.current_state, "script_draft")
        d = load_manifest("p", self.cfg).gate_decisions[-1]
        self.assertEqual((d.decision, d.rollback_to, d.comment), ("rejected", "script_draft", "3장면 사실 확인"))
        # 재승인 후 계속
        self.to(S.SCRIPT_APPROVAL)
        self.assertEqual(approve_gate(self.m, "script_approval", by="t", cfg=self.cfg).current_state, "voice_timeline")

    def test_reject_preview_three_targets(self) -> None:
        # 각 되돌림 대상에서 다시 게이트 ② 까지 가는 앞 방향 경로
        back_to_gate2 = {
            "direction": [S.PREVIEW_QA, S.PREVIEW_APPROVAL],
            "assets": [S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL],
        }
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self.to(S.ASSETS, S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL)
        for tgt in ("direction", "assets", "script_draft"):
            with self.subTest(tgt=tgt):
                self.m = reject_gate(self.m, "preview_approval", tgt, by="t", comment=f"{tgt} 문제", cfg=self.cfg)
                self.assertEqual(self.m.current_state, tgt)
                self.assertEqual(load_manifest("p", self.cfg).gate_decisions[-1].rollback_to, tgt)
                if tgt in back_to_gate2:
                    self.to(*back_to_gate2[tgt])

    def test_reject_rules(self) -> None:
        self.to_gate1()
        with self.assertRaises(ValueError):
            reject_gate(self.m, "script_approval", "assets", by="t", comment="x", cfg=self.cfg)   # 게이트 ① 은 script_draft 만
        with self.assertRaises(ValueError):
            reject_gate(self.m, "script_approval", "script_draft", by="t", comment="  ", cfg=self.cfg)   # 사유 필수
        with self.assertRaises(ValueError):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)   # 다른 게이트

    def test_config_two_gates_only(self) -> None:
        self.assertEqual(set(ReviewGatesConfig().require_human_approval), {"script_approval", "preview_approval"})
        with self.assertRaises(ValueError):
            ReviewGatesConfig(require_human_approval={"script_approval": True, "preview_approval": False})
        with self.assertRaises(ValueError):
            ReviewGatesConfig(require_human_approval={"script_review": True})


class PipelineTest(_Proj):
    def _to_voice(self) -> None:
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)

    def test_engine_states_to_gate2_then_done(self) -> None:
        self._to_voice()
        log: list[str] = []
        for _ in range(4):   # voice_timeline → assets → direction → preview_qa → preview_approval
            m, res = advance("p", self.cfg, runner=fake_runner(log=log))
            self.assertTrue(all(r.ok for r in res))
        self.assertEqual(m.current_state, "preview_approval")
        with self.assertRaises(PipelineError):
            advance("p", self.cfg, runner=fake_runner())
        approve_gate(m, "preview_approval", by="t", cfg=self.cfg)
        for _ in range(3):   # render → audio_mix → deliver → done
            m, _ = advance("p", self.cfg, runner=fake_runner(log=log))
        self.assertEqual(m.current_state, "done")
        self.assertEqual(log, ["plan", "geo", "lint", "preview", "render", "mix", "mux"])
        recs = load_manifest("p", self.cfg).stage_records
        self.assertEqual([r.stage for r in recs], ["plan", "assets", "direction_validate", "preview", "render", "mix", "deliver"])
        self.assertTrue((self.root / "p" / recs[0].log).exists())

    def test_failure_and_drops_stay(self) -> None:
        self._to_voice()
        m, res = advance("p", self.cfg, runner=fake_runner())            # plan ok → assets
        m, res = advance("p", self.cfg, runner=fake_runner(fail="geo", drops=True))
        self.assertEqual(m.current_state, "assets")                        # 머문다(15 P6)
        self.assertFalse(res[-1].ok)
        self.assertEqual(load_manifest("p", self.cfg).stage_records[-1].drops, 1)
        m, res = advance("p", self.cfg, runner=fake_runner(fail="geo"))
        self.assertEqual(m.current_state, "assets")

    def test_llm_states_not_advanced(self) -> None:
        with self.assertRaises(PipelineError) as ctx:
            advance("p", self.cfg, runner=fake_runner())
        self.assertIn("plan-intake", str(ctx.exception))
        self.assertIn("승인 대기", next_action("script_approval"))


class GateViewTest(_Proj):
    def test_script_gate_view_sections(self) -> None:
        from orchestrator.gate_view import gate_view  # noqa: PLC0415
        text, shown = gate_view(self.root / "p", "script_approval")
        for part in ("장면 목록", "원고 전문(자막)", "출처 표", "린트 — 오류 0", "미디어 후보"):
            self.assertIn(part, text)
        self.assertIn("open_0", text)
        self.assertEqual(shown["lint_errors"], "0")

    def test_preview_gate_view_reads_prev(self) -> None:
        from orchestrator.gate_view import gate_view  # noqa: PLC0415
        prev = self.root / "p" / "prev"
        prev.mkdir()
        (prev / "sheet.jpg").write_bytes(b"x")
        (prev / "p_0001.00.png").write_bytes(b"x")
        (prev / "provenance.json").write_text(json.dumps({"stages": {"preview": True, "render": False},
                                                          "features_used": {"badges": 8, "panels": ["relation"]}, "drops": []}), encoding="utf-8")
        text, shown = gate_view(self.root / "p", "preview_approval")
        self.assertIn("sheet.jpg", text)
        self.assertIn("뱃지 8", text)
        self.assertIn('"render": false', text)
        self.assertEqual(shown["drops"], "0")


class CliTest(_Proj):
    def test_cli_approve_reject(self) -> None:
        self.to_gate1()
        import orchestrator.main as om  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415
        with mock.patch("orchestrator.config.load_config", return_value=self.cfg), \
             mock.patch("orchestrator.project_manager.load_config", return_value=self.cfg):
            self.assertEqual(om.main(["reject", "--project", "p", "--gate", "script_approval", "--to", "script_draft",
                                      "--comment", "고쳐라"]), 0)
            self.assertEqual(load_manifest("p", self.cfg).current_state, "script_draft")
            self.assertEqual(om.main(["approve", "--project", "p", "--gate", "script_approval"]), 2)   # 게이트 아님
        self.assertEqual(cli_main(["reject", "--project", "nope_zz", "--gate", "script_approval", "--to", "script_draft",
                                   "--comment", "x"]), 1)


class CommandCenterKeysTest(_Proj):
    def test_approve_key_and_gate_panel(self) -> None:
        from orchestrator.tui_app import CommandCenterApp  # noqa: PLC0415
        self.to_gate1()

        async def go() -> str:
            app = CommandCenterApp(project_id="p", project_dir=self.root / "p", cfg=self.cfg, current_state="script_approval")
            async with app.run_test() as pilot:
                await pilot.pause()
                title = str(app.gate_panel.border_title)   # type: ignore[union-attr]
                await pilot.press("a")
                await pilot.pause()
            return title

        title = asyncio.run(go())
        self.assertIn("script_approval", title)
        m = load_manifest("p", self.cfg)
        self.assertEqual(m.current_state, "voice_timeline")
        self.assertEqual(m.gate_decisions[-1].by, "command-center")
        self.assertEqual(m.gate_decisions[-1].shown.get("lint_errors"), "0")


if __name__ == "__main__":
    unittest.main()

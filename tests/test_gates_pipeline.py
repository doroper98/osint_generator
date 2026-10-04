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
from tests._fonts import NO_FONTS_REASON, fonts_ready

S = ProjectState
REPO = Path(__file__).resolve().parent.parent
PRE_GATE = [S.INTAKE, S.SOURCE_VERIFY, S.RESEARCH, S.SCRIPT_DRAFT, S.SCRIPT_APPROVAL]
STAGE_NAME = {"script.plan": "plan", "geo.prep": "geo", "script.lint": "lint", "engine.validate": "validate", "audio.mix": "mix", "engine.mux": "mux", "engine.camera_suggest": "camera_suggest"}


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


def write_animatic(pdir: Path, total_sec: float = 292.44, animatic: bool = True) -> None:
    """게이트 ② 시험용 콘티 판 기록(engine.render --animatic 이 남기는 provenance 의 최소 필드)."""
    (pdir / "out").mkdir(parents=True, exist_ok=True)
    import hashlib  # noqa: PLC0415

    sp = pdir / "script.yaml"   # v5.6.0 — 콘티 판을 만든 원고 지문(게이트 ① 승인 원고와 대조)
    sha = hashlib.sha1(sp.read_bytes()).hexdigest() if sp.exists() else None
    prov = {"animatic": animatic, "total_sec": total_sec,
            "animatic_run": {"output": "out/animatic.mp4", "direction_sha1": "0" * 40, "script_sha1": sha} if animatic else None}
    (pdir / "out" / "animatic_provenance.json").write_text(json.dumps(prov), encoding="utf-8")


def _v550_script(src: Path, dst: Path) -> None:
    """기준 원고(v3)를 v5.5.0 서술 규약에 맞춘 사본 — 미확인 마무리를 확인된 사실로, 문장 둘에 하나는 연결어로(게이트 ① 차단 방지).
    기준 원고 자체는 고치지 않는다(골든)."""
    import yaml  # noqa: PLC0415

    d = yaml.safe_load(src.read_text(encoding="utf-8"))
    k = 0
    for sc in d["scenes"]:
        for s in sc["sentences"]:
            if "정해지지 않았" in s["text"]:
                s["text"] = s["tts"] = "결국 파병 여부는 국회 동의 절차를 거쳐 결정됩니다."
            elif k % 2 and not s["text"].startswith("결국"):
                s["text"] = "또한 " + s["text"]
                if s.get("tts"):
                    s["tts"] = "또한 " + s["tts"]
            k += 1
    dst.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


class _Proj(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cfg = AppConfig(paths=PathsConfig(projects_root=str(self.root)))
        self.m = new_project("p", "t", "geopolitics", cfg=self.cfg)
        _v550_script(REPO / "projects" / "hormuz_korea" / "script.yaml", self.root / "p" / "script.yaml")
        shutil.copytree(REPO / "projects" / "hormuz_korea" / "intake", self.root / "p" / "intake")   # v3.2.0 — claims.json(18 §7 게이트 ① 전 검사)
        write_animatic(self.root / "p")   # v5.2.0 — 게이트 ② 는 콘티 판 의무(PIPELINE-AP-014)

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
        shown = dict(d.shown)
        self.assertEqual(len(shown.pop("script_sha1")), 40)   # v5.6.0 — 승인 원고 지문(PIPELINE-AP-015)
        self.assertEqual((d.gate, d.decision, d.by, d.comment, shown), ("script_approval", "approved", "tester", "좋다", {"lint_errors": "0"}))

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
        shutil.copy(REPO / "projects" / "hormuz_korea" / "direction.yaml", self.root / "p" / "direction.yaml")  # 사람 연출 — 연출가·검수 루프 없음
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
        self.assertEqual(log, ["plan", "geo", "geo", "lint", "validate", "camera_suggest", "preview", "render", "mix", "mux"])   # v5.5.1 — assets + assets_final(배포 720p 티어)
        recs = load_manifest("p", self.cfg).stage_records
        self.assertEqual([r.stage for r in recs], ["plan", "assets", "assets_final", "direction_validate", "validate", "camera_suggest", "preview", "render", "mix", "deliver"])
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
    @unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)   # 게이트 ① 뷰 = 린트 서브프로세스(자막 줄 수 = 글자 폭) — NB27
    def test_script_gate_view_sections(self) -> None:
        from orchestrator.gate_view import gate_view  # noqa: PLC0415
        text, shown = gate_view(self.root / "p", "script_approval")
        for part in ("장면 목록", "원고 전문(자막)", "출처 표", "린트 — 오류 0", "미디어 후보"):   # v5.5.0 — 규약에 맞춘 기준 원고 사본(_v550_script)
            self.assertIn(part, text)
        self.assertIn("open_0", text)
        self.assertEqual(shown["lint_errors"], "0")   # v5.5.0 — 규약에 맞춘 사본

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


class ProjectPathsTest(_Proj):
    def test_16_s6_paths(self) -> None:
        from orchestrator.project_manager import PROJECT_PATHS, artifact_status  # noqa: PLC0415
        self.assertEqual(load_manifest("p", self.cfg).paths, PROJECT_PATHS)
        for k in ("script", "plan", "direction", "prev_sheet", "prev_provenance", "final", "provenance"):
            self.assertIn(k, PROJECT_PATHS)
        st = artifact_status("p", self.cfg)
        self.assertTrue(st["script"])
        self.assertFalse(st["plan"])


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
        self.assertEqual(m.gate_decisions[-1].shown.get("lint_errors"), "0")   # v5.5.0 — 규약에 맞춘 사본


class CommandCenterSourceConfirmTest(_Proj):
    """v3.2.0 18 §7 — intake 상태 소스 확인 화면과 'c' 확인 키."""

    def test_source_view_and_confirm_key(self) -> None:
        from datetime import datetime  # noqa: PLC0415

        from orchestrator import source_intake as si  # noqa: PLC0415
        from orchestrator.gate_view import source_view  # noqa: PLC0415
        from orchestrator.tui_app import CommandCenterApp  # noqa: PLC0415

        pdir = self.root / "p"
        shutil.rmtree(pdir / "intake")
        self.to(ProjectState.INTAKE)
        rec = si.add_x_text(pdir, account_name="A", handle="@abc_def", text="t", lang="en", posted_at=datetime(2026, 9, 1))
        self.assertIn("미확인 — c 로 확인", source_view(pdir))

        async def go() -> str:
            app = CommandCenterApp(project_id="p", project_dir=pdir, cfg=self.cfg, current_state="intake")
            async with app.run_test() as pilot:
                await pilot.pause()
                title = str(app.gate_panel.border_title)   # type: ignore[union-attr]
                await pilot.press("c")
                await pilot.pause()
                for ch in rec.id:
                    await pilot.press(ch)
                await pilot.press("enter")
                await pilot.pause()
            return title

        title = asyncio.run(go())
        self.assertIn("Sources · intake", title)
        self.assertEqual(si.load_sources(pdir).sources[0].confirmed_by, "command-center")
        self.assertIn("확인 command-center", source_view(pdir))


if __name__ == "__main__":
    unittest.main()


class ChosenVersionTest(_Proj):
    """D-0049 쟁점 3 — 게이트 ② 에서 사람이 다른 AI 판을 고르면 direction.yaml 복원 + 기록."""

    def test_choose_version(self) -> None:
        from engine.qa import QALoopRecord, QALoopRound  # noqa: PLC0415
        from orchestrator.gate_view import preview_gate_view  # noqa: PLC0415

        pdir = self.root / "p"
        (pdir / "prev").mkdir()
        for n in (1, 2):
            (pdir / f"direction.v{n}.yaml").write_text(f"v: {n}\n", encoding="utf-8")
        (pdir / "direction.yaml").write_text("v: 2\n", encoding="utf-8")
        rec = QALoopRecord(rounds=[QALoopRound(version=n, checks_hard=0, checks_file="", sheet=f"sheet.v{n}.jpg") for n in (1, 2)])
        (pdir / "prev" / "qa_loop.json").write_text(rec.model_dump_json(), encoding="utf-8")
        text, shown = preview_gate_view(pdir)
        self.assertIn("v1  checks hard 0", text)
        self.assertEqual(shown["qa_rounds"], "2")
        self.to(*PRE_GATE)
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        with self.assertRaises(ValueError):
            approve_gate(self.m, "script_approval", by="t", cfg=self.cfg, chosen_version=1)
        self.to(S.ASSETS, S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL)
        self.m = approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg, chosen_version=1)
        self.assertEqual((pdir / "direction.yaml").read_text(encoding="utf-8"), "v: 1\n")
        self.assertEqual(self.m.gate_decisions[-1].chosen_version, 1)
        rec2 = QALoopRecord.model_validate_json((pdir / "prev" / "qa_loop.json").read_text(encoding="utf-8"))
        self.assertEqual((rec2.selected.version, rec2.selected.by), (1, "human"))  # type: ignore[union-attr]


class AnimaticGateTest(_Proj):
    """PIPELINE-AP-014 — 콘티 판 없이 게이트 ② 승인 불가(우회 플래그 없음, 사용자 결정 2026-10-01)."""

    def _to_gate2(self) -> None:
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self.to(S.ASSETS, S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL)

    def test_missing_animatic_blocks_gate2(self) -> None:
        from orchestrator.project_manager import AnimaticMissingError  # noqa: PLC0415

        self._to_gate2()
        (self.root / "p" / "out" / "animatic_provenance.json").unlink()
        with self.assertRaises(AnimaticMissingError) as ctx:
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        self.assertIn("--animatic", str(ctx.exception))
        self.assertEqual(self.m.current_state, "preview_approval")

    def test_unfinished_animatic_blocks_gate2(self) -> None:
        from orchestrator.project_manager import AnimaticMissingError  # noqa: PLC0415

        self._to_gate2()
        write_animatic(self.root / "p", animatic=False)
        with self.assertRaises(AnimaticMissingError):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)

    def test_script_changed_after_approval_blocks_gate2(self) -> None:
        """v5.6.0 사용자 결정 2026-10-04 — 자막(원고) → 콘티 → 승인 후 본편. 승인 뒤 원고를 고치고 옛 콘티 판으로 게이트 ② 불가(PIPELINE-AP-015)."""
        from orchestrator.project_manager import AnimaticMissingError  # noqa: PLC0415

        self._to_gate2()
        sp = self.root / "p" / "script.yaml"
        sp.write_text(sp.read_text(encoding="utf-8") + "\n# 승인 뒤 수정\n", encoding="utf-8")
        write_animatic(self.root / "p", total_sec=300.02)   # 고친 원고로 만든 콘티 판 — 승인 원고와 지문이 다르다
        with self.assertRaises(AnimaticMissingError):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)

    def test_stale_voice_blocks_gate2(self) -> None:
        from orchestrator.project_manager import AnimaticMissingError  # noqa: PLC0415

        self._to_gate2()
        (self.root / "p" / "plan.json").write_text(json.dumps({"total": 300.0}), encoding="utf-8")
        with self.assertRaises(AnimaticMissingError) as ctx:
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        self.assertIn("옛 음성", str(ctx.exception))
        write_animatic(self.root / "p", total_sec=300.02)
        m = approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        self.assertEqual(m.current_state, "render")
        self.assertIn("out/animatic.mp4", m.gate_decisions[-1].shown["animatic"])

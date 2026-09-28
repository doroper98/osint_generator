"""상태 머신 회귀 테스트 (v3.0.0, docs/handoff/16 §2, SCHEMA-AP-001).

1. 앞 방향 — `SEQUENCE` 의 인접 페어만 허용.
2. 임의 점프·역방향 거부 — 역전이 표 밖의 뒤로 가기는 ValueError.
3. 역전이 3종 — SCRIPT_APPROVAL → SCRIPT_DRAFT, PREVIEW_APPROVAL → DIRECTION·SCRIPT_DRAFT·ASSETS.
4. self-loop 거부, DONE 종착.
5. 옛 상태 삭제 — ProjectState 는 16 §2 의 15개뿐.
6. manifest — schema_version 2, 손상 = ManifestCorruptError, v1 = ManifestVersionError(폴백 없음).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.config import AppConfig, PathsConfig
from orchestrator.errors import ManifestCorruptError, ManifestVersionError
from orchestrator.project_manager import load_manifest, new_project, transition_state
from orchestrator.state_machine import (
    GATES,
    ROLLBACKS,
    SEQUENCE,
    allowed_next_states,
    is_rollback,
    validate_transition,
)
from schemas.models import ProjectState

S = ProjectState


class ForwardTransitions(unittest.TestCase):
    def test_every_adjacent_pair_is_allowed(self) -> None:
        for current, target in zip(SEQUENCE, SEQUENCE[1:]):
            with self.subTest(current=current.value, target=target.value):
                validate_transition(current, target)

    def test_string_input_is_coerced(self) -> None:
        validate_transition("created", "intake")

    def test_sequence_matches_16_s2(self) -> None:
        self.assertEqual([s.value for s in SEQUENCE], [
            "created", "intake", "source_verify", "research", "script_draft", "script_approval",
            "voice_timeline", "assets", "direction", "preview_qa", "preview_approval",
            "render", "audio_mix", "deliver", "done"])


class JumpsRejected(unittest.TestCase):
    def test_created_to_render_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_transition(S.CREATED, S.RENDER)
        self.assertIn("잘못된 상태 전이", str(ctx.exception))
        self.assertIn("intake", str(ctx.exception))

    def test_backwards_outside_rollbacks_is_rejected(self) -> None:
        for cur, tgt in [(S.SCRIPT_DRAFT, S.RESEARCH), (S.DIRECTION, S.ASSETS), (S.RENDER, S.PREVIEW_APPROVAL),
                         (S.SCRIPT_APPROVAL, S.RESEARCH), (S.PREVIEW_APPROVAL, S.PREVIEW_QA)]:
            with self.subTest(cur=cur.value, tgt=tgt.value), self.assertRaises(ValueError):
                validate_transition(cur, tgt)


class Rollbacks(unittest.TestCase):
    def test_three_rollback_kinds(self) -> None:
        self.assertEqual(ROLLBACKS, {
            S.SCRIPT_APPROVAL: frozenset({S.SCRIPT_DRAFT}),
            S.PREVIEW_APPROVAL: frozenset({S.DIRECTION, S.SCRIPT_DRAFT, S.ASSETS}),
        })
        self.assertEqual(GATES, frozenset({S.SCRIPT_APPROVAL, S.PREVIEW_APPROVAL}))

    def test_rollbacks_are_allowed(self) -> None:
        for gate, targets in ROLLBACKS.items():
            for tgt in targets:
                with self.subTest(gate=gate.value, tgt=tgt.value):
                    validate_transition(gate, tgt)
                    self.assertTrue(is_rollback(gate, tgt))

    def test_gate_forward_is_not_rollback(self) -> None:
        self.assertEqual(allowed_next_states(S.SCRIPT_APPROVAL), {S.VOICE_TIMELINE, S.SCRIPT_DRAFT})
        self.assertFalse(is_rollback(S.SCRIPT_APPROVAL, S.VOICE_TIMELINE))


class TerminalAndSelfLoop(unittest.TestCase):
    def test_same_state_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_transition(S.CREATED, S.CREATED)
        self.assertIn("동일 상태", str(ctx.exception))

    def test_done_is_terminal(self) -> None:
        self.assertEqual(allowed_next_states(S.DONE), set())
        with self.assertRaises(ValueError):
            validate_transition(S.DONE, S.CREATED)


class OldStatesDeleted(unittest.TestCase):
    def test_only_new_states(self) -> None:
        self.assertEqual(len(ProjectState), 15)
        for old in ("intake_planning", "intake_pending_user", "source_collecting", "blueprint_review",
                    "script_writing", "scene_planning", "render_debug", "publish_ready", "archived"):
            with self.subTest(old=old), self.assertRaises(ValueError):
                ProjectState(old)


class ManifestContract(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cfg = AppConfig(paths=PathsConfig(projects_root=str(self.root)))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_new_manifest_is_v2_and_round_trips(self) -> None:
        m = new_project("p1", "t", "geopolitics", cfg=self.cfg)
        self.assertEqual(m.schema_version, 2)
        raw = json.loads((self.root / "p1" / "project_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["schema_version"], 2)
        m = transition_state(m, S.INTAKE, reason="x", cfg=self.cfg)
        self.assertEqual(load_manifest("p1", self.cfg).current_state, "intake")

    def test_v1_manifest_is_version_error(self) -> None:
        new_project("p2", "t", "geopolitics", cfg=self.cfg)
        path = self.root / "p2" / "project_manifest.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["schema_version"] = 1
        raw["current_state"] = "script_writing"
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(ManifestVersionError) as ctx:
            load_manifest("p2", self.cfg)
        self.assertIn("재생성 필요", str(ctx.exception))

    def test_bad_state_in_v2_is_corrupt(self) -> None:
        new_project("p3", "t", "geopolitics", cfg=self.cfg)
        path = self.root / "p3" / "project_manifest.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["current_state"] = "script_writing"
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(ManifestCorruptError):
            load_manifest("p3", self.cfg)


if __name__ == "__main__":
    unittest.main()

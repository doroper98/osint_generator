"""v7.4.0 back_and_forth D-0237(사용자 결정 D246) — 게이트 ① 승인 뒤 원고 사실 수정 되돌림(`rollback`, 렌더 전 → script_draft).
(a) 네 상태에서 사유 있는 되돌림 성공·manifest 기록 (b) 사유 없으면 거부 (c) 되돌린 뒤 옛 승인 지문으로는 게이트 ② 거부(재승인 강제)
(d) 골든·옛 프로젝트 상태 파일 무변화(새 필드는 선택, 게이트 집합 불변)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import pytest

from orchestrator.state_machine import GATES, SCRIPT_FIX_ROLLBACKS
from schemas.models import ProjectManifest
from schemas.models import ProjectState as S  # noqa: N817
from tests.test_gates_pipeline import _Proj, write_animatic

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.slow   # C8.3(D187) — 프로젝트 사본을 만든다(느린 묶음)
class RollbackScriptDraftTest(_Proj):
    def _after_gate1(self) -> None:
        from orchestrator.project_manager import approve_gate  # noqa: PLC0415

        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)

    def test_a_four_states_record(self) -> None:
        from orchestrator.project_manager import approve_gate, load_manifest, rollback, script_sha1  # noqa: PLC0415

        self._after_gate1()
        path = [S.ASSETS, S.DIRECTION, S.PREVIEW_QA]
        for i, st in enumerate([S.VOICE_TIMELINE, *path]):
            self.to(*path[:i])
            self.assertEqual(self.m.current_state, st.value)
            fp = script_sha1(self.root / "p")
            m = rollback(self.m, "script_draft", by="user", reason=f"원고 사실 수정 {i}", cfg=self.cfg)
            self.assertEqual(m.current_state, "script_draft")
            r = load_manifest("p", self.cfg).rollbacks[-1]
            self.assertEqual((r.from_state, r.to_state, r.by, r.reason, r.script_fingerprint_before),
                             (st.value, "script_draft", "user", f"원고 사실 수정 {i}", fp))
            self.to(S.SCRIPT_APPROVAL)
            self.m = approve_gate(self.m, "script_approval", by="user", cfg=self.cfg)
        self.assertEqual(len(load_manifest("p", self.cfg).rollbacks), 4)

    def test_b_reason_and_state_rules(self) -> None:
        from orchestrator.project_manager import rollback  # noqa: PLC0415

        self.to_gate1()
        with self.assertRaises(ValueError):   # 게이트 ① 에서는 반려(reject) 길
            rollback(self.m, "script_draft", by="u", reason="x", cfg=self.cfg)
        self._approve_gate1()
        with self.assertRaises(ValueError):   # 사유 필수
            rollback(self.m, "script_draft", by="u", reason="  ", cfg=self.cfg)
        with self.assertRaises(ValueError):   # script_draft 로만
            rollback(self.m, "research", by="u", reason="x", cfg=self.cfg)
        self.assertEqual(self.m.current_state, "voice_timeline")

    def _approve_gate1(self) -> None:
        from orchestrator.project_manager import approve_gate  # noqa: PLC0415

        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)

    def test_c_old_approval_blocks_gate2(self) -> None:
        from orchestrator.project_manager import AnimaticMissingError, approve_gate, rollback  # noqa: PLC0415

        self._after_gate1()
        self.to(S.ASSETS)
        self.m = rollback(self.m, "script_draft", by="user", reason="날짜 수정", cfg=self.cfg)
        sp = self.root / "p" / "script.yaml"
        sp.write_text(sp.read_text(encoding="utf-8") + "\n# 수정\n", encoding="utf-8")
        write_animatic(self.root / "p")   # 고친 원고로 만든 콘티 판
        # 재승인 없이 앞으로 가려 해도 게이트 ① 을 지나야 한다 — 옛 승인 지문 그대로면 게이트 ② 거부
        self.to(S.SCRIPT_APPROVAL)
        self.m.current_state = S.PREVIEW_APPROVAL.value   # type: ignore[assignment] — 재승인 건너뛴 상태를 흉내
        with self.assertRaises(AnimaticMissingError):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)


class RollbackShapeTest(unittest.TestCase):
    def test_d_gates_and_old_manifests_unchanged(self) -> None:
        self.assertEqual(GATES, frozenset({S.SCRIPT_APPROVAL, S.PREVIEW_APPROVAL}))   # 되돌림 표는 게이트가 아니다
        self.assertEqual(set(SCRIPT_FIX_ROLLBACKS), {S.VOICE_TIMELINE, S.ASSETS, S.DIRECTION, S.PREVIEW_QA})
        for mp in sorted(REPO.glob("projects/*/project_manifest.json")):
            raw = json.loads(mp.read_text(encoding="utf-8"))
            m = ProjectManifest.model_validate(raw)   # 옛 manifest(rollbacks 없음) 그대로 읽힌다
            if "rollbacks" not in raw:
                self.assertEqual(m.rollbacks, [], mp)
        self.assertFalse((REPO / "projects" / "hormuz_korea" / "project_manifest.json").exists()
                         and "rollbacks" in (REPO / "projects" / "hormuz_korea" / "project_manifest.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

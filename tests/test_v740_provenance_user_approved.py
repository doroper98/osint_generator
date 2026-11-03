"""v7.4.0 back_and_forth D-0345 — provenance qa.user_approved 는 manifest gate_decisions 의 마지막 게이트 ② 결정에서 읽는다
(옛 engine/provenance.py False 상수 — 사용자 승인을 받은 쇼케이스 전편에도 false 로 남았다, P5)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.provenance import user_approval


def _root(decisions: list[dict] | None) -> Path:
    d = Path(tempfile.mkdtemp())
    if decisions is not None:
        (d / "project_manifest.json").write_text(json.dumps({"gate_decisions": decisions}), encoding="utf-8")
    return d


G1 = {"gate": "script_approval", "decision": "approved", "by": "user", "at": "2026-11-01T00:00:00Z"}
G2 = {"gate": "preview_approval", "decision": "approved", "by": "user", "at": "2026-11-01T08:44:06Z"}


class UserApprovalTest(unittest.TestCase):
    def test_no_manifest_or_no_gate2(self) -> None:
        self.assertEqual(user_approval(_root(None)), {"user_approved": False})
        self.assertEqual(user_approval(_root([G1])), {"user_approved": False})   # 게이트 ① 만 = 프리뷰 단계

    def test_gate2_approved_by_user(self) -> None:
        r = user_approval(_root([G1, G2]))
        self.assertTrue(r["user_approved"])
        self.assertEqual(r["approval"]["at"], "2026-11-01T08:44:06Z")

    def test_last_decision_wins(self) -> None:
        rej = {**G2, "decision": "rejected", "at": "2026-11-02T00:00:00Z"}
        self.assertFalse(user_approval(_root([G1, G2, rej]))["user_approved"])

    def test_mux_writes_real_value(self) -> None:
        src = (Path(__file__).resolve().parents[1] / "engine" / "mux.py").read_text(encoding="utf-8")
        self.assertIn('prov["qa"] = {**prov["qa"], **user_approval(P.root)}', src)


if __name__ == "__main__":
    unittest.main()

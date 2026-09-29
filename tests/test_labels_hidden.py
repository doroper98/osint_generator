"""검증 라벨 화면 표시 끄기 — order.yaml decisions.verification_labels (dmz_mine_2026, 사용자 결정 2026-09-29).

사용자(by: user)가 hidden 으로 정했을 때만 끈다. 지침 기본값(by: default)이나 주문 없는 프로젝트는 그대로 표시.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from engine.project import labels_hidden

REPO = Path(__file__).resolve().parent.parent


def _order(decisions: dict) -> dict:
    return {"schema_version": 1, "topic": "시험 주제", "genre": "geopolitics", "instructions": ["시험"],
            "media": {"wanted": ["지도"], "rights": "권리 기록"}, "decisions": decisions}


class LabelsHiddenTest(unittest.TestCase):
    def _proj(self, decisions: dict | None) -> Path:
        d = Path(tempfile.mkdtemp())
        if decisions is not None:
            (d / "order.yaml").write_text(yaml.safe_dump(_order(decisions), allow_unicode=True), encoding="utf-8")
        return d

    def test_user_hidden(self) -> None:
        self.assertTrue(labels_hidden(self._proj({"verification_labels": {"value": "hidden", "by": "user"}})))

    def test_default_cannot_hide(self) -> None:
        self.assertFalse(labels_hidden(self._proj({"verification_labels": {"value": "hidden", "by": "default"}})))

    def test_no_order_or_no_decision(self) -> None:
        self.assertFalse(labels_hidden(self._proj(None)))
        self.assertFalse(labels_hidden(self._proj({})))

    def test_existing_projects_unchanged(self) -> None:
        for pid in ("hormuz_korea", "fed_policy_2026", "ratcliffe2026"):
            self.assertFalse(labels_hidden(REPO / "projects" / pid), pid)
        self.assertTrue(labels_hidden(REPO / "projects" / "dmz_mine_2026"))


if __name__ == "__main__":
    unittest.main()

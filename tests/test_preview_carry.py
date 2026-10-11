"""v5.22.5 D208 — 전편 provenance 에 프리뷰 검사·사용자 의견 장치 결과를 옮겨 적는다(출처·연출 지문 대조, P5·P6)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.provenance import direction_sha1, preview_carry


def _proj(root: Path, direction: str, prev: dict | None) -> None:
    (root / "direction.yaml").write_text(direction, encoding="utf-8")
    if prev is not None:
        (root / "prev").mkdir()
        (root / "prev" / "provenance.json").write_text(json.dumps(prev), encoding="utf-8")


GUARDS = [{"id": "UF-01", "checks": {"card_exposure": 0}}]
CHECKS = {"hard": 0, "warnings": 3, "passed": True}


class PreviewCarryTest(unittest.TestCase):
    def test_carries_checks_and_guards_with_current_direction(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "direction.yaml").write_text("a: 1\n", encoding="utf-8")
            sha = direction_sha1(root)
            (root / "prev").mkdir()
            (root / "prev" / "provenance.json").write_text(json.dumps(
                {"preview": {"direction_sha1": sha}, "checks": CHECKS, "user_feedback_guards": GUARDS}), encoding="utf-8")
            pc = preview_carry(root)
            self.assertIsNotNone(pc)
            self.assertEqual(pc["user_feedback_guards"], GUARDS)
            self.assertEqual(pc["checks"], CHECKS)
            self.assertIs(pc["from_current_direction"], True)
            self.assertEqual(pc["source"], "prev/provenance.json")

    def test_stale_preview_is_marked_not_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _proj(root, "a: 2\n", {"preview": {"direction_sha1": "0" * 40}, "checks": CHECKS, "user_feedback_guards": GUARDS})
            self.assertIs(preview_carry(root)["from_current_direction"], False)

    def test_preview_without_sha_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _proj(root, "a: 1\n", {"preview": {}, "checks": CHECKS})
            pc = preview_carry(root)
            self.assertIsNone(pc["from_current_direction"])
            self.assertEqual(pc["user_feedback_guards"], [])

    def test_no_preview_no_record(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _proj(root, "a: 1\n", None)
            self.assertIsNone(preview_carry(root))


if __name__ == "__main__":
    unittest.main()

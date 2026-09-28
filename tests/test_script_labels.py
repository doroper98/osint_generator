"""script/labels — 검증 라벨은 코드가 도시어 status 로 계산 (v3.0.0, back_and_forth D-0043, D42)."""

from __future__ import annotations

import unittest

from rules import load_rules
from schemas.models import ResearchClaimStatus
from script.labels import LabelError, compute_labels
from script.schema import Script


def _script(*sources: list[str]) -> Script:
    return Script.model_validate({"title": "t", "subtitle": "s", "date": "2026.09.18", "scenes": [
        {"id": "a", "sentences": [{"date": "2026", "text": f"문장 {chr(0xAC00 + i)}", "sources": src} for i, src in enumerate(sources)]}]})


ST = {"c1": "confirmed", "c2": "inferred", "c3": "claim", "c4": "unverified", "c5": "disputed"}


class LabelsTest(unittest.TestCase):
    def test_rule_keys_are_dossier_statuses(self) -> None:
        r = load_rules().script_schema
        self.assertEqual(set(r.labels), {s.value for s in ResearchClaimStatus})
        self.assertEqual(r.label_strength_order[0], "disputed")
        self.assertIsNone(r.labels["confirmed"])

    def test_weakest_status_wins(self) -> None:
        lab = compute_labels(_script(["c1"], ["c1", "c2"], ["c2", "c3"], ["c3", "c4", "c1"], ["c5", "c4"], []), ST).labels
        self.assertEqual([lab[f"a_{i}"].status for i in range(6)], ["confirmed", "inferred", "claim", "unverified", "disputed", None])

    def test_label_text_from_rules(self) -> None:
        r = load_rules().script_schema.labels
        lab = compute_labels(_script(["c4"], ["c1"]), ST).labels
        self.assertEqual(lab["a_0"].label, r["unverified"])
        self.assertIsNone(lab["a_1"].label)

    def test_unknown_claim_id_is_error(self) -> None:
        with self.assertRaises(LabelError) as ctx:
            compute_labels(_script(["c1"], ["zz"]), ST)
        self.assertIn("a_1:zz", str(ctx.exception))

    def test_counts(self) -> None:
        c = compute_labels(_script(["c1"], ["c4"], ["c4", "c1"], []), ST).counts()
        self.assertEqual(c, {"confirmed": 1, "inferred": 0, "claim": 0, "unverified": 2, "disputed": 0})


if __name__ == "__main__":
    unittest.main()

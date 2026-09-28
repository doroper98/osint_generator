"""script/labels — 검증 라벨은 코드가 claims.json status 로 계산 (v3.0.0 D42 → v3.2.0 D-0051 작업 7)."""

from __future__ import annotations

import unittest

from rules import load_rules
from schemas.source_models import Claim
from script.labels import LabelError, compute_labels, status_label
from script.schema import Script


def _script(*sources: list[str]) -> Script:
    return Script.model_validate({"title": "t", "subtitle": "s", "date": "2026.09.18", "scenes": [
        {"id": "a", "sentences": [{"date": "2026", "text": f"문장 {chr(0xAC00 + i)}", "sources": src} for i, src in enumerate(sources)]}]})


ST = {"c1": "verified", "c2": "corroborated", "c4": "unverified", "c5": "disputed"}


class LabelsTest(unittest.TestCase):
    def test_rule_keys_are_claim_statuses(self) -> None:
        import typing  # noqa: PLC0415

        r = load_rules().script_schema
        self.assertEqual(set(r.labels), set(typing.get_args(Claim.model_fields["status"].annotation)))
        self.assertEqual(r.label_strength_order[0], "disputed")
        self.assertIsNone(r.labels["verified"])
        self.assertIsNone(r.labels["corroborated"])
        self.assertEqual(status_label("unverified"), "<미검증>")
        self.assertIsNone(status_label(None))

    def test_weakest_status_wins(self) -> None:
        lab = compute_labels(_script(["c1"], ["c1", "c2"], ["c4", "c1"], ["c5", "c4"], []), ST).labels
        self.assertEqual([lab[f"a_{i}"].status for i in range(5)], ["verified", "corroborated", "unverified", "disputed", None])

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
        self.assertEqual(c, {"verified": 1, "corroborated": 0, "unverified": 2, "disputed": 0})


if __name__ == "__main__":
    unittest.main()

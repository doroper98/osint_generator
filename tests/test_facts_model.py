"""script.schema:Facts 최소 모델 (v3.1.0, D-0048 — 6.95 에서 ResearchWorker 전환)."""

from __future__ import annotations

import unittest

from script.schema import Facts


class FactsTest(unittest.TestCase):
    def test_contested_needs_both_sides(self) -> None:
        base = {"id": "f1", "text": "논쟁", "source_ids": ["s1"], "confidence": "medium", "contested": True}
        with self.assertRaises(ValueError):
            Facts.model_validate({"facts": [dict(base, sides=["한쪽만"])]})
        Facts.model_validate({"facts": [dict(base, sides=["찬성", "반대"])]})

    def test_source_required(self) -> None:
        with self.assertRaises(ValueError):
            Facts.model_validate({"facts": [{"id": "f1", "text": "출처 없는 수치 61%", "source_ids": [], "confidence": "low"}]})


if __name__ == "__main__":
    unittest.main()

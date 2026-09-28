"""engine/qa — 시각 검수 판정·수정 계약 (v3.1.0, 17 §4.3·§5.5, back_and_forth D-0047 작업 7·9)."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from engine.direction import load_direction_doc
from engine.qa import QAVerdict, Revision, unchanged_violations

REPO = Path(__file__).resolve().parent.parent
HORMUZ = REPO / "prompts" / "examples" / "hormuz_direction.yaml"


class QAVerdictTest(unittest.TestCase):
    def test_evidence_required(self) -> None:
        with self.assertRaises(ValueError):
            QAVerdict.model_validate({"verdict": "revise", "issues": [{"frame": "p_1", "severity": "hard", "category": "occlusion",
                                                                      "evidence": "가림"}]})
        v = QAVerdict.model_validate({"verdict": "revise", "issues": [{"frame": "p_1", "severity": "hard", "category": "occlusion",
                                                                      "evidence": "부산 뱃지가 카드 뒤에 가려짐"}]})
        self.assertEqual(v.hard_count(), 1)

    def test_unknown_category_rejected(self) -> None:
        with self.assertRaises(ValueError):
            QAVerdict.model_validate({"verdict": "pass", "issues": [{"frame": "p", "severity": "soft", "category": "vibes",
                                                                    "evidence": "그냥 별로다 느낌"}]})


class RevisionTest(unittest.TestCase):
    def test_changelog_required(self) -> None:
        d = load_direction_doc(HORMUZ).model_dump()
        with self.assertRaises(ValueError):
            Revision.model_validate({"direction": d, "changelog": []})

    def test_untouched_change_detected(self) -> None:
        before = load_direction_doc(HORMUZ)
        raw = copy.deepcopy(before.model_dump())
        busan = next(e for e in raw["events"] if e.get("label") == "부산에서 출항")
        busan["place"] = "map_upper_left"
        seoul = next(e for e in raw["events"] if e.get("label") == "서울")
        seoul["sub"] = "바뀐 부제"            # 지적받지 않은 변경
        after = Revision.model_validate({"direction": raw, "changelog": [{"issue_ref": "badge|flag|부산에서 출항", "change": "슬롯"}]})
        v = unchanged_violations(before, after.direction, {"부산에서 출항"})
        self.assertEqual(len(v), 1)
        self.assertIn("서울", v[0])


if __name__ == "__main__":
    unittest.main()

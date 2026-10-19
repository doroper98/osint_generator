"""v7.4.0 back_and_forth D-0229 §2.8 — 원고 어휘 린트: [verb-target-mismatch](UF-114) 오류, [contrast-conjunction](UF-108) 경고.
재현: diesel_road_2026 v1 원고 act1_0·act1_2('정유소를 맞혔습니다'·'2차 설비를 맞히는')·cold_2('반면 우크라이나 당국자는')."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from script.lint import vocab_issues
from script.schema import Script

REPO = Path(__file__).resolve().parent.parent


def _sc(*texts: str) -> Script:
    return Script.model_validate(dict(title="t", subtitle="s", date="2026.10.18",
                                      scenes=[dict(id="a", sentences=[dict(date="2026.10.15", text=t) for t in texts])]))


def _kinds(*texts: str) -> list[tuple[str, str, str]]:
    return [(i.kind, i.severity, i.sid) for i in vocab_issues(_sc(*texts))]


class VerbTargetTest(unittest.TestCase):
    def test_fixed_target_hard(self) -> None:
        self.assertEqual(_kinds("우크라이나는 러시아 정유소를 맞혔습니다."), [("verb-target-mismatch", "error", "a_0")])

    def test_strike_ok(self) -> None:
        self.assertEqual(_kinds("우크라이나는 러시아 정유소를 타격했습니다.", "2차 설비를 때리는 일이 늘었습니다."), [])

    def test_moving_target_ok(self) -> None:
        self.assertEqual(_kinds("방공망이 무인기를 맞혔습니다."), [])


class ContrastTest(unittest.TestCase):
    def test_after_statement_warns(self) -> None:
        self.assertEqual(_kinds("러시아 국방부는 파편이 불을 냈다고 밝혔습니다.", "반면 우크라이나 당국자는 공격을 확인했습니다."),
                         [("contrast-conjunction", "warning", "a_1")])

    def test_ie_daehae_ok(self) -> None:
        self.assertEqual(_kinds("러시아 국방부는 파편이 불을 냈다고 밝혔습니다.", "이에 대해 우크라이나 당국자는 공격을 확인했습니다."), [])

    def test_numeric_contrast_ok(self) -> None:
        self.assertEqual(_kinds("수출은 3.4% 줄었습니다.", "반면 수입은 늘었습니다."), [])


class V1ReproTest(unittest.TestCase):
    def test_diesel_v1(self) -> None:
        sc = REPO / "tests" / "fixtures" / "diesel_road_v1_script.yaml"
        doc = yaml.safe_load(sc.read_text(encoding="utf-8"))
        got = {(i.kind, i.sid) for i in vocab_issues(Script.model_validate(doc))}
        self.assertLessEqual({("verb-target-mismatch", "act1_0"), ("verb-target-mismatch", "act1_2"), ("contrast-conjunction", "cold_2")}, got)


if __name__ == "__main__":
    unittest.main()

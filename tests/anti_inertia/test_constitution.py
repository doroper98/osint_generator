"""test_constitution — 헌법 문서가 새 영상 기준을 가리킨다 (docs/handoff/15 P7, 19 부록 B)."""

from __future__ import annotations

import unittest

from tests.anti_inertia._ast_util import REPO


def _read(name: str) -> str:
    return (REPO / name).read_text(encoding="utf-8")


class ConstitutionTest(unittest.TestCase):
    def test_claude_md(self) -> None:
        text = _read("CLAUDE.md")
        for needle in ("docs/handoff/15", "byte-equal", "C11", "C0.1"):
            self.assertIn(needle, text)

    def test_goal_md(self) -> None:
        text = _read("GOAL.md")
        for needle in ("G7", "docs/handoff", "[legacy"):
            self.assertIn(needle, text)
        for n in range(13, 21):
            self.assertIn(f"\n{n}. ", text, f"GOAL G4-{n} 없음")

    def test_handoff_md(self) -> None:
        self.assertIn("docs/handoff/KICKOFF_PROMPT.md", _read("HANDOFF.md"))


if __name__ == "__main__":
    unittest.main()

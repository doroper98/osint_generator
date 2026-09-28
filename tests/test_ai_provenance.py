"""AI 연출 provenance (v3.1.0, 15 P5, back_and_forth D-0047 작업 9) — 워커 산출 파일이 있을 때만 ai_direction·visual_qa true."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.provenance import ai_direction_summary


class AIProvenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "prev").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ai(self) -> None:
        (self.root / "direction.meta.json").write_text(json.dumps({"origin": "ai", "model": "m", "prompt_sha1": "abc"}), encoding="utf-8")
        for n, body in ((1, "a: 1\n"), (2, "a: 2\n")):
            (self.root / f"direction.v{n}.yaml").write_text(body, encoding="utf-8")
        (self.root / "direction.yaml").write_text("a: 2\n", encoding="utf-8")
        (self.root / "prev" / "qa_verdict.v1.json").write_text(json.dumps({"verdict": "revise", "issues": [
            {"severity": "hard"}, {"severity": "soft"}]}), encoding="utf-8")
        (self.root / "prev" / "qa_verdict.v2.json").write_text(json.dumps({"verdict": "pass", "issues": []}), encoding="utf-8")
        (self.root / "prev" / "revision.v2.json").write_text(json.dumps({"direction_version": 2, "changelog": [{}, {}]}), encoding="utf-8")

    def test_human_direction_none(self) -> None:
        (self.root / "direction.yaml").write_text("a: 1\n", encoding="utf-8")
        self.assertIsNone(ai_direction_summary(self.root))

    def test_ai_summary(self) -> None:
        self._ai()
        s = ai_direction_summary(self.root)
        assert s is not None
        self.assertEqual(s["origin"], "ai")
        self.assertEqual(s["direction_versions"], 2)
        self.assertEqual([q["verdict"] for q in s["visual_qa"]], ["revise", "pass"])
        self.assertEqual(s["visual_qa"][0]["hard"], 1)
        self.assertEqual(s["revisions"], [{"direction_version": 2, "changes": 2}])   # 수정 기록은 v2 부터(v1 = 연출가 초안)

    def test_earlier_version_selected(self) -> None:
        """D-0049 쟁점 3 — 최선 판 선택으로 v1 이 쓰여도 AI 연출(사람 수정 아님)."""
        self._ai()
        (self.root / "direction.yaml").write_text("a: 1\n", encoding="utf-8")
        (self.root / "prev" / "qa_loop.json").write_text(json.dumps({"rounds": [{"version": 1, "checks_hard": 0}],
                                                                       "selected": {"version": 1, "by": "code", "reason": "r"}}),
                                                           encoding="utf-8")
        s = ai_direction_summary(self.root)
        assert s is not None
        self.assertEqual((s["origin"], s["used_version"], s["selected"]["version"]), ("ai", 1, 1))

    def test_human_edit_marked(self) -> None:
        self._ai()
        (self.root / "direction.yaml").write_text("a: 3\n", encoding="utf-8")
        s = ai_direction_summary(self.root)
        assert s is not None
        self.assertEqual(s["origin"], "ai+human_edit")


if __name__ == "__main__":
    unittest.main()

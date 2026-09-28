"""engine/camera_suggest — 연출가 제안 경로(v3.3.0, D-0056 작업 5). 제안은 옵션이다(P8)."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.camera_suggest import CameraSuggest, main, suggest
from engine.framing import place, plain_point

ROOT = Path(__file__).resolve().parents[1]
HORMUZ = ROOT / "projects" / "hormuz_korea"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


@unittest.skipUnless((HORMUZ / "direction.yaml").exists(), "hormuz 프로젝트 없음")
class CameraSuggestHormuzTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project  # noqa: PLC0415

        cls.P = load_project(HORMUZ)
        cls.cs = suggest(cls.P)

    def test_schema_roundtrip(self) -> None:
        again = CameraSuggest.model_validate_json(self.cs.model_dump_json())
        self.assertEqual(again, self.cs)
        self.assertEqual(again.schema_version, 1)

    def test_one_entry_per_camera_key(self) -> None:
        self.assertEqual(len(self.cs.shots), len(self.P.keys))

    def test_user_approved_v3_camera_fits(self) -> None:
        """사용자 합격 v3 카메라는 '장소가 화면 안'으로 판정돼야 한다(판정기가 골든을 틀렸다고 하면 판정기가 틀린 것)."""
        bad = [s.t for s in self.cs.shots if s.current_fits is False]
        self.assertEqual(bad, [])

    def test_shot_rules_clean_on_v3(self) -> None:
        self.assertEqual(self.cs.shot_issues_current, [])

    def test_transition_only_from_rule(self) -> None:
        for s in self.cs.shots:
            if s.suggested is not None and s.t > 0:
                self.assertIn(s.suggested_transition, ("move", "dip"))

    def test_cli_does_not_touch_direction(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "hz"
            shutil.copytree(HORMUZ, proj, ignore=shutil.ignore_patterns("prev", "out", "tts", "cache"))
            before = _md5(proj / "direction.yaml")
            self.assertEqual(main([str(proj)]), 0)
            self.assertEqual(_md5(proj / "direction.yaml"), before)
            data = json.loads((proj / "prev" / "camera_suggest.json").read_text(encoding="utf-8"))
            CameraSuggest.model_validate(data)


class LenientLineTest(unittest.TestCase):
    def test_line_point_may_pass_under_subtitle_only_in_lenient(self) -> None:
        low = plain_point(0.0, -7.0, "route#end", avoid_reserve=False)
        self.assertTrue(place([low], 0.0, 0.0, 30.0, lenient=True)[0])
        self.assertFalse(place([low], 0.0, 0.0, 30.0)[0])


if __name__ == "__main__":
    unittest.main()

"""원고 장면 music_intensity 힌트(v3.4.0, D-0060 작업 4, 10 §7-2) — 연출가 입력일 뿐, 코드 자동 주입 없음(P8)."""

from __future__ import annotations

import unittest
from pathlib import Path

from pydantic import ValidationError

from script.schema import Scene

REPO = Path(__file__).resolve().parents[1]
S = {"id": "a", "sentences": [{"text": "가.", "date": "2026"}]}


class MusicIntensityHintTest(unittest.TestCase):
    def test_range(self) -> None:
        self.assertEqual(Scene.model_validate({**S, "music_intensity": 0.7}).music_intensity, 0.7)
        self.assertIsNone(Scene.model_validate(S).music_intensity)
        for bad in (-0.1, 1.2):
            with self.assertRaises(ValidationError):
                Scene.model_validate({**S, "music_intensity": bad})

    def test_no_code_injects_hint_into_direction(self) -> None:
        """엔진·오디오·오케스트레이터 코드는 힌트를 읽지 않는다 — 연출가 프롬프트만 안다(P8)."""
        hits = [str(p.relative_to(REPO)) for d in ("engine", "audio", "orchestrator", "workers")
                for p in (REPO / d).rglob("*.py") if "music_intensity" in p.read_text(encoding="utf-8")]
        self.assertEqual(hits, [])
        self.assertIn("music_intensity", (REPO / "prompts" / "director.md").read_text(encoding="utf-8"))

    def test_hormuz_v3_has_no_hint(self) -> None:
        self.assertNotIn("music_intensity", (REPO / "projects" / "hormuz_korea" / "script.yaml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

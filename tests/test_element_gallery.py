"""요소 예제·갤러리 (v4.2.0, docs/handoff/20 §12 G2, back_and_forth D-0081 작업 6·9).

등록 요소마다 예제가 있고 모델을 통과한다(P4·P10), 예제 정본(prompts/examples)과 레지스트리 프리뷰 예제(tests/fixtures/preview)가
같은 event 다, 갤러리가 `--only` 없이 전체를 실제 엔진으로 그린다(빠진 예제 0).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from engine.registry import validate_events
from rules import load_rules
from tools.element_gallery import EXAMPLES, badge_variants, items

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "preview"


def expected_count() -> int:
    reg = load_rules().registries
    return len(reg.event_types) + len(reg.panel_kinds) + len(reg.badge_kinds) + len(reg.primitives) + len(badge_variants())


class ElementExamplesTest(unittest.TestCase):
    def test_every_registered_element_has_valid_example(self) -> None:
        got = items()
        self.assertEqual(len(got), expected_count())
        for label, _, doc in got:
            with self.subTest(element=label):
                self.assertEqual(len(validate_events([doc["event"]])), 1)

    def test_examples_match_preview_fixtures(self) -> None:
        pairs = [(EXAMPLES / "events" / f"{t}.yaml", FIXTURES / f"{t}.yaml") for t in load_rules().registries.event_types
                 if (EXAMPLES / "events" / f"{t}.yaml").exists()]
        pairs += [(EXAMPLES / "panels" / f"{k}.yaml", FIXTURES / f"panel_{k}.yaml") for k in load_rules().registries.panel_kinds]
        pairs.append((EXAMPLES / "badges" / "person.yaml", FIXTURES / "badge.yaml"))
        self.assertGreaterEqual(len(pairs), 26)
        for ex, fx in pairs:
            with self.subTest(example=ex.name):
                a = yaml.safe_load(ex.read_text(encoding="utf-8"))["event"]
                b = yaml.safe_load(fx.read_text(encoding="utf-8"))["event"]
                self.assertEqual(a, b)


class ElementGalleryRenderTest(unittest.TestCase):
    def test_full_gallery_renders(self) -> None:
        proj = REPO / "projects" / "hormuz_korea"
        missing = [p for p in ("plan.json", "tts", "assets", "media") if not (proj / p).exists()]
        if missing:
            raise RuntimeError(f"hormuz_korea 자산 없음 {missing} — HANDOFF §4 컨테이너 준비")
        from tools.element_gallery import main  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "gallery"
            self.assertEqual(main(["--proj", str(proj), "--out", str(out)]), 0)
            rep = json.loads((Path(d) / "gallery.json").read_text(encoding="utf-8"))
            self.assertTrue(rep["full"])
            self.assertEqual(rep["count"], expected_count())
            self.assertEqual(len(list(out.glob("*.png"))), expected_count())
            self.assertTrue((Path(d) / "gallery.jpg").exists())


if __name__ == "__main__":
    unittest.main()

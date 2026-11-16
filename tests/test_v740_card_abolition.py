"""v7.4.0 back_and_forth D-0306(사용자 의견 UF-148) — 구석 카드(card 이벤트) 폐지·이식 도구·화면 글자 되풀이 검사.

UF-148 원문: "이 오른쪽 상단에 뜨는 아일랜드 없애도 될거 같아. 어짜피 자막으로도, 음성으로도 그 이야기를 하는데 … 오른쪽 상단의 카드 자체의
규약을 없애라는 뜻이야."
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

from engine import checks
from rules import load_rules
from tools.migrate_cards import migrate_text

REPO = Path(__file__).resolve().parents[1]

SAMPLE = """events:
# 막 1
- type: marker
  t0: 1.0
  t1: 3.0
- type: card
  tag: 여러 매체가 확인
  lines:
  - 한 줄
  bigs:
  - [−3.4%, 전년 대비]
  start: s1
# 막 2
- type: route
  t0: 4.0
  t1: 6.0
"""


class RegistryTest(unittest.TestCase):
    def test_card_gone_from_registry(self) -> None:
        R = load_rules()  # noqa: N806
        self.assertNotIn("card", R.registries.event_types)
        self.assertNotIn("card", R.qa_checks.card_over_panel.cover_types)
        self.assertNotIn("card", R.qa_checks.chart_only_run.chart_types)
        self.assertFalse((REPO / "engine/cards.py").exists())
        self.assertFalse((REPO / "tests/fixtures/preview/card.yaml").exists())

    def test_no_card_in_live_directions(self) -> None:
        """현재 연출(direction.yaml)에 card 가 남지 않았다 — 옛 판(direction.vN.yaml)은 이력이라 보지 않는다."""
        left = []
        for f in sorted(REPO.glob("projects/*/direction.yaml")):
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
            evs = d.get("events") if isinstance(d, dict) else d
            left += [f.parent.name for e in evs or [] if isinstance(e, dict) and e.get("type") == "card"]
        self.assertEqual(left, [])


class MigrateTest(unittest.TestCase):
    def test_removes_block_keeps_rest(self) -> None:
        new, removed = migrate_text(SAMPLE)
        self.assertEqual([r["tag"] for r in removed], ["여러 매체가 확인"])
        self.assertEqual(removed[0]["bigs"], [["−3.4%", "전년 대비"]])
        self.assertEqual([e["type"] for e in yaml.safe_load(new)["events"]], ["marker", "route"])
        self.assertIn("# 막 1", new)
        self.assertIn("# 막 2", new)   # 같은 깊이 주석 = 다음 항목 머리(지우지 않는다)

    def test_cli_check_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "direction.yaml"
            f.write_text(SAMPLE, encoding="utf-8")
            run = [sys.executable, str(REPO / "tools/migrate_cards.py")]
            self.assertEqual(subprocess.run([*run, str(f), "--check"], capture_output=True, cwd=REPO).returncode, 1)
            rep = Path(d) / "table.md"
            self.assertEqual(subprocess.run([*run, str(f), "--report", str(rep)], capture_output=True, cwd=REPO).returncode, 0)
            self.assertIn("| 여러 매체가 확인 |", rep.read_text(encoding="utf-8"))
            self.assertEqual(subprocess.run([*run, str(f), "--check"], capture_output=True, cwd=REPO).returncode, 0)


class RestateTest(unittest.TestCase):
    def _P(self, events: list[dict]) -> SimpleNamespace:  # noqa: N802
        s = SimpleNamespace(t0=0.0, t1=5.0, sid="s1", text="미국 연준이 기준금리를 0.25%포인트 내려 4.00%로 정했습니다.")
        return SimpleNamespace(events=events, plan=SimpleNamespace(sentences=[s]))

    def test_restating_panel_title_is_hard(self) -> None:
        ev = {"type": "panel", "t0": 1.0, "t1": 4.0, "title": "미국 연준이 기준금리를 0.25%포인트 내려"}
        self.assertEqual(len(checks.check_text_restates_narration(self._P([ev]))), 1)
        self.assertIn("text_restates_narration", checks.HARD)

    def test_short_label_and_new_fact_pass(self) -> None:
        short = {"type": "marker", "t0": 1.0, "t1": 4.0, "label": "미국 연준"}                       # 이름표 = 최소 어절 미만
        new = {"type": "panel", "t0": 1.0, "t1": 4.0, "title": "점도표 중간값 3.6% 위원 19명 분포"}   # 자막에 없는 수치·목록
        later = {"type": "panel", "t0": 6.0, "t1": 8.0, "title": "미국 연준이 기준금리를 0.25%포인트 내려"}   # 다른 순간
        self.assertEqual(checks.check_text_restates_narration(self._P([short, new, later])), [])

    def test_rule_keys(self) -> None:
        q = load_rules().qa_checks
        self.assertEqual((q.restate_overlap_max, q.restate_min_words), (0.6, 4))


if __name__ == "__main__":
    unittest.main()

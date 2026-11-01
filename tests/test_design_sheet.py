"""디자인 시트 = 규칙의 거울(v7.4.0 전쟁사 W5, back_and_forth D-0307 §1-2 "시트의 값 = 규칙 값").

tools/design_sheet.py 는 load_rules()(Pydantic) 로 값을 읽는다. 이 시험은 rules/video_rules.yaml 원문(yaml.safe_load)과 대조한다 —
모델 기본값이 파일과 어긋나거나 시트가 값을 손으로 옮기면 실패한다. 렌더는 하지 않는다(컷은 시트 생성 때 실제 엔진으로).
"""

from __future__ import annotations

import html
import json
import sys
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import design_sheet as ds  # noqa: E402

RAW = yaml.safe_load((REPO / "rules" / "video_rules.yaml").read_text(encoding="utf-8"))


def raw_value(dotted: str) -> object:
    cur: object = RAW
    for part in dotted.split("."):
        assert isinstance(cur, dict), dotted
        cur = cur[part]
    return cur


class SheetValuesTest(unittest.TestCase):
    def test_rows_equal_rule_file(self) -> None:
        rows = ds.rule_rows()
        self.assertEqual(len(rows), len(ds.WAR_RULE_KEYS))
        for r in rows:
            with self.subTest(key=r["key"]):
                self.assertEqual(json.loads(json.dumps(r["value"])), json.loads(json.dumps(raw_value(r["key"]))))

    def test_cut_keys_are_table_rows(self) -> None:
        table = {k for _, k in ds.WAR_RULE_KEYS}
        for c in ds.WAR_CUTS:
            for k in c.rule_keys:
                with self.subTest(cut=c.cid, key=k):
                    self.assertIn(k, table)
            self.assertTrue((REPO / c.project / "sketch.yaml").is_file(), c.project)

    def test_html_shows_every_value(self) -> None:
        rows = ds.rule_rows()
        s = ds.Sheet("war_history", "0.0.0", rows, ds.era_rows(), [], None, None, None, ds.counterexamples())
        page = ds.render_html(s)
        for r in rows:
            with self.subTest(key=r["key"]):
                self.assertIn(f"data-key='{html.escape(r['key'])}'>{html.escape(ds.fmt_value(r['value']))}<", page)

    def test_era_badges_come_from_rules(self) -> None:
        fmt = raw_value("hud.date_badge.era_format")
        assert isinstance(fmt, dict)
        badges = {r["input"]: r["badge"] for r in ds.era_rows()}
        self.assertTrue(badges["-216.08.02R"].endswith(fmt["roman_suffix"]))
        self.assertTrue(badges["-216"].startswith(fmt["bce_prefix"]))

    def test_counterexamples_all_rejected(self) -> None:
        bad = ds.counterexamples()   # 하나라도 통과하면 SystemExit
        self.assertEqual(len(bad), 5)
        self.assertTrue(all(b["error"] for b in bad))


if __name__ == "__main__":
    unittest.main()

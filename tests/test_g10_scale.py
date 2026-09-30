"""v4.11.0 G10 §3 — 글자 크기 2차 표(자막 22·카드 line 16) (back_and_forth D-0118 §3, 사용자 위임 D103)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from golden_compare import load_expected_deltas  # noqa: E402

L = load_rules().layout_480p
G10 = REPO / "docs" / "handoff" / "reports" / "phaseG10"
GOLDEN = REPO / "docs" / "handoff" / "golden"


class ScaleTableTest(unittest.TestCase):
    def test_second_table_values(self) -> None:
        self.assertEqual(L.subtitle.size, 22)
        self.assertEqual(L.card.line_size, 16)
        # 그 밖 무변경(D-0113 표 3 유지 + 표 1·2 의 다른 값)
        self.assertEqual((L.card.big_size, L.card.tag_size, L.card.src_size, L.card.cap_size, L.card.line_gap), (30, 12, 11, 12, 24))
        self.assertEqual((L.subtitle.last_line_y, L.subtitle.line_gap), (452, 26))
        self.assertEqual((L.title_card.title_size, L.end_card.item_size, L.marker.label_size), (46, 9.2, 13))

    def test_golden_delta_registered(self) -> None:
        """g10_scale_d0118 컷 md5 = phaseG10 hormuz 기준선, 차이 사본이 있고, 요소 밖 변경 0, 타이틀·엔딩 컷 무변경."""
        raw = json.loads((GOLDEN / "expected_deltas.json").read_text(encoding="utf-8"))["deltas"]["g10_scale_d0118"]
        self.assertIn("g10_scale_d0118", load_expected_deltas())
        self.assertEqual(raw["old_rules"], {"layout_480p.subtitle.size": 21, "layout_480p.card.line_size": 15})
        self.assertEqual(raw["new_rules"], {"layout_480p.subtitle.size": L.subtitle.size, "layout_480p.card.line_size": L.card.line_size})
        base = json.loads((G10 / "hormuz_baseline.json").read_text(encoding="utf-8"))
        md5 = {c["png"]: c["md5"] for c in base["cuts"]}
        self.assertEqual(len(raw["cuts"]) + len(raw["unchanged"]), 25)
        self.assertEqual(raw["unchanged"], ["02_TITLE", "25_END"])
        self.assertEqual(sorted(d["render"] for d in raw["cut_detail"].values()), base["changed_vs_g7"])
        for c in raw["cuts"]:
            d = raw["cut_detail"][c]
            self.assertEqual(d["md5"], md5[d["render"]], c)
            self.assertEqual(d["outside_px"], 0, c)
            self.assertTrue((G10 / "golden_delta" / d["render"].replace(".png", "_old_new_diff.png")).exists(), c)
        self.assertGreaterEqual(raw["inside_ratio"], 0.99)
        self.assertEqual(base["checks"]["hard"], 0)

    def test_subtitle_lines_record(self) -> None:
        """2줄 자막 수 전/후 기록, 3줄 0(qa_checks.subtitle_lines_max 2)."""
        rec = json.loads((G10 / "subtitle_lines.json").read_text(encoding="utf-8"))["projects"]
        mx = load_rules().qa_checks.subtitle_lines_max
        for p, d in rec.items():
            for size, by in d["lines_by_size"].items():
                self.assertEqual(sum(by.values()), d["sentences"], (p, size))
                self.assertLessEqual(max(int(n) for n in by), mx, (p, size))
        self.assertEqual(rec["hormuz_korea"]["lines_by_size"]["22"], {"1": 28, "2": 17})

    def test_regression_baselines_hard_zero(self) -> None:
        rb = json.loads((G10 / "regression_baselines.json").read_text(encoding="utf-8"))["projects"]
        self.assertEqual(set(rb), {"ratcliffe2026", "fed_policy_2026", "fed_timeline_demo"})
        for p, d in rb.items():
            self.assertEqual(d["checks_hard"], 0, p)
            self.assertEqual(d["old_render_eq_prev_baseline"], f"{d['of']}/{d['of']}", p)   # 옛 렌더 = phaseG7 기준선


if __name__ == "__main__":
    unittest.main()

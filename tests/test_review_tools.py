"""눈 검수 도구(v7.4.0 back_and_forth D-1000 S4, LLM-AP-023) — tools/review_sheet.py · tools/uf_checklist.py.

다시 렌더하지 않는다: 합성 프로젝트(fed_timeline_demo, 자산 없음) + ffmpeg lavfi 로 만든 짧은 mp4 를 콘티 판 자리에 둔다.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class ReviewToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from tests.test_g8_animatic import synthetic_project

        cls.tmp = tempfile.TemporaryDirectory()
        cls.proj = synthetic_project("fed_timeline_demo", Path(cls.tmp.name) / "demo")
        (cls.proj / "out").mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=854x480:r=24:d=13", "-pix_fmt", "yuv420p",
                        str(cls.proj / "out" / "animatic.mp4")], check=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_review_sheet_cells_and_labels(self) -> None:
        from tools import review_sheet

        self.assertEqual(review_sheet.main([str(self.proj), "--src", "animatic", "--every", "3"]), 0)
        rv = self.proj / "out" / "review"
        self.assertTrue((rv / "animatic_sheet_01.jpg").exists())
        md = (rv / "animatic_elements.md").read_text(encoding="utf-8")
        self.assertIn("| # | 종류 | 이름 | 시작 | 끝 | 완전 노출(초) | 지도 사건 가림 최대 | 가린 사건 |", md)

    def test_hud_date_matches_draw_rule(self) -> None:
        from engine.project import load_project
        from tools.review_sheet import hud_date

        P = load_project(self.proj, animatic=True)  # noqa: N806
        tb = P.R.tb
        s = next(tb.sent[i] for i in tb.order[1:] if not tb.in_fullcard(tb.sent[i].t0 - 0.2))
        self.assertEqual(hud_date(tb, s.t0 + 0.1), s.date)
        self.assertEqual(hud_date(tb, s.t0 - 0.2), s.date)   # 문장 시작 0.3초 전부터(engine.hud.draw_date)

    def test_missing_mp4_is_error(self) -> None:
        from tools import review_sheet

        with self.assertRaises(FileNotFoundError):
            review_sheet.main([str(self.proj), "--src", "final"])   # 렌더하지 않는다 — 없으면 오류(P6)

    def test_uf_checklist_all_entries(self) -> None:
        from rules import load_user_feedback
        from tools import uf_checklist

        prov = self.proj / "out" / "animatic_provenance.json"
        prov.write_text(json.dumps({"user_feedback_guards": [{"id": "UF-01", "checks": {"card_exposure": 0}},
                                                             {"id": "UF-171", "checks": {"element_hold": 2}}]}), encoding="utf-8")
        try:
            self.assertEqual(uf_checklist.main([str(self.proj), "--src", "animatic"]), 0)
        finally:
            prov.unlink()
        md = (self.proj / "out" / "uf_checklist.md").read_text(encoding="utf-8")
        rows = [ln for ln in md.splitlines() if ln.startswith("| UF-")]
        self.assertEqual(len(rows), len(load_user_feedback().entries))   # 원장 전부(빠짐 없음)
        self.assertIn("card_exposure: pass", next(r for r in rows if r.startswith("| UF-01 |")))
        self.assertIn("element_hold: **fail 2**", next(r for r in rows if r.startswith("| UF-171 |")))
        self.assertTrue(any("[ ]" in r for r in rows))   # 눈 확인 칸

    def test_classes_and_look_times(self) -> None:
        from tools.uf_checklist import classes_of, look_times

        self.assertEqual(classes_of("뱃지나 사진이나 기사 조판"), ["사진", "배지"])
        ev = [{"type": "photo", "t0": 10.0, "t1": 18.0}, {"type": "marker", "t0": 0.0, "t1": 4.0}]
        self.assertEqual(look_times(ev, ("photo",), 3.0), [15.0])


if __name__ == "__main__":
    unittest.main()

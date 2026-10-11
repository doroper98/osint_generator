"""v5.21.4 D-0190 §3-1 — 전편 provenance 의 국소 대비 보정 기록: 청크별 기록을 합친다(이름마다 최저), 청크 기록이 없으면 오류(P6)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.render import contrast_fix_path, merge_contrast_fix


class MergeTest(unittest.TestCase):
    def test_merge_min_per_name_and_missing_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p0, p1 = Path(d) / "part00.mp4", Path(d) / "part01.mp4"
            contrast_fix_path(p0).write_text(json.dumps({"무스카트": 4.06, "후티 장악": 3.6}), encoding="utf-8")
            contrast_fix_path(p1).write_text(json.dumps({"후티 장악": 3.46}), encoding="utf-8")
            self.assertEqual(merge_contrast_fix([p0, p1]), {"무스카트": 4.06, "후티 장악": 3.46})
            with self.assertRaises(RuntimeError):
                merge_contrast_fix([p0, Path(d) / "part02.mp4"])

    def test_empty_chunks_give_empty_record(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p0 = Path(d) / "part00.mp4"
            contrast_fix_path(p0).write_text("{}", encoding="utf-8")
            self.assertEqual(merge_contrast_fix([p0]), {})


if __name__ == "__main__":
    unittest.main()

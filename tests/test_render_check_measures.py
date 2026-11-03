"""provenance 에 검사가 잰 값 옮기기(v7.4.0 R-0335) — provenance 는 검사 전에 만들어져 명료도·terrain3d 이음 MAD 가 비어 있었다(콘티 판 v2, P5)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine.render import record_check_measures


class RecordCheckMeasuresTest(unittest.TestCase):
    def test_fills_after_checks(self) -> None:
        P = NS(R=NS(cache={"narration_clarity": {"min_db": 15.6}, "terrain3d_seam": [{"mad": 6.2}]}))  # noqa: N806
        prov = {"narration_clarity": None, "terrain3d": {"seam": None}}
        record_check_measures(P, prov)
        self.assertEqual(prov["narration_clarity"], {"min_db": 15.6})
        self.assertEqual(prov["terrain3d"]["seam"], [{"mad": 6.2}])

    def test_absent_stays_absent(self) -> None:
        prov = {"narration_clarity": None}
        record_check_measures(NS(R=NS(cache={})), prov)
        self.assertEqual(prov, {"narration_clarity": None})   # 돌지 않은 검사는 기록하지 않는다(P5)


if __name__ == "__main__":
    unittest.main()

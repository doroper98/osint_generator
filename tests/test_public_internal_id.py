"""v7.4.0 D-0634 — 공개 문안(엔딩 카드 크레딧 줄·설명문·제목·태그)에 내부 번호가 있으면 실패(칸나이 v1 엔딩 카드 'D-0630(UF-263)')."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine import checks as C
from tools import deliver_package as D


class InternalIdTest(unittest.TestCase):
    def test_hits(self) -> None:
        self.assertEqual(C.internal_ids("편집: 악구 이어 붙임(원곡 8구간, 녹음 불변) — D-0630(UF-263)"), ["D-0630", "UF-263"])
        for s in ("감독 D754 결정", "R-0337 참조", "RENDER-AP-040 사고"):
            self.assertTrue(C.internal_ids(s), s)

    def test_public_numbers_pass(self) -> None:
        for s in ("루브르 AO 5244", "루브르 MR 2093", "폴리비오스 『역사』 III.113~116", "Op. 62", "doi:10.1038/srep09989",
                  "B-52 폭격기", "D-Day", "2026. 11. 01", "#칸나이전투"):
            self.assertEqual(C.internal_ids(s), [], s)

    def test_package_rejects_internal_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            thumb = Path(td) / "t.jpg"
            thumb.write_bytes(b"x")
            errs = D.check_package("제목", "음악: 코리올란 — 편집: 악구 이어 붙임 — D-0630(UF-263)", ["태그"], ["#a", "#b", "#c"], thumb)
            self.assertTrue(any("내부 번호" in e for e in errs), errs)

    def test_registered_hard(self) -> None:
        self.assertIn("public_internal_id", C.HARD)


if __name__ == "__main__":
    unittest.main()

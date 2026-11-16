"""v7.4.0 — 엔딩 카드 라이선스 줄 줄바꿈. showcase_geo 게이트 ② 자료 엔딩 컷에서 인물 사진(auto: people) 권리 문구
"This image is available from the United States Library of Congress's Prints and …" 가 화면 오른쪽 밖으로 나갔다(항목 줄만 접고 라이선스 줄은 안 접었다)."""

from __future__ import annotations

import unittest

from engine.fullcards import COL_W, LICENSE_LINE, endcard_layout, license_lines
from engine.style import END_CARD
from engine.typography import adv

LONG = "This image is available from the United States Library of Congress's Prints and Photographs division under the digital ID ppmsca.12345"


class LicenseWrapTest(unittest.TestCase):
    def test_long_license_fits_column(self) -> None:
        ls = license_lines(LONG, 1)
        self.assertGreater(len(ls), 1)
        self.assertTrue(all(adv(x, END_CARD.license_size, "monom") <= COL_W[1] for x in ls), ls)
        self.assertEqual(" ".join(ls), LONG)

    def test_short_license_unchanged(self) -> None:
        self.assertEqual(license_lines("Public domain", 1), ["Public domain"])

    def test_layout_advances_by_wrapped_lines(self) -> None:
        secs = [("인물 사진", [("도널드 트럼프", LONG), ("다음 항목", "MIT")])]
        (_, _, _, _, rows), = endcard_layout(secs, [1])[0]
        n = len(license_lines(LONG, 1))
        self.assertEqual(rows[0][1].count("\n"), n - 1)
        self.assertEqual(rows[1][2] - rows[0][2], 23 + LICENSE_LINE * (n - 1))


if __name__ == "__main__":
    unittest.main()

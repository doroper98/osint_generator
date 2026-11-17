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


SA_NOTICE = ("aismallard · File:Thurgood Marshall United States Courthouse 2018-06-14.jpg · CC BY-SA 3.0 · "
             "https://commons.wikimedia.org/wiki/File:Thurgood_Marshall_United_States_Courthouse_2018-06-14.jpg · 자르기·크기 조정·색 보정")


class LongTokenWrapTest(unittest.TestCase):
    """v7.4.0 D935(RENDER-AP-041) — CC BY-SA 고지 줄의 링크는 띄어쓰기 없는 한 낱말이라 줄바꿈되지 않고 옆 열 글자 위로 넘어갔다
    (nvidia-chips-china-2026 엔딩 카드). 돌려주는 모든 줄은 열 폭 안이고, 글자는 하나도 빠지지 않는다."""

    def test_link_is_broken_inside_the_column(self) -> None:
        for ci in (0, 1):
            with self.subTest(column=ci):
                ls = license_lines(SA_NOTICE, ci)
                self.assertTrue(all(adv(x, END_CARD.license_size, "monom") <= COL_W[ci] for x in ls), ls)
                self.assertEqual("".join(ls).replace(" ", ""), SA_NOTICE.replace(" ", ""), "글자 유실 없음")

    def test_break_prefers_separator(self) -> None:
        from engine.fullcards import break_long

        url = "https://commons.wikimedia.org/wiki/File:Thurgood_Marshall_United_States_Courthouse_2018-06-14.jpg"
        parts = break_long(url, COL_W[0], END_CARD.license_size, "monom")
        self.assertGreater(len(parts), 1)
        self.assertEqual("".join(parts), url)
        self.assertTrue(all(p[-1] in "/_-.·" for p in parts[:-1]), parts)


if __name__ == "__main__":
    unittest.main()

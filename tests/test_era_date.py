"""EraDate(v7.4.0 전쟁사 W1, back_and_forth D-0600 §3) — 파서 왕복·정렬·뱃지 문구·린트."""

from __future__ import annotations

import unittest

from schemas.era_date import EraDate, badge_text, day_date, is_era_date, parse_era_date
from script.schema import Sentence


class ParseTest(unittest.TestCase):
    def test_legacy_forms_unchanged(self) -> None:
        for s, prec in (("2026", "year"), ("2026.07", "month"), ("2026.07.07", "day")):
            d = parse_era_date(s)
            self.assertEqual((d.astronomical_year, d.precision), (2026, prec))
            self.assertEqual(d.calendar, "gregorian")

    def test_bce_is_historical_notation(self) -> None:
        d = parse_era_date("-216.08.02")
        self.assertEqual((d.astronomical_year, d.month, d.day, d.precision), (-215, 8, 2, "day"))
        self.assertTrue(d.bce)
        self.assertEqual(d.historical_year, 216)
        self.assertEqual(parse_era_date("-1").astronomical_year, 0)

    def test_circa_and_period(self) -> None:
        self.assertEqual(parse_era_date("c.-216").precision, "circa")
        self.assertEqual(parse_era_date("c.1450").astronomical_year, 1450)
        p = parse_era_date("-218~-201")
        self.assertEqual((p.precision, p.astronomical_year, p.end.astronomical_year), ("period", -217, -200))
        self.assertEqual(parse_era_date("1950~1953").end.astronomical_year, 1953)

    def test_rejects(self) -> None:
        for bad in ("0", "-0", "2026.13", "2026.02.30", "c.-216.08", "-201~-218", "2026-07-07", "기원전 216", "", "c.2026~2027"):
            self.assertFalse(is_era_date(bad), bad)
        self.assertTrue(is_era_date("2024.02.29"))
        self.assertFalse(is_era_date("2023.02.29"))

    def test_model_validation(self) -> None:
        with self.assertRaises(ValueError):
            EraDate(astronomical_year=-215, month=8, precision="day")
        with self.assertRaises(ValueError):
            EraDate(astronomical_year=-215, precision="period")


class OrderTest(unittest.TestCase):
    def test_bce_before_ce(self) -> None:
        xs = ["2026.07.07", "-216.08.02", "-218", "1950.09.15", "-1.12.31", "1"]
        got = [s for s in sorted(xs, key=lambda s: parse_era_date(s).day_number())]
        self.assertEqual(got, ["-218", "-216.08.02", "-1.12.31", "1", "1950.09.15", "2026.07.07"])
        self.assertLess(parse_era_date("-216"), parse_era_date("-215"))

    def test_day_gaps_match_datetime_for_ce(self) -> None:
        a, b = parse_era_date("1950.09.15"), parse_era_date("1950.09.28")
        self.assertEqual(a.days_to(b), 13)
        self.assertEqual(parse_era_date("-1.12.31").days_to(parse_era_date("1.01.01")), 1)
        self.assertEqual(parse_era_date("2026.03.01").iso(), "2026-03-01")

    def test_day_date(self) -> None:
        self.assertEqual(str(day_date("1950.09.15")), "1950-09-15")
        self.assertIsNone(day_date("1950.09"))
        self.assertIsNone(day_date("-216.08.02"))


class BadgeTest(unittest.TestCase):
    def test_ce_legacy_text(self) -> None:
        self.assertEqual(badge_text("2026.07.07"), "2026. 07. 07")
        self.assertEqual(badge_text("2026.07"), "2026. 07")
        self.assertEqual(badge_text("2026"), "2026")

    def test_era_text(self) -> None:
        self.assertEqual(badge_text("-216.08.02"), "기원전 216년 8월 2일")
        self.assertEqual(badge_text("-216.08"), "기원전 216년 8월")
        self.assertEqual(badge_text("-216"), "기원전 216년")
        self.assertEqual(badge_text("c.-216"), "기원전 3세기경")
        self.assertEqual(badge_text("c.-201"), "기원전 3세기경")
        self.assertEqual(badge_text("c.-200"), "기원전 2세기경")
        self.assertEqual(badge_text("c.1450"), "15세기경")
        self.assertEqual(badge_text("-218~-201"), "기원전 218~201년")
        self.assertEqual(badge_text("1950~1953"), "1950~1953")
        self.assertEqual(badge_text("-27~14"), "기원전 27년~서기 14년")


class ScriptSchemaTest(unittest.TestCase):
    def test_sentence_accepts_era(self) -> None:
        for d in ("2026.07.07", "-216.08.02", "c.-216", "-218~-201"):
            Sentence(date=d, text="칸나이에서 두 군대가 만났습니다.")
        with self.assertRaises(ValueError):
            Sentence(date="216 BC", text="칸나이에서 두 군대가 만났습니다.")


if __name__ == "__main__":
    unittest.main()


class RomanCalendarTest(unittest.TestCase):
    """v7.4.0 D-0610 ④ — 로마력 날짜 'R' 표시: calendar roman, 뱃지 뒤 rules era_format.roman_suffix, 일까지 적은 날짜에만."""

    def test_roman_suffix(self) -> None:
        from schemas.era_date import badge_text, parse_era_date

        d = parse_era_date("-216.08.02R")
        self.assertEqual((d.calendar, d.historical_year, d.month, d.day), ("roman", 216, 8, 2))
        self.assertTrue(badge_text("-216.08.02R").endswith("(로마력)"))
        self.assertNotIn("로마력", badge_text("-216.08.02"))
        with self.assertRaises(ValueError):
            parse_era_date("-216R")

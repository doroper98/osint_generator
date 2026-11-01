"""v7.4.0 back_and_forth D-0326 — 연준 금리 아일랜드 band(목표 범위)와 선(실효금리) 어긋남(사용자 의견 UF-200 "왜 상한과 하한의 밴드와 금리 기준 선(노란색)이
다른 구간이 있지?"). 원인: 목표 범위 등재본이 월 표본(달 첫날로 당겨짐), 선은 월평균. 고침: band = 일별 원자료(발효일 계단), 선 = 월평균 그대로,
출처 줄에 입자. 장치: [band-line-outside] hard·[series-date-convention] warning."""

from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace as NS
from unittest import mock

from data.series import load_series
from engine import checks


def _rec(sid: str, values: list, freq: str, within: list | None = None, grain: str | None = "g") -> NS:
    return NS(series_id=sid, values=values, frequency=freq, within=within or [], grain=grain)


class DataTest(unittest.TestCase):
    def test_band_daily_effective_dates(self) -> None:
        lo, hi = load_series("DFEDTARL"), load_series("DFEDTARU")
        self.assertEqual((lo.frequency, lo.transform.op), ("daily", "raw"))
        v = dict(lo.values)
        self.assertEqual((v[date(2025, 10, 29)], v[date(2025, 10, 30)]), (4.0, 3.75))   # 발효일 10/30
        self.assertEqual((v[date(2025, 12, 10)], v[date(2025, 12, 11)]), (3.75, 3.5))   # 발효일 12/11
        self.assertEqual(load_series("FEDFUNDS").within, ["DFEDTARL", "DFEDTARU"])
        self.assertTrue(all(r.grain for r in (lo, hi, load_series("FEDFUNDS"))))


class CheckTest(unittest.TestCase):
    def _P(self, line: list, freq: str = "monthly") -> NS:
        days = [date(2025, 9, 1), date(2025, 10, 30), date(2025, 12, 11)]
        recs = {"LO": _rec("LO", list(zip(days, [4.0, 3.75, 3.5])), "daily"), "HI": _rec("HI", list(zip(days, [4.25, 4.0, 3.75])), "daily"),
                "LINE": _rec("LINE", line, freq, within=["LO", "HI"])}
        ev = [{"type": "series", "lane": "r", "series_id": "LO", "upper_id": "HI", "style": "band"},
              {"type": "series", "lane": "r", "series_id": "LINE", "style": "step"}]
        P = NS(events=ev, R=NS(stage=NS(name="backdrop"), cache={}))  # noqa: N806
        self._recs = recs
        return P

    def test_outside_in_quiet_month_fails_change_month_passes(self) -> None:
        P = self._P([(date(2025, 9, 1), 4.6), (date(2025, 10, 1), 4.09), (date(2025, 11, 1), 3.88)])  # noqa: N806
        with mock.patch("data.series.load_series", side_effect=lambda s: self._recs[s]):
            out = checks.check_band_line_outside(P)
        self.assertEqual(len(out), 1)   # 9월(변경 없음) 4.6 > 4.25 만. 10월(10/30 변경) 은 월평균이라 제외, 11월 3.88 은 안
        self.assertIn("2025-09-01", out[0])
        self.assertIn("band_line_outside", checks.HARD)

    def test_date_convention_warning(self) -> None:
        P = self._P([(date(2025, 9, 1), 4.1), (date(2025, 10, 1), 4.0)])  # noqa: N806
        self._recs["LINE"].grain = None
        with mock.patch("data.series.load_series", side_effect=lambda s: self._recs[s]):
            out = checks.check_series_date_convention(P)
        self.assertEqual(len(out), 1)
        self.assertIn("series_date_convention", checks.WARN)


if __name__ == "__main__":
    unittest.main()

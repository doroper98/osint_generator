"""v7.4.0 D-0278 §4.2(E3) — 공시 레코드(source_kind filing)·분기·일별·가이던스(issued_on)·fetch_filing 오프라인 경로.

시험 입력은 시험 전용 표(HTML)·응답(JSON)이다 — 실제 회사 값이 아니다(영상 데이터로 쓰지 않는다).
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml
from pydantic import ValidationError

from data.series import SeriesError, chart_close, load_series_file
from rules import load_rules
from schemas.data_models import SeriesRecord
from tools import fetch_filing as ff

TR = load_rules().data.transforms
URL = "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/ex991.htm"
F = {"form": "8-K Ex.99.1", "number": "0000000001-26-000001", "filed_on": "2026-10-29", "item": "Net revenue",
     "locator": "표 0 · 행 'Net revenue' · 열 1", "url": URL, "raw_unit": "백만 달러"}
BASE: dict = {
    "source_kind": "filing", "series_id": "TEST_REV_Q", "source": "시험 공시", "source_url": URL,
    "retrieved_at": "2026-10-30", "transform": {"op": "filing", "formula": TR["filing"]}, "as_of": "2026-09",
    "unit": "십억 달러", "frequency": "quarterly", "license": "public_filing", "license_note": "공개 공시 기록",
    "values": [("2026-06-30", 12.9), ("2026-09-30", 13.7)],
    "filings": [{**F, "date": "2026-06-30", "raw_value": 12_861.0}, {**F, "date": "2026-09-30", "raw_value": 13_653.0}],
}


def rec(**over: object) -> dict:
    d = copy.deepcopy(BASE)
    d.update(over)
    return d


class FilingRecordTest(unittest.TestCase):
    def test_valid(self) -> None:
        r = SeriesRecord.model_validate(rec())
        self.assertEqual(r.filing(date(2026, 9, 30)).scaled(), ("십억 달러", 13.7))

    def test_hand_edited_value_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "환산"):
            SeriesRecord.model_validate(rec(values=[("2026-06-30", 12.9), ("2026-09-30", 13.8)]))

    def test_each_value_needs_filing(self) -> None:
        with self.assertRaisesRegex(ValidationError, "filings 하나"):
            SeriesRecord.model_validate(rec(filings=BASE["filings"][1:]))

    def test_filing_domain(self) -> None:
        bad = copy.deepcopy(BASE["filings"])
        bad[0]["url"] = "https://example.com/x.htm"
        with self.assertRaisesRegex(ValidationError, "sources_allowed"):
            SeriesRecord.model_validate(rec(filings=bad))

    def test_unit_mismatch(self) -> None:
        with self.assertRaisesRegex(ValidationError, "레코드 단위"):
            SeriesRecord.model_validate(rec(unit="조 원"))

    def test_license_must_be_public_filing(self) -> None:
        with self.assertRaisesRegex(ValidationError, "public_filing"):
            SeriesRecord.model_validate(rec(license="cc_by_4"))

    def test_filings_only_on_filing_kind(self) -> None:
        with self.assertRaisesRegex(ValidationError, "filings 는"):
            SeriesRecord.model_validate(rec(source_kind="fetched"))


class QuarterlyDailyTest(unittest.TestCase):
    def test_quarter_end_dates(self) -> None:
        with self.assertRaisesRegex(ValidationError, "분기 마지막 날"):
            SeriesRecord.model_validate(rec(values=[("2026-06-30", 12.9), ("2026-09-29", 13.7)],
                                            filings=[{**F, "date": "2026-06-30", "raw_value": 12_861.0},
                                                     {**F, "date": "2026-09-29", "raw_value": 13_653.0}]))

    def test_gap_quarter_must_be_missing(self) -> None:
        fl = [{**F, "date": "2026-03-31", "raw_value": 12_861.0}, {**F, "date": "2026-09-30", "raw_value": 13_653.0}]
        with self.assertRaisesRegex(ValidationError, "빈 분기"):
            SeriesRecord.model_validate(rec(values=[("2026-03-31", 12.9), ("2026-09-30", 13.7)], filings=fl))
        r = SeriesRecord.model_validate(rec(values=[("2026-03-31", 12.9), ("2026-09-30", 13.7)], filings=fl,
                                            missing=[{"date": "2026-06-30", "note": "시험 — 공시 없음"}]))
        self.assertEqual(r.missing_dates(), [date(2026, 6, 30)])

    def test_guidance_issued_on(self) -> None:
        """가이던스(미래 분기 한 열) — as_of = 발표 달, 값 날짜는 retrieved_at 뒤."""
        fl = [{**F, "date": "2026-12-31", "raw_value": 15_000.0, "item": "Revenue outlook (low)"}]
        g = rec(series_id="TEST_GUIDE_LO", values=[("2026-12-31", 15.0)], filings=fl)
        with self.assertRaisesRegex(ValidationError, "as_of"):
            SeriesRecord.model_validate(g)
        r = SeriesRecord.model_validate({**g, "issued_on": "2026-10-29", "as_of": "2026-10"})
        self.assertEqual(r.as_of_label(), "2026년 10월 기준")

    def test_daily_weekend_rejected(self) -> None:
        d = {"series_id": "TEST_PX_D", "source": "시험 시세", "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/TEST",
             "retrieved_at": "2026-10-30", "transform": {"op": "chart_close", "formula": TR["chart_close"]}, "as_of": "2026-10",
             "unit": "달러", "frequency": "daily", "license": "private_only_market_data", "license_note": "시험"}
        SeriesRecord.model_validate({**d, "values": [("2026-10-28", 1.0), ("2026-10-29", 1.05)]})
        with self.assertRaisesRegex(ValidationError, "거래일"):
            SeriesRecord.model_validate({**d, "values": [("2026-10-23", 1.0), ("2026-10-24", 1.05)]})


def _chart_json(days: list[date], closes: list[float | None], off: int = -14400) -> str:
    ts = [int((datetime(d.year, d.month, d.day, 9, 30, tzinfo=timezone.utc) - timedelta(seconds=off)).timestamp()) for d in days]
    return json.dumps({"chart": {"result": [{"meta": {"gmtoffset": off}, "timestamp": ts,
                                             "indicators": {"quote": [{"close": closes}]}}]}})


HTML = b"""<html><body><table>
<tr><th>(In Millions)</th><th>Q3 2026</th><th>Q3 2025</th></tr>
<tr><td>Net revenue</td><td>13,653</td><td>12,861</td></tr>
<tr><td>Operating income (loss)</td><td>(1,234)</td><td>683</td></tr>
</table></body></html>"""


class FetchFilingOfflineTest(unittest.TestCase):
    def test_parse_number(self) -> None:
        self.assertEqual(ff.parse_number("(1,234)"), -1234.0)
        self.assertEqual(ff.parse_number("$ 0.52"), 0.52)
        for bad in ("—", "", "n/m"):
            with self.assertRaises(SeriesError):
                ff.parse_number(bad)

    def test_table_cell(self) -> None:
        self.assertEqual(ff.table_cell(HTML, 0, "Net revenue", 1)[:2], (13653.0, 0))
        self.assertEqual(ff.table_cell(HTML, None, "Operating income (loss)", 1)[:2], (-1234.0, 0))
        self.assertEqual(ff.parse_part("$15.0 - $16.0", "hi"), 16.0)
        self.assertEqual(ff.parse_number("$8.5 billion"), 8.5)
        with self.assertRaisesRegex(SeriesError, "0개"):
            ff.table_cell(HTML, 0, "Gross margin", 1)

    def test_filing_cli_offline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "raw").mkdir()
            (out / "raw" / ff.raw_name(URL, "htm")).write_bytes(HTML)
            spec = {"series_id": "TEST_REV_Q", "source": "시험 공시", "unit": "십억 달러",
                    "values": [{"date": "2026-09-30", "form": "8-K Ex.99.1", "number": "0000000001-26-000001",
                                "filed_on": "2026-10-29", "url": URL, "table": 0, "row": "Net revenue", "col": 1,
                                "raw_unit": "백만 달러"}]}
            sp = out / "spec.yaml"
            sp.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
            self.assertEqual(ff.main(["filing", str(sp), "--offline", "--out", str(out), "--retrieved-at", "2026-10-30"]), 0)
            r = load_series_file(out / "TEST_REV_Q.yaml")
            self.assertEqual(r.values, [(date(2026, 9, 30), 13.7)])
            self.assertEqual(r.filings[0].raw_value, 13653.0)
            self.assertTrue(r.filings[0].raw_md5)
            # 원문 없음 + offline = 오류(받지 않은 값을 만들지 않는다)
            (out / "raw" / ff.raw_name(URL, "htm")).unlink()
            self.assertEqual(ff.main(["filing", str(sp), "--offline", "--out", str(out)]), 2)

    def test_dart_without_key_stops(self) -> None:
        import os  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            spec = {"series_id": "TEST_OP_Q", "source": "시험", "unit": "조 원",
                    "values": [{"kind": "opendart", "date": "2026-09-30", "form": "분기보고서", "corp_code": "00000000",
                                "bsns_year": 2026, "reprt_code": "11014", "sj_div": "IS", "account_nm": "영업이익"}]}
            sp = out / "spec.yaml"
            sp.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
            old = os.environ.pop("DART_API_KEY", None)
            try:
                self.assertEqual(ff.main(["filing", str(sp), "--out", str(out)]), 3)
            finally:
                if old is not None:
                    os.environ["DART_API_KEY"] = old

    def test_price_offline_and_raw_check(self) -> None:
        days = [date(2026, 10, 27), date(2026, 10, 28), date(2026, 10, 29)]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "raw").mkdir()
            (out / "raw" / "TEST_PX_D.json").write_text(_chart_json(days, [10.0, 10.5, 9.75]), encoding="utf-8")
            self.assertEqual(ff.main(["price", "TEST_PX_D", "--ticker", "TEST", "--start", "2026-10-27", "--end", "2026-10-29",
                                      "--unit", "달러", "--source", "시험 시세", "--offline", "--out", str(out),
                                      "--retrieved-at", "2026-10-30"]), 0)
            r = load_series_file(out / "TEST_PX_D.yaml")
            self.assertEqual(r.values[-1], (date(2026, 10, 29), 9.75))
            (out / "TEST_PX_D.csv").write_text("date,value\n2026-10-27,10.0\n2026-10-28,10.5\n2026-10-29,9.5\n", encoding="utf-8")
            with self.assertRaisesRegex(SeriesError, "종가와 다르다"):
                load_series_file(out / "TEST_PX_D.yaml")

    def test_price_outlier_needs_citation(self) -> None:
        """[price-outlier] — 하루 변동 ≥ rules data.price_outlier_pct 는 보도 확인(cited) 필수(감독 점검 2026-10-30)."""
        d = {"series_id": "TEST_PX_D", "source": "시험 시세", "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/TEST",
             "retrieved_at": "2026-10-30", "transform": {"op": "chart_close", "formula": TR["chart_close"]}, "as_of": "2026-10",
             "unit": "달러", "frequency": "daily", "license": "private_only_market_data", "license_note": "시험",
             "values": [("2026-10-27", 100.0), ("2026-10-28", 112.0), ("2026-10-29", 111.0)]}
        with self.assertRaisesRegex(ValidationError, r"price-outlier.*2026-10-28 \+12.0%"):
            SeriesRecord.model_validate(d)
        cite = {"date": "2026-10-28", "outlet": "시험 매체", "pub_date": "2026-10-28", "url": "https://example.com/a"}
        SeriesRecord.model_validate({**d, "cited": [cite]})
        with self.assertRaisesRegex(ValidationError, "급변일에만"):
            SeriesRecord.model_validate({**d, "cited": [cite, {**cite, "date": "2026-10-29"}]})

    def test_daily_missing_breaks_outlier_pair(self) -> None:
        """급변일을 missing 으로 비우면 그 사이 변동은 그려지지 않으므로 [price-outlier] 가 재지 않는다(감독 지시 2026-10-30)."""
        d = {"series_id": "TEST_PX_D", "source": "시험 시세", "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/TEST",
             "retrieved_at": "2026-10-30", "transform": {"op": "chart_close", "formula": TR["chart_close"]}, "as_of": "2026-10",
             "unit": "달러", "frequency": "daily", "license": "private_only_market_data", "license_note": "시험",
             "values": [("2026-10-26", 100.0), ("2026-10-28", 112.0), ("2026-10-29", 111.0)]}
        with self.assertRaisesRegex(ValidationError, "price-outlier"):
            SeriesRecord.model_validate(d)
        r = SeriesRecord.model_validate({**d, "missing": [{"date": "2026-10-27", "note": "시험 — 급변일 보도 미확인"}]})
        self.assertEqual(r.missing_dates(), [date(2026, 10, 27)])
        with self.assertRaisesRegex(ValidationError, "거래일"):
            SeriesRecord.model_validate({**d, "values": [("2026-10-23", 100.0), ("2026-10-26", 101.0), ("2026-10-28", 102.0)],
                                         "missing": [{"date": "2026-10-25", "note": "일요일"}]})

    def test_chart_close_null_is_error(self) -> None:
        with self.assertRaisesRegex(SeriesError, "종가 없음"):
            chart_close(_chart_json([date(2026, 10, 28), date(2026, 10, 29)], [1.0, None]))


class SpacedUnitAndSegmentsTest(unittest.TestCase):
    """v7.4.0 T1 — 공백 있는 단위(십억 달러·조 원)의 화면 단위 판정, daily·quarterly 선은 missing 에서만 끊는다."""

    def test_unit_head(self) -> None:
        from engine.honesty import _first_token  # noqa: PLC0415

        self.assertEqual(_first_token("십억 달러"), "십억 달러")
        self.assertEqual(_first_token("조 원 (연결)"), "조 원")
        self.assertEqual(_first_token("% (전년 대비)"), "%")

    def test_segments_daily(self) -> None:
        from engine.layers.series import segments  # noqa: PLC0415

        v = [(date(2026, 10, 27), 1.0), (date(2026, 10, 28), 1.0), (date(2026, 10, 30), 1.0)]
        self.assertEqual(len(segments(v, [])), 1)                     # 휴장일(10-29 없음)은 끊지 않는다
        self.assertEqual(len(segments(v, [date(2026, 10, 29)])), 2)   # missing 이면 끊는다
        self.assertEqual(len(segments(v)), 3)                         # 월별 규칙(종전) — daily 에 쓰면 점마다 끊겼다


if __name__ == "__main__":
    unittest.main()

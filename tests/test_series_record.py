"""데이터 레코드 SeriesRecord·로더 (v4.3.0, docs/handoff/20 §5.1, back_and_forth D-0084 작업 1·9).

허용 목록(rules data) 밖 단위·라이선스·도메인·변환, 날짜 역순·빈 달, as_of > retrieved_at = 로드 오류(15 P6).
원자료(raw/)에 transform 을 다시 적용한 값이 csv 와 다르면 오류(값을 손으로 고치지 않았음을 증명).
"""

from __future__ import annotations

import copy
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml
from pydantic import ValidationError

from data.series import SeriesError, apply_transform, load_series_file, write_csv
from rules import load_rules
from schemas.data_models import SeriesRecord

TR = load_rules().data.transforms
BASE: dict = {
    "series_id": "TESTSER",
    "source": "FRED(세인트루이스 연은) · 원출처 시험",
    "source_url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TESTSER&cosd=2024-01-01",
    "retrieved_at": "2024-05-10",
    "transform": {"op": "raw", "formula": TR["raw"]},
    "as_of": "2024-04",
    "revision_note": None,
    "unit": "%",
    "frequency": "monthly",
    "license": "us_gov_public_domain",
    "license_note": "Public Domain: Citation Requested",
    "values": [("2024-01-01", 5.33), ("2024-02-01", 5.33), ("2024-03-01", 5.33), ("2024-04-01", 5.33)],
}


def rec(**over: object) -> dict:
    d = copy.deepcopy(BASE)
    d.update(over)
    return d


class SeriesRecordSchemaTest(unittest.TestCase):
    def test_minimal_passes(self) -> None:
        r = SeriesRecord.model_validate(rec())
        self.assertEqual((r.start, r.end, r.as_of_label()), (date(2024, 1, 1), date(2024, 4, 1), "2024년 4월 기준"))

    def test_unit_outside_rules_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "rules data.units"):
            SeriesRecord.model_validate(rec(unit="퍼센트"))

    def test_license_outside_rules_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "licenses_allowed"):
            SeriesRecord.model_validate(rec(license="proprietary"))

    def test_source_domain_outside_rules_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "sources_allowed"):
            SeriesRecord.model_validate(rec(source_url="https://example.com/x.csv"))

    def test_dates_must_increase(self) -> None:
        v = [("2024-02-01", 1.0), ("2024-01-01", 1.0), ("2024-03-01", 1.0), ("2024-04-01", 1.0)]
        with self.assertRaisesRegex(ValidationError, "증가하지 않는다"):
            SeriesRecord.model_validate(rec(values=v))

    def test_monthly_gap_rejected(self) -> None:
        v = [("2024-01-01", 1.0), ("2024-03-01", 1.0), ("2024-04-01", 1.0)]
        with self.assertRaisesRegex(ValidationError, "빈 달"):
            SeriesRecord.model_validate(rec(values=v))

    def test_declared_missing_month_passes(self) -> None:
        """D-0086 A — missing 에 적힌 빈 달만 허용(보간 없음)."""
        v = [("2024-01-01", 1.0), ("2024-03-01", 1.0), ("2024-04-01", 1.0)]
        r = SeriesRecord.model_validate(rec(values=v, missing=[{"date": "2024-02-01", "note": "미발표"}]))
        self.assertEqual(r.missing_dates(), [date(2024, 2, 1)])
        with self.assertRaisesRegex(ValidationError, "missing 날짜에 값이 있다"):
            SeriesRecord.model_validate(rec(missing=[{"date": "2024-02-01", "note": "미발표"}]))

    def test_as_of_after_retrieved_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "retrieved_at"):
            SeriesRecord.model_validate(rec(retrieved_at="2024-03-20"))

    def test_as_of_must_be_last_value_month(self) -> None:
        with self.assertRaisesRegex(ValidationError, "마지막 값의 달"):
            SeriesRecord.model_validate(rec(as_of="2024-03"))

    def test_transform_formula_must_match_rules(self) -> None:
        with self.assertRaisesRegex(ValidationError, "문구와 다르다"):
            SeriesRecord.model_validate(rec(transform={"op": "raw", "formula": "대충"}))
        with self.assertRaisesRegex(ValidationError, "data.transforms 에 없다"):
            SeriesRecord.model_validate(rec(transform={"op": "log", "formula": "x"}))

    def test_extra_field_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SeriesRecord.model_validate(rec(chart_type="bar"))


class SeriesLoaderTest(unittest.TestCase):
    def _write(self, d: Path, values: list, raw: list | None) -> Path:
        body = {k: v for k, v in rec().items() if k != "values"}
        yp = d / "TESTSER.yaml"
        yp.write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
        write_csv(d / "TESTSER.csv", [(date.fromisoformat(a), b) for a, b in values])
        if raw is not None:
            (d / "raw").mkdir()
            write_csv(d / "raw" / "TESTSER.csv", [(date.fromisoformat(a), b) for a, b in raw])
        return yp

    def test_roundtrip_with_raw(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            yp = self._write(Path(t), BASE["values"], BASE["values"])
            self.assertEqual(len(load_series_file(yp).values), 4)

    def test_edited_value_detected_against_raw(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            vals = list(BASE["values"])
            vals[2] = ("2024-03-01", 5.5)
            yp = self._write(Path(t), vals, BASE["values"])
            with self.assertRaisesRegex(SeriesError, "다시 적용한 값과 다르다"):
                load_series_file(yp)

    def test_raw_empty_must_match_missing(self) -> None:
        """원자료 빈 값 → yoy 는 t 와 t+12 가 빈 날짜(D-0086)."""
        raw = [(date(2023, m, 1), 100.0) for m in range(1, 13)] + [(date(2024, 1, 1), None), (date(2024, 2, 1), 102.0)]
        vals, miss = apply_transform("yoy_pct", raw, date(2024, 1, 1))
        self.assertEqual((vals, miss), ([(date(2024, 2, 1), 2.0)], [date(2024, 1, 1)]))
        vals, miss = apply_transform("raw", raw, date(2024, 1, 1))
        self.assertEqual(miss, [date(2024, 1, 1)])

    def test_yoy_transform(self) -> None:
        raw = [(date(2023, m, 1), 100.0) for m in range(1, 13)] + [(date(2024, 1, 1), 103.0), (date(2024, 2, 1), 101.5)]
        self.assertEqual(apply_transform("yoy_pct", raw, date(2024, 1, 1)), ([(date(2024, 1, 1), 3.0), (date(2024, 2, 1), 1.5)], []))
        with self.assertRaisesRegex(SeriesError, "12개월 전"):
            apply_transform("yoy_pct", raw[1:], date(2024, 1, 1))


class CommittedSeriesTest(unittest.TestCase):
    """저장소에 커밋된 레코드는 전부 로드된다(원자료 재적용 일치 포함)."""

    def test_committed_records_load(self) -> None:
        from data.series import series_dir  # noqa: PLC0415

        files = sorted(series_dir().glob("*.yaml"))
        for p in files:
            with self.subTest(p.name):
                r = load_series_file(p)
                self.assertIn(r.license, load_rules().data.licenses_allowed)
                raw = f"{r.series_id}.htm" if r.kind == "scatter" else f"{r.series_id}.csv"   # v4.4.0 scatter 원자료 = SEP HTML
                self.assertTrue((p.parent / "raw" / raw).exists(), "raw/ 원자료 필수(재현)")


if __name__ == "__main__":
    unittest.main()

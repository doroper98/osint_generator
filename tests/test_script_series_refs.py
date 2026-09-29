"""원고의 데이터 레코드 참조 `series:<id>`·수치 대조 린트 (v4.3.0, back_and_forth D-0088, docs/handoff/20 §9-4, D-0086 보정 2)."""

from __future__ import annotations

import unittest

from script.labels import compute_labels
from script.lint import lint
from script.schema import Script
from script.series_refs import check_series_sentence

FED = ["series:FEDFUNDS"]
CPI = ["series:CPIAUCSL"]


def script(text: str, date: str, sources: list[str]) -> Script:
    return Script.model_validate({"schema_version": 1, "title": "t", "subtitle": "s", "date": "2026.09.29",
                                  "scenes": [{"id": "a", "sentences": [{"date": date, "text": text, "emphasis": [], "sources": sources}]}]})


def kinds(sc: Script) -> list[str]:
    return [i.kind for i in lint(sc).errors if i.kind != "tts-symbol"]   # 발음 텍스트 없는 시험 문장(자막 = 발음)


class SeriesRefTest(unittest.TestCase):
    def test_series_ref_passes_source_check(self) -> None:
        self.assertEqual(kinds(script("2023년 8월, 금리 월평균은 5.33%였습니다.", "2023.08", FED)), [])

    def test_unknown_record_is_error(self) -> None:
        self.assertIn("source-unknown", kinds(script("2023년 8월 값입니다.", "2023.08", ["series:NOPE"])))

    def test_value_mismatch(self) -> None:
        self.assertIn("series-value-mismatch", kinds(script("2023년 8월, 금리 월평균은 5.4%였습니다.", "2023.08", FED)))
        self.assertEqual(check_series_sentence("5.3%", "2023.08", FED), [])
        self.assertTrue(check_series_sentence("5.4%", "2023.08", FED))

    def test_half_up_rounding_boundary(self) -> None:
        # CPI 2022-06 = 8.98 → 한 자리 9.0, 정수 9 / FEDFUNDS 2020-04 = 0.05 → 한 자리 0.1(half-up)
        self.assertEqual(check_series_sentence("9.0%", "2022.06", CPI), [])
        self.assertEqual(check_series_sentence("9%", "2022.06", CPI), [])
        self.assertEqual(check_series_sentence("0.1%", "2020.04", FED), [])
        self.assertTrue(check_series_sentence("0.0%", "2020.04", FED))

    def test_percent_point_difference(self) -> None:
        # FEDFUNDS 2022-12 4.10 − 2022-11 3.78 = 0.32
        self.assertEqual(check_series_sentence("0.32%p 올랐습니다", "2022.12", FED), [])
        self.assertTrue(check_series_sentence("0.5%p 올랐습니다", "2022.12", FED))
        # 두 날짜: 2023년 8월 5.33 − 2022년 3월 0.2 = 5.13
        self.assertEqual(check_series_sentence("2022년 3월에서 2023년 8월까지 5.13%p", "2023.08", FED), [])

    def test_missing_month_value_is_error(self) -> None:
        self.assertTrue(check_series_sentence("2025년 10월 물가는 3.0%였습니다.", "2025.10", CPI))
        self.assertEqual(check_series_sentence("2025년 10월 소비자물가 지표는 발표되지 않았습니다.", "2025.10", CPI), [])

    def test_two_refs_with_number_is_error(self) -> None:
        self.assertTrue(check_series_sentence("금리 3.63%, 물가 3.35%", "2026.08", FED + CPI))
        self.assertEqual(check_series_sentence("두 값은 공개 자료입니다.", "2026.08", FED + CPI), [])

    def test_labels_skip_series_refs(self) -> None:
        labels = compute_labels(script("2023년 8월, 5.33%였습니다.", "2023.08", FED), {})
        self.assertIsNone(labels.labels["a_0"].label)
        self.assertEqual(labels.labels["a_0"].claim_ids, [])


if __name__ == "__main__":
    unittest.main()

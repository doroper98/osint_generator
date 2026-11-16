"""예산 레코드 — source_kind document·frequency annual·budget_stage (v7.4.0, back_and_forth D-1003 §1·§2).

정부안/국회 확정/결산 구분은 값마다(doc_values.budget_stage). 원값·원단위를 다시 환산해 values 와 대조(P6).
시험 값은 실데이터가 아니다(픽스처).
"""

from __future__ import annotations

import unittest
from datetime import date

from rules import load_rules
from schemas.data_models import SeriesRecord


def rec(**kw: object) -> SeriesRecord:
    years = [2024, 2025, 2026, 2027]
    vals = [(date(y, 1, 1), v) for y, v in zip(years, [10.0, 11.0, 12.5, 14.0])]
    stages = ["settled", "settled", "enacted", "proposed"]
    raw = {"series_id": "FIXTURE_TOTAL_EXP", "source_kind": "document", "source": "시험 문서", "source_url": "https://www.mopb.go.kr/",
           "retrieved_at": "2026-11-02", "transform": {"op": "document", "formula": load_rules().data.transforms["document"]},
           "as_of": "2026-09", "issued_on": "2026-09-01", "unit": "조 원", "frequency": "annual", "license": "kogl_1", "license_note": "공공누리 제1유형",
           "source_file": {"path": "fixture.pdf", "sha1": "a" * 40, "title": "시험", "publisher": "시험 기관", "published_on": "2026-09-01"},
           "values": vals,
           "doc_values": [{"date": d.isoformat(), "page": 5, "locator": f"표 2 · {d.year}", "raw_value": v, "raw_unit": "조 원",
                           "budget_stage": st} for (d, v), st in zip(vals, stages)]}
    raw.update(kw)
    return SeriesRecord.model_validate(raw)


class FiscalRecordTest(unittest.TestCase):
    def test_document_annual_ok(self) -> None:
        r = rec()
        self.assertEqual([d.budget_stage for d in r.doc_values], ["settled", "settled", "enacted", "proposed"])

    def test_value_must_match_raw(self) -> None:
        r = rec()
        dv = [d.model_dump(mode="json") for d in r.doc_values]
        dv[3]["raw_value"] = 14.5
        with self.assertRaisesRegex(ValueError, "P6"):
            rec(doc_values=dv)

    def test_raw_unit_scaled(self) -> None:
        r = rec()
        dv = [d.model_dump(mode="json") for d in r.doc_values]
        dv[0].update(raw_value=100000.0, raw_unit="억 원")   # 10만 억 원 = 10.0 조 원
        self.assertEqual(rec(doc_values=dv).values[0][1], 10.0)

    def test_annual_dates(self) -> None:
        dec = [(date(2024, 12, 31), 1.0), (date(2025, 12, 31), 2.0)]
        with self.assertRaisesRegex(ValueError, "1월 1일"):
            rec(values=dec, doc_values=[{"date": d.isoformat(), "page": 1, "locator": "x", "raw_value": v, "raw_unit": "조 원"} for d, v in dec])
        with self.assertRaisesRegex(ValueError, "빈 해"):
            r = rec()
            rec(values=[r.values[0], r.values[2]], doc_values=[r.doc_values[0].model_dump(mode="json"), r.doc_values[2].model_dump(mode="json")])

    def test_document_needs_source_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_file"):
            rec(source_file=None)
        with self.assertRaisesRegex(ValueError, "document 레코드만"):
            SeriesRecord.model_validate({**rec().model_dump(mode="json"), "source_kind": "fetched"})


class ProposedTailTest(unittest.TestCase):
    """시간축 선 — 정부안 값으로 가는 조각은 점선, 끝값 라벨 꼬리 " · 정부안"(engine.layers.series)."""

    def test_proposed_from_and_tag(self) -> None:
        from engine.layers.series import budget_stage_of, proposed_from, proposed_tag  # noqa: PLC0415

        r = rec()
        ds = [d for d, _ in r.values]
        self.assertEqual(proposed_from(r, ds), 3)
        self.assertEqual(budget_stage_of(r, ds[2]), "enacted")
        self.assertEqual(proposed_tag(r, ds[3]), " · 정부안")
        self.assertEqual(proposed_tag(r, ds[2]), "")
        self.assertEqual(proposed_from(r, ds[:3]), 3)


if __name__ == "__main__":
    unittest.main()

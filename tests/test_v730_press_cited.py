"""v7.3.0 사용자 결정 D232 U2·U4 — 보도 인용 시리즈(press_cited)·dual_line 빈 달 끊기·위성 인셋 밀도·인셋 라이선스(U1·D234)."""

from __future__ import annotations

import types
import unittest
from datetime import date

from engine.events import PanelDualLine
from engine.media_plan import density_report
from schemas.data_models import SeriesRecord
from schemas.media_models import MediaAsset


def _rec(**kw: object) -> dict:
    r = dict(series_id="RU_TEST", source="IEA·블룸버그 보도 인용", source_url="https://www.iea.org/reports/oil-market-report", retrieved_at="2026-10-17",
             transform={"op": "press_cited", "formula": "보도 인용값(매체·날짜)"}, as_of="2026-07", unit="mb/d", frequency="monthly",
             license="press_cited", license_note="보도 인용값(사실) — 매체·날짜 표기", source_kind="press_cited",
             missing=[{"date": "2026-05-01", "note": "추정치 없음"}],
             values=[(date(2026, 3, 1), 5.1), (date(2026, 4, 1), 4.7), (date(2026, 6, 1), 3.8), (date(2026, 7, 1), 3.6)],
             cited=[{"date": f"2026-0{m}-01", "outlet": "IEA", "pub_date": "2026-08-01", "url": "https://www.iea.org/x"} for m in (3, 4, 6, 7)])
    r.update(kw)
    return r


class PressCitedRecordTest(unittest.TestCase):
    def test_valid(self) -> None:
        SeriesRecord.model_validate(_rec())

    def test_each_value_cited(self) -> None:
        with self.assertRaisesRegex(ValueError, "cited"):
            SeriesRecord.model_validate(_rec(cited=_rec()["cited"][:3]))

    def test_gap_must_be_listed(self) -> None:
        """보간 금지 — 빈 달은 missing 에 적힌 것만."""
        with self.assertRaisesRegex(ValueError, "missing"):
            SeriesRecord.model_validate(_rec(missing=[]))

    def test_fetched_cannot_claim_press(self) -> None:
        with self.assertRaises(ValueError):
            SeriesRecord.model_validate(_rec(source_kind="fetched"))


class DualLineGapTest(unittest.TestCase):
    def _panel(self, values: list) -> dict:
        return dict(type="panel", kind="dual_line", t0=0, t1=8, title="정제 처리량", provenance={"verification": "verified", "sources": ["IEA"]},
                    y_min=3, y_max=6, y_step=1, unit="mb/d", x_labels=["3월", "4월", "5월", "6월", "7월"],
                    series=[{"label": "러시아", "col": "ru", "values": values, "decimals": 1, "open_idx": []}])

    def test_null_allowed(self) -> None:
        PanelDualLine.model_validate(self._panel([5.1, 4.7, None, 3.8, 3.6]))

    def test_draw_breaks_line(self) -> None:
        """빈 달에서 선이 끊긴다 — 구간 [3월,4월]·[6월,7월] 두 개(5월을 잇지 않는다)."""
        from engine.panels.dual_line import present_runs  # noqa: PLC0415

        self.assertEqual(present_runs([5.1, 4.7, None, 3.8, 3.6]), [[0, 1], [3, 4]])
        self.assertEqual(present_runs([5.1, None, 4.7, None, 3.6]), [])


class InsetDensityTest(unittest.TestCase):
    def test_gap_warning(self) -> None:
        tb = types.SimpleNamespace(scenes=["a"], SC=lambda s: 0.0)
        ev = [dict(type="flight", t0=t, t1=t + 8, inset={"mid": m}) for t, m in ((10, "x"), (13, "y"))]
        w = density_report(ev, tb, 300.0)["warnings"]
        self.assertTrue(any(s.startswith("[inset-density]") for s in w), w)


class InsetLicenseTest(unittest.TestCase):
    def _a(self, **kw: object) -> dict:
        a = dict(kind="inset", title="HLS 2026-10-07 Ryazan", license="NASA GIBS (public domain)", author="NASA", credit_author="NASA GIBS/HLS",
                 date="2026-10-07", url="https://gibs.earthdata.nasa.gov/", caption="랴잔 정유소", file_note="위성 · 2026. 10", depicts=["랴잔 정유소"],
                 is_file_photo=False, verified_by={"by": "t", "on": "2026-10-17", "casualty_free": True, "relevance": "x"},
                 rights_status="rights_clear", retrieved_at="2026-10-17", tool={"name": "gibs"}, source_hash="0" * 32, file="inset_ryazan.png")
        a.update(kw)
        return a

    def test_allowed(self) -> None:
        MediaAsset.model_validate(self._a())

    def test_not_in_list(self) -> None:
        with self.assertRaisesRegex(ValueError, "허용 목록"):
            MediaAsset.model_validate(self._a(license="Google Maps"))

    def test_private_only_scope(self) -> None:
        lic = "Esri World Imagery (Maxar et al.) — 비공개 시청 한정, 사용자 결정 D234"
        with self.assertRaisesRegex(ValueError, "private_only"):
            MediaAsset.model_validate(self._a(license=lic))
        MediaAsset.model_validate(self._a(license=lic, scope="private_only"))
        with self.assertRaisesRegex(ValueError, "scope"):
            MediaAsset.model_validate(self._a(kind="photo", scope="private_only"))


if __name__ == "__main__":
    unittest.main()

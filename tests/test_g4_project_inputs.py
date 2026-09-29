"""G4 실증 입력·검사 보강 (v4.4.0, back_and_forth D-0090 작업 4·8, D-0091).

- 글리프 검사: 실제로 그린 글꼴에 없는 글자 = hard(카드 큰 숫자 '−' 두부 사고).
- 뱃지: 시간축 앵커 date·lane(배치 슬롯이 돌려주는 값).
- statement_diff 문구 = intake 원문(주문 있는 프로젝트).
- 연출 입력: 주문 프로젝트는 자기 미디어만·원문 문서 블록·scatter 레코드 요약.
- Flickr 사진 라이선스를 페이지에서 코드가 읽는다(권리 불확실 = 받지 않음).
- provenance: 주문의 사용자 결정 상태·새 요소 승인 상태.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import cairo
import yaml
from pydantic import ValidationError

from engine import typography
from engine.events import BadgeEvent
from tests.test_genre_prompts import ORDER, write_order

REPO = Path(__file__).resolve().parent.parent


class GlyphPerFontTest(unittest.TestCase):
    def test_missing_in_drawn_font_is_logged(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10))
        typography.GLYPH_MISS = []
        try:
            typography.text(ctx, "약 −630", 1, 5, 20, "disp")
            typography.text(ctx, "약 -630", 1, 5, 20, "disp")
        finally:
            miss, typography.GLYPH_MISS = typography.GLYPH_MISS, None
        self.assertEqual([(n, c) for n, c, _ in miss], [("disp", "−")])

    def test_check_glyphs_reports_logged_miss(self) -> None:
        from engine.checks import check_glyphs  # noqa: PLC0415

        P = SimpleNamespace(plan=SimpleNamespace(sentences=[], title="t", subtitle="s", date="2026.09.29"),  # noqa: N806
                            events=[], R=SimpleNamespace(cache={"glyph_miss": [("t=1.00", "disp", "−", "약 −630")] * 2}))
        out = check_glyphs(P)
        self.assertEqual(len(out), 1)
        self.assertIn("글꼴 disp", out[0])


class BadgeAnchorTest(unittest.TestCase):
    BASE = {"type": "badge", "t0": 0.0, "t1": 5.0, "kind": "person", "pid": "warsh", "flag": "us"}

    def test_timeline_or_map_pair(self) -> None:
        BadgeEvent.model_validate({**self.BASE, "date": "2026-09-16", "lane": "events"})
        BadgeEvent.model_validate({**self.BASE, "lon": 1.0, "lat": 2.0})
        for bad in ({}, {"date": "2026-09-16"}, {"lon": 1.0, "lat": 2.0, "date": "2026-09-16", "lane": "events"},
                    {"date": "2026.09.16", "lane": "events"}):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                BadgeEvent.model_validate({**self.BASE, **bad})

    def test_map_badge_dict_unchanged(self) -> None:
        from engine.registry import validate_events  # noqa: PLC0415

        e = validate_events([{**self.BASE, "lon": 1.0, "lat": 2.0}])[0]
        self.assertNotIn("date", e)
        self.assertNotIn("lane", e)


class QuoteCheckTest(unittest.TestCase):
    def _proj(self, td: str, order: bool) -> Path:
        pdir = Path(td)
        (pdir / "intake" / "bodies").mkdir(parents=True)
        (pdir / "intake" / "bodies" / "src_doc_0001.txt").write_text(
            "Inflation remains elevated.   Today's policy action will support a timelier return to the Committee's 2 percent goal.",
            encoding="utf-8")
        if order:
            write_order(pdir)
        return pdir

    def test_quotes_must_be_in_bodies(self) -> None:
        from engine.project import ProjectError, _check_quotes  # noqa: PLC0415

        ok = {"type": "primitive", "id": "statement_diff", "before": "Inflation remains elevated.",
              "after": "Today's policy action will support a timelier return"}
        bad = {**ok, "after": "Today's policy action will surely support a return"}
        with tempfile.TemporaryDirectory() as td:
            pdir = self._proj(td, order=True)
            _check_quotes(pdir, [ok])
            with self.assertRaises(ProjectError):
                _check_quotes(pdir, [bad])
        with tempfile.TemporaryDirectory() as td:
            _check_quotes(self._proj(td, order=False), [bad])   # 주문 없는 프로젝트(예시 문구) = 대상 아님


class DirectorInputsTest(unittest.TestCase):
    def test_scatter_summary_and_documents(self) -> None:
        from workers.direction_io import documents_text, series_records_text  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td)
            write_order(pdir, data={"series": ["SEP_20260916"], "documents": ["https://example.org/s1"]})
            out = series_records_text(pdir)
            self.assertIn("scatter(dot_plot 프리미티브 record 로만)", out)
            self.assertIn("2026 18명 중앙값 4.125", out)
            self.assertEqual(documents_text(pdir), "")   # 소스 없음
            (pdir / "intake" / "bodies").mkdir(parents=True)
            (pdir / "intake" / "sources.json").write_text(json.dumps({"schema_version": 1, "sources": [{
                "id": "src_doc_0001", "url": "https://example.org/s1", "retrieved_at": "2026-09-29", "lang": "en", "type": "document",
                "issuer": "연준 FOMC", "title": "성명 2026.9.16", "published_at": "2026-09-16", "key_facts": ["x"]}]}), encoding="utf-8")
            (pdir / "intake" / "bodies" / "src_doc_0001.txt").write_text("Inflation   remains\nelevated.", encoding="utf-8")
            self.assertIn("src_doc_0001 · 2026-09-16 · Inflation remains elevated.", documents_text(pdir))

    def test_media_list_is_project_own_only_with_order(self) -> None:
        from workers.direction_io import media_text  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td)
            full = media_text(pdir)
            self.assertIn("hormuz_transit", full)   # 주문 없음 = 기존 그대로(레지스트리 전부)
            write_order(pdir)
            self.assertNotIn("hormuz_transit", media_text(pdir))


class FlickrLicenseTest(unittest.TestCase):
    def test_license_read_for_that_photo(self) -> None:
        from tools.media_fetch import MediaFetchError, flickr_license  # noqa: PLC0415

        page = ('"license":4,"sizes":{"data":{"sq":{"data":{"displayUrl":"//live.staticflickr.com/65535/111_aa_s.jpg"'
                '"license":10,"sizes":{"data":{"sq":{"data":{"displayUrl":"//live.staticflickr.com/65535/222_bb_s.jpg"')
        self.assertEqual(flickr_license(page, "222"), "10")
        self.assertEqual(flickr_license(page, "111"), "4")
        with self.assertRaises(MediaFetchError):
            flickr_license(page, "333")

    def test_rules_allow_only_public_domain_like(self) -> None:
        from rules import load_rules  # noqa: PLC0415

        self.assertEqual(set(load_rules().media.flickr.licenses_allowed), {"8", "9", "10"})

    def test_registry_photos_are_pdm(self) -> None:
        from engine.media_registry import load_media_registry  # noqa: PLC0415

        reg = load_media_registry()
        for mid in ("fed_presser_0916", "fed_presser_0916_b", "fed_presser_0729"):
            self.assertEqual(reg[mid].license, "Public Domain Mark")
            self.assertTrue(reg[mid].url.startswith("https://www.flickr.com/photos/federalreserve/"))


class OrderFileTest(unittest.TestCase):
    def test_project_order_loads(self) -> None:
        from genres.load import load_order  # noqa: PLC0415

        o = load_order(REPO / "projects" / "fed_policy_2026")
        self.assertIsNotNone(o)
        self.assertEqual(o.genre, "macro_monetary")
        self.assertEqual(o.decisions["elements_approval"].value, "pending")
        self.assertEqual(o.decisions["macro_monetary_status"].value, "proposed")
        self.assertEqual({d.by for d in o.decisions.values()}, {"default"})   # 사용자 답 전 = 지침 기본값

    def test_order_fixture_is_template_shape(self) -> None:
        self.assertEqual(yaml.safe_load(yaml.safe_dump(ORDER))["genre"], "macro_monetary")


if __name__ == "__main__":
    unittest.main()

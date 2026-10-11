"""통신사 사진 "보도 인용"(B) — v5.21.0, back_and_forth D-0177(사용자 결정 D172).

예외 없는 restricted 사진 거부 · 예외 사진은 그 기사 카드의 프레스 칸에서만(독립 비트·배경·다른 기사 = 오류) ·
게이트 ① 표(검색 기록 0건 없으면 오류, 통과 후보 있으면 A 먼저) · 크레딧 3곳(카드 줄·엔딩·설명란) ·
provenance rights.exceptions·mux `[rights-exceptions]` 경고 · 등록 도구 기록 필드.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cairo
import yaml

from engine.credits import (Credits, RightsError, check_credits, description_press_photos, required_refs, rights_exception,
                            rights_exceptions)
from engine.layers import article as ART
from engine.layers.backdrop import validate_backdrop
from engine.layers.media import validate_media
from engine.mux import rights_exception_warning
from schemas.emblem_models import USER_EXCEPTIONS, press_exception_ok
from schemas.media_models import MediaRegistryFile
from script import media_table as MT
from tests.test_p1_media_plan import _Proj
from tools import article_register as AR

ART_URL = "https://example.com/news/riyadh-airport"
VERIFY = {"by": "test", "on": "2026-10-11", "casualty_free": True, "relevance": "리야드 공항"}


def _article() -> dict:
    return {"kind": "article", "title": "Arab News 2026-10-09 — Airport hit", "license": AR.LICENSE, "author": "Arab News",
            "credit_author": "Arab News", "date": "2026-10-09", "url": ART_URL, "caption": "Arab News", "file_note": "2026. 10. 09",
            "depicts": ["공항"], "is_file_photo": False, "verified_by": VERIFY, "rights_status": "rights_clear",
            "retrieved_at": "2026-10-11", "tool": {"name": "article_typeset"}, "headline": "리야드 공항 피격", "sub": "사우디 발표",
            "note": "헤드라인 번역 · 원문 영어", "headline_original": "Airport hit"}


def _press(**over: object) -> dict:
    _, e, _ = AR.press_photo_entry({"art_a": _article()}, ART_URL, "Reuters", b"jpegbytes", "https://img.example.com/p.jpg", ".jpg",
                                   "사용자 라운드", "리야드 공항 피격 현장", True, on="2026-10-11T00:00:00+00:00")
    return {**e, **over}


def _registry(**press_over: object) -> dict:
    other = {**_article(), "url": "https://example.com/other", "title": "other"}
    doc = {"schema_version": 1, "assets": {"art_a": _article(), "art_b": other, "art_a_press": _press(**press_over)}}
    return MediaRegistryFile.model_validate(doc).assets


class ModelTest(unittest.TestCase):
    def test_category_exception_registered(self) -> None:
        self.assertEqual(USER_EXCEPTIONS["U20261011"], frozenset({"press_quote"}))
        self.assertTrue(press_exception_ok("U20261011"))
        self.assertFalse(press_exception_ok("U20261010"))   # 인물 예외는 사진 범주가 아니다
        self.assertFalse(press_exception_ok(None))

    def test_press_record_fields_required(self) -> None:
        reg = _registry()
        p = reg["art_a_press"]
        self.assertEqual((p.rights_status, p.user_exception, p.press_of, p.agency), ("restricted", "U20261011", "art_a", "Reuters"))
        for bad in ({"user_exception": "U20261010"}, {"rights_status": "rights_clear"}, {"agency": None}, {"photo_url": None},
                    {"exception": "보도 인용"}, {"kind": "video"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                _registry(**bad)
        with self.assertRaises(ValueError):   # 기사가 아닌 곳을 가리키는 press_of
            _registry(press_of="nope")
        doc = {"schema_version": 1, "assets": {"x": {**_press(), "press_of": None}}}
        with self.assertRaises(ValueError):   # press_of 없는 사진의 사용자 예외 = 오류(미디어 예외는 보도 인용뿐)
            MediaRegistryFile.model_validate(doc)


class RenderGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = _registry()

    def test_restricted_photo_without_exception_refused(self) -> None:
        doc = {"schema_version": 1, "assets": {"art_a": _article(), "ph": {**_press(), "press_of": None, "agency": None,
                                                                           "user_exception": None, "exception": None}}}
        reg = MediaRegistryFile.model_validate(doc).assets
        with self.assertRaises(RightsError):
            ART.validate_press({"type": "article", "mid": "art_a", "press": "ph"}, reg)
        with self.assertRaises(RightsError):
            validate_media({"type": "photo", "mid": "ph", "t0": 1.0}, reg)

    def test_press_only_in_its_article_card(self) -> None:
        a = ART.validate_press({"type": "article", "mid": "art_a", "press": "art_a_press"}, self.reg)
        self.assertEqual(a.agency, "Reuters")
        with self.assertRaisesRegex(RightsError, "art_a 의 카드에서만"):
            ART.validate_press({"type": "article", "mid": "art_b", "press": "art_a_press"}, self.reg)
        with self.assertRaisesRegex(RightsError, "독립 사진·배경 금지"):
            validate_media({"type": "photo", "mid": "art_a_press", "t0": 1.0}, self.reg)
        with self.assertRaisesRegex(RightsError, "독립 사진·배경 금지"):
            validate_backdrop({"type": "backdrop", "img": "art_a_press", "t0": 1.0}, self.reg)

    def test_card_credit_line_only_for_b(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        with mock.patch.object(ART, "cached_registry", return_value=self.reg):
            b = ART.article_layout(ctx, {"type": "article", "mid": "art_a", "press": "art_a_press", "t0": 0.0, "t1": 3.0})
            n = ART.article_layout(ctx, {"type": "article", "mid": "art_a", "t0": 0.0, "t1": 3.0})
            usage = ART.article_usage([{"type": "article", "mid": "art_a", "press": "art_a_press", "t0": 0.0, "t1": 3.0}])
        self.assertEqual(b.credit, "사진: Reuters via Arab News")
        self.assertGreater(b.credit_base, b.source_base)
        self.assertGreater(b.box[3], n.box[3])
        self.assertIsNone(n.credit)   # B 사진 없는 카드(A 공식 사진·블러 폴백)는 줄 없음 — 호르무즈 무변화
        self.assertEqual(usage[0]["press_quote"], "사진: Reuters via Arab News")


class CreditsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.media = {k: v.model_dump() for k, v in _registry().items()}
        self.rights = {"fonts": {"f": {"name": "F", "license": "OFL", "rights_status": "rights_clear"}}}
        ev = [{"type": "article", "mid": "art_a", "press": "art_a_press", "t0": 0.0, "t1": 3.0}]
        self.req = required_refs(ev, self.rights, lambda _x: None, set(), uses_map=False) - {"map.?", "narration.?"}
        self.desc = ["F · OFL"]

    def _credits(self, with_photo: bool) -> Credits:
        items = [{"main": "Arab News", "license": "기사 조판", "rights": ["media.art_a"]}]
        if with_photo:
            items.append({"main": "사진: Reuters via Arab News", "license": "통신사 저작물 — 인용(Reuters)", "rights": ["media.art_a_press"]})
        return Credits.model_validate({"sections": [{"title": "보도", "column": 0, "items": items}]})

    def test_end_card_row_required_and_exception_passes(self) -> None:
        self.assertIn("media.art_a_press", self.req)
        check_credits(self._credits(True), self.rights, self.media, self.req, description=self.desc)
        with self.assertRaisesRegex(RightsError, "엔딩 크레딧 누락: media.art_a_press"):
            check_credits(self._credits(False), self.rights, self.media, self.req, description=self.desc)
        bad = copy.deepcopy(self.media)
        bad["art_a_press"]["user_exception"] = "U20261010"
        self.assertIsNone(rights_exception("media.art_a_press", bad["art_a_press"]))
        with self.assertRaisesRegex(RightsError, "권리 미확인 자산"):
            check_credits(self._credits(True), self.rights, bad, self.req, description=self.desc)

    def test_description_provenance_and_mux_warning(self) -> None:
        lines = description_press_photos(self.req, self.media)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("사진: Reuters via Arab News — https://img.example.com/p.jpg (보도 인용 · U20261011"))
        self.assertIn("공개 배포 전 재확인", lines[0])
        exc = rights_exceptions(self.req, self.rights, self.media)
        self.assertEqual([(x["ref"], x["user_exception"]) for x in exc], [("media.art_a_press", "U20261011")])
        self.assertEqual(rights_exceptions(self.req, self.rights), [])   # 미디어를 넘기지 않으면 사진은 안 보인다(mux 는 넘긴다)
        w = rights_exception_warning({"rights": {"exceptions": exc}})
        self.assertEqual(w, "[rights-exceptions] 공개 배포 전 재확인 1건: media.art_a_press(U20261011)")
        self.assertIsNone(rights_exception_warning({}))


class GateTableTest(_Proj):
    def setUp(self) -> None:
        super().setUp()
        self.cands = MT.article_candidates(self.proj)
        self.sid = "review_0"
        self.assertIn(self.sid, self.cands)

    def _search(self, sid: str, passed: int) -> None:
        (self.proj / MT.SEARCH_FILE).write_text(json.dumps({"schema_version": 1, "searches": [
            {"sid": sid, "query": "riyadh airport", "pool": "us_dod_pd", "on": "2026-10-11", "found": 3, "passed": passed}]}),
            encoding="utf-8")

    def _errs(self) -> list[str]:
        return [e for e in MT.media_table(self.proj).errors if e.startswith("[press-quote]")]

    def test_b_needs_zero_pass_search_log(self) -> None:
        self._notes({"sentences": {self.sid: {"press_quote": "Reuters 사진(Arab News 기사)"}}})
        self.assertRegex(self._errs()[0], "검색 기록이 없다")
        self._search(self.sid, 2)
        self.assertRegex(self._errs()[0], "권리 통과 후보 2건이 있다 — A 먼저")
        self._search(self.sid, 0)
        self.assertEqual(self._errs(), [])
        t = MT.media_table(self.proj)
        line = next(x for x in MT.table_lines(t) if x.strip().startswith(self.sid))
        self.assertIn("보도 인용(B)", line)
        self.assertIn("B: Reuters 사진(Arab News 기사) · 근거 검색 us_dod_pd 'riyadh airport' 3건·통과 0", line)

    def test_b_only_on_article_candidate(self) -> None:
        non = next(sid for sid, _ in MT.sentence_ids(MT._script(self.proj)) if sid not in self.cands)
        self._search(non, 0)
        self._notes({"sentences": {non: {"press_quote": "Reuters 사진"}}})
        self.assertRegex(self._errs()[0], "기사 카드 후보가 아니다")


class SearchPassCountTest(unittest.TestCase):
    def test_documents_not_counted_and_relog_replaces(self) -> None:
        """B 조건 '권리 통과 0' 의 분모 — 문서(pdf)·도식(svg)은 사진 후보가 아니다. 같은 문장·검색어·풀 재검색은 최신이 대체."""
        from tools.media_fetch import search_pools  # noqa: PLC0415

        def fake(q: str, limit: int) -> list[dict]:
            return [{"title": "File:R.pdf", "lic": "Public domain", "restrictions": [], "allowed": True, "page": "r", "mime": "application/pdf"},
                    {"title": "File:M.svg", "lic": "Public domain", "restrictions": [], "allowed": True, "page": "m", "mime": "image/svg+xml"}]

        def photo(q: str, limit: int) -> list[dict]:
            return [{"title": "File:P.jpg", "lic": "Public domain", "restrictions": [], "allowed": True, "page": "p", "mime": "image/jpeg"}]

        with tempfile.TemporaryDirectory() as d:
            search_pools("airport", 5, log=Path(d), sid="s_0", searcher=photo)
            search_pools("airport", 5, log=Path(d), sid="s_0", searcher=fake)
            log = json.loads((Path(d) / MT.SEARCH_FILE).read_text(encoding="utf-8"))["searches"]
        self.assertEqual([(s["pool"], s["found"], s["passed"]) for s in log], [("us_dod_pd", 2, 0), ("commons_cc", 2, 0)])
        self.assertEqual(log[1]["rejected"], ["문서·도식(application/pdf)", "문서·도식(image/svg+xml)"])


class RegisterToolTest(unittest.TestCase):
    def test_entry_fields_and_og_image(self) -> None:
        mid, e, name = AR.press_photo_entry({"art_a": _article()}, ART_URL, "AFP", b"abc", "https://img/x.jpg", ".jpg", "사용자", "현장",
                                            True, photographer="Jane Doe", on="2026-10-11T01:02:03+00:00")
        self.assertEqual((mid, name), ("art_a_press", "press_art_a.jpg"))
        self.assertEqual({k: e[k] for k in ("rights_status", "user_exception", "license", "author", "credit_author", "press_of",
                                             "photo_url", "source_hash", "retrieved_at")},
                         {"rights_status": "restricted", "user_exception": "U20261011", "license": "통신사 저작물 — 인용(AFP)",
                          "author": "Jane Doe", "credit_author": "AFP", "press_of": "art_a", "photo_url": "https://img/x.jpg",
                          "source_hash": "900150983cd24fb0d6963f7d28e17f72", "retrieved_at": "2026-10-11T01:02:03+00:00"})
        self.assertEqual(e["verified_by"]["relevance"], "현장")
        with self.assertRaises(ValueError):   # 사상자 확인 없이 등록 안 됨(다른 사진과 같은 규칙)
            MediaRegistryFile.model_validate({"schema_version": 1, "assets": {"art_a": _article(), mid: {
                **e, "verified_by": {**e["verified_by"], "casualty_free": False}}}})
        with self.assertRaisesRegex(ValueError, "url 의 기사"):
            AR.press_photo_entry({"art_a": _article()}, "https://nope", "AFP", b"", "u", ".jpg", "a", "b", True)
        html = '<head><meta property="og:image" content="https://cdn.example.com/a.jpg?w=1&amp;h=2"></head>'
        self.assertEqual(AR.og_image(html), "https://cdn.example.com/a.jpg?w=1&h=2")
        with self.assertRaises(ValueError):
            AR.og_image("<head></head>")

    def test_write_mode_writes_registry_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            reg_p, proj, photo = Path(d) / "reg.json", Path(d) / "p", Path(d) / "x.png"
            proj.mkdir()
            photo.write_bytes(b"png")
            reg_p.write_text(json.dumps({"schema_version": 1, "assets": {"art_a": _article()}}), encoding="utf-8")
            with mock.patch("engine.media_registry.registry_path", return_value=reg_p):
                rc = AR.main([str(proj), "--press-photo", ART_URL, "--agency", "Reuters", "--file", str(photo), "--photo-url",
                              "https://img/x.png", "--verified-by", "사용자", "--relevance", "현장", "--casualty-free", "--write"])
            self.assertEqual(rc, 0)
            self.assertEqual((proj / "media" / "press_art_a.png").read_bytes(), b"png")
            got = json.loads(reg_p.read_text(encoding="utf-8"))["assets"]["art_a_press"]
            self.assertEqual((got["file"], got["press_of"]), ("press_art_a.png", "art_a"))


class HormuzUnchangedTest(unittest.TestCase):
    def test_hormuz_article_cards_have_no_credit_line(self) -> None:
        """호르무즈 기사 카드(15_review_0·19_debate_0 골든)는 B 사진이 없어 크레딧 줄을 그리지 않는다 — 출력 변화 0."""
        d = yaml.safe_load((Path(__file__).resolve().parent.parent / "projects" / "hormuz_korea" / "direction.yaml").read_text(encoding="utf-8"))
        arts = [e for e in d["events"] if e.get("type") == "article"]
        self.assertTrue(arts)
        for e in arts:
            self.assertIsNone(ART.press_credit_text(e, "x"))


if __name__ == "__main__":
    unittest.main()

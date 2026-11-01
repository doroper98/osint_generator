"""전쟁사 W2(v7.4.0, back_and_forth D-0600 §2·§4) — 규칙·장르 프로필·작품 레코드·판정 함수."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from pydantic import ValidationError

from schemas.data_models import ForceFigure, ForceFiguresFile
from schemas.era_date import parse_era_date
from schemas.media_models import MediaAsset
from schemas.war_history import (ToponymyEntry, ToponymyFile, asset_layer, casualty_unsourced, era_of, evidence_missing,
                                 period_art_label, period_art_label_missing, probable_caption, symbol_set_mixed, video_era)


def art(**kw: object) -> dict:
    base = {
        "kind": "period_art", "title": "File:Carthaginian shekel elephant.jpg", "license": "CC BY 3.0", "author": "Classical Numismatic Group",
        "credit_author": "CNG", "date": "2010-01-01", "url": "https://commons.wikimedia.org/wiki/File:x.jpg",
        "caption": "코끼리를 새긴 카르타고 은화", "file_note": "은화 · 기원전 3세기", "depicts": ["코끼리", "카르타고 은화"],
        "is_file_photo": False, "verified_by": {"by": "t", "on": "2026-11-01", "casualty_free": True, "relevance": "t"},
        "rights_status": "rights_clear", "retrieved_at": "2026-11-01", "tool": {"name": "media_fetch.photo"},
        "source_hash": "0" * 32, "file": "x.jpg", "created": "c.-220", "work_kind": "coin", "holder": "개인 소장(CNG 경매)",
        "art_history": "바르카 가문이 히스파니아에서 찍은 은화로, 전투 코끼리를 권력의 상징으로 새겼다.",
        "art_history_source": "CNG 경매 해설",
    }
    base.update(kw)
    return base


class RecordTest(unittest.TestCase):
    def test_period_art_record(self) -> None:
        a = MediaAsset.model_validate(art())
        self.assertEqual(a.created.precision, "circa")
        self.assertEqual(asset_layer(a), "period_art")

    def test_period_art_required_fields(self) -> None:
        for f in ("created", "work_kind", "holder", "art_history", "art_history_source"):
            with self.assertRaises(ValidationError, msg=f):
                MediaAsset.model_validate(art(**{f: None}))

    def test_license_cc_by_sa_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            MediaAsset.model_validate(art(license="CC BY-SA 4.0"))

    def test_document_needs_id(self) -> None:
        doc = art(kind="document", work_kind="document", art_history=None, art_history_source=None)
        with self.assertRaises(ValidationError):
            MediaAsset.model_validate(doc)
        self.assertEqual(asset_layer(MediaAsset.model_validate({**doc, "archive_id": "UN S/RES/82"})), "document")

    def test_site_photo_layer(self) -> None:
        p = art(kind="photo", created=None, work_kind=None, holder=None, art_history=None, art_history_source=None,
                site_report="Cannae 발굴 보고(출처)")
        self.assertEqual(asset_layer(MediaAsset.model_validate(p)), "site")


class LabelTest(unittest.TestCase):
    def test_contemporary_and_later(self) -> None:
        ev = parse_era_date("-216.08.02")
        self.assertEqual(period_art_label(parse_era_date("c.-220"), ev), "당대 묘사")
        self.assertEqual(period_art_label(parse_era_date("1773"), ev), "후대의 묘사(1773)")
        self.assertEqual(period_art_label(parse_era_date("-50"), ev), "후대의 묘사(기원전 50년)")
        self.assertIsNone(period_art_label(None, ev))
        self.assertEqual(period_art_label(parse_era_date("-237~-209"), ev), "당대 묘사")
        self.assertEqual(period_art_label(parse_era_date("-100~400"), ev), "후대의 묘사(기원전 100년~서기 400년)")

    def test_probable_caption(self) -> None:
        self.assertEqual(probable_caption("한니발 흉상", "probable"), "…로 추정되는 한니발 흉상")
        self.assertEqual(probable_caption("한니발 흉상", "certain"), "한니발 흉상")


class EraTest(unittest.TestCase):
    def test_era_boundaries(self) -> None:
        self.assertEqual(era_of("-216"), "ancient")
        self.assertEqual(era_of("1500"), "ancient")
        self.assertEqual(era_of("1501"), "early_modern")
        self.assertEqual(era_of("1850"), "early_modern")
        self.assertEqual(era_of("1950.09.15"), "modern")
        self.assertEqual(video_era(["1950.09.28", "-216"]), "ancient")

    def test_symbol_set_mixed(self) -> None:
        self.assertEqual(symbol_set_mixed("ancient", ["infantry_block", "cavalry_wedge"]), [])
        bad = symbol_set_mixed("ancient", ["app6_inf"])
        self.assertTrue(bad and bad[0].startswith("[symbol-set-mixed]"))


class EvidenceTest(unittest.TestCase):
    def test_required_layers(self) -> None:
        self.assertEqual(evidence_missing("ancient", {"period_art", "site", "toponymy"}), [])
        self.assertEqual(len(evidence_missing("ancient", {"period_art"})), 2)
        self.assertEqual(evidence_missing("modern", {"clip", "document", "toponymy"}), [])
        self.assertEqual(len(evidence_missing("modern", {"photo", "toponymy"})), 1)

    def test_toponymy(self) -> None:
        e = ToponymyEntry(id="cannae", place="칸나이", name="Cannae", language="라틴어", meaning="canna '갈대' 에서 왔다는 설",
                          source="t", confidence="이설")
        self.assertEqual(e.line(), "canna '갈대' 에서 왔다는 설(이설)")
        with self.assertRaises(ValidationError):
            ToponymyEntry(id="x", place="x", name="x", language="x", meaning="x", source="x", confidence="확실")
        with self.assertRaises(ValidationError):
            ToponymyFile(entries=[e, e])

    def test_period_art_label_missing(self) -> None:
        good = MediaAsset.model_validate(art())
        ev = [{"type": "photo", "mid": "m", "t0": 1.0}]
        self.assertEqual(period_art_label_missing(ev, {"m": good}, lambda t: "-216.08.02"), [])
        self.assertTrue(period_art_label_missing(ev, {"m": good}, lambda t: None))


class CasualtyTest(unittest.TestCase):
    def _fig(self, **kw: object) -> dict:
        d = {"id": "roman_dead", "side": "로마군", "metric": "killed", "source_kind": "ancient_text", "ancient_value": 70000,
             "ancient": {"author": "Polybius", "work": "Histories", "book": "III", "chapter": "117", "translation": "W. R. Paton(1922)",
                         "translation_url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/3*.html",
                         "translation_license": "Public domain"},
             "band": {"low": 45000, "high": 70000, "source": "Goldsworthy, Cannae(2001)"}}
        d.update(kw)
        return d

    def test_force_record(self) -> None:
        f = ForceFigure.model_validate(self._fig())
        self.assertEqual(f.ancient.locator(), "Polybius, Histories III.117")
        with self.assertRaises(ValidationError):
            ForceFigure.model_validate(self._fig(band=None))
        with self.assertRaises(ValidationError):
            ForceFigure.model_validate(self._fig(ancient=None))

    def test_sentence_needs_force_ref(self) -> None:
        forces = ForceFiguresFile(figures=[ForceFigure.model_validate(self._fig())])
        s_bad = NS(sid="a_0", text="로마군 전사자는 7만 명에 이르렀다고 전합니다.", sources=["c1"])
        s_ok = NS(sid="a_1", text="로마군 전사자는 7만 명에 이르렀다고 전합니다.", sources=["force:roman_dead"])
        s_free = NS(sid="a_2", text="두 군대가 아우피두스 강가에서 만났습니다.", sources=[])
        self.assertEqual(len(casualty_unsourced([s_bad], forces)), 1)
        self.assertEqual(casualty_unsourced([s_ok, s_free], forces), [])
        self.assertEqual(len(casualty_unsourced([s_ok], None)), 1)


class GenreTest(unittest.TestCase):
    def test_profile_and_prompt(self) -> None:
        from genres.load import load_genre
        from rules import load_rules
        from workers.prompt_loader import load_prompt

        g = load_genre("war_history")
        self.assertEqual((g.status, g.stage.primary, g.stage.mercator["theme"], g.photo_age_check), ("proposed", "mercator", "dark", False))
        t = load_prompt("script", load_rules(), g)
        nar = load_rules().genre_prompt.narration
        for k in ("etymology_once", "past_tense", "art_history_line", "source_quote", "evidence_first"):
            self.assertIn(nar[k][:20], t, k)


if __name__ == "__main__":
    unittest.main()

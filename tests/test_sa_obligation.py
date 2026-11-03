"""v7.4.0 사용자 결정 D612 — 사진·영상 CC BY-SA 허용과 고지 의무(작가·제목·라이선스·링크·변경 사항).

휘장·초상 관문(license_allowed)은 그대로 SA 불허. 사진·영상 관문(media_license_allowed)만 SA 를 받고 NC·ND 는 거부한다.
SA 자산은 modifications·url 이 없으면 레지스트리 모델 오류, 화면 출처 줄·엔딩 크레딧·설명란·provenance 에 고지가 남는다."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from schemas.media_models import MediaAsset

BASE = {
    "kind": "photo", "title": "File:Example SA.jpg", "license": "CC BY-SA 4.0", "author": "Example Author",
    "credit_author": "Example Author", "date": "2024-05-01",
    "url": "https://commons.wikimedia.org/wiki/File:Example_SA.jpg", "caption": "예시", "file_note": "자료사진 · 2024. 05",
    "depicts": ["예시"], "is_file_photo": True,
    "verified_by": {"by": "test", "on": "2026-11-03", "casualty_free": True, "relevance": "시험"},
    "rights_status": "rights_clear", "retrieved_at": "2026-11-03",
    "tool": {"name": "media_fetch.photo", "params": {}}, "source_hash": "0" * 32, "file": "x.jpg",
    "modifications": "자르기·크기 조정",
}


class LicenseGateTest(unittest.TestCase):
    def test_media_gate_takes_sa_emblem_gate_does_not(self) -> None:
        from schemas.emblem_models import license_allowed, media_license_allowed

        for lic in ("CC BY-SA 2.0", "CC BY-SA 3.0", "CC BY-SA 4.0"):
            self.assertTrue(media_license_allowed(lic), lic)
            self.assertFalse(license_allowed(lic), lic)          # 휘장·초상은 그대로(D612 범위 밖)
        for lic in ("CC BY-NC-SA 2.0", "CC BY-NC 4.0", "CC BY-ND 4.0", "CC BY-NC-ND 2.0"):
            self.assertFalse(media_license_allowed(lic), lic)
        self.assertTrue(media_license_allowed("CC BY 4.0"))
        self.assertTrue(media_license_allowed("Public domain"))

    def test_search_marks_sa_allowed_only_for_media(self) -> None:
        from tools import commons_fetch

        page = {"title": "File:A.jpg", "imageinfo": [{"url": "u", "thumburl": "t", "descriptionurl": "d", "mime": "image/jpeg",
                                                      "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}}}]}
        orig = commons_fetch.api
        commons_fetch.api = lambda params: {"query": {"pages": {"1": page}}}  # type: ignore[assignment]
        try:
            self.assertTrue(commons_fetch.search("q", media=True)[0]["allowed"])
            self.assertFalse(commons_fetch.search("q")[0]["allowed"])
        finally:
            commons_fetch.api = orig  # type: ignore[assignment]


class ObligationTest(unittest.TestCase):
    def test_sa_needs_modifications_and_url(self) -> None:
        MediaAsset.model_validate(BASE)
        with self.assertRaisesRegex(ValidationError, "modifications"):
            MediaAsset.model_validate({**BASE, "modifications": None})
        with self.assertRaisesRegex(ValidationError, "url"):
            MediaAsset.model_validate({**BASE, "url": None, "source_ref": "x", "pending_source": "p"})
        with self.assertRaisesRegex(ValidationError, "sa-obligation"):
            MediaAsset.model_validate({**BASE, "license": "CC BY-NC-SA 2.0"})

    def test_screen_line_card_description_provenance(self) -> None:
        from engine.credits import description_sa_credits, sa_line, sa_obligations
        from engine.media_registry import credit_line

        a = MediaAsset.model_validate(BASE)
        self.assertIn("자르기·크기 조정", credit_line(a))                       # 화면 출처 줄
        media = {"ex": a.model_dump()}
        line = sa_line(media["ex"])
        for k in ("Example Author", "File:Example SA.jpg", "CC BY-SA 4.0", BASE["url"], "자르기·크기 조정"):
            self.assertIn(k, line)
        self.assertEqual(description_sa_credits({"media.ex"}, media), [line])  # 설명란
        obs = sa_obligations({"media.ex", "people.x"}, media)                    # provenance
        self.assertEqual([o["ref"] for o in obs], ["media.ex"])
        self.assertIs(obs[0]["sa_obligation"], True)
        b = MediaAsset.model_validate({**BASE, "license": "CC BY 4.0", "modifications": None})
        self.assertEqual(sa_obligations({"media.b"}, {"b": b.model_dump()}), [])

    def test_check_fails_when_card_lacks_notice(self) -> None:
        from engine import checks, credits

        a = MediaAsset.model_validate(BASE)
        P = SimpleNamespace(R=SimpleNamespace(cache={"credit_refs": {"media.ex"}}, credits=None,  # noqa: N806
                                              assets=SimpleNamespace(media={"ex": a.model_dump()}, media_assets={"ex": a}, rights={})))
        orig = credits.credit_lines
        try:
            credits.credit_lines = lambda *a_, **k: ["사진 · Example Author · CC BY-SA 4.0"]  # type: ignore[assignment]
            self.assertTrue(any("엔딩 크레딧" in x for x in checks.check_sa_obligation(P)))
            credits.credit_lines = lambda *a_, **k: ["사진 · " + credits.sa_line(a.model_dump())]  # type: ignore[assignment]
            self.assertEqual(checks.check_sa_obligation(P), [])
        finally:
            credits.credit_lines = orig  # type: ignore[assignment]


class RestrictionPhraseTest(unittest.TestCase):
    """D613(RIGHTS-AP-003) — CC 라이선스 번호가 붙어 있어도 사진 쪽 별도 이용 조건이면 거부(Flickr·Commons 같은 규칙 키)."""

    PAGE = ('<meta name="description" content="21th Cabinet meeting of 2026 All photographs in the official Flickr account of the '
            'Republic of Korea are available only for publication by news organizations and/or for public purposes … use of the photograph '
            'with other images is strictly prohibited without the express written permission">'
            '"license":12,"sizes":{"data":{"sq":{"data":{"displayUrl":"//live.staticflickr.com/65535/55268178942_ab_s.jpg"')

    def test_flickr_terms_reject_even_with_cc_license(self) -> None:
        from tools.media_fetch import flickr_check, flickr_license_ok

        self.assertTrue(flickr_license_ok("12", "CC BY-SA 4.0"))   # 번호만 보면 통과
        r = flickr_check("https://www.flickr.com/photos/koreanet/55268178942/", page=self.PAGE)
        self.assertFalse(r["allowed"])
        self.assertTrue(any("별도 이용 조건" in x for x in r["reasons"]))
        clean = self.PAGE.split("All photographs")[0] + '">' + self.PAGE.split('">', 1)[1]
        self.assertTrue(flickr_check("https://www.flickr.com/photos/koreanet/55268178942/", page=clean)["allowed"])
        for nc in ("13", "14", "15", "16"):
            self.assertFalse(flickr_license_ok(nc, "CC BY 4.0"), nc)

    def test_commons_terms_reject(self) -> None:
        from tools import commons_fetch

        page = {"title": "File:A.jpg", "imageinfo": [{"url": "u", "thumburl": "t", "descriptionurl": "d", "mime": "image/jpeg", "extmetadata": {
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
            "UsageTerms": {"value": "보도 혹은 공익목적으로만 사용, 부분 복제 금지"}}}]}
        orig = commons_fetch.api
        commons_fetch.api = lambda params: {"query": {"pages": {"1": page}}}  # type: ignore[assignment]
        try:
            c = commons_fetch.search("q", media=True)[0]
            self.assertFalse(c["allowed"])
            self.assertTrue(c["terms_hits"])
        finally:
            commons_fetch.api = orig  # type: ignore[assignment]


if __name__ == "__main__":
    unittest.main()

"""schemas/source_models — 소스 레코드·주장 계약 (v3.2.0, 18 §2·§3, back_and_forth D-0051 작업 3)."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from orchestrator.project_manager import PROJECT_PATHS
from schemas.source_models import ClaimsFile, SourcesFile, check_claim_sources


def _x(i: str = "src_x_0001", **kw: object) -> dict:
    d = {"id": i, "type": "x_post", "input": "text", "account_name": "U.S. Central Command", "handle": "@CENTCOM",
         "posted_at": "2026-09-20T14:05:00Z", "text_original": "Strikes conducted.", "retrieved_at": "2026-09-26", "lang": "en"}
    return d | kw


def _art(i: str = "src_art_0001") -> dict:
    return {"id": i, "type": "article", "publisher": "연합뉴스", "headline_original": "해협 통항 재개", "published_at": "2026-09-21",
            "key_facts": ["통항 재개"], "retrieved_at": "2026-09-26", "url": "https://www.yna.co.kr/view/AKR0000"}


class SourcesTest(unittest.TestCase):
    def test_three_types_parse(self) -> None:
        doc = {"id": "src_doc_0001", "type": "document", "issuer": "국방부", "title": "보도자료", "key_facts": ["파견 연장"],
               "retrieved_at": "2026-09-26"}
        f = SourcesFile.model_validate({"schema_version": 1, "sources": [_x(), _art(), doc]})
        self.assertEqual([s.type for s in f.sources], ["x_post", "article", "document"])
        self.assertEqual(f.sources[0].account_class, "unknown")     # 공식 여부는 코드가 목록으로 정한다
        self.assertFalse(f.sources[0].confirmed)

    def test_capture_needs_path_and_bad_handle(self) -> None:
        with self.assertRaises(ValidationError):
            SourcesFile.model_validate({"sources": [_x(input="capture")]})
        with self.assertRaises(ValidationError):
            SourcesFile.model_validate({"sources": [_x(handle="CENTCOM")]})

    def test_duplicate_ids_and_unknown_field(self) -> None:
        with self.assertRaises(ValidationError):
            SourcesFile.model_validate({"sources": [_x(), _x()]})
        with self.assertRaises(ValidationError):
            SourcesFile.model_validate({"sources": [_x(body="원문 전체")]})

    def test_article_needs_key_facts(self) -> None:
        a = _art() | {"key_facts": []}
        with self.assertRaises(ValidationError):
            SourcesFile.model_validate({"sources": [a]})


class ClaimsTest(unittest.TestCase):
    def test_contested_without_two_sides_must_be_unverified(self) -> None:
        base = {"claim_id": "clm_0001", "text": "공습이 있었다", "source_ids": ["src_x_0001"], "contested": True}
        with self.assertRaises(ValidationError):
            ClaimsFile.model_validate({"claims": [base | {"status": "corroborated"}]})
        ok = ClaimsFile.model_validate({"claims": [base | {"status": "unverified"}]})
        self.assertEqual(ok.ids(), {"clm_0001"})
        sides = [{"party": "미국", "text": "방어적 공습", "source_ids": ["src_x_0001"]},
                 {"party": "이란", "text": "침략", "source_ids": ["src_art_0001"]}]
        ClaimsFile.model_validate({"claims": [base | {"status": "corroborated", "sides": sides}]})

    def test_claim_sources_must_exist(self) -> None:
        s = SourcesFile.model_validate({"sources": [_x()]})
        c = ClaimsFile.model_validate({"claims": [{"claim_id": "clm_0001", "text": "t", "source_ids": ["src_x_0001", "src_art_9"],
                                                    "status": "unverified"}]})
        self.assertEqual(len(check_claim_sources(c, s)), 1)

    def test_paths_registered(self) -> None:
        self.assertEqual(PROJECT_PATHS["sources"], "intake/sources.json")
        self.assertEqual(PROJECT_PATHS["claims"], "intake/claims.json")


if __name__ == "__main__":
    unittest.main()

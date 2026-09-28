"""번들 출처·claim 후보 → 6.95 인테이크(v3.5.0, D-0063 작업 2, D-0064 쟁점 2·3). 네트워크 없음(가져오기 주입)."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from bundle.to_sources import BUNDLE_CLAIMS_FILE, claim_hints, parse_citation, resolve_sources
from orchestrator.source_verify import judge
from schemas.models import BundleSource, ReportBundle
from schemas.source_models import ArticleSource, SourcesFile, VerifyDraft

CITE = "CNN Politics, 'Ratcliffe was in Moscow to warn Russia', 2026-08-27 (https://www.cnn.com/2026/08/27/politics/x)"


def _bundle(sources: list[dict], **extra: object) -> ReportBundle:
    return ReportBundle.model_validate({
        "schema_version": 1, "producer": {"system": "agents_reviewer", "version": "v8.5.9"},
        "generated_at": "2026-08-29T11:55:08+09:00",
        "report": {"report_id": "r1", "headline": "h"}, "sources": sources, **extra})


def _fetch(url: str) -> dict[str, str]:
    if "fail" in url:
        raise OSError("HTTP Error 403: Forbidden")
    return {"title": "Fetched title", "publisher": "Example", "published_at": "2026-08-20T09:00:00Z",
            "body": "The director met the spy chief in Moscow on Monday."}


class CitationTest(unittest.TestCase):
    def test_citation_string(self) -> None:
        c = parse_citation(BundleSource(source_id="s", url=CITE))
        self.assertEqual((c.publisher, c.title, c.published_at), ("CNN Politics", "Ratcliffe was in Moscow to warn Russia", date(2026, 8, 27)))
        self.assertEqual(c.url, "https://www.cnn.com/2026/08/27/politics/x")

    def test_month_only_date_not_guessed(self) -> None:
        c = parse_citation(BundleSource(source_id="s", url="UNITED24 Media, 'T', 2026-08 (https://u.example/a)"))
        self.assertIsNone(c.published_at)                   # 일자 없는 날짜를 1일로 채우지 않는다
        self.assertEqual(c.date_text, "2026-08")

    def test_plain_url(self) -> None:
        c = parse_citation(BundleSource(source_id="s", url="https://a.example/n", publisher="a.example"))
        self.assertEqual((c.url, c.publisher, c.title, c.published_at), ("https://a.example/n", "a.example", "", None))


class ResolveTest(unittest.TestCase):
    def test_article_only_and_unresolved_reasons(self) -> None:
        b = _bundle([{"source_id": "s1", "url": CITE}, {"source_id": "s2", "url": "https://x.com/a/status/1"},
                     {"source_id": "s3", "url": "https://fail.example/a"}, {"source_id": "s4", "url": "책 한 권"},
                     {"source_id": "s5", "url": "https://ok.example/b", "publisher": "ok.example"}])
        ok, bad = resolve_sources(b, fetch=_fetch, blocked=lambda u: "x.com" in u)
        self.assertEqual([a.bundle_source_id for a in ok], ["s1", "s5"])
        self.assertEqual(ok[0].published_at, date(2026, 8, 27))              # 인용 문자열 날짜가 가져온 날짜보다 먼저
        self.assertEqual(ok[1].published_at, date(2026, 8, 20))              # 순수 URL → 가져온 메타
        why = {u.bundle_source_id: u.reason for u in bad}
        self.assertEqual(why["s2"], "blocked_host")
        self.assertTrue(why["s3"].startswith("fetch_failed:"))
        self.assertEqual(why["s4"], "no_url")

    def test_no_fetch_leaves_unresolved_not_invented(self) -> None:
        ok, bad = resolve_sources(_bundle([{"source_id": "s1", "url": CITE}]), fetch=None, blocked=lambda u: False)
        self.assertEqual(ok, [])
        self.assertIn("missing:body", bad[0].reason)                         # 본문을 지어내지 않는다


class HintsTest(unittest.TestCase):
    def test_contradiction_sides_and_bundle_status_reference_only(self) -> None:
        b = _bundle([], claims=[{"claim_id": "C-1", "statement": "회담이 열렸다.", "status": "confirmed", "confidence": "high"}],
                    contradictions=[{"side_a": "경고였다", "side_b": "통상 방문이었다",
                                     "video": {"label_a": "경고론", "label_b": "축소론", "line_a": "경고 전달", "line_b": "준일상"}}])
        f = claim_hints(b)
        self.assertEqual(f.hints[0].bundle_status, "confirmed")              # 참고 필드로만
        c = f.hints[1]
        self.assertEqual((c.kind, [s.party for s in c.sides]), ("contested", ["경고론", "축소론"]))   # video 라벨이 읽힌다

    def test_hint_without_quote_never_reaches_claims(self) -> None:
        """번들이 confirmed 라 해도 인용이 본문에 없으면 claims 에 없다 — status 부풀림 0(D-0064 쟁점 3)."""
        src = SourcesFile(sources=[ArticleSource(id="src_art_0001", type="article", publisher="CNN", headline_original="H",
                                                 published_at=date(2026, 8, 27), key_facts=["H"], retrieved_at=date(2026, 8, 29),
                                                 confirmed_by="tester")])
        body = {"src_art_0001": "H\nThe director met the spy chief in Moscow on Monday."}
        draft = VerifyDraft(claims=[
            {"text": "회담이 열렸다.", "evidence": [{"source_id": "src_art_0001", "quote": "met the spy chief in Moscow", "stance": "supports"}]},
            {"text": "푸틴이 계산된 선택을 했다.", "evidence": [{"source_id": "src_art_0001", "quote": "Putin chose not to meet", "stance": "supports"}]}])
        claims, drops = judge(draft, src, body)
        self.assertEqual([c.text for c in claims.claims], ["회담이 열렸다."])
        self.assertEqual(claims.claims[0].status, "unverified")             # 기사 1곳 — 번들 confidence 와 무관
        self.assertTrue(any("본문에 없음" in d for d in drops))


class ImportE2ETest(unittest.TestCase):
    def test_import_writes_unconfirmed_articles_and_view(self) -> None:
        from orchestrator import bundle_service as bs  # noqa: PLC0415
        from orchestrator.gate_view import source_view  # noqa: PLC0415
        from orchestrator.source_intake import load_sources  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            pdir, f = Path(d) / "p", Path(d) / "b.bundle.json"
            pdir.mkdir()
            raw = json.loads(_bundle([{"source_id": "s1", "url": CITE}, {"source_id": "s2", "url": "https://fail.example/a"}],
                                     contradictions=[{"side_a": "a", "side_b": "b"}]).model_dump_json(exclude_none=True))
            f.write_text(json.dumps(raw), encoding="utf-8")
            with mock.patch("orchestrator.source_intake.fetch_article", _fetch):
                r = bs.import_sources(pdir, f)
                again = bs.import_sources(pdir, f)
            recs = load_sources(pdir).sources
            self.assertEqual([s.type for s in recs], ["article"])            # DocumentSource 로 만들지 않는다
            self.assertFalse(recs[0].confirmed)                              # 사용자 확인 전(18 §7)
            self.assertTrue(recs[0].note.startswith("번들 이관 r1 s1"))
            self.assertIsNone(recs[0].verification)                          # status 는 검증 단계가 정한다
            self.assertEqual((len(r.imported_sources), len(r.unresolved_sources)), (1, 1))
            self.assertEqual(again.skipped_existing, ["s1"])                 # 다시 넣어도 중복 없음
            self.assertTrue((pdir / "intake" / BUNDLE_CLAIMS_FILE).exists())
            view = source_view(pdir)
            self.assertIn("번들 r1", view)
            self.assertIn("미해결 s2: fetch_failed", view)


class VerifyHintsBlockTest(unittest.TestCase):
    def _prompt(self, pdir: Path) -> str:
        from workers.verify_sources_worker import VerifySourcesWorker  # noqa: PLC0415

        w = VerifySourcesWorker()
        args = argparse.Namespace(project_id=pdir.name, task_id="t", projects_root=str(pdir.parent))
        with mock.patch("orchestrator.source_verify.verify_inputs",
                        return_value=(SourcesFile(sources=[]), {})):
            return w.build_user_prompt(args, None)  # type: ignore[arg-type]

    def test_block_only_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d) / "p"
            (pdir / "intake").mkdir(parents=True)
            plain = self._prompt(pdir)
            self.assertNotIn("{bundle_hints}", plain)
            self.assertNotIn("번들이 제시한 주장 후보", plain)
            f = claim_hints(_bundle([], contradictions=[{"side_a": "경고였다", "side_b": "통상 방문"}]))
            (pdir / "intake" / BUNDLE_CLAIMS_FILE).write_text(f.model_dump_json(), encoding="utf-8")
            hinted = self._prompt(pdir)
            self.assertIn("후보일 뿐", hinted)
            self.assertIn("경고였다", hinted)
            self.assertNotIn("confirmed", hinted)                            # 번들 status 는 넣지 않는다


if __name__ == "__main__":
    unittest.main()

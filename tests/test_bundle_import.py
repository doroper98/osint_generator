"""import-bundle 복귀(v3.5.0, D-0063 작업 5) — CLI·웹 번들 업로드·provenance `bundle` 단계·초안은 초안(최종 파일 안 씀)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from fastapi.testclient import TestClient

from engine.provenance import bundle_summary
from orchestrator.main import main as cli_main
from script.schema import Script
from tests.test_intake_flow import VALID_PLAN_JSON, _IsolatedProjectsRoot

CITE = "CNN, 'Director visits Moscow', 2026-08-25 (https://www.cnn.com/2026/08/25/x)"
BUNDLE = {
    "schema_version": 1, "bundle_kind": "report_bundle", "generated_at": "2026-08-29T11:00:00+09:00",
    "producer": {"system": "agents_reviewer", "version": "v8.5.9"},
    "report": {"report_id": "rtest", "headline": "수송기 한 대", "deck": "덱",
               "video": {"intro_narration": ["모스크바에 내렸습니다."], "outro_narration": ["끝입니다."]}},
    "sections": [{"section_id": "s1", "heading": "떠난 한 대", "video": {"narration": ["8월 25일 모스크바에 도착했습니다."]}},
                 {"section_id": "s2", "heading": "계산서", "chart_refs": ["ch-1"], "video": {"narration": ["비율을 봅니다."]}}],
    "charts": [{"chart_id": "ch-1", "type": "dot_matrix", "title": "몫",
                "data": [{"label": "움직인 몫", "value": 1, "accent": True}, {"label": "나머지", "value": 99}],
                "provenance": {"origin": "narrative_inference", "verification": "inferred"}}],
    "map": {"markers": [{"id": "moscow", "name": "모스크바", "lng": 37.62, "lat": 55.75, "kind": "capital"}]},
    "contradictions": [{"side_a": "경고", "side_b": "통상", "video": {"label_a": "경고론", "label_b": "축소론"}}],
    "sources": [{"source_id": "src-1", "url": CITE}],
    "timeline": {"points": [{"date": "2026-08-25", "label": "도착"}]},
}


def _fetch(url: str) -> dict[str, str]:
    return {"title": "", "publisher": "", "published_at": "", "body": "The director arrived in Moscow on Aug. 25."}


class ImportBundleCLITest(_IsolatedProjectsRoot):
    def _project(self) -> Path:
        self.assertEqual(cli_main(["new-project", "bun1", "--title", "번들 실험", "--category", "geopolitics",
                                   "--topic-summary", "요약"]), 0)
        return self.projects_root / "bun1"

    def test_cli_writes_drafts_not_finals(self) -> None:
        pdir = self._project()
        f = self.root / "rtest.bundle.json"
        f.write_text(json.dumps(BUNDLE, ensure_ascii=False), encoding="utf-8")
        with mock.patch("orchestrator.source_intake.fetch_article", _fetch):
            self.assertEqual(cli_main(["import-bundle", "bun1", "--file", str(f)]), 0)
        for rel in ("intake/sources.json", "intake/bundle_claims.json", "intake/bundle_import.json", "intake/bundle_materials.json",
                    "script.draft.yaml", "script.draft.notes.json", "direction.draft.yaml", "intake/files/rtest.bundle.json"):
            self.assertTrue((pdir / rel).exists(), rel)
        self.assertFalse((pdir / "script.yaml").exists())                    # 원고는 ScriptWorker 몫(P8)
        self.assertFalse((pdir / "direction.yaml").exists())                 # 연출은 DirectorWorker 몫
        self.assertFalse((pdir / "intake" / "claims.json").exists())         # claims 는 확인 → 검증 뒤
        sc = Script.model_validate(yaml.safe_load((pdir / "script.draft.yaml").read_text(encoding="utf-8")))
        self.assertEqual(sc.scenes[0].sentences[1].date, "2026.08.25")       # timeline 대응
        rec = json.loads((pdir / "intake" / "bundle_import.json").read_text(encoding="utf-8"))
        self.assertEqual((len(rec["imported_sources"]), rec["draft"]["panels"]), (1, 1))

    def test_cli_missing_file_is_error(self) -> None:
        self._project()
        self.assertEqual(cli_main(["import-bundle", "bun1", "--file", str(self.root / "none.json")]), 1)

    def test_web_bundle_upload(self) -> None:
        self._project()
        self._stub(VALID_PLAN_JSON)
        self.assertEqual(cli_main(["plan-intake", "bun1"]), 0)
        from web.intake_page_app import app  # noqa: PLC0415

        with mock.patch("orchestrator.source_intake.fetch_article", _fetch):
            r = TestClient(app).post("/intake/bun1/source", data={"kind": "bundle"}, follow_redirects=False,
                                     files={"file": ("rtest.bundle.json", json.dumps(BUNDLE).encode(), "application/json")})
        self.assertEqual(r.status_code, 303, r.text)
        page = TestClient(app).get("/intake/bun1").text
        self.assertIn("분석 번들 업로드", page)
        self.assertTrue((self.projects_root / "bun1" / "script.draft.yaml").exists())


class BundleProvenanceTest(unittest.TestCase):
    def test_summary_only_for_bundle_projects(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertIsNone(bundle_summary(root))                          # 돌지 않은 단계는 기록하지 않는다(P5)
            (root / "intake").mkdir()
            (root / "intake" / "bundle_import.json").write_text(json.dumps({
                "bundle_id": "rtest", "producer": "agents_reviewer v8.5.9", "imported_sources": [{}], "unresolved_sources": [{}, {}],
                "claim_hints": 1, "draft": {"sections": 12, "scenes": 7, "rewrite_required": 0, "unmatched": 14}}), encoding="utf-8")
            s = bundle_summary(root)
            self.assertEqual((s["scenes"], s["sources_unresolved"], s["draft_used"]), (7, 2, False))
            (root / "script.meta.json").write_text(json.dumps({"draft_sha1": "abc"}), encoding="utf-8")
            self.assertTrue(bundle_summary(root)["draft_used"])


if __name__ == "__main__":
    unittest.main()

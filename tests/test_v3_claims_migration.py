"""hormuz v3 원고 claims 이관(v3.2.0, D-0052 D51) — 45문장 전부 claim id, 라벨 없음(골든 무변경), 매체 단위 근거."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from schemas.source_models import ClaimsFile, SourcesFile, check_claim_sources
from script.labels import check_project_labels
from script.lint import lint
from script.schema import Script
from tools.migrate_v3_claims import ALL, SCENE_SOURCES, migrate

REPO = Path(__file__).resolve().parent.parent


class V3ClaimsMigrationTest(unittest.TestCase):
    def _load(self, proj: Path) -> tuple[Script, ClaimsFile, SourcesFile]:
        s = Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))
        c = ClaimsFile.model_validate_json((proj / "intake" / "claims.json").read_text(encoding="utf-8"))
        f = SourcesFile.model_validate_json((proj / "intake" / "sources.json").read_text(encoding="utf-8"))
        return s, c, f

    def test_hormuz_every_sentence_cites_claim_and_no_label(self) -> None:
        for name in ("hormuz_korea", "hormuz_ai"):
            proj = REPO / "projects" / name
            s, c, f = self._load(proj)
            self.assertEqual(check_claim_sources(c, f), [])
            sents = [x for sc in s.scenes for x in sc.sentences]
            self.assertEqual(len(sents), 45)
            self.assertTrue(all(len(x.sources) == 1 and x.sources[0] in c.ids() for x in sents))
            labels = check_project_labels(proj, s)
            assert labels is not None
            self.assertEqual(labels.counts()["corroborated"], 45)
            self.assertTrue(all(sl.label is None for sl in labels.labels.values()))    # 골든 무변경(D51)
            self.assertEqual([i for i in lint(s).issues if i.kind.startswith("source")], [])

    def test_scene_level_sources_only(self) -> None:
        s, c, _ = self._load(REPO / "projects" / "hormuz_korea")
        by = c.by_id()
        for sc in s.scenes:
            for x in sc.sentences:
                self.assertEqual(by[x.sources[0]].source_ids, SCENE_SOURCES.get(sc.id, ALL))
        self.assertTrue(all(src.url is None for src in self._load(REPO / "projects" / "hormuz_korea")[2].sources))

    def test_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "h"
            shutil.copytree(REPO / "projects" / "hormuz_korea", p, ignore=shutil.ignore_patterns("tts", "media", "assets", "prev", "out"))
            before = (p / "script.yaml").read_text(encoding="utf-8")
            migrate(p)
            self.assertEqual((p / "script.yaml").read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()

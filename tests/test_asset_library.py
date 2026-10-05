"""v5.6.0 사용자 결정 2026-10-04 — 제작 자산 공용 보관(PIPELINE-AP-016)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from tools import asset_library as al

REPO = Path(__file__).resolve().parent.parent


class AssetLibraryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        lib = self.tmp / "lib.json"
        shutil.copyfile(al.LIB, lib)
        self.proj = self.tmp / "p"
        (self.proj / "assets" / "portraits").mkdir(parents=True)
        Image.new("RGBA", (10, 10)).save(self.proj / "assets" / "portraits" / "zz_new.png")
        Image.new("RGBA", (10, 10)).save(self.proj / "assets" / "portraits" / "zz_norights.png")
        (self.proj / "assets" / "rights_registry.json").write_text(json.dumps({"people": {"zz_new": {
            "src": "wikimedia_commons", "license": "CC0", "artist": "a", "url": "https://commons.wikimedia.org/wiki/File:x.jpg",
            "rights_status": "rights_clear", "processing": {"tool": "tools/portrait_fallback.py cutout", "style": "engraving"}}}}),
            encoding="utf-8")
        self.people = self.tmp / "people"
        self.people.mkdir()
        self.emb = self.tmp / "emb"
        for k, v in (("LIB", lib), ("PEOPLE_DIR", self.people), ("EMBLEM_FILES", self.emb)):
            p = mock.patch.object(al, k, v)
            p.start()
            self.addCleanup(p.stop)

    def test_promote_people_with_rights_only(self) -> None:
        self.assertEqual(al.pending(self.proj)["people"], ["zz_new", "zz_norights"])
        out = al.promote(self.proj)
        self.assertEqual(out["people"], ["zz_new"])                       # 권리 기록 있는 것만(C9)
        self.assertTrue(any("zz_norights" in s for s in out["skipped"]))
        self.assertTrue((self.people / "zz_new_mono_v01.png").exists())
        lib = json.loads(al.LIB.read_text(encoding="utf-8"))
        ent = next(p for p in lib["people"] if p["person_id"] == "zz_new")
        self.assertEqual(ent["source"]["url"], "https://commons.wikimedia.org/wiki/File:x.jpg")
        self.assertEqual(al.pending(self.proj)["people"], ["zz_norights"])

    def test_repo_has_promoted_nato_and_people(self) -> None:
        """나토 휘장·kaliningrad 초상 5인이 공용 자산에 있다(저장소 추적 파일)."""
        self.assertTrue((REPO / "assets" / "emblems" / "files" / "nato.png").exists())
        lib = {p["person_id"] for p in json.loads((REPO / "assets/library/library_manifest.json").read_text(encoding="utf-8"))["people"]}
        self.assertTrue({"lukashenko", "tusk", "merz", "rutte", "nauseda"} <= lib)


if __name__ == "__main__":
    unittest.main()

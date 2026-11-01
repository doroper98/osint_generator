"""v7.4.0 D-0609 ④ — verify-sources --supplement: 기존 claims 를 두고 같은 judge() 로 덧붙인다. 근거 폐기가 있으면 아무것도 쓰지 않는다(P6)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from orchestrator.source_verify import apply_supplement, load_claims
from schemas.source_models import VerifyDraft

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "projects" / "cannae_216bc" / "intake"


def _project(d: Path) -> Path:
    """칸나이 소스 1개(Macrobius 라틴 원문 — 저장소 추적 texts)만 남긴 최소 프로젝트."""
    p = d / "p"
    (p / "intake" / "bodies").mkdir(parents=True)
    raw = json.loads((SRC / "sources.json").read_text(encoding="utf-8"))
    raw["sources"] = [s for s in raw["sources"] if s["id"] == "src_doc_0012"]
    (p / "intake" / "sources.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    shutil.copy(SRC / "texts" / "macrobius_sat_i16_26_teubner1893.txt", p / "intake" / "bodies" / "src_doc_0012.txt")
    from orchestrator.source_verify import apply_draft, verify_inputs  # 기존 검증 1건을 같은 경로로 만든다

    srcs, bodies = verify_inputs(p)
    assert apply_draft(p, _draft("Q.  Glavdivs  Annalivm  quinto"), srcs, bodies).ok
    return p


def _draft(quote: str) -> VerifyDraft:
    return VerifyDraft.model_validate({"claims": [{"text": "칸나이 패전 날짜(로마력)", "evidence": [
        {"source_id": "src_doc_0012", "quote": quote, "stance": "supports"}]}]})


class SupplementTest(unittest.TestCase):
    def test_appends_with_next_id_and_tag(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _project(Path(d))
            res = apply_supplement(p, _draft("cladem illam uastissimam pugnae Cannensis factam refert ante diem quartum Nonas"), "t1")
            self.assertTrue(res.ok, res.errors)
            cl = load_claims(p).claims
            self.assertEqual([c.claim_id for c in cl][-1], "clm_0002")
            self.assertIn("supplement:t1", cl[-1].checks)
            self.assertEqual(cl[-1].status, "verified")

    def test_bad_quote_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _project(Path(d))
            before = (p / "intake" / "claims.json").read_text(encoding="utf-8")
            res = apply_supplement(p, _draft("Hannibal crossed the Alps with elephants"), "t2")
            self.assertFalse(res.ok)
            self.assertEqual((p / "intake" / "claims.json").read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()

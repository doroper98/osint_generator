"""v5.21.15 D-0196 — 화면 전용 사실의 근거 claim(이벤트 claims) → 엔딩·설명란 출처. 없는 id = 렌더 전 오류."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.project import cited_sources
from engine.registry import validate_events
from workers.direction_io import event_fields_table


def _proj(d: Path) -> Path:
    (d / "intake").mkdir(parents=True)
    src = lambda i, pub: {"id": i, "url": f"https://example.com/{i}", "retrieved_at": "2026-10-11", "lang": "en", "type": "article",  # noqa: E731
                         "publisher": pub, "headline_original": "h", "published_at": "2026-10-05", "key_facts": ["k"]}
    (d / "intake" / "sources.json").write_text(json.dumps({"schema_version": 1, "sources": [src("src_s1", "A"), src("src_s2", "B")]}), encoding="utf-8")
    cl = lambda c, s: {"claim_id": c, "text": "t", "source_ids": [s], "status": "unverified", "contested": False,  # noqa: E731
                       "event_date": "2026-10-05", "checks": [], "attributed_only": True, "claim_kind": "statement", "notes": ""}
    (d / "intake" / "claims.json").write_text(json.dumps({"schema_version": 1, "claims": [cl("clm_0001", "src_s1"), cl("clm_0002", "src_s2")]}), encoding="utf-8")
    (d / "script.yaml").write_text("scenes:\n- id: a\n  sentences:\n  - id: a_0\n    text: x\n    sources: [clm_0001]\n", encoding="utf-8")
    return d


MK = {"type": "marker", "t0": 0.0, "t1": 1.0, "lon": 43.2, "lat": 13.3, "label": "모카", "sub": "10.5 정부군 장악 주장"}


class TestEventClaims(unittest.TestCase):
    def test_dict_unchanged_without_claims(self) -> None:
        self.assertNotIn("claims", validate_events([dict(MK)])[0])

    def test_event_claim_sources_cited(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _proj(Path(d))
            self.assertEqual([s.id for s in cited_sources(p, validate_events([dict(MK)]))], ["src_s1"])
            self.assertEqual([s.id for s in cited_sources(p, validate_events([{**MK, "claims": ["clm_0002"]}]))], ["src_s1", "src_s2"])

    def test_unknown_claim_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _proj(Path(d))
            with self.assertRaises(ValueError):
                cited_sources(p, validate_events([{**MK, "claims": ["nope"]}]))

    def test_field_table_mentions_once(self) -> None:
        tab = event_fields_table()
        self.assertEqual(tab.count("claims"), 1)   # 공통 줄 한 번(이벤트마다 반복하지 않는다)


if __name__ == "__main__":
    unittest.main()

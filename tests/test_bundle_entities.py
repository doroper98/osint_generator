"""번들 노드·마커 → 엔티티 레지스트리 조인(v3.5.0, D-0063 작업 1) — id 매칭, unmatched 기록, 추측 생성 금지."""

from __future__ import annotations

import unittest

from bundle.entities import join_entities, mentions
from engine.entities import load_entities
from schemas.models import ReportBundle


def _bundle() -> ReportBundle:
    return ReportBundle.model_validate({
        "schema_version": 1, "producer": {"system": "agents_reviewer", "version": "v8.5.9"},
        "report": {"report_id": "r1", "headline": "h"},
        "charts": [{"chart_id": "ch-1", "type": "stakeholder_map", "title": "t",
                    "provenance": {"origin": "narrative_inference", "verification": "inferred"},
                    "data": {"nodes": [
                        {"id": "trump", "label": "도널드 트럼프", "kind": "person", "flag": "US", "col": "left"},
                        {"id": "ratcliffe", "label": "존 랫클리프", "kind": "person", "flag": "US", "col": "center"},
                        {"id": "iran", "label": "이란", "col": "right"}],
                        "edges": []}}],
        "map": {"markers": [{"id": "moscow", "name": "모스크바", "lng": 37.62, "lat": 55.75}]},
    })


class EntityJoinTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = load_entities()
        self.join = join_entities(_bundle(), self.reg)

    def test_id_match_joins(self) -> None:
        e = self.join.by_id()["trump"]
        self.assertEqual(e.entity_id, "trump")
        self.assertEqual(e.flag, "us")                      # 번들 대문자 ISO2 → 소문자

    def test_unmatched_recorded_not_invented(self) -> None:
        ids = {u.id for u in self.join.unmatched}
        self.assertIn("ratcliffe", ids)                      # 레지스트리에 없는 인물
        self.assertIsNone(self.join.by_id()["ratcliffe"].entity_id)
        self.assertNotIn("ratcliffe", self.reg.entities)     # 조인이 레지스트리를 만들지 않는다

    def test_label_alias_is_candidate_only(self) -> None:
        u = next(x for x in self.join.unmatched if x.id == "iran")
        self.assertEqual(u.alias_candidate, "ir")           # 라벨 "이란" = 레지스트리 별칭
        self.assertIsNone(self.join.by_id()["iran"].entity_id)   # 그래도 조인하지 않는다(id 매칭만)

    def test_markers_listed(self) -> None:
        self.assertEqual(self.join.by_id()["moscow"].origin, "marker")

    def test_mentions_fallback_surname_and_position(self) -> None:
        ms = mentions("푸틴은 랫클리프를 만나지 않았고 트럼프는 말을 아꼈다.", self.join, self.reg)
        self.assertEqual([m.id for m in ms], ["ratcliffe", "trump"])   # 성(마지막 어절) 별칭, 위치 순
        self.assertTrue(all(0 <= m.at <= 1 for m in ms))


if __name__ == "__main__":
    unittest.main()

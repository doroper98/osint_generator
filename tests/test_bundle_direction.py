"""번들 지도·차트 → 연출 재료·초안(v3.5.0, D-0063 작업 4) — 추정 태그, 패널 모델 통과(P4), 선언 필드 사용, 재료 블록."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from bundle.entities import join_entities
from bundle.to_direction import MATERIALS_FILE, build_direction_draft, build_materials, chart_panel, dump_direction_draft
from engine.direction import Direction
from engine.entities import load_entities
from schemas.models import ReportBundle

REG = load_entities()


def _bundle(**extra: object) -> ReportBundle:
    return ReportBundle.model_validate({
        "schema_version": 1, "producer": {"system": "agents_reviewer", "version": "v8"}, "generated_at": "2026-08-29T10:00:00+09:00",
        "report": {"report_id": "r1", "headline": "h"},
        "sections": [{"section_id": "s1", "chart_refs": ["ch-1", "ch-2"], "video": {"narration": ["모스크바"], "highlights": ["인용 한 줄"]}}],
        "charts": [
            {"chart_id": "ch-1", "type": "dot_matrix", "title": "점",
             "data": [{"label": "움직인 몫", "value": 1, "accent": True}, {"label": "나머지", "value": 99}],
             "provenance": {"origin": "narrative_inference", "verification": "inferred"}},
            {"chart_id": "ch-2", "type": "dual_line", "title": "유가",
             "data": {"left": {"label": "브렌트", "unit": "달러", "series": [{"x": "a", "y": 87.7}, {"x": "b", "y": 94.4}]},
                      "right": {"label": "WTI", "series": [{"x": "a", "y": 82.1}, {"x": "b", "y": 87.1}]}},
             "provenance": {"origin": "measured", "verification": "confirmed", "sources": [{"provider": "EIA", "code": "RBRTE"}]}},
            {"chart_id": "ch-3", "type": "candle", "title": "주가", "data": [],
             "provenance": {"origin": "measured", "verification": "confirmed"}},
            {"chart_id": "ch-4", "type": "stakeholder_map", "title": "관계",
             "provenance": {"origin": "narrative_inference", "verification": "inferred"},
             "data": {"nodes": [{"id": "trump", "label": "도널드 트럼프", "kind": "person", "flag": "US", "col": "left"},
                                {"id": "ratcliffe", "label": "존 랫클리프", "kind": "person", "flag": "US", "col": "center", "accent": True},
                                {"id": "nato", "label": "나토", "col": "center", "logo": "nato.int"},
                                {"id": "putin", "label": "블라디미르 푸틴", "kind": "person", "flag": "RU", "col": "right"},
                                {"id": "atlantis", "label": "아틀란티스", "flag": "QZ", "col": "right"}],
                      "edges": [{"source": "trump", "target": "ratcliffe", "type": "영향", "label": "축소"},
                                {"source": "ratcliffe", "target": "nato", "type": "대립"},
                                {"source": "ratcliffe", "target": "putin", "type": "연관", "label": "불발"}]}}],
        "map": {"markers": [{"id": "moscow", "name": "모스크바", "lng": 37.62, "lat": 55.75, "kind": "capital", "value": "8월 25일 회담", "label_side": "right"},
                            {"id": "riga", "name": "리가", "lng": 24.11, "lat": 56.95}],
                "arcs": [{"from_id": "riga", "to_id": "moscow", "kind": "flow", "weight": 3, "label": "8월 25일 도착", "label_t": 0.5}]},
        "contradictions": [{"side_a": "경고였다", "side_b": "통상 방문", "video": {"label_a": "경고론", "label_b": "축소론", "line_a": "경고", "line_b": "준일상"}}],
        **extra})


class ChartPanelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.b = _bundle()
        self.j = join_entities(self.b, REG)

    def test_inferred_gets_estimate_tag(self) -> None:
        p = chart_panel(self.b.charts[0], self.j, REG, None)
        self.assertEqual((p.kind, p.data["provenance"]["verification"], p.prov_tag), ("dots", "estimated", "추정 · 출처 미기재"))

    def test_confirmed_with_source_no_tag(self) -> None:
        p = chart_panel(self.b.charts[1], self.j, REG, None)
        self.assertEqual((p.kind, p.prov_tag, p.data["provenance"]["sources"]), ("dual_line", None, ["EIA RBRTE"]))

    def test_unsupported_chart_is_error_not_silent(self) -> None:
        with self.assertRaises(ValueError):
            chart_panel(self.b.charts[2], self.j, REG, None)
        m = build_materials(self.b, self.j, REG, {"s1": "sc01"}, {"sc01": ["moscow"]})
        self.assertEqual([(u.chart_id, u.chart_type) for u in m.unsupported], [("ch-3", "candle")])

    def test_network_badges_only_and_notes(self) -> None:
        p = chart_panel(self.b.charts[3], self.j, REG, None)
        kinds = {n["id"]: n["kind"] for n in p.data["nodes"]}
        self.assertEqual(kinds, {"trump": "person", "ratcliffe": "flag", "putin": "person"})   # 미등재 인물 = 국기, 국기 없는 기관 = 뺌
        self.assertTrue(any("nato" in x for x in p.notes))                   # 뺀 노드·선은 notes 에(조용한 드롭 아님)
        self.assertTrue(any("국기 qz" in x for x in p.notes))                # 레지스트리에 없는 국기는 넘기지 않는다(P10)
        self.assertEqual([e["type"] for e in p.data["edges"]], ["influence", "related"])


class MaterialsTest(unittest.TestCase):
    def test_declared_fields_reach_materials(self) -> None:
        b = _bundle()
        m = build_materials(b, join_entities(b, REG), REG, {"s1": "sc01"}, {"sc01": ["moscow", "trump"]})
        mo = next(p for p in m.places if p.id == "moscow")
        self.assertEqual((mo.kind, mo.value, mo.label_side, mo.scenes), ("capital", "8월 25일 회담", "right", ["sc01"]))
        self.assertEqual((m.paths[0].kind, m.paths[0].weight, m.paths[0].label_t), ("flow", 3, 0.5))
        self.assertEqual((m.versus[0].label_a, m.versus[0].line_b), ("경고론", "준일상"))
        self.assertEqual([x.entity_id for x in m.badges], ["trump", "nato", "putin"])   # v5.5.1 — 엔티티 nato(나토) 등록
        self.assertEqual([q.text for q in m.quotes], ["인용 한 줄"])

    def test_direction_draft_schema_and_panels_only(self) -> None:
        b = _bundle()
        m = build_materials(b, join_entities(b, REG), REG, {"s1": "sc01"}, {"sc01": ["moscow"]})
        d = Direction.model_validate(yaml.safe_load(dump_direction_draft(build_direction_draft(m, ["sc01"]), m)))
        self.assertEqual({e["type"] for e in d.events}, {"panel"})           # places·paths·패널만(연출은 DirectorWorker)
        self.assertEqual(d.shots[0].at, {"scene_start": "sc01"})
        self.assertIn("moscow", d.places)


class DirectorBlockTest(unittest.TestCase):
    def test_materials_block_only_with_file(self) -> None:
        from workers.direction_io import bundle_materials_text  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            self.assertEqual(bundle_materials_text(pdir), ("", None))
            b = _bundle()
            m = build_materials(b, join_entities(b, REG), REG, {"s1": "sc01"}, {})
            (pdir / "intake").mkdir()
            (pdir / "intake" / MATERIALS_FILE).write_text(m.model_dump_json(), encoding="utf-8")
            text, sha = bundle_materials_text(pdir)
            self.assertIn("강제 아님", text)
            self.assertIn("8월 25일 회담", text)
            self.assertIsNotNone(sha)
            self.assertNotIn("{materials}", text)


if __name__ == "__main__":
    unittest.main()

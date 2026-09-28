"""관계 패널 데이터화 (D-0032 작업 2·6, 08 §3 정돈된 관계선 규칙)."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

from engine.events import PanelRelation
from engine.panels import relation
from engine.refs import emblem_ids
from rules import RULES_PATH, load_rules
from schemas.rules_models import RelationPanelRules

FIX = Path(__file__).resolve().parent / "fixtures"


def _event(name: str) -> dict:
    return yaml.safe_load((FIX / name).read_text(encoding="utf-8"))["event"]


class RelationLintTest(unittest.TestCase):
    def test_eight_edges_warn_and_suggest_split(self) -> None:
        e = PanelRelation.model_validate(_event("relation/edges_8.yaml")).model_dump()
        self.assertEqual(len(relation.lint(e)), 1)
        sug = relation.split_suggestion(e)
        self.assertIsNotNone(sug)
        self.assertFalse(sug["applied"])   # 제안만(P8)
        self.assertEqual([len(p["edges"]) for p in sug["parts"]], [4, 4])
        self.assertTrue(all(len(p["edges"]) <= load_rules().panels.relation.max_edges for p in sug["parts"]))

    def test_seven_edges_clean(self) -> None:
        e = PanelRelation.model_validate(_event("relation/edges_7.yaml")).model_dump()
        self.assertEqual(relation.lint(e), [])
        self.assertIsNone(relation.split_suggestion(e))


class RelationModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ev = _event("preview/panel_relation.yaml")

    def test_unknown_edge_style_is_error(self) -> None:
        bad = copy.deepcopy(self.ev)
        bad["edges"][0]["style"] = "influence_typo"
        with self.assertRaises(ValidationError):
            PanelRelation.model_validate(bad)

    def test_state_change_without_edge_is_error(self) -> None:
        bad = copy.deepcopy(self.ev)
        bad["state_changes"][0]["dst"] = "nowhere"
        with self.assertRaises(ValidationError):
            PanelRelation.model_validate(bad)

    def test_edge_end_must_be_node(self) -> None:
        bad = copy.deepcopy(self.ev)
        bad["edges"][0]["dst"] = "ghost"
        with self.assertRaises(ValidationError):
            PanelRelation.model_validate(bad)

    def test_edges_start_after_all_nodes(self) -> None:
        """규칙 1 — 첫 선은 마지막 노드 등장 뒤. v3 값(2.2초)과 같다."""
        e = PanelRelation.model_validate(self.ev).model_dump()
        last_node = max(p[3] for p in relation.node_positions(e).values())
        self.assertGreater(relation.edge_start(e), last_node)
        self.assertAlmostEqual(relation.edge_start(e), 2.2, places=9)

    def test_target_column_centered_v3(self) -> None:
        e = PanelRelation.model_validate(self.ev).model_dump()
        pos = relation.node_positions(e)
        self.assertEqual([pos[c][1] for c in ("de", "gb", "jp", "au", "kr")], [138, 200, 262, 324, 386])
        self.assertEqual(pos["trump"][:2], (235, 262))

    def test_emblem_node_is_seen_by_rights_checks(self) -> None:
        e = copy.deepcopy(self.ev)
        e["nodes"].append(dict(id="navcent", group="target", kind="emblem", img="navcent", label="미 해군 중부사령부"))
        self.assertEqual(emblem_ids(PanelRelation.model_validate(e).model_dump()), ["navcent"])


class RelationRulesTest(unittest.TestCase):
    def test_rule_ranges_enforced(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["panels"]["relation"]
        for key, val in (("edge_dur_sec", 0.8), ("edge_gap_sec", 0.18)):   # v2 관계도 실패값(08 §3)
            bad = dict(raw, **{key: val})
            with self.assertRaises(ValidationError):
                RelationPanelRules.model_validate(bad)


if __name__ == "__main__":
    unittest.main()

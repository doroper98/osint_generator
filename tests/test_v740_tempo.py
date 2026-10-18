"""v7.4.0 back_and_forth D-0229 §2.9(UF-104·115) — 막 구조 [act-frame] 오류, 사실 문장 밀도 [tempo-density] 경고, order tempo: breath 문장 간격."""

from __future__ import annotations

import unittest

from rules import load_rules
from schemas.order_models import Order
from script.lint import act_frame_issues, tempo_density
from script.schema import Script
from script.timeline import layout, sentence_rows

T = load_rules().tempo
G = load_rules().layout_480p.timeline_gaps


def _sc(roles: list, kind: str = "act") -> Script:
    return Script.model_validate(dict(title="t", subtitle="s", date="2026.10.18", scenes=[
        dict(id="a", kind=kind, sentences=[dict(date="2026.10.15", text=f"문장{i}.", **({"role": r} if r else {})) for i, r in enumerate(roles)])]))


class ActFrameTest(unittest.TestCase):
    def test_missing_frame_hard(self) -> None:
        self.assertEqual([i.severity for i in act_frame_issues(_sc([None, None, None]))], ["error"])

    def test_frame_ok_bridge_counts_as_intro(self) -> None:
        self.assertEqual(act_frame_issues(_sc(["bridge", "intro", None, "outro"])), [])
        self.assertEqual(len(act_frame_issues(_sc(["intro", None, "outro"]))), 1)   # 도입 1 < 2

    def test_cold_ending_exempt(self) -> None:
        self.assertEqual(act_frame_issues(_sc([None], "cold")), [])
        self.assertEqual(act_frame_issues(_sc([None], "ending")), [])


class DensityTest(unittest.TestCase):
    def test_over_limit_warns(self) -> None:
        rows = [dict(sid=f"a_{i}", t0=i * 5.0, text="AP통신은 이렇게 보도했습니다.") for i in range(T.fact_sentences_per_min_max + 3)]
        self.assertEqual(len(tempo_density(rows)), 1)

    def test_spread_ok(self) -> None:
        rows = [dict(sid=f"a_{i}", t0=i * 12.0, text="AP통신은 이렇게 보도했습니다.") for i in range(20)]
        self.assertEqual(tempo_density(rows), [])

    def test_non_fact_not_counted(self) -> None:
        rows = [dict(sid=f"a_{i}", t0=i * 2.0, text="정유소가 멈췄습니다.") for i in range(30)]
        self.assertEqual(tempo_density(rows), [])


class GapTest(unittest.TestCase):
    def test_breath_gap(self) -> None:
        rows = sentence_rows(_sc(["intro", "intro", None, "outro"]))
        for x in rows:
            x["dur"] = 3.0
        a = [dict(r) for r in rows]
        b = [dict(r) for r in rows]
        layout(a)
        layout(b, None, T.sentence_gap_sec)
        self.assertAlmostEqual(a[1]["t0"] - a[0]["t1"], G.gap_sec)
        self.assertAlmostEqual(b[1]["t0"] - b[0]["t1"], T.sentence_gap_sec)

    def test_order_field(self) -> None:
        self.assertEqual(Order.model_fields["tempo"].default, "default")


if __name__ == "__main__":
    unittest.main()

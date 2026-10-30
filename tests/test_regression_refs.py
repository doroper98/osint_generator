"""v7.4.0 back_and_forth D-0311 — 회귀 기준 면제(qa_checks.regression_refs)는 폴더 이름이 아니라 프로젝트 id 로 판정한다.

g8 합성 사본(폴더 demo)이 fed_timeline_demo 면제를 못 받아 콘티 판 셋업이 hard 로 막히던 것(R-0289 §6)을 고친다.
면제는 hard 만 — 검사는 돌고 줄은 provenance regression_waived 에 남는다(D-0251·D-0271 원칙).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from engine import checks
from engine.direction import load_direction_doc

REPO = Path(__file__).resolve().parents[1]
QA = checks.QA


def _P(folder: str, pid: str | None) -> NS:  # noqa: N802
    return NS(root=Path("/x") / folder, R=NS(cache={} if pid is None else {"project_id": pid}))


class RegressionRefsTest(unittest.TestCase):
    def test_scope_fixed(self) -> None:
        """범위 고정 — 회귀 기준 둘(골든·엔진 데모)만. 새 영상·쇼케이스는 넣지 않는다."""
        self.assertEqual(sorted(QA.regression_refs), ["fed_timeline_demo", "hormuz_korea"])
        self.assertEqual(sorted(QA.regression_ref_checks), ["axis_empty_band", "chart_only_run", "media_density", "plot_height"])
        self.assertTrue(set(QA.regression_ref_checks) <= set(checks.HARD))

    def test_project_id_beats_folder_name(self) -> None:
        self.assertEqual(checks.regression_ref(_P("demo", "fed_timeline_demo")), "fed_timeline_demo")   # 합성 사본
        self.assertIsNone(checks.regression_ref(_P("hormuz_korea", "showcase_geo")))                    # id 가 이긴다
        self.assertEqual(checks.regression_ref(_P("hormuz_korea", None)), "hormuz_korea")               # 폴더 이름 폴백

    def test_waive_moves_lines_to_cache(self) -> None:
        P = _P("demo", "fed_timeline_demo")  # noqa: N806
        self.assertEqual(checks.waive_regression(P, "plot_height", ["[plot-height] x"]), [])
        self.assertEqual(P.R.cache["regression_waived"], {"plot_height": ["[plot-height] x"]})
        self.assertEqual(checks.waive_regression(P, "glyphs", ["[glyph] y"]), ["[glyph] y"])          # 목록 밖 검사는 그대로
        self.assertEqual(checks.waive_regression(_P("x", "showcase_econ"), "plot_height", ["z"]), ["z"])   # 새 영상은 면제 없음

    def test_regression_directions_carry_id(self) -> None:
        for pid in QA.regression_refs:
            self.assertEqual(load_direction_doc(REPO / "projects" / pid / "direction.yaml").project_id, pid)


if __name__ == "__main__":
    unittest.main()

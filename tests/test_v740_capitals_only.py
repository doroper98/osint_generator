"""디자인 시스템 지도의 배경 지명 — 도시는 수도만, 행정구역 이름 없음 (v7.4.0 사용자 의견 UF-918, D936).

사용자 원문(2026-11-17): "지도의 확대 되는 과정 혹은 축소 되는 씬에서 자꾸 도시 이름이 스케일에 따라 지정 되었는지 나왔다가 사라져. …
그냥 수도만 나오게 하고, 행정구역 표기가 필요하면 옅은 얇은 선으로만 보이게 해."
원인: 도시 이름 후보를 화면 폭(확대 정도)에 따른 등급 문턱으로 골랐다 — 카메라가 확대·축소하면 문턱이 바뀌어 도시가 나타났다 사라졌다.
"""

from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace

import numpy as np

from engine.layers import labels
from engine.layers.labels import city_candidates
from engine.stage import MERCATOR_LOD as LOD
from engine.stage import by_w
from rules import load_rules

A = SimpleNamespace(plc_rank=np.array([1, 2, 3, 5, 7, 8, 2, 6]),
                    plc_cap=np.array([True, False, True, False, False, True, False, False]),      # 1급 행정 중심 포함
                    plc_cap0=np.array([True, False, True, False, False, True, False, False]),     # 나라 수도 + 옛 수도·제2 수도(capital alt)
                    plc_cap_main=np.array([True, False, False, False, False, True, False, False]))  # 지금의 수도만
WIDTHS = (96, 66, 62, 48, 44, 30, 26, 14, 8, 4)


class CapitalsOnlyTest(unittest.TestCase):
    def test_rule_keys(self) -> None:
        r = load_rules().labels
        self.assertIs(r.capitals_only, True)
        self.assertIs(r.admin_names, False)

    def test_skin_map_shows_capitals_only_at_every_width(self) -> None:
        for w in WIDTHS:
            with self.subTest(w=w):
                cand = city_candidates(A, w, by_w(w, LOD["city_rank_max"]), True)
                self.assertTrue(np.array_equal(cand, A.plc_cap_main), "수도가 아닌 도시(옛 수도 포함)가 후보에 있다")

    def test_candidates_do_not_change_with_zoom(self) -> None:
        sets = {tuple(city_candidates(A, w, by_w(w, LOD["city_rank_max"]), True)) for w in WIDTHS}
        self.assertEqual(len(sets), 1, "확대·축소에 따라 도시 후보가 바뀐다(나타났다 사라진다)")

    def test_old_geo_asset_is_an_error_not_a_silent_fallback(self) -> None:
        old = SimpleNamespace(plc_rank=A.plc_rank, plc_cap=A.plc_cap, plc_cap0=A.plc_cap0, plc_cap_main=None)
        with self.assertRaisesRegex(ValueError, "cap_main"):
            city_candidates(old, 44, 2, True)

    def test_prep_marks_current_capital_only(self) -> None:
        src = inspect.getsource(__import__("geo.prep_geometry", fromlist=["x"]))
        self.assertIn('cap_main=(p.get("FEATURECLA") or "").lower() == "admin-0 capital"', src)

    def test_legacy_themes_keep_rank_lod(self) -> None:
        wide = city_candidates(A, 96, by_w(96, LOD["city_rank_max"]), False)
        near = city_candidates(A, 4, by_w(4, LOD["city_rank_max"]), False)
        self.assertGreater(int(near.sum()), int(wide.sum()), "옛 테마(회귀 기준 재현)는 종전 등급 문턱 그대로")

    def test_admin_names_are_not_drawn_on_skin_map(self) -> None:
        src = inspect.getsource(labels)
        self.assertIn("lr.admin_names or not on", src, "행정구역 이름 그리기가 규칙 키(labels.admin_names)를 보지 않는다")


if __name__ == "__main__":
    unittest.main()

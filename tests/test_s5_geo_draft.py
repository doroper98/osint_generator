"""v7.4.0 back_and_forth D-1000 S5 — 연출 LLM 초안의 출처 없는 좌표 제거.

① 연출 프롬프트에 좌표 규칙(rules geo.director_coords)이 실제로 들어간다(P3 — 프롬프트는 템플릿 + 규칙에서 생성).
② 저장 전 점검(check_direction)이 지명 사전과 대조하지 못한 place·marker 좌표를 오류로 돌려준다 — 렌더 검사 [geo-unsourced] 와 같은 목록.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from rules import load_rules


class DirectorPromptCoordsTest(unittest.TestCase):
    def test_rule_lines_in_director_prompt(self) -> None:
        from workers.prompt_loader import load_prompt

        r = load_rules()
        text = load_prompt("director", r)
        for ln in r.geo.director_coords:
            self.assertIn(ln, text)
        self.assertNotIn('`places: {"hormuz": [56.35, 26.55]}` 로 이름을 만들고', text)   # 옛 안내(좌표를 직접 만드는 예)
        self.assertNotIn("{{RULES.geo.director_coords}}", text)


class DraftGeoErrorsTest(unittest.TestCase):
    def _P(self, items: list[dict]) -> SimpleNamespace:  # noqa: N802
        return SimpleNamespace(R=SimpleNamespace(cache={"geo_check": {"unsourced": items}}))

    def test_place_and_marker_are_errors_path_is_not(self) -> None:
        from workers.direction_io import draft_geo_errors

        items = [{"kind": "place", "name": "가짜항", "lonlat": [50.0, 25.0]},
                 {"kind": "marker", "name": "events[3] 어딘가", "lonlat": [51.0, 26.0]},
                 {"kind": "path", "name": "항로", "points": 4, "ends": [[50, 25], [56, 26]]}]
        errs = draft_geo_errors(self._P(items))
        self.assertEqual(len(errs), 2)
        self.assertTrue(all(e.startswith("[geo-unsourced] ") for e in errs))
        self.assertEqual(set(load_rules().geo.draft_unsourced_error_kinds), {"place", "marker"})

    def test_all_sourced_passes(self) -> None:
        from workers.direction_io import draft_geo_errors

        self.assertEqual(draft_geo_errors(self._P([])), [])

    def test_wired_in_check_direction(self) -> None:
        import inspect

        from workers.direction_io import check_direction

        self.assertIn("draft_geo_errors(P)", inspect.getsource(check_direction))


if __name__ == "__main__":
    unittest.main()

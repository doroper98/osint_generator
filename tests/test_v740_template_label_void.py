"""v7.4.0 back_and_forth D-0312 — ③ 템플릿 표시 줄(UF-147)을 타이틀 부제 앞·엔딩 카드 머리 줄에, ① [scene-visual-void] hard.

① 카드를 지운 자리가 지도 + 자막뿐으로 남았다(showcase_geo 194·206초). 요소 없는 구간 ≥ qa_checks.visual_void_max_sec → hard.
③ template_label 은 경제 템플릿 브랜치(e2c37d71)와 같은 조판 함수 — 연출 template_label 이 장르 값보다 앞선다(쇼케이스용).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from engine import checks
from engine.direction import load_direction_doc
from engine.fullcards import TPL, template_label, title_subtitle

REPO = Path(__file__).resolve().parents[1]


class TemplateLabelTest(unittest.TestCase):
    def _R(self, lab: str | None, sub: str = "부제") -> NS:  # noqa: N802
        return NS(cache={"template_label": lab}, tb=NS(plan=NS(subtitle=sub)))

    def test_title_subtitle_prefix(self) -> None:
        self.assertEqual(title_subtitle(self._R("쇼케이스 템플릿 · 경제")), f"쇼케이스 템플릿 · 경제{TPL.sep}부제")
        self.assertEqual(title_subtitle(self._R(None)), "부제")          # 라벨 없으면 부제 그대로(골든 불변)
        self.assertIsNone(template_label(self._R(None)))

    def test_showcase_directions_carry_label(self) -> None:
        for pid, lab in (("showcase_geo", "쇼케이스 템플릿 · 지경학"), ("showcase_econ", "쇼케이스 템플릿 · 경제")):
            self.assertEqual(load_direction_doc(REPO / "projects" / pid / "direction.yaml").template_label, lab)
        self.assertIsNone(load_direction_doc(REPO / "projects/hormuz_korea/direction.yaml").template_label)


class VisualVoidTest(unittest.TestCase):
    def _P(self, events: list[dict], keys: list | None = None) -> NS:  # noqa: N802
        cards = [NS(kind="title", t0=2.0, t1=6.0), NS(kind="end", t0=40.0, t1=50.0)]
        return NS(events=events, keys=keys or [], plan=NS(total=50.0, cards=cards),
                  R=NS(tb=NS(in_fullcard=lambda t: any(c.t0 - 0.3 <= t <= c.t1 + 0.3 for c in cards))))

    def test_long_void_is_hard(self) -> None:
        ev = [{"type": "marker", "t0": 6.0, "t1": 20.0}, {"type": "photo", "t0": 27.0, "t1": 40.0}]
        prov: dict = {}
        out = checks.check_scene_visual_void(self._P(ev), prov)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[scene-visual-void] 20.0~27.0"), out)
        self.assertEqual(len(prov["visual_void"]), 1)
        self.assertIn("scene_visual_void", checks.HARD)

    def test_cold_open_move_and_country_rules(self) -> None:
        ev = [{"type": "marker", "t0": 6.0, "t1": 20.0}, {"type": "country", "t0": 20.0, "t1": 27.0}, {"type": "photo", "t0": 27.0, "t1": 40.0}]
        self.assertEqual(len(checks.check_scene_visual_void(self._P(ev))), 1)   # 나라 칠하기는 요소가 아니다(rules visual_void_types)
        move = NS(t=19.0, dur=6.0, mode="move")
        self.assertEqual(checks.check_scene_visual_void(self._P(ev, [move])), [])   # 이동 중은 끊긴다 → 남은 빈 구간 < 5초
        self.assertEqual(checks.visual_voids(self._P([{"type": "marker", "t0": 2.0, "t1": 40.0}]))[:1], [])   # 콜드 오픈(0~2초)은 보지 않는다

    def test_rules_keys(self) -> None:
        q = checks.QA
        self.assertEqual((q.visual_void_max_sec, q.visual_void_step_sec), (5, 0.1))
        self.assertNotIn("country", q.visual_void_types)


if __name__ == "__main__":
    unittest.main()

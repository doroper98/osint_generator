"""relief 지도 테마 정식(v7.4.0, back_and_forth D-0608 §1-3, 사용자 UF-250·UF-253).

- 이름 목록(GeoThemes.names)에 relief — 본편 stage_config.mercator.theme·geo.prep·sketch.war 가 같은 목록을 쓴다.
- 구상 칸(geo.themes.proposed)·MercatorStage(proposed_theme=) 는 삭제(P2) — 다시 들어오면 실패.
- 밝은 바탕 테마(light·relief)는 지도 글자 토큰(colors.themes)이 있어야 한다(없으면 흰 글자가 모래 위에 오른다).
- 전쟁사 장르 기본 = relief(UF-253). 없는 테마 = 오류.
"""

from __future__ import annotations

import inspect
import unittest

import yaml

from engine.stage import MercatorStage, StageError, mercator_theme
from genres.load import load_genre
from rules import load_rules
from tests.anti_inertia._ast_util import REPO


def _lum(rgb: str) -> float:
    c = [int(rgb.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


class ReliefThemeTest(unittest.TestCase):
    def test_relief_is_formal_name(self) -> None:
        th = load_rules().geo.themes
        self.assertEqual(th.names(), ["dark", "light", "relief"])
        self.assertIs(th.get("relief"), th.relief)
        self.assertEqual(mercator_theme({"theme": "relief"}), "relief")
        with self.assertRaises(StageError):
            mercator_theme({"theme": "sepia"})

    def test_proposed_slot_is_gone(self) -> None:
        raw = yaml.safe_load((REPO / "rules" / "video_rules.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("proposed", raw["geo"]["themes"])
        self.assertNotIn("proposed_theme", inspect.signature(MercatorStage.__init__).parameters)
        self.assertEqual(MercatorStage(config={"theme": "relief"}).theme_name, "relief")

    def test_light_ground_themes_have_text_tokens(self) -> None:
        r = load_rules()
        for name in r.geo.themes.names():
            if _lum(r.geo.themes.get(name).terrain.land_stops[0][1]) > 0.3:   # 밝은 저지
                self.assertIn(name, r.colors.themes, f"{name}: 밝은 바탕인데 colors.themes 토큰이 없다")

    def test_war_history_genre_default_relief(self) -> None:
        self.assertEqual(load_genre("war_history").stage.mercator["theme"], "relief")


if __name__ == "__main__":
    unittest.main()

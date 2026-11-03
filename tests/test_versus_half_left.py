"""versus 왼쪽 모음(v7.4.0 back_and_forth D-0629 §3, C0 같은 무게) — 모델·렌더·[card-over-panel] (세 곳 동시, 15 P10).

두 사료 패널의 한쪽 기둥을 사진 카드가 덮으면 양측 균형이 깨진다(15cf1736 칸나이 배치). 연출이 half_left_from 을 걸면
두 기둥이 왼쪽 짝 자리에 위아래로 모이고, 오른쪽 짝 자리 사진은 패널을 덮지 않는다.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import cairo
import numpy as np
import yaml

from engine import checks as C
from engine.events import PanelVersus
from engine.panels import versus as V

FIX = Path(__file__).resolve().parent / "fixtures" / "preview" / "war" / "panel_versus_half_left.yaml"
RIGHT_PAIR = (436.0, 100.0, 812.0, 389.0)   # map_pair_right 자리 슬로츠 상(세로 사진) 실측 상자


def _doc() -> dict:
    return yaml.safe_load(FIX.read_text(encoding="utf-8"))


def _render(e: dict, t: float) -> np.ndarray:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    ctx = cairo.Context(surf)
    V.draw(ctx, NS(cache={}), t, e, 1.0)
    surf.flush()
    return np.ndarray((480, 854, 4), np.uint8, surf.get_data()).copy()


class VersusHalfLeftTest(unittest.TestCase):
    def test_fixture_validates_and_drops_none(self) -> None:
        e = PanelVersus.model_validate(_doc()["event"])
        self.assertEqual(e.half_left_from, 8.0)
        plain = {k: v for k, v in _doc()["event"].items() if k != "half_left_from"}
        self.assertIsNone(PanelVersus.model_validate(plain).half_left_from)

    def test_layout_moves_left_and_stacks(self) -> None:
        e = _doc()["event"]
        before, after = _render(e, 7.0), _render(e, 12.0)
        right = slice(int(RIGHT_PAIR[0]) + 4, int(RIGHT_PAIR[2]))
        self.assertGreater(int(before[120:380, right, 3].astype(int).sum()), 0)     # 모으기 전 = 오른쪽 기둥이 있다
        self.assertEqual(int(after[100:389, right, 3].astype(int).sum()), 0)         # 모은 뒤 = 오른쪽 짝 자리 비어 있음
        x0, y0, x1, y1 = V.half_box()
        self.assertGreater(int(after[int(y0):int(y1), int(x0):int(x1), 3].astype(int).sum()), 0)
        hx, hy, hw, hh = V.half_frame()
        self.assertLessEqual(hy + 2 * hh + V.VS.half_left.gap, V.VS.half_left.bottom + 1e-6)

    def test_plain_versus_unchanged(self) -> None:
        """half_left_from 없는 versus 는 옛 자리(좌우 기둥) 그대로 — t 와 무관하게 u = 0."""
        e = {k: v for k, v in _doc()["event"].items() if k != "half_left_from"}
        self.assertEqual(V.half_u(100.0, e), 0.0)
        img = _render(e, 12.0)
        self.assertGreater(int(img[120:380, 450:794, 3].astype(int).sum()), 0)

    def test_overflow_is_error(self) -> None:
        e = _doc()["event"]
        e["sides"][0]["items"] = [{"text": f"항목 {i}", "t": 2.0} for i in range(6)]
        with self.assertRaises(V.VersusOverflowError):
            _render(e, 12.0)

    def test_card_over_panel(self) -> None:
        d = _doc()
        e, card = dict(d["event"]), dict(d["card"])
        boxes = lambda x: None  # noqa: E731
        media = lambda x: [RIGHT_PAIR]  # noqa: E731
        self.assertEqual(C.cards_over_panel([e, card], boxes, media), [])            # 모은 뒤에 들어온 카드 = 통과
        plain = {k: v for k, v in e.items() if k != "half_left_from"}
        self.assertEqual(len(C.cards_over_panel([plain, card], boxes, media)), 1)    # 15cf1736 배치 = 실패
        early = {**e, "half_left_from": 10.0}                                        # 카드가 모으기 전에 들어옴 = 실패
        self.assertEqual(len(C.cards_over_panel([early, card], boxes, media)), 1)


if __name__ == "__main__":
    unittest.main()

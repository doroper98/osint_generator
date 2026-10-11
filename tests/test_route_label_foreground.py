"""v5.22.6 D208 후속 — 전경 층(인용 초상·국기 뱃지·글자) 상자가 경로 이름표 장애물에 든다(gulf 240~245초: 국기 뱃지가 이름표 끝을 덮음)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import cairo
import numpy as np

from engine.layers.routes import foreground_boxes, place_route_label
from engine.quote import quote_box
from rules import load_rules

CTX = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
LIGHT = SimpleNamespace(theme=load_rules().geo.themes.light.map)
QUOTE = {"type": "quote", "t0": 10.0, "t1": 16.0, "flag": "sa", "speaker": "사우디 주도 연합군", "role": "연합군 성명",
         "text": "전면적 전쟁범죄", "src": "Al Jazeera", "date": "2026.10.10", "accent": "ru", "pos": "center"}


def _hits(a: tuple, b: tuple) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class TestForeground(unittest.TestCase):
    def test_quote_box_only_while_visible(self) -> None:
        self.assertIn(quote_box(CTX, QUOTE), foreground_boxes(CTX, [QUOTE], 13.0))
        self.assertEqual(foreground_boxes(CTX, [QUOTE], 9.0), [])
        self.assertEqual(foreground_boxes(CTX, [QUOTE], 16.5), [])

    def test_route_label_avoids_quote(self) -> None:
        qb = quote_box(CTX, QUOTE)
        cx, cy = (qb[0] + qb[2]) / 2, (qb[1] + qb[3]) / 2
        S = np.linspace((cx - 330, cy + 30), (cx + 330, cy - 30), 80)  # noqa: N806 — 인용 상자 한가운데를 가로지르는 궤적
        free = place_route_label(CTX, LIGHT, "탄도미사일 궤적 · 개략", S, [], [S])
        self.assertTrue(_hits(free[2], qb))   # 장애물이 없으면 원래 자리는 인용 위
        placed = place_route_label(CTX, LIGHT, "탄도미사일 궤적 · 개략", S, foreground_boxes(CTX, [QUOTE], 13.0), [S])
        self.assertTrue(placed[3])
        self.assertFalse(_hits(placed[2], qb))


if __name__ == "__main__":
    unittest.main()


class TestFixedSlot(unittest.TestCase):
    """v5.22.7 D209 — 이름표는 나타날 때 정한 후보 그대로, 나중에 나타난 전경 층에 가리면 흐린다."""

    def test_fade_only_under_foreground(self) -> None:
        from engine.layers.routes import label_fade

        qb = quote_box(CTX, QUOTE)
        inside = (qb[0] + 5, qb[1] + 5, qb[0] + 60, qb[1] + 20)
        outside = (qb[2] + 40, qb[1], qb[2] + 100, qb[1] + 15)
        self.assertEqual(label_fade(CTX, [QUOTE], 13.0, outside), 1.0)
        self.assertEqual(label_fade(CTX, [QUOTE], 13.0, inside), 0.0)   # 완전 불투명 구간 = 완전히 흐림
        self.assertEqual(label_fade(CTX, [QUOTE], 9.0, inside), 1.0)    # 인용 전

    def test_slot_ignores_new_obstacles(self) -> None:
        from engine.layers.routes import pick_route_label, slot_route_label

        qb = quote_box(CTX, QUOTE)
        cx, cy = (qb[0] + qb[2]) / 2, (qb[1] + qb[3]) / 2
        S = np.linspace((cx - 330, cy + 30), (cx + 330, cy - 30), 80)  # noqa: N806
        k, first = pick_route_label(CTX, LIGHT, "탄도미사일 궤적 · 개략", S, [], [S])
        later = slot_route_label(CTX, LIGHT, "탄도미사일 궤적 · 개략", S, k, foreground_boxes(CTX, [QUOTE], 13.0), [S])
        self.assertEqual(later[:3], first[:3])   # 장애물이 나중에 생겨도 자리는 그대로(통과 여부만 바뀐다)
        self.assertFalse(later[3])

    def test_label_jump_registered_hard(self) -> None:
        from engine.checks import HARD
        from rules import load_rules

        self.assertIn("label_jump", HARD)
        self.assertGreater(load_rules().qa_checks.label_jump_px, 0)

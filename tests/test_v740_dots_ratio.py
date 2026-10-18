"""v7.4.0 back_and_forth D-0229 §2.6(UF-113) — "N 중 M" 점 패널(total·accent·분수 big) + [ratio-without-graphic] warning."""

from __future__ import annotations

import types
import unittest

import cairo
import numpy as np
from pydantic import ValidationError

from engine.checks import ratio_graphic
from engine.events import PanelDots
from engine.panels import dots

PANEL = dict(type="panel", t0=0.0, t1=12.0, kind="dots", title="제재 대상 유조선", subtitle="일곱 척 · 열네 번 항해 · 가디언",
             provenance={"verification": "verified", "sources": ["가디언"]}, total=7, highlight=3, accent="ru", big="3 / 7",
             caption="영국·EU 제재 대상")


def _s(text: str, t0: float = 1.0, t1: float = 5.0, sid: str = "act2_10") -> types.SimpleNamespace:
    return types.SimpleNamespace(sid=sid, text=text, t0=t0, t1=t1)


class PanelTest(unittest.TestCase):
    def test_model(self) -> None:
        PanelDots.model_validate(PANEL)
        with self.assertRaises(ValidationError):
            PanelDots.model_validate(dict(PANEL, highlight=8))

    def test_render_seven_dots(self) -> None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
        R = types.SimpleNamespace(cache={}, stage=None)  # noqa: N806
        e = PanelDots.model_validate(PANEL).model_dump()
        dots.draw(cairo.Context(surf), R, 10.0, e, 1.0)
        a = np.frombuffer(surf.get_data(), np.uint8).reshape(480, -1, 4)[..., :3].astype(int)
        row = a[int(dots.D.few.y) - 2:int(dots.D.few.y) + 2 + 40, :520].sum(axis=2) > 0   # 한 줄 큰 점(본문은 태그 줄만큼 아래로 밀릴 수 있다)
        self.assertGreater(int(row.sum()), 0)


class RatioCheckTest(unittest.TestCase):
    def test_warns_without_graphic(self) -> None:
        self.assertEqual(len(ratio_graphic([_s("그 가운데 세 척은 영국·EU 제재 대상이었습니다.")], [])), 1)
        self.assertEqual(len(ratio_graphic([_s("유조선 일곱 척 중 세 척이 제재 대상입니다.")], [])), 1)

    def test_ok_with_dots(self) -> None:
        self.assertEqual(ratio_graphic([_s("그 가운데 세 척은 제재 대상이었습니다.")], [PANEL]), [])

    def test_no_ratio_sentence(self) -> None:
        self.assertEqual(ratio_graphic([_s("유조선이 울산을 떠났습니다.")], []), [])


if __name__ == "__main__":
    unittest.main()

"""프리미티브 site_diagram — 사건 현장 개념도(벡터) (v4.4.0, dmz_mine_2026 사용자 요청 2026-09-29).

불변 층: 출처·날짜·축척 표기 필수. 표시(marks)는 제 시각 전에는 그리지 않는다(폭발이 차례로 더해진다).
등장 배율은 연속 변환이라 상자는 매 프레임 같은 자리(예약 영역 고정).
"""

from __future__ import annotations

import unittest

import cairo
from pydantic import ValidationError

from engine.primitives import event_model, module, style_for
from genres.load import load_genre

MOD = module("site_diagram")
FX = MOD.PREVIEW_FIXTURE


def _render(t: float, e: dict) -> bytes:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    MOD.draw(cairo.Context(surf), None, t, e, style_for("site_diagram", load_genre("geopolitics").color_semantics))
    return bytes(surf.get_data())


class SiteDiagramTest(unittest.TestCase):
    def test_fixture_passes_schema(self) -> None:
        event_model("site_diagram", MOD.SCHEMA).model_validate(FX)

    def test_required_invariants(self) -> None:
        for k in ("source", "footnote"):
            with self.subTest(k=k), self.assertRaises(ValidationError):
                MOD.SCHEMA.model_validate({**{x: v for x, v in FX.items() if x not in ("type", "id", "t0", "t1")}, k: " "})
        with self.assertRaises(ValidationError):
            MOD.SCHEMA.model_validate({**{x: v for x, v in FX.items() if x not in ("type", "id", "t0", "t1")}, "date": "9월"})

    def test_marks_appear_in_order(self) -> None:
        """두 번째 폭발 시각 전후로 화면이 달라지고, 첫 폭발 뒤·두 번째 전 사이에는 두 번째가 없다."""
        b1, b2 = (m["t"] for m in FX["marks"] if m["kind"] == "burst")
        before, between, after = _render(b1 - 0.2, FX), _render((b1 + b2) / 2, FX), _render(b2 + 1.0, FX)
        self.assertNotEqual(before, between)
        self.assertNotEqual(between, after)
        no_second = {**FX, "marks": [m for m in FX["marks"] if m["t"] != b2]}
        self.assertEqual(_render((b1 + b2) / 2, no_second), between)

    def test_box_is_fixed(self) -> None:
        boxes = {MOD.draw(cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)), None, t, FX,
                          style_for("site_diagram", load_genre("geopolitics").color_semantics)) for t in (0.1, 3.0, 8.9, 20.0)}
        self.assertEqual(len(boxes), 1)


if __name__ == "__main__":
    unittest.main()

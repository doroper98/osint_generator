"""프리미티브 era_numeral — 큰 연도 숫자(옅게, 굴러 바뀜) (v7.4.0, 사용자 결정 UF-401 ③ · 영상 분석 D7).

불변 층: 문구는 네 자리 연도를 품는다(지어낸 연도 금지 — 원고 날짜의 해). 바뀜은 roll_sec 안에서 끝나고, 예약 상자는 점 하나
(배경 글자 — 뱃지·카드를 밀어내지 않는다).
"""

from __future__ import annotations

import copy
import unittest

import cairo
from pydantic import ValidationError

from engine.primitives import event_model, module, style_for
from engine.primitives.era_numeral import current
from engine.style import PRIMITIVES
from genres.load import load_genre

MOD = module("era_numeral")
FX = MOD.PREVIEW_FIXTURE
L = PRIMITIVES["era_numeral"]


def _render(t: float, e: dict) -> bytes:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    MOD.draw(cairo.Context(surf), None, t, e, style_for("era_numeral", load_genre("political_history").color_semantics))
    return bytes(surf.get_data())


class EraNumeralTest(unittest.TestCase):
    def test_fixture_passes_schema(self) -> None:
        event_model("era_numeral", MOD.SCHEMA).model_validate(FX)

    def test_invalid_data_is_error(self) -> None:
        bad = {"no year": [{"t": 0.0, "label": "그해 봄"}], "too long": [{"t": 0.0, "label": "1976년 가을 무렵 즈음"}],
               "order": [{"t": 3.0, "label": "1979년"}, {"t": 1.0, "label": "1980년"}], "empty": []}
        for why, steps in bad.items():
            with self.subTest(why=why), self.assertRaises(ValidationError):
                MOD.SCHEMA.model_validate({"steps": steps})

    def test_roll_finishes(self) -> None:
        e = copy.deepcopy(FX)
        t2 = e["steps"][1]["t"]
        self.assertEqual(current(e, t2 - 0.01)[0], 0)
        k, p = current(e, t2 + L.roll_sec / 2)
        self.assertEqual(k, 1)
        self.assertTrue(0 < p < 1)
        self.assertEqual(current(e, t2 + L.roll_sec)[1], 1.0)
        self.assertNotEqual(_render(t2 + L.roll_sec / 2, e), _render(t2 + L.roll_sec, e))

    def test_reserves_a_point_only(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        x0, y0, x1, y1 = MOD.draw(ctx, None, 2.0, FX, style_for("era_numeral", load_genre("political_history").color_semantics))
        self.assertEqual((x0, y0), (x1, y1), "배경 글자는 뱃지·카드를 밀어내지 않는다")


if __name__ == "__main__":
    unittest.main()

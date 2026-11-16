"""v7.4.0 사용자 결정 UF-401 ③-3 — 사진·영상 속 점선 원(spot, 영상 분석 D15).

spot 은 photo·clip 의 선택 필드. 안 쓰면 dict 옛 모양. 원은 t 전에는 없고 draw_sec 동안 그어진다. dim 은 원 밖만 어둡게(원 안 화소는 그대로).
"""

from __future__ import annotations

import unittest

import cairo

from engine.layers.media import SPOT, draw_spot
from engine.registry import RegistryError, validate_events

PH = {"type": "photo", "t0": 0.0, "t1": 8.0, "mid": "m1"}


def _surf(e: dict, t: float) -> cairo.ImageSurface:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 140)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0.6, 0.6, 0.6)
    ctx.paint()
    draw_spot(ctx, t, e, 0, 0, 200, 125, 1.0)
    surf.flush()
    return surf


def _px(s: cairo.ImageSurface, x: int, y: int) -> bytes:
    i = y * s.get_stride() + x * 4
    return bytes(s.get_data()[i:i + 4])


class MediaSpotTest(unittest.TestCase):
    def test_plain_media_dict_unchanged(self) -> None:
        for e in (PH, {**PH, "type": "clip"}):
            with self.subTest(type=e["type"]):
                self.assertNotIn("spot", validate_events([e])[0])

    def test_spot_validated(self) -> None:
        self.assertEqual(validate_events([{**PH, "spot": {"x": 0.5, "y": 0.4, "r": 0.12, "t": 2.0}}])[0]["spot"]["r"], 0.12)
        for bad in ({"x": 1.2, "y": 0.4, "r": 0.1}, {"x": 0.5, "y": 0.4, "r": 0.0}, {"x": 0.5, "y": 0.4, "r": 0.1, "color": "red"}):
            with self.subTest(spot=bad), self.assertRaises(RegistryError):
                validate_events([{**PH, "spot": bad}])

    def test_circle_waits_then_draws(self) -> None:
        e = {**PH, "spot": {"x": 0.5, "y": 0.5, "r": 0.2, "t": 2.0}}
        blank = bytes(_surf(PH, 3.0).get_data())
        self.assertEqual(bytes(_surf(e, 1.9).get_data()), blank)
        self.assertNotEqual(bytes(_surf(e, 2.0 + SPOT.draw_sec / 3).get_data()), bytes(_surf(e, 2.0 + SPOT.draw_sec).get_data()))

    def test_dim_only_outside(self) -> None:
        e = {**PH, "spot": {"x": 0.5, "y": 0.5, "r": 0.2, "dim": True}}
        s, base = _surf(e, 5.0), _surf(PH, 5.0)
        self.assertEqual(_px(s, 100, 62), _px(base, 100, 62), "원 안 화소는 그대로")
        self.assertNotEqual(_px(s, 10, 10), _px(base, 10, 10), "원 밖은 어둡게")


if __name__ == "__main__":
    unittest.main()

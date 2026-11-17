"""v7.4.0 4b-2(UF-903·UF-906, C0.0) — skin 지도 위 요소(rules skin.map_overlays).

- 지도 마커: 흰 알약 라벨(밝은 면·짙은 잉크 글자·테두리 없음), 번호 마커 = 강조 원 + 흰 숫자. 상자 함수(marker_box·marker_text_boxes)가 그린 알약을 보고한다.
- skin 이 꺼지면 지도 마커 상자는 종전 식 그대로.
- island_boxes: skin 지도에서는 패널(흰 카드 = island.panel_box)만, skin 꺼진 지도 = [].
- 지도 위 패널 = 흰 장막 + 흰 카드(어두운 덮개 없음). 자막·날짜 번짐 = 지도에서만 map_overlays 토큰(스튜디오 = None).
설계 해상도 854×480(k = 1), 합성 컨텍스트.
"""

from __future__ import annotations

import types
import unittest

import cairo
import numpy as np
import pydantic

from engine import skin
from engine.island import island_boxes
from engine.layers import markers
from engine.style import ISLAND, SKIN, apply_palette
from rules import load_rules
from schemas.rules_models import SkinMapOverlays

W, H = 854, 480
BG = (0.80, 0.80, 0.82)   # 지도 비슷한 중간 회색 바탕


def _skin(on: bool) -> None:
    skin.apply("mercator" if on else None, "porcelain")
    apply_palette(SKIN.palette if on else None)


def _canvas() -> tuple[cairo.ImageSurface, cairo.Context]:
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*BG)
    ctx.paint()
    return surf, ctx


def _img(surf: cairo.ImageSurface) -> np.ndarray:
    surf.flush()
    a = np.ndarray((H, surf.get_stride() // 4, 4), np.uint8, buffer=surf.get_data())[:, :W, [2, 1, 0]]
    return a.astype(float) / 255


class MapOverlaysRulesTest(unittest.TestCase):
    def test_strict(self) -> None:
        d = load_rules().skin.map_overlays.model_dump()
        with self.assertRaises(pydantic.ValidationError):
            SkinMapOverlays.model_validate({**d, "vignette": True})
        with self.assertRaises(pydantic.ValidationError):
            SkinMapOverlays.model_validate({**d, "quote_veil_alpha": 1.5})


class MapMarkerTest(unittest.TestCase):
    def tearDown(self) -> None:
        _skin(False)

    def _draw(self, e: dict, x: float = 300.0, y: float = 240.0) -> tuple[np.ndarray, types.SimpleNamespace]:
        surf, ctx = _canvas()
        R = types.SimpleNamespace(zones=[], reserved=[])  # noqa: N806
        markers._draw_map_marker(ctx, R, e["t0"] + 3.0, e, x, y, 1.0)
        return _img(surf), R

    def test_pill_label_light_with_ink(self) -> None:
        _skin(True)
        e = {"type": "marker", "t0": 0.0, "t1": 9.0, "lon": 51.5, "lat": 25.3, "label": "도하", "sub": "카타르", "side": "right"}
        self.assertTrue(markers.map_skin(e))
        im, R = self._draw(e)
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        x0, y0, x1, y1 = markers.map_pill_rect(ctx, e, 300.0, 240.0)
        self.assertGreater(x0, 300.0)                                   # 오른쪽 알약
        self.assertEqual(markers.marker_text_boxes(ctx, e, 300.0, 240.0), [(x0, y0, x1, y1)])
        bx = markers.marker_box(ctx, e, 300.0, 240.0)
        self.assertTrue(bx[0] <= x0 and bx[1] <= y0 and bx[2] >= x1 and bx[3] >= y1)
        self.assertEqual(R.reserved, [bx])
        lum = im[int(y0) + 2:int(y1) - 2, int(x0) + 3:int(x1) - 3].mean(2)
        self.assertGreaterEqual(float(lum.mean()), 0.85)                 # 밝은 알약(어두운 상자 아님)
        self.assertLess(float(lum.min()), 0.35)                          # 짙은 잉크 글자
        self.assertGreaterEqual(float(lum.max()), 0.98)                  # 흰 면(테두리 halo 아님)

    def test_sides(self) -> None:
        _skin(True)
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        base = {"type": "marker", "t0": 0.0, "t1": 9.0, "lon": 51.5, "lat": 25.3, "label": "호르무즈 해협"}
        left = markers.map_pill_rect(ctx, {**base, "side": "left"}, 300.0, 240.0)
        top = markers.map_pill_rect(ctx, {**base, "side": "top"}, 300.0, 240.0)
        bot = markers.map_pill_rect(ctx, {**base, "side": "bottom"}, 300.0, 240.0)
        self.assertLess(left[2], 300.0)
        self.assertLess(top[3], 240.0)
        self.assertGreater(bot[1], 240.0)
        self.assertAlmostEqual((top[0] + top[2]) / 2, 300.0)
        edge = markers.map_pill_rect(ctx, {**base, "side": "top"}, 2.0, 240.0)   # 화면 밖 알약은 안쪽으로 민다
        self.assertGreaterEqual(edge[0], markers.CENTER_PAD)

    def test_numbered_marker(self) -> None:
        _skin(True)
        e = {"type": "marker", "t0": 0.0, "t1": 9.0, "lon": 56.3, "lat": 26.5, "label": "호르무즈 해협", "side": "bottom", "num": 1}
        im, _ = self._draw(e)
        N = SKIN.map_overlays.marker.num  # noqa: N806
        ring = im[240, int(300 - N.r + 2)]
        self.assertGreater(ring[0], 0.85)                                 # 강조(주황) 원
        self.assertLess(ring[2], 0.45)
        num = im[240 - int(N.r * 0.6):240 + int(N.r * 0.6), 297:304]
        self.assertGreater(float(num.min(2).max()), 0.9)                  # 흰 숫자
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertGreater(markers.map_pill_rect(ctx, e, 300.0, 240.0)[1], 240.0 + N.r)   # 알약 = 번호 원 아래

    def test_off_skin_box_unchanged(self) -> None:
        _skin(False)
        e = {"type": "marker", "t0": 0.0, "t1": 9.0, "lon": 51.5, "lat": 25.3, "label": "도하", "side": "right"}
        self.assertFalse(markers.map_skin(e))
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        w = markers.tw(ctx, "도하", markers.MK.label_size, "sansb") + 20
        self.assertEqual(markers.marker_box(ctx, e, 300.0, 240.0), (286.0, 224.0, 300.0 + w, 266.0))

    def test_island_and_pin_markers_not_map(self) -> None:
        _skin(True)
        self.assertFalse(markers.map_skin({"label": "a", "lat": 1.0, "in_island": True}))
        self.assertFalse(markers.map_skin({"label": "a", "date": "2026-01-01", "lane": "x"}))


class MapIslandBoxesTest(unittest.TestCase):
    def tearDown(self) -> None:
        _skin(False)

    def test_panels_only_on_skin_map(self) -> None:
        evs = [{"type": "panel", "kind": "versus", "t0": 1.0, "t1": 5.0},
               {"type": "photo", "mid": "x", "t0": 1.0, "t1": 5.0}]
        _skin(False)
        self.assertEqual(island_boxes(evs, {}, "mercator"), [])
        _skin(True)
        out = island_boxes(evs, {}, "mercator")
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0][0].startswith("panel versus"))
        self.assertEqual(tuple(out[0][3]), tuple(ISLAND.panel_box))


class MapPanelGlowTest(unittest.TestCase):
    def tearDown(self) -> None:
        _skin(False)

    def test_panel_on_map_light(self) -> None:
        from engine.panels.base import make_panel_renderer  # noqa: PLC0415

        _skin(True)
        stage = types.SimpleNamespace(name="mercator", theme_name="porcelain")
        render = make_panel_renderer(lambda ctx, R, t, e, a: None)  # noqa: N803
        surf, ctx = _canvas()
        render(ctx, types.SimpleNamespace(stage=stage), 3.0, {"t0": 0.0, "t1": 9.0})
        im = _img(surf)
        x, y, w, h = ISLAND.panel_box
        self.assertGreaterEqual(float(im[int(y) + 4:int(y + h) - 4, int(x) + 4:int(x + w) - 4].mean()), 0.95)   # 흰 카드
        out = float(im[5:20, 5:20].mean())
        self.assertGreater(out, float(np.mean(BG)))                       # 카드 밖 = 흰 장막(어두운 덮개 아님)

    def test_glow_tokens_map_only(self) -> None:
        from engine.hud import _on_map  # noqa: PLC0415
        from engine.subtitles import _map_glow  # noqa: PLC0415

        _skin(True)
        R = types.SimpleNamespace(stage=types.SimpleNamespace(name="mercator", theme_name="porcelain"))  # noqa: N806
        self.assertIs(_map_glow(R), SKIN.map_overlays.subtitle_glow)
        self.assertTrue(_on_map(R))
        S = types.SimpleNamespace(stage=types.SimpleNamespace(name="studio", theme_name=None))  # noqa: N806
        self.assertIsNone(_map_glow(S))
        self.assertFalse(_on_map(S))


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 back_and_forth D-0229 §2.5(UF-112) — 굴절 항로(declared): 꺾임점 앞 = muted 점선 + 신고 라벨, 뒤 = 이벤트 col 실선."""

from __future__ import annotations

import types
import unittest
from unittest import mock

import cairo
import numpy as np
from pydantic import ValidationError

from engine.events import RouteEvent
from engine.layers import routes as rt
from engine.projection import View
from engine.stage import MercatorStage, ym

TIERS = {"W": {"lon0": 120.0, "lat0": 30.0, "lon1": 145.0, "lat1": 48.0}}
PTS = [(129.4, 35.5), (138.2, 38.3), (131.9, 43.1)]   # 울산 → 니가타 앞바다 → 블라디보스토크


def _e(**kw: object) -> dict:
    e = dict(type="route", t0=0.0, t1=20.0, pts=PTS, grow=4.0, col="ru", label="레일라호",
             declared=dict(label="신고: 니가타", bend_index=1, place="니가타"))
    e.update(kw)
    return e


class SchemaTest(unittest.TestCase):
    def test_valid(self) -> None:
        RouteEvent.model_validate(_e())

    def test_bend_must_be_interior(self) -> None:
        for b in (0, 2):
            with self.assertRaises(ValidationError):
                RouteEvent.model_validate(_e(declared=dict(label="신고: 니가타", bend_index=b)))


class DrawTest(unittest.TestCase):
    def _draw(self, t: float) -> tuple[list, list]:
        st = MercatorStage(tiers=TIERS)
        view = View(st, np.array([134.0, ym(39.0), 20.0]))
        e = _e()
        e["world_pts"] = [st.to_world(lon=x, lat=y) for x, y in e["pts"]]
        lines: list = []
        labels: list = []
        real = rt.glow_line

        def rec(ctx, S_, col, a, w, dash=None, casing=None):  # noqa: ANN001, ANN202, N803
            lines.append((len(S_), tuple(col), dash, np.asarray(S_)))
            return real(ctx, S_, col, a, w, dash, casing)

        R = types.SimpleNamespace(cache={}, reserved=[])  # noqa: N806
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
        with mock.patch.object(rt, "glow_line", rec), mock.patch.object(rt, "text", lambda c, s, x, y, *a, **k: labels.append((s, x, y)) or 0):
            rt.draw_route(ctx, R, view, t, e)
        return lines, labels, view, st

    def test_dashed_then_solid_with_label_near_bend(self) -> None:
        lines, labels, view, st = self._draw(10.0)
        self.assertEqual(len(lines), 2)
        (n0, c0, d0, s0), (n1, c1, d1, s1) = lines
        self.assertEqual(d0, [5, 4])          # 신고 구간 점선
        self.assertIsNone(d1)                 # 실제 구간 실선
        self.assertNotEqual(c0, c1)           # muted ↔ ru
        bx, by = view.to_screen(*st.to_world(lon=138.2, lat=38.3))
        self.assertTrue(np.allclose(s0[-1], (bx, by), atol=1e-6))   # 점선 끝 = 꺾임점
        self.assertTrue(np.allclose(s1[0], (bx, by), atol=1e-6))    # 실선 시작 = 꺾임점
        lab = [x for x in labels if x[0] == "신고: 니가타"]
        self.assertEqual(len(lab), 1)
        self.assertLess(abs(lab[0][1] - bx) + abs(lab[0][2] - by), 30)

    def test_before_bend_only_dashed(self) -> None:
        lines, _, _, _ = self._draw(0.8)
        self.assertEqual([d for _, _, d, _ in lines], [[5, 4]])


if __name__ == "__main__":
    unittest.main()

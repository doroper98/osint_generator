"""v5.22.10 D-0201 결정 2 — 국경 경로 일괄(numpy) 생성이 종전 한 고리씩 생성과 cairo 경로(점·순서·닫힘)가 같다."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import cairo
import numpy as np

from engine.layers.borders import path_lines, path_rings


def _ref(ctx: cairo.Context, view, items: list, min_px: float, close: bool) -> int:  # noqa: ANN001 — v5.22.9 까지의 구현 그대로
    n = 0
    for uv, mn, mx in items:
        if not view.visible(mn, mx) or (mx - mn).max() * view.s < min_px:
            continue
        pts = view.to_screen_arr(uv)
        ctx.move_to(*pts[0])
        for x, y in pts[1:]:
            ctx.line_to(x, y)
        if close:
            ctx.close_path()
        n += 1
    return n


class _View:
    def __init__(self, x0: float, y1: float, w: float, h: float, s: float) -> None:
        self.x0, self.y1, self.w, self.h, self.s, self.sy = x0, y1, w, h, s, s * 1.0003

    def to_screen_arr(self, xy: np.ndarray) -> np.ndarray:
        return np.column_stack([(xy[:, 0] - self.x0) * self.s, (self.y1 - xy[:, 1]) * self.sy])

    def visible(self, mn: np.ndarray, mx: np.ndarray) -> bool:
        return not (mx[0] < self.x0 or mn[0] > self.x0 + self.w or mx[1] < self.y1 - self.h or mn[1] > self.y1)


def _items(seed: int) -> list:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(300):
        c = rng.uniform(-50, 50, 2)
        uv = c + rng.normal(0, rng.uniform(0.01, 4), (int(rng.integers(3, 40)), 2))
        out.append((uv, uv.min(axis=0), uv.max(axis=0)))
    return out


class TestBorderPaths(unittest.TestCase):
    def test_same_cairo_path(self) -> None:
        items = _items(7)
        for x0, y1, w, h, s in ((-60, 60, 120, 70, 7.0), (-10, 20, 15, 9, 55.0), (30, 0, 4, 2, 210.0), (200, 200, 5, 5, 9.0)):
            v = _View(x0, y1, w, h, s)
            for mp in (0.0, 1.0, 2.0):
                for fn, close in ((path_rings, True), (path_lines, False)):
                    a = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))
                    b = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))
                    self.assertEqual(fn(a, v, items, mp), _ref(b, v, items, mp, close))
                    self.assertEqual(list(a.copy_path()), list(b.copy_path()))

    def test_empty(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))
        self.assertEqual(path_rings(ctx, _View(0, 0, 1, 1, 1.0), [], 1.0), 0)


if __name__ == "__main__":
    unittest.main()

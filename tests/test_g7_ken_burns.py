"""G7 사진 켄 번스 연속 변환 (v4.8.0, back_and_forth D-0104 D6 — R-0119 S8 계단 결함)."""

from __future__ import annotations

import inspect
import unittest

import cairo
import numpy as np
from PIL import Image

from engine.assets import surf_from_pil
from engine.layers import media
from engine.layers.media import KEN_BURNS_MAX, ken_burns_source


def _frame(src: cairo.ImageSurface, k: float, w: int = 280, h: int = 175) -> np.ndarray:
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    c = cairo.Context(s)
    ken_burns_source(c, src, 0, 0, w, h, k)
    c.paint()
    s.flush()
    return np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :w, :3].astype(float)


class KenBurnsTest(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(7)
        img = (rng.random((450, 720, 3)) * 255).astype("uint8")
        img[::9, :, :] = 255          # 글자처럼 가는 선 — 계단이 잘 보이는 무늬
        self.src, self._buf = surf_from_pil(Image.fromarray(img))

    def test_continuous_no_steps(self) -> None:
        """프레임 사이 차이가 고르다 — 옛 3px 양자화는 몇 프레임마다 한 번 크게 튀었다(최대/평균 ≫ 1)."""
        n = 120
        ks = [1 + (KEN_BURNS_MAX - 1) * i / n for i in range(n + 1)]
        fr = [_frame(self.src, k) for k in ks]
        d = np.array([np.abs(fr[i + 1] - fr[i]).mean() for i in range(n)])
        self.assertLess(d.max() / d.mean(), 2.0, d)

    def test_scale_matches_k(self) -> None:
        """끝 배율 KEN_BURNS_MAX 가 실제로 적용된다(첫 프레임과 다르다)."""
        f1, f2 = _frame(self.src, 1.0), _frame(self.src, KEN_BURNS_MAX)
        self.assertGreater(np.abs(f1 - f2).mean(), 1.0)

    def test_draw_photo_uses_original_surface(self) -> None:
        src = inspect.getsource(media.draw_photo)
        self.assertIn("original(", src)
        self.assertNotIn("raster(", src)


if __name__ == "__main__":
    unittest.main()

"""장치 변환 렌더 (v3.6.0, back_and_forth D-0066 작업 2·4, D-0067 A).

모든 레이어는 설계 좌표(854×480)로 그리고, 렌더 진입의 `translate(pad_x)·scale(k)` 한 번이 장치 해상도를 맡는다.
- k=1 항등: 변환을 걸지 않고 래스터도 예전 호출 그대로
- 글자 폭 측정은 480p 측정 컨텍스트 → 줄바꿈·카드 폭·자막 줄 수가 해상도와 무관
- 위치(뱃지·마커 상자)는 설계 좌표라 두 프로파일에서 같다
"""

from __future__ import annotations

import unittest
from pathlib import Path

import cairo
import numpy as np

from engine.assets import set_raster
from engine.checks import missing_fonts
from engine.style import SUBTITLE, SUBTITLE_WRAP_PX, output_profile
from engine.typography import tw, wrap

_MISSING = missing_fonts()
HORMUZ = Path(__file__).resolve().parent.parent / "projects" / "hormuz_korea"
_HAS_HORMUZ = (HORMUZ / "assets" / "tiers.pkl").exists() and (HORMUZ / "plan.json").exists()
_WHY_HORMUZ = "hormuz 자산 없음 — `fetch_data`·`geo.prep projects/hormuz_korea`·phase7 artifacts 복원(run_log §0)"


def _ctx(k: float = 1.0, w: int = 64, h: int = 64) -> cairo.Context:
    c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, w, h))
    if k != 1:
        c.scale(k, k)
    return c


class RasterTest(unittest.TestCase):
    def _img(self) -> cairo.ImageSurface:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8)
        c = cairo.Context(s)
        c.set_source_rgb(1, 0, 0)
        c.paint()
        return s

    def test_k1_is_set_source_surface(self) -> None:
        a, b = _ctx(), _ctx()
        img = self._img()
        a.set_source_surface(img, 3.5, 2.25)
        set_raster(b, img, 1.0, 3.5, 2.25)
        self.assertEqual(tuple(a.get_source().get_matrix()), tuple(b.get_source().get_matrix()))

    def test_device_pattern_matrix(self) -> None:
        """k 배 표면을 설계 좌표 (x, y) 에 — 사용자 좌표 u 는 패턴 좌표 k·(u − x) 로."""
        c = _ctx()
        set_raster(c, self._img(), 2.25, 10.0, 4.0)
        m = c.get_source().get_matrix()
        self.assertEqual(m.transform_point(10.0, 4.0), (0.0, 0.0))
        self.assertEqual(m.transform_point(14.0, 8.0), (9.0, 9.0))

    def test_device_raster_fills_same_design_box(self) -> None:
        """k=2.25 장치 표면(설계 8px → 18px)을 scale(k) 컨텍스트에 그리면 장치 18px 을 채운다(업스케일 없음)."""
        k = 2.25
        dev = cairo.ImageSurface(cairo.FORMAT_ARGB32, 18, 18)
        c = cairo.Context(dev)
        c.scale(k, k)
        src = cairo.ImageSurface(cairo.FORMAT_ARGB32, 18, 18)
        s2 = cairo.Context(src)
        s2.set_source_rgb(0, 1, 0)
        s2.paint()
        set_raster(c, src, k, 0, 0)
        c.paint()
        dev.flush()
        a = np.frombuffer(dev.get_data(), np.uint8).reshape(18, 18, 4)
        self.assertTrue((a[..., 1] == 255).all())


@unittest.skipIf(_MISSING, f"글꼴 없음 {_MISSING} — `python tools/fetch_data.py fonts`")
class MeasureTest(unittest.TestCase):
    def test_tw_independent_of_ctm(self) -> None:
        for s, size, name in (("정부, 전투 격화·반대 여론 확산에", 13, "sansm"), ("2026. 09. 07", 15, "mono"),
                              ("호르무즈와 한국", 46, "disp"), ("The Korea Herald", 12, "serifb")):
            self.assertEqual(tw(_ctx(2.25), s, size, name), tw(_ctx(), s, size, name), s)

    def test_subtitle_lines_same(self) -> None:
        """자막 줄 수(린트·렌더 공유 wrap)가 해상도와 무관 — 1080p 에서 줄이 늘거나 줄지 않는다."""
        s = "9월 7일, 정부는 전투가 격해지고 반대 여론이 커지자 계획을 다시 조정하기 시작했습니다. 국방부는 협의 중이라고 밝혔습니다."
        self.assertEqual(wrap(_ctx(2.25), s, SUBTITLE_WRAP_PX, SUBTITLE.size, "sansm"),
                         wrap(_ctx(), s, SUBTITLE_WRAP_PX, SUBTITLE.size, "sansm"))


@unittest.skipIf(not _HAS_HORMUZ or _MISSING, _WHY_HORMUZ if not _HAS_HORMUZ else f"글꼴 없음 {_MISSING}")
class HormuzScaleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project  # noqa: PLC0415

        cls.P480 = load_project(HORMUZ)
        cls.P1080 = load_project(HORMUZ, out=output_profile("1080p"))

    def test_positions_identical(self) -> None:
        """위치 비율(D-0067 요건 4-③): 뱃지·마커 상자(place_over)가 두 프로파일에서 같다(설계 좌표 불변)."""
        from engine.checks import place_over  # noqa: PLC0415

        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        n = 0
        for e in [e for e in self.P480.events if e["type"] in ("badge", "marker")]:
            t = (e["t0"] + e["t1"]) / 2
            a, b = place_over(self.P480, c, e, t), place_over(self.P1080, c, e, t)
            self.assertEqual(a, b, e.get("label"))
            n += a is not None
        self.assertGreater(n, 5)

    def test_frame_size_and_identity(self) -> None:
        from engine.render import render_frame  # noqa: PLC0415

        i = int(22.27 * 24)
        s480, _ = render_frame(self.P480, i)
        s1080, _ = render_frame(self.P1080, i)
        self.assertEqual((s480.get_width(), s480.get_height()), (854, 480))
        self.assertEqual((s1080.get_width(), s1080.get_height()), (1920, 1080))


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 4b(UF-903·UF-906, C0.0) — skin 지도(porcelain): 켜기·지명·국기 채움·단색 채움·바다 점.

- skin.apply(mercator, 지도 테마) — rules skin.map_themes 안의 테마면 켠다, 옛 테마(dark·light·slate)는 끈 채 종전 그대로.
- 지명: 도시 = 굵지 않은 잉크 + 밝은 halo(대비 ≥ map_contrast_text), 국기로 채운 나라 이름 = 흰 알약(밝은 상자, 짙은 글자).
- 국기 채움: 평지의 국기 흰 면 ≥ 235(흰 땅 아래로 가라앉지 않는다), 오른쪽 아래 부드러운 그림자, 흰 테.
- 단색 채움: 옅은 틴트(alpha_max) + 가는 윤곽 한 줄.
- 바다 점: 바다에만(육지가 덮는다), 화면 간격 [lo, 2·lo], 단 전환에서 튀지 않는다(전환 앞뒤 같은 점·알파).
- skin 이 꺼지면(옛 테마·studio 아닌 무대) 점·알약 없음.
합성 무대(네트워크 자산 없음), 설계 해상도 854×480(k = 1).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cairo
import numpy as np
import pydantic
from PIL import Image

import geo.prep_tiers as pt
from engine import skin, typography
from engine.assets import Assets, Labels
from engine.checks import QA, measure_contrast
from engine.layers.areas import draw_country
from engine.projection import View
from engine.registry import validate_events
from engine.stage import MercatorStage, sea_dot_grid, skin_map, ym
from engine.style import SKIN, apply_palette
from rules import load_rules
from schemas.rules_models import SkinMap, SkinMapSeaDots

W, H = 854, 480


def _ring(lon0: float, lat0: float, lon1: float, lat1: float) -> np.ndarray:
    return np.array([[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]], dtype=float)


def _skin(on: bool) -> None:
    skin.apply("mercator" if on else None, "porcelain")
    apply_palette(SKIN.palette if on else None)


class SkinMapRulesTest(unittest.TestCase):
    def test_strict(self) -> None:
        d = load_rules().skin.map.model_dump()
        with self.assertRaises(pydantic.ValidationError):
            SkinMap.model_validate({**d, "vignette": True})

    def test_dot_spacing_is_one_octave(self) -> None:
        with self.assertRaises(pydantic.ValidationError):
            SkinMapSeaDots.model_validate({**load_rules().skin.map.sea_dots.model_dump(), "spacing": [20, 30]})

    def test_map_themes_are_geo_themes(self) -> None:
        r = load_rules()
        self.assertEqual(r.skin.map_themes, ["porcelain"])
        self.assertTrue(set(r.skin.map_themes) <= set(r.geo.themes.names()))


class ApplyTest(unittest.TestCase):
    def tearDown(self) -> None:
        _skin(False)

    def test_mercator_porcelain_on_legacy_off(self) -> None:
        self.assertTrue(skin.apply("mercator", "porcelain"))
        self.assertTrue(typography.INK_MODE)
        for th in ("dark", "light", "slate", None):
            with self.subTest(th=th):
                self.assertFalse(skin.apply("mercator", th))
                self.assertFalse(typography.INK_MODE)
        self.assertTrue(skin.apply("studio"))          # 옛 호출 모양 그대로
        self.assertFalse(skin.apply("backdrop", "porcelain"))


class SeaDotGridTest(unittest.TestCase):
    D = SKIN.map.sea_dots

    def _dots(self, s: float) -> dict[tuple[float, float], float]:
        """월드 창 [0, 64)² 안 점 → 보이는 알파(굵은 단 1, 덧점 f, 0 은 뺀다)."""
        d, f = sea_dot_grid(s)
        out = {}
        n = int(round(64 / d))
        for i in range(n):
            for j in range(n):
                a = 1.0 if i % 2 == 0 and j % 2 == 0 else f
                if a > 1e-6:
                    out[(round(i * d, 9), round(j * d, 9))] = round(a, 6)
        return out

    def test_spacing_in_range(self) -> None:
        lo, hi = self.D.spacing
        for s in np.geomspace(0.5, 400.0, 157):
            d, f = sea_dot_grid(float(s))
            self.assertTrue(lo - 1e-6 <= d * s < hi + 1e-6, (s, d))
            self.assertTrue(0.0 <= f <= 1.0)

    def test_no_pop_at_level_switch(self) -> None:
        lo, _ = self.D.spacing
        for n in (-1, 0, 2):
            s = lo / 2.0 ** n   # 촘촘한 단 간격이 정확히 lo 가 되는 배율 = 단 전환점
            a, b = self._dots(s * (1 - 1e-7)), self._dots(s * (1 + 1e-7))
            self.assertEqual(set(a), set(b), s)
            self.assertTrue(all(abs(a[k] - b[k]) < 1e-3 for k in a), s)


class SkinMapRenderTest(unittest.TestCase):
    """합성 무대 — 육지 = 경도 40~56(porcelain 평지색), 바다 = 그 동쪽. 나라 AA(국기 aa: 흰 위·빨강 아래), BB, 도시 가나시."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        (root / "assets" / "flags").mkdir(parents=True)
        fl = np.zeros((90, 120, 3), np.uint8)
        fl[:45] = (255, 255, 255)
        fl[45:] = (220, 0, 0)
        Image.fromarray(fl).save(root / "assets" / "flags" / "aa_4x3.png")
        A = Assets(root, Labels(), geo=False)  # noqa: N806
        lv = 6
        T = {"lon0": 40.0, "lat0": 15.0, "lon1": 70.0, "lat1": 40.0, "levels": [lv], "z": 5}  # noqa: N806
        h = int(round((ym(40.0) - ym(15.0)) * lv))
        tt = pt.terrain_theme("porcelain")
        base = np.empty((h, 30 * lv, 3), np.uint8)
        base[:] = pt.hexc(tt.sea_stops[0][1])
        base[:, : 16 * lv] = pt.hexc(tt.land_stops[0][1])
        A.tiers = {"W": T}
        A.base = {("W", lv): Image.fromarray(base)}
        rings = {"AA": [_ring(50, 25, 56, 31)], "BB": [_ring(40, 25, 50, 31)], "CC": [_ring(40, 15, 56, 25)], "DD": [_ring(40, 31, 56, 40)]}
        place = {"lon": 48.0, "lat": 27.0, "rank": 1, "pop": 1_000_000, "cap": True, "cap0": True, "ko": "가나시", "name": "Gana"}
        A.geo = {"coarse": rings, "fine": rings, "admin1": {}, "meta": {"AA": {"ko": "가나", "lx": 53.0, "ly": 29.0, "rank": 1}},
                 "places": [place],
                 "roads": {lod_: {c: [] for c in ("motorway", "trunk", "primary")} for lod_ in ("coarse", "fine")},
                 "rivers": {lod_: {"major": [], "minor": []} for lod_ in ("coarse", "fine")}}
        A.plc = [place]
        A.plc_rank, A.plc_pop = np.array([1]), np.array([1_000_000])
        A.plc_cap, A.plc_cap0 = np.array([True]), np.array([True])
        A.theme = "porcelain"
        cls.A = A
        cls.st = MercatorStage(A, config={"theme": "porcelain", "theme_reason": "시험"})
        cls.view = View(cls.st, np.array([54.0, ym(28.0), 16.0]))
        cls.R = type("R", (), {"assets": A, "cache": {}})()
        cls.sea = np.array(pt.hexc(tt.sea_stops[0][1]))
        cls.land = np.array(pt.hexc(tt.land_stops[0][1]))

    @classmethod
    def tearDownClass(cls) -> None:
        _skin(False)
        cls.tmp.cleanup()

    def _render(self, on: bool, ev: dict | None = None, labels: bool = False, t: float = 5.0) -> tuple[np.ndarray, bytes, list]:
        _skin(on)
        self.R.cache = {}
        buf = bytearray(W * H * 4)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W, H, W * 4)
        ctx = cairo.Context(surf)
        old = typography.CONTRAST_LOG
        typography.CONTRAST_LOG = []
        try:
            self.st.render_base(ctx, self.view)
            if ev is not None:
                draw_country(ctx, self.R, self.view, t, validate_events([ev])[0])
            if labels:
                self.st.draw_labels(ctx, self.view, [], 1.0)
            log = list(typography.CONTRAST_LOG)
        finally:
            typography.CONTRAST_LOG = old
        surf.flush()
        raw = bytes(buf)
        return np.frombuffer(raw, np.uint8).reshape(H, W, 4)[..., [2, 1, 0]].astype(int), raw, log

    def _px(self, lon: float, lat: float) -> tuple[int, int]:
        x, y = self.view.to_screen(lon, ym(lat))
        return int(round(y)), int(round(x))

    def _sea_box(self) -> np.ndarray:
        r0, c0 = self._px(58.0, 34.0)
        r1, c1 = self._px(61.5, 22.0)
        return np.s_[r0:r1, c0:c1]

    def test_skin_map_flag(self) -> None:
        _skin(True)
        self.assertTrue(skin_map(self.st))
        _skin(False)
        self.assertFalse(skin_map(self.st))

    def test_sea_dots_on_sea_only(self) -> None:
        im, _, _ = self._render(True)
        sea = im[self._sea_box()]
        dark = (np.abs(sea - self.sea).max(axis=2) > 6)
        self.assertGreater(dark.sum(), 4)                     # 점이 있다
        self.assertLess(dark.mean(), 0.05)                    # 작고 드문 점
        r0, c0 = self._px(41.0, 33.0)
        r1, c1 = self._px(49.0, 26.0)
        land = im[r0:r1, c0:c1]
        self.assertEqual(int((np.abs(land - self.land).max(axis=2) > 2).sum()), 0)   # 육지 안 = 점 없음
        off, _, _ = self._render(False)
        self.assertEqual(int((np.abs(off[self._sea_box()] - self.sea).max(axis=2) > 2).sum()), 0)   # skin 꺼짐 = 점 없음

    def test_flag_white_stays_white_and_lifted(self) -> None:
        ev = {"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["AA"], "fill": "flag", "flag": "aa"}
        on, _, _ = self._render(True, ev)
        off, _, _ = self._render(False, ev)
        r, c = self._px(53.0, 30.0)   # 흰 띠, 평지
        self.assertGreaterEqual(on[r - 2:r + 3, c - 2:c + 3].min(), 235)
        self.assertLess(off[r, c].min(), 235)   # 옛 그림(skin 꺼짐)은 회색 — 고친 대상
        r, c = self._px(55.0, 25.0)   # 아래 가장자리 바로 밖(오른쪽 아래 그림자 쪽, 바다 위)
        below = on[r + 3:r + 14, c].mean(axis=1)
        self.assertLess(below.min(), self.sea.mean() - 6)            # 그림자가 있다
        self.assertTrue(np.all(np.diff(below) >= -1.0), below)       # 멀어질수록 옅어진다(부드러움)
        r, c = self._px(53.0, 25.0)   # 아래 경계 — 흰 테가 빨강 위에 섞여 밝은 분홍 화소(테 없으면 빨강·그림자뿐)
        px = on[r - 2:r + 3, c]
        self.assertTrue(((px[:, 0] > 230) & (px[:, 1] > 100)).any(), px.tolist())

    def test_color_fill_soft(self) -> None:
        ev = {"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["AA"], "col": "ru", "a": 0.5}
        on, _, _ = self._render(True, ev)
        off, _, _ = self._render(False, ev)
        r, c = self._px(53.0, 28.0)
        cap = SKIN.map.color_fill.alpha_max
        self.assertLess(np.abs(on[r, c] - self.land).max(), 255 * cap + 2)   # 옅은 틴트(연출 a 0.5 를 자른다)
        self.assertGreater(np.abs(off[r, c] - self.land).max(), 255 * cap + 2)

    def test_labels_ink_light_halo_contrast(self) -> None:
        im, raw, log = self._render(True, labels=True)
        req = [g for g in log if g[0] == "required"]
        self.assertTrue(req)
        x0, y0, x1, y1 = (int(v) for v in req[0][1])
        patch = im[max(0, y0):y1 + 1, max(0, x0):x1 + 1].mean(2)
        self.assertLess(patch.min(), 70)
        self.assertGreater(patch.max(), 240)
        ms = [m for m in measure_contrast((raw, W, H), req) if m["kind"] == "required"]
        self.assertTrue(ms and all(m["ratio"] >= QA.map_contrast_text for m in ms), ms)

    def test_flag_country_name_on_white_pill(self) -> None:
        """v7.4.0 4b-2 — 국기로 채운 나라 이름 = 흰 알약, 자리 = 나라 외곽 상자 아래(국기 문장 위가 아니다). 위·아래 자리가 없으면 이름 없음."""
        from engine.layers.labels import _flag_anchor  # noqa: PLC0415

        ev = {"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["AA"], "fill": "flag", "flag": "aa"}
        one = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertIsNone(_flag_anchor(one, self.view, "AA", "가나"))   # 나라가 화면 세로를 거의 채운다 — 국기 위로 올리지 않는다
        near = self.view
        self.view = View(self.st, np.array([54.0, ym(28.0), 30.0]))
        try:
            im, _, _ = self._render(True, ev, labels=True)
            F = SKIN.map.flag_label  # noqa: N806
            anc = _flag_anchor(one, self.view, "AA", "가나")
            self.assertIsNotNone(anc)
            x, y = anc
            _, bottom = self.view.to_screen(50.0, ym(25.0))
            self.assertGreater(y + F.dy - F.h / 2, bottom)   # 알약 위 끝 > 나라 아래 끝
            y0, y1 = int(y + F.dy - F.h / 2) + 2, int(y + F.dy + F.h / 2) - 2
            pill = im[y0:y1, int(x) - 14:int(x) + 14]
            lum = pill.mean(2) / 255
            self.assertGreaterEqual(float(lum.mean()), 0.85)   # 밝은 알약(어두운 상자 아님)
            self.assertLess(float(lum.min()), 0.35)            # 짙은 잉크 글자
            self.assertFalse(self.st.flag_codes == {})
        finally:
            self.view = near


if __name__ == "__main__":
    unittest.main()

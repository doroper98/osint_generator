"""v7.4.0 UF-903 ③(D910) — 중립 지도 테마 `porcelain` 하나(사용자 "지도도 중립적인 컬러감으로 통일 하자. 이 테마로 할지 저 테마로 할지 고민 하지 말고").

- rules: porcelain 이 등록되고 지도 키 집합이 다른 테마와 맞는다. land_shadow 는 선택 키(porcelain 만). 모든 장르 기본값 = porcelain,
  geo.themes.default 는 그대로(장르 없는 옛 프로젝트·v3 골든).
- 굽기(합성 고도, 네트워크 없음): 육지가 바다보다 밝고, 바다는 단색, 해안 바다 쪽(빛 반대쪽)에만 그림자, 육지 위에는 칠하지 않는다.
  다른 테마(dark·light·slate) 굽기는 HEAD 와 같은 화소(land_shadow 없음 = 종전 계산).
- 무대: porcelain 무대가 그려지고 국경은 회색(흰색·검정 아님), 지명은 짙은 잉크 + 밝은 halo, 지도 대비 검사 통과. 국경 발광 겹 0 = 그리지 않는다.
- [map-theme-legacy] hard: 새 프로젝트가 장르 기본값과 다른 테마를 고정하면 실패, 옛 프로젝트 목록·장르 기본값(테마 없음)은 통과.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import cairo
import numpy as np
import yaml
from PIL import Image
from shapely.geometry import box

import geo.prep_tiers as pt
from engine import typography
from engine.assets import Assets, Labels
from engine.checks import QA, map_theme_legacy, measure_contrast
from engine.direction import load_direction_doc
from engine.layers.borders import draw_border_glow
from engine.projection import View
from engine.stage import MercatorStage, ym
from genres.load import genre_names, load_genre
from rules import load_rules
from schemas.rules_models import GeoThemes

REPO = Path(__file__).resolve().parent.parent
HORMUZ_DIR = REPO / "projects" / "hormuz_korea" / "direction.yaml"
TIER = pt.TierSpec("T", 24, 5, 50.0, 20.0, 58.0, 28.0)
LAND = {"XX": box(50.0, 20.0, 53.0, 28.0)}   # 서쪽 3/8 = 육지, 해안 = 경도 53 세로선
# HEAD(land_shadow 도입 전) 의 같은 합성 굽기 화소 md5 — 다른 테마는 바이트 동일(UF-903 ③ 요건)
HEAD_PIXELS = {"dark": "b402ce9b5bedb2e019f25c457899b68c", "light": "eb2e0ed15fb47c332121bb8861b9ce4e", "slate": "6fb9bbadd35f7930b4ab0ab42c883aa8"}


def _keys(m: object, pre: str = "") -> set[str]:
    out: set[str] = set()
    for k in type(m).model_fields:
        v = getattr(m, k)
        if v is None:
            continue
        out.add(pre + k)
        if hasattr(type(v), "model_fields"):
            out |= _keys(v, pre + k + ".")
    return out


def _relief_mosaic(_tiles: Path, T: pt.TierSpec) -> tuple[np.ndarray, int, int]:  # noqa: N803
    """합성 고도 — 서쪽 절반은 남북으로 물결치는 언덕(0~1200 m), 동쪽 절반은 바다(−10~−5000 m 기울기)."""
    xr, yr = pt.tile_range(T)
    h, w = len(yr) * pt.TILE, len(xr) * pt.TILE
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    land = 600.0 + 600.0 * np.sin(yy / 9.0)
    M = np.where(xx < w * 0.5, land, -10.0 - 5000.0 * (xx - w * 0.5) / (w * 0.5))
    return M.astype(np.float32), xr.start, yr.start


def _bake(theme: object) -> np.ndarray:
    with tempfile.TemporaryDirectory() as d:
        with mock.patch.object(pt, "mosaic", _relief_mosaic):
            pt.build_tier(TIER, LAND, Path(d), Path(d), 1.0, theme=theme)
        return np.asarray(Image.open(Path(d) / "base_T_24.png").convert("RGB"), np.int16)


def _coast_col(img: np.ndarray) -> int:
    return int(round((53.0 - TIER.lon0) * TIER.ppd))


def _doc(stage_config: dict | None):  # noqa: ANN202 — Direction
    """골든 연출에서 stage_config 블록만 바꾼 연출(tests/test_q3_map_theme 과 같은 방식)."""
    text = HORMUZ_DIR.read_text(encoding="utf-8")
    head, rest = text.split("stage_config:", 1)
    rest = rest[rest.index("\nplaces:") + 1:]
    block = yaml.safe_dump({"stage_config": stage_config}, allow_unicode=True) if stage_config is not None else ""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "direction.yaml"
        p.write_text(head + block + rest, encoding="utf-8")
        return load_direction_doc(p)


class PorcelainRulesTest(unittest.TestCase):
    def test_registered_default_unchanged(self) -> None:
        th = load_rules().geo.themes
        self.assertIn("porcelain", GeoThemes.names())
        self.assertIs(th.get("porcelain"), th.porcelain)
        self.assertEqual(th.default, "dark")   # 장르 없는 옛 프로젝트·v3 골든은 그대로

    def test_map_key_sets(self) -> None:
        """필수 지도 키·도로·강 키 집합은 모든 테마가 같다. porcelain 은 dark 키 전부 + 밝은 지도 글자 모양·국소 보정·발광 값."""
        th = load_rules().geo.themes
        dk = _keys(th.dark.map)
        for name in GeoThemes.names():
            k = _keys(th.get(name).map)
            self.assertEqual({x for x in k if x.startswith(("roads", "rivers"))}, {x for x in dk if x.startswith(("roads", "rivers"))}, name)
            self.assertEqual(dk - k, set(), name)
            self.assertEqual(set(type(th.get(name).terrain).model_fields), set(type(th.dark.terrain).model_fields))
        pk = _keys(th.porcelain.map)
        self.assertTrue({"route_label", "label_contrast_fix", "border_glow"} <= pk)

    def test_land_shadow_optional(self) -> None:
        th = load_rules().geo.themes
        for name in ("dark", "light", "slate"):
            self.assertIsNone(th.get(name).terrain.land_shadow, name)
        sd = th.porcelain.terrain.land_shadow
        self.assertIsNotNone(sd)
        self.assertGreater(sd.dx, 0)   # 해 = 북서(315°) → 그림자는 남동(빛 반대쪽)
        self.assertGreater(sd.dy, 0)

    def test_white_land_flat_sea(self) -> None:
        t = load_rules().geo.themes.porcelain.terrain
        sea = {c.lower() for _, c in t.sea_stops}
        self.assertEqual(len(sea), 1)
        self.assertIsNone(t.sea_shade)
        self.assertIsNone(t.sea_tint)
        self.assertEqual(t.coast_glow.strength, 0.0)
        self.assertGreater(min(sum(pt.hexc(c)) for _, c in t.land_stops), sum(pt.hexc(sea.pop())))

    def test_glow_empty_and_ink_labels(self) -> None:
        m = load_rules().geo.themes.porcelain.map
        self.assertEqual((m.border_glow.halo, m.border_glow.run_layers), ([], []))
        self.assertLess(max(m.city_label), 0.15)
        self.assertLess(max(m.country_label), 0.15)
        self.assertGreater(min(m.halo), 0.9)
        self.assertEqual(m.route_label.style, "ink")
        self.assertIn("porcelain", load_rules().colors.themes)

    def test_every_genre_defaults_to_porcelain(self) -> None:
        names = genre_names()
        self.assertTrue(names)
        for g in names:
            self.assertEqual((load_genre(g).stage.settings().get("mercator") or {}).get("theme"), "porcelain", g)

    def test_legacy_list_is_exactly_tracked_pins(self) -> None:
        """qa_checks.map_theme_legacy_projects = 이 결정 전에 stage_config.mercator.theme 을 고정한 추적 프로젝트 전부(그 밖 없음)."""
        files = subprocess.run(["git", "ls-files", "projects/*direction*.yaml"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        pinned = set()
        for f in files:
            doc = yaml.safe_load((REPO / f).read_text(encoding="utf-8"))
            if isinstance(doc, dict) and "theme" in ((doc.get("stage_config") or {}).get("mercator") or {}):
                pinned.add(f.split("/")[1])
        self.assertEqual(set(QA.map_theme_legacy_projects), pinned)

    def test_director_told_theme_is_fixed(self) -> None:
        g = "\n".join(load_rules().direction_grammar)
        self.assertIn("[map-theme-legacy]", g)
        self.assertIn("지도 테마는 고르지 않는다", g)


class PorcelainBakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        th = pt.terrain_theme("porcelain")
        cls.img = _bake(th)
        cls.flat = _bake(th.model_copy(update={"land_shadow": None}))
        cls.sea_rgb = np.array(pt.hexc(th.sea_stops[0][1]))

    def test_land_brighter_than_sea(self) -> None:
        h, w, _ = self.img.shape
        c = _coast_col(self.img)
        land = self.img[4:-4, 4:c - 6].reshape(-1, 3).mean(1)
        sea = self.img[4:-4, c + 30:].reshape(-1, 3).mean(1)
        self.assertGreater(np.median(land), np.median(sea) + 6)

    def test_sea_flat_away_from_coast(self) -> None:
        c = _coast_col(self.img)
        sea = self.img[4:-4, c + 30:].reshape(-1, 3)
        self.assertLessEqual(float(sea.std(0).max()), 0.6)   # 깊이와 무관(단색 두 정지점 보간 부동소수 ±1)
        self.assertLessEqual(int(np.abs(sea - self.sea_rgb).max()), 1)

    def test_shadow_on_sea_side_only(self) -> None:
        c = _coast_col(self.img)
        mid = slice(20, -20)   # 위아래 끝(그림자가 옮겨 가는 가장자리) 제외
        near = self.img[mid, c + 1:c + 5].mean()
        open_ = self.img[mid, c + 30:].mean()
        self.assertLess(near, open_ - 3)   # 해안 몇 px 안 바다 = 열린 바다보다 어둡다(빛 반대쪽)
        np.testing.assert_array_equal(self.img[mid, c + 30:], self.flat[mid, c + 30:])   # 먼바다는 그림자 없음과 같다
        np.testing.assert_array_equal(self.img[:, :c - 3], self.flat[:, :c - 3])          # 육지 위에는 칠하지 않는다

    def test_other_themes_byte_identical_to_head(self) -> None:
        for name, md5 in HEAD_PIXELS.items():
            got = hashlib.md5(_bake(pt.terrain_theme(name)).astype(np.uint8).tobytes()).hexdigest()
            self.assertEqual(got, md5, name)


def _ring(lon0: float, lat0: float, lon1: float, lat1: float) -> np.ndarray:
    return np.array([[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]], dtype=float)


class PorcelainStageTest(unittest.TestCase):
    """합성 무대 — 나라 AA·BB 가 경도 50 에서 국경을 공유. 바탕 = porcelain 육지·바다 색(설계 해상도 854×480)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        A = Assets(Path(cls.tmp.name), Labels(), geo=False)  # noqa: N806
        lv = 6
        T = {"lon0": 40.0, "lat0": 15.0, "lon1": 70.0, "lat1": 40.0, "levels": [lv], "z": 5}  # noqa: N806
        h = int(round((ym(40.0) - ym(15.0)) * lv))
        tt = pt.terrain_theme("porcelain")
        base = np.empty((h, 30 * lv, 3), np.uint8)
        base[:] = pt.hexc(tt.sea_stops[0][1])
        base[:, : 16 * lv] = pt.hexc(tt.land_stops[0][1])   # 경도 40~56 육지
        A.tiers = {"W": T}
        A.base = {("W", lv): Image.fromarray(base)}
        rings = {"AA": [_ring(50, 25, 56, 31)], "BB": [_ring(44, 25, 50, 31)]}
        place = {"lon": 53.0, "lat": 27.0, "rank": 1, "pop": 1_000_000, "cap": True, "cap0": True, "ko": "가나시", "name": "Gana"}
        A.geo = {"coarse": rings, "fine": rings, "admin1": {}, "meta": {"AA": {"ko": "가나", "lx": 53.0, "ly": 29.5, "rank": 1}},
                 "places": [place],
                 "roads": {lod_: {c: [] for c in ("motorway", "trunk", "primary")} for lod_ in ("coarse", "fine")},
                 "rivers": {lod_: {"major": [], "minor": []} for lod_ in ("coarse", "fine")}}
        A.plc = [place]
        A.plc_rank, A.plc_pop = np.array([1]), np.array([1_000_000])
        A.plc_cap, A.plc_cap0 = np.array([True]), np.array([True])
        A.theme = "porcelain"
        cls.A = A
        cls.st = MercatorStage(A, config={"theme": "porcelain", "theme_reason": "시험"})
        cls.view = View(cls.st, np.array([52.0, ym(28.0), 16.0]))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def _render(self, labels: bool) -> tuple[np.ndarray, bytes]:
        buf = bytearray(854 * 480 * 4)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, 854, 480, 854 * 4)
        ctx = cairo.Context(surf)
        self.st.render_base(ctx, self.view)
        if self.st.border_glow:
            draw_border_glow(ctx, self.st, self.view, 2.0)
        if labels:
            self.st.draw_labels(ctx, self.view, [], 1.0)
        surf.flush()
        raw = bytes(buf)
        return np.frombuffer(raw, np.uint8).reshape(480, 854, 4)[..., [2, 1, 0]].astype(int), raw

    def _px(self, lon: float, lat: float) -> tuple[int, int]:
        x, y = self.view.to_screen(lon, ym(lat))
        return int(round(y)), int(round(x))

    def test_border_grey(self) -> None:
        im, _ = self._render(False)
        r, c = self._px(50.0, 28.0)
        line = im[r, c - 3:c + 4].mean(1)
        self.assertLess(line.min(), 215)    # 바탕(236)보다 어둡다 — 흰 선 아님
        self.assertGreater(line.min(), 110)   # 검은 선도 아님(가는 회색)

    def test_glow_draws_nothing(self) -> None:
        buf = bytearray(854 * 480 * 4)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, 854, 480, 854 * 4)
        draw_border_glow(cairo.Context(surf), self.st, self.view, 2.0)
        surf.flush()
        self.assertEqual(bytes(buf), bytes(854 * 480 * 4))

    def test_labels_ink_with_light_halo_and_contrast(self) -> None:
        old = typography.CONTRAST_LOG
        typography.CONTRAST_LOG = []
        try:
            im, raw = self._render(True)
            log = list(typography.CONTRAST_LOG)
        finally:
            typography.CONTRAST_LOG = old
        req = [g for g in log if g[0] == "required"]
        self.assertTrue(req)   # 도시 이름 = required
        x0, y0, x1, y1 = (int(v) for v in req[0][1])
        patch = im[max(0, y0):y1 + 1, max(0, x0):x1 + 1].mean(2)
        self.assertLess(patch.min(), 70)      # 짙은 잉크 글자
        self.assertGreater(patch.max(), 240)  # 밝은 halo(바탕 236 보다 밝다)
        ms = [m for m in measure_contrast((raw, 854, 480), req) if m["kind"] == "required"]
        self.assertTrue(ms)
        self.assertTrue(all(m["ratio"] >= QA.map_contrast_text for m in ms), ms)


class MapThemeLegacyTest(unittest.TestCase):
    def test_new_project_pinning_dark_fails(self) -> None:
        mt = load_direction_doc(HORMUZ_DIR).map_theme("hormuz_korea")   # dark 고정
        self.assertEqual(mt["genre_default"], "porcelain")
        out = map_theme_legacy(mt, "new_project_2027")
        self.assertEqual(len(out), 1)
        self.assertIn("[map-theme-legacy]", out[0])

    def test_listed_legacy_passes(self) -> None:
        mt = load_direction_doc(HORMUZ_DIR).map_theme("hormuz_korea")
        self.assertEqual(map_theme_legacy(mt, "hormuz_korea"), [])

    def test_genre_default_passes(self) -> None:
        mt = _doc(None).map_theme("new_project_2027")
        self.assertEqual((mt["effective"], mt["declared"]), ("porcelain", False))
        self.assertEqual(map_theme_legacy(mt, "new_project_2027"), [])
        same = _doc({"mercator": {"theme": "porcelain", "theme_reason": "장르와 같음"}}).map_theme("new_project_2027")
        self.assertEqual(map_theme_legacy(same, "new_project_2027"), [])
        self.assertEqual(map_theme_legacy(None, "new_project_2027"), [])   # 지도 무대 아님

    def test_registered_hard(self) -> None:
        from engine.checks import HARD  # noqa: PLC0415

        self.assertIn("map_theme_legacy", HARD)


if __name__ == "__main__":
    unittest.main()

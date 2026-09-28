"""engine/stage — Stage 프로토콜·MercatorStage·무대 레지스트리 (v4.1.0, back_and_forth D-0076 작업 1·2·8, docs/handoff/20 §2.3)."""

from __future__ import annotations

import math
import unittest
from unittest import mock

import numpy as np

from engine import stage as S
from engine.camera import Director
from engine.projection import View
from engine.stage import MercatorStage, Stage, StageError, lat_of, make_stage, ym
from engine.style import H_OUT, W_OUT
from rules import load_rules

TIERS = {"W": {"lon0": 20.0, "lon1": 150.0, "lat0": -10.0, "lat1": 60.0, "levels": []}}


def _old_view(cam: np.ndarray, tiers: dict) -> tuple[float, float, float, float]:
    """v4.0.0 projection.View 의 식 그대로(비교용) → (u0, v1, s, w)."""
    lon, v, w = cam
    tw_ = tiers["W"]
    umin, umax = tw_["lon0"], tw_["lon1"]
    vmin, vmax = ym(tw_["lat0"]), ym(tw_["lat1"])
    w = min(w, umax - umin - 0.01, (vmax - vmin - 0.01) * W_OUT / H_OUT)
    h = w * H_OUT / W_OUT
    return min(max(lon - w / 2, umin), umax - w), min(max(v + h / 2, vmin + h), vmax), W_OUT / w, w


class ProtocolTest(unittest.TestCase):
    def test_mercator_is_stage(self) -> None:
        self.assertIsInstance(MercatorStage(tiers=TIERS), Stage)
        for m in ("to_world", "from_world", "render_base", "draw_labels", "lod_rules"):
            self.assertTrue(callable(getattr(MercatorStage, m)), m)

    def test_bounds_are_world_tier_w(self) -> None:
        self.assertEqual(MercatorStage(tiers=TIERS).bounds, (20.0, ym(-10.0), 150.0, ym(60.0)))

    def test_bounds_without_tiers_is_error(self) -> None:
        with self.assertRaises(StageError):
            _ = MercatorStage().bounds

    def test_missing_w_tier_is_error(self) -> None:
        with self.assertRaises(KeyError):
            MercatorStage(tiers={"G": TIERS["W"]})

    def test_anchor_keys_enforced(self) -> None:
        with self.assertRaises(StageError):
            MercatorStage().to_world(lon=1.0)
        with self.assertRaises(StageError):
            MercatorStage().to_world(date=2020.0, lane=1.0)

    def test_lod_rules_are_v3_values(self) -> None:
        lod = MercatorStage().lod_rules()
        self.assertEqual(S.by_w(61, lod["country_rank_max"]), 2)
        self.assertEqual(S.by_w(60, lod["country_rank_max"]), 4)
        self.assertEqual(S.by_w(3, lod["city_rank_max"]), 8)
        self.assertEqual(lod["borders_fine_below_w"], 22)


class WorldRoundTripTest(unittest.TestCase):
    def test_to_world_from_world(self) -> None:
        M = MercatorStage()  # noqa: N806
        for lon, lat in ((56.35, 26.55), (-76.9, 38.8), (127.0, 37.5), (0.0, 0.0), (37.6, 55.75)):
            x, y = M.to_world(lon=lon, lat=lat)
            self.assertEqual((x, y), (lon, ym(lat)))
            a = M.from_world(x, y)
            self.assertEqual(a["lon"], lon)
            self.assertAlmostEqual(a["lat"], lat, places=9)

    def test_screen_pixels_equal_old_view(self) -> None:
        """새 View(stage, cam).to_screen(stage.to_world(...)) = v4.0.0 View.xy(lon, lat) — 부동소수 비트 단위로 같다."""
        M = MercatorStage(tiers=TIERS)  # noqa: N806
        for cam in (np.array([56.0, ym(26.0), 14.0]), np.array([90.0, ym(20.0), 96.0]), np.array([21.0, ym(55.0), 3.4])):
            u0, v1, s, w = _old_view(cam, TIERS)
            v = View(M, cam)
            self.assertEqual((v.x0, v.y1, v.s, v.w), (u0, v1, s, w))
            for lon, lat in ((56.35, 26.55), (51.4, 35.7), (22.0, 50.0)):
                self.assertEqual(v.to_screen(*M.to_world(lon=lon, lat=lat)), ((lon - u0) * s, (v1 - ym(lat)) * s))

    def test_view_inverse(self) -> None:
        M = MercatorStage(tiers=TIERS)  # noqa: N806
        v = View(M, np.array([56.0, ym(26.0), 14.0]))
        x, y = v.to_world(700.0, 90.0)
        px, py = v.to_screen(x, y)
        self.assertAlmostEqual(px, 700.0, places=9)
        self.assertAlmostEqual(py, 90.0, places=9)
        self.assertAlmostEqual(M.from_world(x, y)["lat"], lat_of(v.y1 - 90.0 / v.s), places=12)

    def test_director_uses_stage(self) -> None:
        d = Director(MercatorStage())
        d.cam(1.0, 56.0, 26.0, 14.0)
        self.assertEqual((d.keys[0].x, d.keys[0].y), (56.0, ym(26.0)))

    def test_attach_world(self) -> None:
        ev = [{"type": "marker", "lon": 56.0, "lat": 26.0}, {"type": "route", "pts": [(56.0, 26.0), (58.0, 24.0)]},
              {"type": "barrier", "p0": [56.0, 26.0], "p1": [57.0, 27.0]}, {"type": "card"}]
        S.attach_world(ev, MercatorStage())
        self.assertEqual(ev[0]["world"], (56.0, ym(26.0)))
        self.assertEqual(ev[1]["world_pts"][1], (58.0, ym(24.0)))
        self.assertEqual((ev[2]["world_p0"], ev[2]["world_p1"]), ((56.0, ym(26.0)), (57.0, ym(27.0))))
        self.assertNotIn("world", ev[3])


class RegistryTest(unittest.TestCase):
    def test_registry_matches_implementations(self) -> None:
        self.assertEqual(sorted(load_rules().registries.stages), sorted(S.STAGE_CLASSES))
        self.assertIn(S.DEFAULT_STAGE, S.STAGE_CLASSES)

    def test_unregistered_stage_is_error(self) -> None:
        with self.assertRaises(StageError) as cm:
            make_stage("timeline")
        self.assertIn("미등록", str(cm.exception))

    def test_registered_without_implementation_is_error(self) -> None:
        rules = load_rules()
        fake = rules.model_copy(update={"registries": rules.registries.model_copy(update={"stages": ["mercator", "chart_wall"]})})
        with mock.patch("rules.load_rules", return_value=fake):
            with self.assertRaises(StageError) as cm:
                make_stage("chart_wall")
        self.assertIn("구현이 없다", str(cm.exception))

    def test_make_mercator(self) -> None:
        st = make_stage("mercator")
        self.assertEqual(st.name, "mercator")
        self.assertTrue(math.isclose(st.to_world(lon=0.0, lat=0.0)[1], 0.0, abs_tol=1e-12))


if __name__ == "__main__":
    unittest.main()

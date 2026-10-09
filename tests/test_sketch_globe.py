"""미사일 3D 전환편(sketch/missile/globe·globe_scene, render.CrossfadeScene) — D-0140 §5 S2, D-0143.

기하(to_local 거리 보존·평면 수렴·가림·볼륨 경계), 카메라(업 벡터 연속·SK-C1(3D) 양성/음성), SK-H6(D136) 양성/음성,
교차 전환 합성, 화면 숫자 포맷, 프레임 렌더 provenance(자산 없으면 사유 있는 skip).
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import yaml

from engine.style import FPS, output_profile
from sketch.common.checks import CheckReport
from sketch.common.geodesy import EARTH_KM, dest, gc_dist, horizon_altitude, to_local
from sketch.common.render import CrossfadeScene
from sketch.common.spec import load_spec
from sketch.missile import globe as gl
from sketch.missile.checks import check_camera_3d, check_globe_render, check_globe_spec, globe_anchor_track, globe_path
from sketch.missile.numbers import Numbers
from sketch.missile.spec import MissileSpec
from tests.anti_inertia._ast_util import REPO

PROJ = REPO / "projects" / "d1_missile_sketch"
CEN = (132.9, 40.3)


def spec() -> MissileSpec:
    return load_spec(PROJ, MissileSpec)


def arc_from_tangent(P: np.ndarray, k: float) -> np.ndarray:
    """국소 3D 점 → 반지름 kR 구 위 접점에서의 호 길이(km)."""
    c = np.array([0.0, 0.0, -k * EARTH_KM])
    v = P - c
    cosang = np.clip(v[:, 2] / np.linalg.norm(v, axis=1), -1, 1)
    return k * EARTH_KM * np.arccos(cosang)


class GeometryTest(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(7)
        self.lon = CEN[0] + rng.uniform(-12, 12, 10)
        self.lat = CEN[1] + rng.uniform(-8, 8, 10)

    def test_to_local_preserves_distance(self) -> None:
        want = np.array([gc_dist(CEN, (a, b)) for a, b in zip(self.lon, self.lat)])
        for k in (1.0, 80.0):
            P = to_local(CEN, self.lon, self.lat, np.zeros(10), k)
            self.assertLess(np.abs(arc_from_tangent(P, k) - want).max(), 1e-3, f"k={k}")   # < 1 m

    def test_large_k_converges_to_plane(self) -> None:
        P = to_local(CEN, self.lon, self.lat, np.zeros(10), 1e7)
        want = np.array([gc_dist(CEN, (a, b)) for a, b in zip(self.lon, self.lat)])
        self.assertLess(np.abs(P[:, 2]).max(), 1e-2)                           # 거의 평면(z ≈ 0)
        self.assertLess(np.abs(np.hypot(P[:, 0], P[:, 1]) - want).max(), 1e-3)  # 방위 등거리

    def test_visible_hides_far_side(self) -> None:
        out = output_profile("trial")
        cam = gl.Cam(np.array([0.0, 0.0, 20000.0]), np.zeros(3), 40.0, gl.Y_AXIS, out.width, out.height)
        near = to_local(CEN, np.array([CEN[0]]), np.array([CEN[1]]), np.zeros(1), 1.0)
        far = to_local(CEN, np.array([CEN[0] + 180]), np.array([-CEN[1]]), np.zeros(1), 1.0)   # 대척점
        self.assertTrue(gl.visible(cam, near, 1.0)[0])
        self.assertFalse(gl.visible(cam, far, 1.0)[0])

    def test_radar_volume_boundary(self) -> None:
        sp = spec()
        s = next(x for x in sp.sensors if x.short == "성주")
        launch = (sp.launch.lon, sp.launch.lat)
        vol = gl.radar_volume(s, launch, CEN, 1.0)

        def pt(az_off: float, el: float, km: float) -> np.ndarray:
            a, e = math.radians(vol["brg"] + az_off), math.radians(el)
            d = math.cos(e) * (math.sin(a) * vol["east"] + math.cos(a) * vol["north"]) + math.sin(e) * vol["up"]
            return (vol["base"] + d * km)[None, :]
        half = s.az_width_deg / 2
        self.assertTrue(gl.in_volume(s, vol, pt(half - 1, 30, s.range_km - 1))[0])
        self.assertFalse(gl.in_volume(s, vol, pt(half + 1, 30, s.range_km - 1))[0])    # 방위 밖
        self.assertFalse(gl.in_volume(s, vol, pt(0, 30, s.range_km + 1))[0])           # 거리 밖
        self.assertFalse(gl.in_volume(s, vol, pt(0, s.el_deg[1] + 1, 100))[0])          # 고각 밖


class CameraTest(unittest.TestCase):
    def test_up_vector_continuous(self) -> None:
        sp = spec()
        path = globe_path(sp, output_profile("trial"))
        ts = [i / FPS for i in range(int(sp.globe.t_2d * FPS), int(sp.globe.duration_sec * FPS))]
        ups = [path.cam(t).up for t in ts]
        jumps = [math.degrees(math.acos(min(1.0, float(np.dot(a, b))))) for a, b in zip(ups, ups[1:])]
        self.assertLess(max(jumps), 5.0, "카메라 업 벡터가 한 프레임에 5° 넘게 돈다")

    def test_sk_c1_3d_reviewed_passes(self) -> None:
        sp, out = spec(), output_profile("trial")
        r = CheckReport()
        worst = check_camera_3d(r, *globe_anchor_track(sp, globe_path(sp, out), FPS), out.width)
        self.assertEqual(r.hard, [], [f.message for f in r.hard])
        self.assertLess(worst["d2 발사점"], 0.001)

    def test_sk_c1_3d_linear_keys_fail(self) -> None:
        """음성 — 키프레임 사이 ease 를 빼면(선형) 키프레임 경계에서 속도가 튀어 2차 차분 위반."""
        sp, out = spec(), output_profile("trial")
        with mock.patch.object(gl, "ease_io", lambda x: max(0.0, min(1.0, x))):
            r = CheckReport()
            check_camera_3d(r, *globe_anchor_track(sp, globe_path(sp, out), FPS), out.width)
        self.assertTrue(any("화면 궤적" in f.message for f in r.hard), [f.message for f in r.hard])


class H6HorizonTest(unittest.TestCase):
    def test_note_required(self) -> None:
        sp = spec()
        r = CheckReport()
        check_globe_spec(r, sp, output_profile("trial"))
        self.assertEqual(r.hard, [])
        sp.globe.panel.note = "  "
        r = CheckReport()
        check_globe_spec(r, sp, output_profile("trial"))
        self.assertEqual([f.id for f in r.hard], ["SK-H6"])

    def test_panel_values_match_formula(self) -> None:
        sp = spec()
        nums = Numbers(sp)
        launch = (sp.launch.lon, sp.launch.lat)
        s = next(x for x in sp.sensors if x.short == "성주")
        d = gc_dist((s.lon, s.lat), launch)
        self.assertEqual(nums.computed(f"horizon.altitude_km:{s.name}", horizon_altitude(d), "km", "f", {}, approx=True), "약 14km")
        r = CheckReport()
        check_globe_render(r, sp, nums, {"horizon_panel": 3, "horizon_panel_note": 3})
        self.assertEqual(r.hard, [])
        self.assertNotIn(f"horizon.altitude_km:{s.name}", nums.shown)          # 계산값은 numbers_shown 에 섞지 않는다
        nums.computed(f"horizon.altitude_km:{s.name}", horizon_altitude(d) + 3, "km", "f", {}, approx=True)
        r = CheckReport()
        check_globe_render(r, sp, nums, {"horizon_panel": 3, "horizon_panel_note": 2})
        self.assertEqual([f.id for f in r.hard], ["SK-H6", "SK-H6"])


class FormatTest(unittest.TestCase):
    def test_radar_sub_and_constant(self) -> None:
        sp = spec()
        nums = Numbers(sp)
        s = next(x for x in sp.sensors if x.short == "성주")
        self.assertEqual(nums.fill(sp.globe.labels.radar_sub, s), "600km · 방위 120° · 고각 0~60°(개념)")
        self.assertIn("6,371km", nums.fill(sp.globe.hud_notes[1]))
        with self.assertRaises(KeyError):
            nums.fill("{sensor.el}", next(x for x in sp.sensors if x.name == "그린파인 레이더"))


class _Solid:
    def __init__(self, v: int) -> None:
        self.out = output_profile("trial")
        self.v = v
        self.calls: list[float] = []

    def frame(self, t: float) -> bytes:
        self.calls.append(t)
        return bytes([self.v]) * (self.out.width * self.out.height * 4)


class CrossfadeTest(unittest.TestCase):
    def test_blend_and_handoff_time(self) -> None:
        a, b = _Solid(200), _Solid(100)
        sc = CrossfadeScene(a, b, lambda t: 41 + t * 0.3, 2.0, 1.0, 19.0, 0.6, 1.0)
        self.assertEqual(sc.frame(1.0)[0], 200)
        self.assertAlmostEqual(a.calls[-1], 41.3)
        self.assertEqual(sc.frame(2.5)[0], 150)              # smooth(0.5) = 0.5 → 반반
        self.assertAlmostEqual(a.calls[-1], 41.6)            # 교차 중 앞 장면은 t_cut 정지 화면
        self.assertEqual(sc.frame(5.0)[0], 100)
        self.assertEqual(sc.frame(0.0)[0], 0)                # 열림 검정


@unittest.skipUnless((PROJ / "globe_tex" / "assets" / "tiers.pkl").is_file() and (PROJ / "assets" / "tiers.pkl").is_file(),
                     "d1 지형·지구본 텍스처 자산 없음 — `python -m geo.prep projects/d1_missile_sketch` + `…/globe_tex`(phaseS0 run_log §0)")
class GlobeFramesTest(unittest.TestCase):
    def test_globe_frames_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "p"
            shutil.copytree(PROJ, proj, ignore=shutil.ignore_patterns("out", "res_720p"))
            r = subprocess.run([sys.executable, "-m", "sketch.missile", str(proj), "--globe", "--frames", "1,12.5"], cwd=REPO,
                               capture_output=True, text=True, timeout=900)
            self.assertEqual(r.returncode, 0, r.stderr)
            prov = json.loads((proj / "out" / "sketch_provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(prov["kind"], "missile_globe")
            self.assertEqual(prov["checks"]["hard"], [])
            self.assertIn("SK-H6", prov["checks"]["ran"])
            keys = {c["key"] for c in prov["numbers_computed"]}
            self.assertIn("horizon.altitude_km:사드 AN/TPY-2 · 성주", keys)
            self.assertFalse(any(s.startswith("horizon.") for s in prov["numbers_shown"]))
            self.assertIn("mod.apogee_km=6,040.9km", prov["numbers_shown"])
            self.assertTrue((proj / "out" / "sketch_globe_012.5.png").is_file())

    def test_bad_el_rejected(self) -> None:
        raw = yaml.safe_load((PROJ / "sketch.yaml").read_text(encoding="utf-8"))
        raw["sensors"][0]["el_deg"] = [0, 120]
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            shutil.copytree(PROJ / "media", proj / "media")
            (proj / "sketch.yaml").write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
            r = subprocess.run([sys.executable, "-m", "sketch.missile", str(proj), "--globe", "--check"], cwd=REPO,
                               capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 1)
            self.assertIn("el_deg", r.stderr)


if __name__ == "__main__":
    unittest.main()

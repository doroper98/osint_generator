"""전황 작전도(sketch/campaign, common/svg_georef) — D-0140 §5 S3, D-0145, D-0146.

정합(잔차·묶음 수·눈금 부족 오류), 포위망 SK-G2 양성/음성, 제대 SK-G3 음성, SK-H5 양성/음성, SK-H1 음성, SK-R1 음성,
부호 예약 상자, 화살표 성장 단조, 전선 이중선 오프셋 방향, 프레임 렌더 provenance(자산 없으면 사유 있는 skip).
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cairo
import numpy as np
import yaml
from pydantic import ValidationError
from shapely.geometry import Polygon

from rules import load_rules
from sketch.campaign import arrows as arrows_mod
from sketch.campaign import fronts as fronts_mod
from sketch.campaign.checks import check_cities, check_spec, city_offsets, pocket_validity
from sketch.campaign.fronts import FrontData
from sketch.campaign.pockets import build_polygon
from sketch.campaign.spec import CampaignSpec
from sketch.common.checks import CheckReport, spec_errors
from sketch.common.spec import load_spec
from sketch.common.svg_georef import collect, fit_graticule, georef
from tests.anti_inertia._ast_util import REPO

PROJ = REPO / "projects" / "uranus_sketch"
SK = load_rules().sketch


def raw_spec() -> dict:
    return yaml.safe_load((PROJ / "sketch.yaml").read_text(encoding="utf-8"))


def run(raw: dict, rights: dict | None = None) -> CheckReport:
    r = CheckReport()
    try:
        spec = CampaignSpec.model_validate(raw)
    except ValidationError as e:
        spec_errors(r, e)
        return r
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        for f in ("fronts.json", "ref_operation_uranus.svg", "RIGHTS.json"):
            shutil.copy(PROJ / f, proj / f)
        if rights is not None:
            (proj / "RIGHTS.json").write_text(json.dumps(rights), encoding="utf-8")
        check_spec(r, spec, proj)
    return r


def ids(r: CheckReport) -> set[str]:
    return {f.id for f in r.hard}


class GeorefTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sp = load_spec(PROJ, CampaignSpec)
        cls.spec = sp
        cls.out, cls.fit = georef(PROJ / sp.fronts.reference.file, [s.model_dump() for s in sp.fronts.style_map],
                                  sp.fronts.graticule.model_dump())

    def test_residual(self) -> None:
        self.assertLessEqual(self.fit.residual_deg, SK.checks.georef_residual_deg)
        self.assertAlmostEqual(self.fit.residual_deg, 0.0084, delta=0.0005)

    def test_bundle_counts_and_repo_data(self) -> None:
        L = self.out["layers"]
        self.assertEqual(len(L["1119"]["axis"]), 2)
        self.assertGreaterEqual(len(L["1123"]["axis"]), 20)
        self.assertGreaterEqual(len(L["1130"]["axis"]), 3)
        self.assertGreaterEqual(len(self.out["rivers"]["minor"]) + len(self.out["rivers"]["major"]), 50)
        repo = json.loads((PROJ / "fronts.json").read_text(encoding="utf-8"))
        self.assertEqual(repo["layers"], L)          # 저장소 fronts.json = 지금 다시 정합한 결과
        self.assertEqual(repo["rivers"], self.out["rivers"])

    def test_missing_graticule_line_fails(self) -> None:
        g = self.spec.fronts.graticule
        grid = collect(PROJ / self.spec.fronts.reference.file)[(g.stroke, round(g.width, 2), g.dash)]
        vert = [x for x in grid if abs(x[0, 0] - x[-1, 0]) < abs(x[0, 1] - x[-1, 1])]
        with self.assertRaises(ValueError):
            fit_graticule([x for x in grid if x is not vert[0]], g.lons, g.lats)   # 세로선 하나 빠짐 → 교차점 6 < 9


class PocketTest(unittest.TestCase):
    def test_reviewed_pockets_pass_with_sliver_warning(self) -> None:
        r = run(raw_spec())
        self.assertEqual(r.hard, [], [f.message for f in r.hard])
        self.assertEqual([f.id for f in r.warnings], ["SK-G2", "SK-G2"])     # D-0146 — 미세 조각 2

    def test_self_intersecting_recipe_fails(self) -> None:
        raw = raw_spec()
        raw["pockets"][0]["build"] = [{"points": [[43.0, 48.5], [44.0, 49.0], [44.0, 48.5], [43.0, 49.0]]}]   # 나비 모양
        self.assertIn("SK-G2", ids(run(raw)))
        r = CheckReport()
        pocket_validity(r, "빈", Polygon(), SK.checks.pocket_sliver_ratio)
        self.assertEqual([f.id for f in r.hard], ["SK-G2"])

    def test_recipe_builds_reviewed_polygon(self) -> None:
        sp = load_spec(PROJ, CampaignSpec)
        data = FrontData(PROJ / "fronts.json")
        ring, north, arc = data.piece("1123:axis:10"), data.piece("1119:axis:1"), data.piece("1123:axis:8")
        city = np.array([[44.61, 48.79], [44.67, 48.92]])
        p23 = np.vstack([ring, city, north[north[:, 0] >= ring[0, 0]]])
        i0 = int(np.argmin(np.linalg.norm(ring - arc[-1], axis=1)))
        p30 = np.vstack([ring[i0:], city, north[north[:, 0] >= arc[0, 0]], arc])
        np.testing.assert_array_equal(build_polygon(sp.pockets[0], data), p23)   # 4d9dc65 pocket_1123 식
        np.testing.assert_array_equal(build_polygon(sp.pockets[1], data), p30)   # pocket_1130 식


class SpecChecksTest(unittest.TestCase):
    def test_echelon_and_arm_typo(self) -> None:
        raw = raw_spec()
        raw["units"][0]["echelon"] = "XXXXX"
        self.assertIn("SK-G3", ids(run(raw)))
        raw = raw_spec()
        raw["units"][0]["arm"] = "artillery"
        self.assertIn("SK-G3", ids(run(raw)))

    def test_h5_approx_note(self) -> None:
        self.assertNotIn("SK-H5", ids(run(raw_spec())))
        raw = raw_spec()
        raw["notes"]["source_lines"][0]["text"] = "전선·부대 위치 — 출처는 끝 화면"
        self.assertIn("SK-H5", ids(run(raw)))
        raw = raw_spec()
        raw["notes"]["source_lines"][0]["t1"] = 30.0          # 중간에 사라짐
        self.assertIn("SK-H5", ids(run(raw)))

    def test_h1_unit_numbers(self) -> None:
        raw = raw_spec()
        raw["tags"][2]["text"] = "포위망 — 약 300km 둘레"
        self.assertIn("SK-H1", ids(run(raw)))

    def test_city_check(self) -> None:
        """도시 검산(D-0147 A) — 두 도시 ≤ checks.georef_city_deg 통과, 임계 0.03 이면 두 도시 모두 실패, places 에 없는 이름은 hard."""
        sp = load_spec(PROJ, CampaignSpec)
        data = FrontData(PROJ / sp.fronts.file)
        off = dict(city_offsets(sp, PROJ, data))
        self.assertEqual(set(off), {"스탈린그라드", "칼라치"})
        self.assertAlmostEqual(off["스탈린그라드"], 0.0645, delta=0.0005)    # 지도 기호 배치 차(볼가강 기슭)
        self.assertAlmostEqual(off["칼라치"], 0.0348, delta=0.0005)
        r = CheckReport()
        check_cities(r, sp, PROJ, data, SK.checks.georef_city_deg)
        self.assertEqual(r.hard, [])
        r = CheckReport()
        check_cities(r, sp, PROJ, data, 0.03)
        self.assertEqual([f.id for f in r.hard], ["SK-G1", "SK-G1"])
        raw = raw_spec()
        raw["fronts"]["city_check"] = ["차리친"]
        self.assertIn("SK-G1", ids(run(raw)))

    def test_r1_reference_license(self) -> None:
        rights = json.loads((PROJ / "RIGHTS.json").read_text(encoding="utf-8"))
        bad = copy.deepcopy(rights)
        bad["files"]["ref_operation_uranus.svg"]["license"] = "CC BY-NC 4.0"
        self.assertIn("SK-R1", ids(run(raw_spec(), bad)))
        bad = copy.deepcopy(rights)
        del bad["files"]["ref_operation_uranus.svg"]
        self.assertIn("SK-R1", ids(run(raw_spec(), bad)))


class _View:
    """화면 = 경위도 그대로(테스트용 항등 뷰)."""

    def to_screen_arr(self, xy: np.ndarray) -> np.ndarray:
        return np.asarray(xy, float) * 100


def _ctx() -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 64, 64))


class DrawingTest(unittest.TestCase):
    def test_unit_reserve_box(self) -> None:
        from sketch.campaign.units import UnitLayer

        sp = load_spec(PROJ, CampaignSpec)
        sp = sp.model_copy(update={"units": [sp.units[0]]})
        layer = UnitLayer(sp)

        class V:
            def to_screen(self, lon: float, lat: float) -> tuple[float, float]:
                return 400.0, 200.0
        res: list = []
        layer.draw(_ctx(), V(), 10.0, res)
        pad, top, bottom = SK.campaign.unit_box
        x0, y0, x1, y1 = res[0]
        self.assertEqual((y0, y1), (200.0 - top, 200.0 + bottom))
        self.assertGreaterEqual(x1 - x0, SK.campaign.symbol.w + 2 * pad)   # 최소 폭 = 부호 폭 + 여백

    def test_arrow_grows_monotonically(self) -> None:
        pts = [(1.0, 1.0), (1.3, 1.2), (1.6, 1.15), (2.0, 1.4)]
        lens = []
        for prog in (0.2, 0.4, 0.6, 0.8, 1.0):
            lens.append(arrows_mod.arrow(_ctx(), _View(), pts, prog, 1.0, (1, 0, 0)))
        xs = [m[0] for m in lens if m]
        self.assertEqual(xs, sorted(xs))            # 가운데 점이 머리 쪽으로만 움직인다
        self.assertGreater(len(set(xs)), 3)

    def test_front_offset_side(self) -> None:
        """소련 선 = 추축 선을 화면 법선 (−dy, dx) 방향으로 offset_px 옮긴 것(서 → 동 선이면 화면 아래 = 남쪽)."""
        calls = []
        orig = fronts_mod.glow_line
        fronts_mod.glow_line = lambda ctx, S, col, a, w, dash=None: calls.append(np.array(S))   # type: ignore[assignment]
        try:
            P = np.array([[1.0, 48.0], [1.5, 48.0], [2.0, 48.0]])
            fronts_mod.front_line(_ctx(), _View(), P, 1.0, 1.0, False)
        finally:
            fronts_mod.glow_line = orig
        axis, soviet = calls
        np.testing.assert_allclose(soviet - axis, [[0, SK.campaign.front.offset_px]] * 3)   # y 증가 = 화면 아래


@unittest.skipUnless((PROJ / "assets" / "tiers.pkl").is_file(),
                     "uranus_sketch 지형 자산 없음 — `python -m geo.prep projects/uranus_sketch`(phaseS0 run_log §0)")
class CampaignFramesTest(unittest.TestCase):
    def test_frames_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "p"
            shutil.copytree(PROJ, proj, ignore=shutil.ignore_patterns("out", "res_720p"))
            r = subprocess.run([sys.executable, "-m", "sketch.campaign", str(proj), "--frames", "20,42"], cwd=REPO,
                               capture_output=True, text=True, timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr)
            prov = json.loads((proj / "out" / "sketch_provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(prov["kind"], "campaign")
            self.assertEqual(prov["checks"]["hard"], [])
            self.assertEqual({w["id"] for w in prov["checks"]["warnings"]} - {"SK-C2"}, {"SK-G2"})
            self.assertIn("pocket:11.23 포위망", prov["features_drawn"])
            self.assertEqual({f["path"] for f in prov["data_files"]}, {"ref_operation_uranus.svg", "fronts.json"})


if __name__ == "__main__":
    unittest.main()

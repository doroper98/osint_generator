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


def _old_arrow_path(S: np.ndarray, prog: float) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """4d9dc65 원본 — 꼭짓점 단위로 자른 경로(searchsorted), u = linspace, 라벨 = P[len // 2]."""
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))])
    k = int(np.searchsorted(L, L[-1] * prog))
    if k < 2:
        return None
    P = S[:k]
    return P, np.linspace(0, 1, len(P)), P[len(P) // 2]


class ArrowGrowthTest(unittest.TestCase):
    """D-0154 S5(사용자 지적 "화살표 애니메이션이 드문드문") — 호 길이 보간. 완성 상태는 원본과 같다."""

    PTS = [[0.0, 0.0], [120.0, 40.0], [260.0, 10.0], [400.0, 90.0]]

    @classmethod
    def full(cls) -> np.ndarray:
        from engine.layers.routes import catmull  # noqa: PLC0415

        return catmull(cls.PTS, SK.campaign.arrow.spline)

    @classmethod
    def path(cls) -> np.ndarray:
        return arrows_mod.drawn_path(cls.full())

    def test_end_moves_continuously(self) -> None:
        P = self.path()
        total = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
        step = 0.01
        ends, es = [], []
        for prog in np.arange(0.05, 1.0 + 1e-9, step):
            g = arrows_mod.grown(P, float(prog))
            assert g is not None
            ends.append(g[0][-1])
            es.append(g[2])
        moves = np.linalg.norm(np.diff(np.array(ends), axis=0), axis=1)
        self.assertTrue(np.all(np.diff(es) > 0))                                     # 끝 위치 단조 증가
        self.assertLessEqual(float(moves.max()), total * step + SK.campaign.arrow.max_step_px)
        self.assertGreater(float(moves.min()), 0)                                    # 멈추는 프레임 없음
        old = [(_old_arrow_path(self.full(), float(p)) or (P[:1],))[0][-1] for p in np.arange(0.05, 1.0 + 1e-9, step)]
        old_moves = np.linalg.norm(np.diff(np.array(old), axis=0), axis=1)
        self.assertGreater(int((old_moves == 0).sum()), 0)                           # 원본은 멈췄다 건너뛰었다(회귀 확인)

    def test_finished_arrow_equals_original(self) -> None:
        P = self.path()
        new = arrows_mod.grown(P, 1.0)
        old = _old_arrow_path(self.full(), 1.0)
        assert new is not None and old is not None
        np.testing.assert_array_equal(new[0], old[0])
        np.testing.assert_allclose(new[1], old[1])
        np.testing.assert_array_equal(arrows_mod.at_index(P, (new[2] + 1) * 0.5), old[2])

    def test_width_and_label_follow_end(self) -> None:
        P = self.path()
        a, b = arrows_mod.grown(P, 0.50), arrows_mod.grown(P, 0.51)
        assert a is not None and b is not None
        self.assertAlmostEqual(float(a[1][-1]), 1.0)                                 # 머리 쪽 폭은 늘 끝점에
        self.assertLess(float(np.linalg.norm(arrows_mod.at_index(P, (b[2] + 1) * 0.5)
                                             - arrows_mod.at_index(P, (a[2] + 1) * 0.5))),
                        float(np.linalg.norm(b[0][-1] - a[0][-1])) + SK.campaign.arrow.max_step_px)


    def test_zero_length_segments_and_start(self) -> None:
        P = np.array([[0.0, 0.0], [0.0, 0.0], [10.0, 0.0], [10.0, 0.0], [20.0, 0.0]])   # 겹친 점
        self.assertIsNone(arrows_mod.grown(P[1:], 0.01))                               # 첫 구간 안 = 아직 그리지 않음
        np.testing.assert_allclose(arrows_mod.grown(P, 0.01)[0][-1], [0.2, 0.0])       # 겹친 점은 건너뛰고 길이대로
        g = arrows_mod.grown(P, 0.75)
        assert g is not None
        np.testing.assert_allclose(g[0][-1], [15.0, 0.0])
        self.assertTrue(np.all(np.isfinite(g[1])))


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

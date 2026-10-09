"""미사일 스케치(sketch/missile) — D-0140 §5 S1, D-0142.

검사 SK-H1~H5·C2·R1 양성·음성 각 1(14) + 포맷터·hatch 가드·prep_eez 분할·CLI 종료 코드·렌더 통합.
음성은 저장소 spec(사용자 검토본) 사본을 한 군데만 깨뜨려 만든다. 렌더 통합은 지형 자산이 없으면 사유 있는 skip.
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
import yaml
from pydantic import ValidationError

from rules import load_rules
from sketch.common.checks import CheckReport, check_label_overlap, check_rights, spec_errors
from sketch.common.draw import hatch
from sketch.common.spec import MediaItem, load_spec
from sketch.missile.checks import check_render, check_spec
from sketch.missile.numbers import Numbers, fmt
from sketch.missile.prep_eez import nk_extension, west_sea_split
from sketch.missile.spec import MissileSpec, Num
from tests.anti_inertia._ast_util import REPO

PROJ = REPO / "projects" / "d1_missile_sketch"
SK = load_rules().sketch


def raw_spec() -> dict:
    return yaml.safe_load((PROJ / "sketch.yaml").read_text(encoding="utf-8"))


def run_checks(raw: dict, media_dir: Path | None = None) -> CheckReport:
    """사본 spec 로 렌더 전 검사. 스키마 위반도 SK 번호 발견으로."""
    r = CheckReport()
    try:
        spec = MissileSpec.model_validate(raw)
    except ValidationError as e:
        spec_errors(r, e)
        return r
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        shutil.copytree(media_dir or PROJ / "media", proj / "media")
        check_spec(r, spec, proj)
    return r


def ids(r: CheckReport) -> set[str]:
    return {f.id for f in r.hard}


class ReviewedSpecTest(unittest.TestCase):
    """양성 — 사용자 검토본 spec 은 렌더 전 검사 hard 0(H1·H2·H3·H4·H5·R1 양성 겸)."""

    def test_reviewed_spec_passes(self) -> None:
        r = run_checks(raw_spec())
        self.assertEqual(r.hard, [], [f.message for f in r.hard])
        for cid in ("SK-H1", "SK-H2", "SK-H3", "SK-H4", "SK-H5", "SK-C1", "SK-R1"):
            self.assertIn(cid, r.ran)


class H1NumbersTest(unittest.TestCase):
    def test_formatter_values(self) -> None:
        self.assertEqual(fmt(Num(v=1000, unit="km", approx=True)), "약 1,000km")
        self.assertEqual(fmt(Num(v=6040.9, unit="km")), "6,040.9km")
        self.assertEqual(fmt(Num(v=22, unit="mach", approx=True)), "약 마하 22")
        self.assertEqual(fmt(Num(v=4135, unit="sec")), "4,135초")
        nums = Numbers(load_spec(PROJ, MissileSpec))
        self.assertEqual(nums.fill("비행 {mod.flight_sec}({mod.flight_min})"), "비행 4,135초(약 69분)")
        self.assertIn("mod.flight_sec", nums.shown)
        with self.assertRaises(KeyError):
            nums.fill("{mod.computed_km}")

    def test_computed_distance_rejected(self) -> None:
        """음성 — 계산한 거리(980km)를 자유 문구로 적으면 위반, 모르는 자리표시도 위반."""
        raw = raw_spec()
        raw["track"]["hud"]["range_line"] = "비행거리 약 980km · 계산"
        self.assertIn("SK-H1", ids(run_checks(raw)))
        raw = raw_spec()
        raw["track"]["impact"]["sub"] = "오시마오시마 서쪽 {track.gc_km}"
        self.assertIn("SK-H1", ids(run_checks(raw)))

    def test_render_numbers_outside_table(self) -> None:
        spec = load_spec(PROJ, MissileSpec)
        nums = Numbers(spec)
        nums.shown["calc.gc_km"] = "약 980km"
        r = CheckReport()
        check_render(r, spec, {"impact_area": 1}, nums, [], 0)
        self.assertIn("SK-H1", ids(r))


class H1FlightClockTest(unittest.TestCase):
    """D-0149 3-3 — 비행 경과 시계 원천 = announced sec 값(없으면 min × 60). 지어낸 값은 SK-H1 hard."""

    def test_reviewed_clock_source(self) -> None:
        r = run_checks(raw_spec())
        self.assertNotIn("SK-H1", ids(r))
        nums = Numbers(MissileSpec.model_validate(raw_spec()))
        nums.clock(4135)
        self.assertEqual(nums.shown, {"track.flight_sec ← mod.flight_sec": "+68:55"})
        r = CheckReport()
        check_render(r, MissileSpec.model_validate(raw_spec()), {}, nums, [], 0.0)
        self.assertEqual(r.hard, [])

    def test_invented_flight_sec(self) -> None:
        raw = raw_spec()
        raw["track"]["flight_sec"] = 9999
        r = run_checks(raw)
        self.assertIn("SK-H1", ids(r))
        self.assertTrue(any("mod.flight_sec=4135" in f.message for f in r.hard))

    def test_minutes_only_source(self) -> None:
        raw = raw_spec()
        del raw["announced"]["mod"]["values"]["flight_sec"]
        raw["announced"]["mod"]["values"]["flight_min"] = {"v": 69, "unit": "min"}
        raw["announced"]["mod"]["rows"] = ["거리 {mod.range_km}", "고도 {mod.apogee_km}", "비행 {mod.flight_min}"]
        raw["track"]["flight_sec"] = 69 * 60
        self.assertNotIn("SK-H1", ids(run_checks(raw)))
        nums = Numbers(MissileSpec.model_validate(raw))
        nums.clock(69 * 60)
        self.assertEqual(list(nums.shown), ["track.flight_sec ← mod.flight_min×60"])


class H2ImpactAreaTest(unittest.TestCase):
    def test_approx_needs_area(self) -> None:
        raw = raw_spec()
        raw["track"]["uncertainty_km"] = 0
        self.assertIn("SK-H2", ids(run_checks(raw)))

    def test_render_without_area(self) -> None:
        spec = load_spec(PROJ, MissileSpec)
        r = CheckReport()
        check_render(r, spec, {"track": 1}, Numbers(spec), [], spec.duration_sec)
        self.assertIn("SK-H2", ids(r))
        r = CheckReport()
        check_render(r, spec, {"track": 1, "impact_area": 3}, Numbers(spec), [], spec.duration_sec)
        self.assertNotIn("SK-H2", ids(r))


class H3UndisclosedTest(unittest.TestCase):
    def test_undisclosed_needs_tag_and_ship_no_range(self) -> None:
        raw = raw_spec()
        g = next(s for s in raw["sensors"] if s["name"] == "그린파인 레이더")
        g.pop("tag")
        self.assertIn("SK-H3", ids(run_checks(raw)))
        raw = raw_spec()
        ship = next(s for s in raw["sensors"] if s["kind"] == "ship")
        ship["range_km"] = 400
        self.assertIn("SK-H3", ids(run_checks(raw)))

    def test_render_point_for_undisclosed(self) -> None:
        spec = load_spec(PROJ, MissileSpec)
        r = CheckReport()
        check_render(r, spec, {"impact_area": 1, "sensor_point:그린파인 레이더": 2, "sensor_point:사드 AN/TPY-2 · 성주": 2},
                     Numbers(spec), [], spec.duration_sec)
        self.assertEqual([f.id for f in r.hard], ["SK-H3"])


class H4OverlapTest(unittest.TestCase):
    def test_single_color_overlap_rejected(self) -> None:
        raw = raw_spec()
        raw["eez"]["nations"]["RU"]["color"] = "teal"     # 쿠릴 = JP(teal)·RU(teal) → 한 색
        self.assertIn("SK-H4", ids(run_checks(raw)))

    def test_hatch_guard_and_render_record(self) -> None:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, 32, 32)
        ctx = cairo.Context(surf)
        ctx.rectangle(0, 0, 32, 32)
        ctx.clip()
        hatch(ctx, [(1, 0, 0), (0, 0, 1)], 1, 5, 1)
        with self.assertRaises(ValueError):
            hatch(ctx, [(1, 0, 0)], 1, 5, 1)
        with self.assertRaises(ValueError):
            hatch(ctx, [(1, 0, 0), (1, 0, 0)], 1, 5, 1)
        spec = load_spec(PROJ, MissileSpec)
        r = CheckReport()
        check_render(r, spec, {"impact_area": 1, "overlap_hatch_colors:1": 1}, Numbers(spec), [], spec.duration_sec)
        self.assertIn("SK-H4", ids(r))


class H5ApproxNoteTest(unittest.TestCase):
    def test_source_line_without_word(self) -> None:
        raw = raw_spec()
        for n in raw["notes"]["source_lines"]:
            n["text"] = n["text"].replace("개략", "")
        self.assertIn("SK-H5", ids(run_checks(raw)))

    def test_end_card_without_word(self) -> None:
        raw = raw_spec()
        for s in raw["sources"]:
            s["text"] = s["text"].replace("개략", "")
        r = run_checks(raw)
        self.assertEqual(ids(r), {"SK-H5"}, [f.message for f in r.hard])


class C2LabelOverlapTest(unittest.TestCase):
    def test_overlap_warning(self) -> None:
        r = CheckReport()
        n = check_label_overlap(r, [(1.0, [(0, 0, 10, 10), (5, 5, 20, 20)]), (2.0, [(0, 0, 10, 10), (20, 0, 30, 10)])], SK.checks)
        self.assertEqual(n, 1)
        self.assertEqual([f.id for f in r.warnings], ["SK-C2"])
        self.assertEqual(r.hard, [])

    def test_touching_is_not_overlap(self) -> None:
        r = CheckReport()
        self.assertEqual(check_label_overlap(r, [(1.0, [(0, 0, 10, 10), (10, 0, 20, 10)])], SK.checks), 0)
        self.assertEqual(r.warnings, [])


class R1RightsTest(unittest.TestCase):
    def _media(self, d: Path, entry: dict | None) -> Path:
        m = d / "media"
        m.mkdir()
        shutil.copy(PROJ / "media" / "hwasong17_diagram.png", m)
        files = {} if entry is None else {"hwasong17_diagram.png": entry}
        (m / "RIGHTS.json").write_text(json.dumps({"schema_version": 1, "files": files}), encoding="utf-8")
        return m

    def test_license_outside_list_and_missing_entry(self) -> None:
        good = json.loads((PROJ / "media" / "RIGHTS.json").read_text(encoding="utf-8"))["files"]["hwasong17_diagram.png"]
        item = [MediaItem(file="hwasong17_diagram.png", credit="Geoarchive", license="CC BY-NC 4.0", t0=0, t1=1)]
        with tempfile.TemporaryDirectory() as d:
            bad = dict(good, license="CC BY-NC 4.0")
            r = CheckReport()
            check_rights(r, self._media(Path(d), bad), item, SK.rights.allowed_licenses)
            self.assertTrue(any("허용 목록" in f.message for f in r.hard))
        with tempfile.TemporaryDirectory() as d:
            r = CheckReport()
            check_rights(r, self._media(Path(d), None), item, SK.rights.allowed_licenses)
            self.assertTrue(any("항목 없음" in f.message for f in r.hard))

    def test_spec_license_mismatch(self) -> None:
        raw = raw_spec()
        raw["media"][0]["license"] = "CC BY 4.0"
        self.assertIn("SK-R1", ids(run_checks(raw)))


class PrepEezTest(unittest.TestCase):
    def test_west_sea_split(self) -> None:
        p = load_spec(PROJ, MissileSpec).eez.prep
        north, south = west_sea_split(p)
        self.assertTrue(north.is_valid and south.is_valid)
        self.assertGreater(north.area, 0)
        self.assertGreater(south.area, 0)
        self.assertEqual(north.intersection(south).area, 0)
        x, y = nk_extension(p)
        self.assertEqual(y, p.west_box[1])
        eez = json.loads((PROJ / "eez.json").read_text(encoding="utf-8"))
        nk = next(f for f in eez["features"] if f["code"] == "NK1999")
        self.assertAlmostEqual(nk["lines"][1][-1][0], round(x, 3), places=3)   # 저장소 eez.json 연장선 끝 = 같은 식


class CliTest(unittest.TestCase):
    def _run(self, proj: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-m", "sketch.missile", str(proj), *args], cwd=REPO, capture_output=True,
                              text=True, timeout=600)

    def test_check_exit_codes(self) -> None:
        self.assertEqual(self._run(PROJ, "--check").returncode, 0)
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            shutil.copytree(PROJ / "media", proj / "media")
            raw = copy.deepcopy(raw_spec())
            raw["eez"]["regions"][0]["claimants"] = ["KR", "KR"]
            (proj / "sketch.yaml").write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
            r = self._run(proj, "--check")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("SK-H4", r.stderr)
            r = self._run(proj)           # 렌더도 거부(지형을 읽기 전에 멈춘다)
            self.assertEqual(r.returncode, 1)


@unittest.skipUnless((PROJ / "assets" / "tiers.pkl").is_file(),
                     "d1_missile_sketch 지형 자산 없음 — `python -m geo.prep projects/d1_missile_sketch`(phaseS1 run_log §0)")
class RenderFramesTest(unittest.TestCase):
    def test_frames_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "p"
            shutil.copytree(PROJ, proj, ignore=shutil.ignore_patterns("out", "res_720p", "globe_tex"))
            r = subprocess.run([sys.executable, "-m", "sketch.missile", str(proj), "--frames", "14,41"], cwd=REPO,
                               capture_output=True, text=True, timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr)
            prov = json.loads((proj / "out" / "sketch_provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(prov["checks"]["hard"], [])
            self.assertEqual(prov["render"]["profile"], "480p")
            self.assertIn("impact_area", prov["features_drawn"])
            self.assertNotIn("sensor_point:그린파인 레이더", prov["features_drawn"])
            self.assertIn("track.distance_km=약 210km", prov["numbers_shown"])
            self.assertTrue((proj / "out" / "sketch_2d_041.0.png").is_file())


if __name__ == "__main__":
    unittest.main()

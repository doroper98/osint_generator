"""스케치 공통(sketch/common) 단위 테스트 — D-0140 §5 S0, D-0141.

geodesy 4 · camera 2 · SK-C1 양성 1·음성 3 · spec 2 · checks 틀 · rules 로드 · CLI --help.
카메라 기대값은 4d9dc65 `projects/d1_missile_sketch/sketch_d1.py camera()` 를 같은 숏·푸시인으로 다시 계산한 값과 대조한다.
"""

from __future__ import annotations

import math
import subprocess
import sys
import unittest

import yaml
from pydantic import ValidationError

from engine.stage import ym
from engine.style import FONT, FPS
from engine.timebase import clamp01, ease_io, smooth
from rules import load_rules
from sketch.common.camera import CameraPath
from sketch.common.checks import CHECK_IDS, CheckReport, SketchCheckError, check_camera
from sketch.common.geodesy import EARTH_KM, bearing, dest, gc_dist, gc_path, horizon_altitude, sector
from sketch.common.spec import SketchSpec, Shot
from tests.anti_inertia._ast_util import REPO

# 4d9dc65 sketch_d1.SHOTS(사용자 검토본) — (시작, 이동 끝, 경도, 위도, w)
MISSILE_SHOTS = [(0.0, 0.0, 132.6, 36.6, 37.0), (8.4, 11.0, 126.9, 38.15, 9.5),
                 (16.8, 19.2, 132.0, 38.6, 25.0), (27.8, 30.2, 132.9, 40.3, 19.5)]
MISSILE_TOTAL = 56.0
# 4d9dc65 uranus_sketch.SHOTS
URANUS_SHOTS = [(0.0, 0.0, 42.75, 48.85, 6.6), (13.0, 15.6, 43.05, 49.22, 2.7), (24.0, 26.6, 44.05, 48.22, 2.7),
                (32.6, 35.2, 43.98, 48.74, 2.3), (43.5, 46.2, 43.35, 48.55, 4.4)]
URANUS_TOTAL = 58.0


def _shots(rows: list[tuple[float, float, float, float, float]]) -> tuple[Shot, ...]:
    return tuple(Shot(t0=a, t1=b, lon=x, lat=y, w=w) for a, b, x, y, w in rows)


def _orig_camera(t: float, push: float) -> tuple[float, float, float]:
    """4d9dc65 sketch_d1.camera() 원문 그대로(대조용)."""
    S = MISSILE_SHOTS
    i = max(j for j, s in enumerate(S) if t >= s[0])
    cur = S[i]
    if i == 0:
        px, py, pw = cur[2], ym(cur[3]), cur[4]
    else:
        prev = S[i - 1]
        px, py, pw = prev[2], ym(prev[3]), prev[4] * (1 - push)
    k = ease_io(clamp01((t - cur[0]) / max(1e-6, cur[1] - cur[0]))) if cur[1] > cur[0] else 1.0
    x = px + (cur[2] - px) * k
    y = py + (ym(cur[3]) - py) * k
    w = math.exp(math.log(pw) + (math.log(cur[4]) - math.log(pw)) * k)
    nxt = S[i + 1][0] if i + 1 < len(S) else MISSILE_TOTAL
    w *= 1 - push * smooth(clamp01((t - cur[1]) / max(1.0, nxt - cur[1])))
    return x, y, w


class GeodesyTest(unittest.TestCase):
    def test_dest_gc_dist_roundtrip(self) -> None:
        for lon, lat, brg, km in ((125.67, 39.20, 95.0, 1000.0), (139.37, 41.51, 270.0, 210.0), (44.5, 48.7, 213.0, 64.0)):
            p = dest(lon, lat, brg, km)
            self.assertAlmostEqual(gc_dist((lon, lat), p), km, delta=1e-6)
            self.assertAlmostEqual(bearing((lon, lat), p), brg, delta=1e-6)

    def test_bearing_known_values(self) -> None:
        self.assertAlmostEqual(bearing((0.0, 0.0), (0.0, 10.0)), 0.0, delta=1e-9)     # 정북
        self.assertAlmostEqual(bearing((0.0, 0.0), (10.0, 0.0)), 90.0, delta=1e-9)    # 적도 정동
        self.assertAlmostEqual(bearing((0.0, 10.0), (0.0, 0.0)), 180.0, delta=1e-9)   # 정남
        self.assertAlmostEqual(gc_dist((0.0, 0.0), (0.0, 1.0)), EARTH_KM * math.pi / 180, delta=1e-9)

    def test_horizon_altitude_known_values(self) -> None:
        self.assertAlmostEqual(horizon_altitude(425), 14.2, delta=0.05)    # 성주 → 순안 패널값 14 km
        self.assertAlmostEqual(horizon_altitude(1260), 127, delta=0.5)     # 교가미사키 → 순안 127 km
        self.assertEqual(horizon_altitude(0), 0.0)
        with self.assertRaises(ValueError):
            horizon_altitude(-1)

    def test_paths_and_sector(self) -> None:
        a, b = (125.67, 39.20), (136.90, 41.42)
        P = gc_path(a, b, 160)
        self.assertEqual(P.shape, (160, 2))
        self.assertAlmostEqual(P[0, 0], a[0], delta=1e-9)
        self.assertAlmostEqual(gc_dist(tuple(P[-1]), b), 0.0, delta=1e-6)
        seg = sum(gc_dist(tuple(P[i]), tuple(P[i + 1])) for i in range(159))
        self.assertAlmostEqual(seg, gc_dist(a, b), delta=1e-6)     # 대원 위 점들 — 구간 합 = 전체 거리
        sec = sector((128.28, 35.99), 300.0, 120.0, 600.0, 48)
        self.assertEqual(sec.shape, (50, 2))
        self.assertEqual(tuple(sec[0]), tuple(sec[-1]))
        for p in sec[1:-1]:
            self.assertAlmostEqual(gc_dist((128.28, 35.99), tuple(p)), 600.0, delta=1e-6)
        with self.assertRaises(ValueError):
            gc_path(a, b, 1)


class CameraTest(unittest.TestCase):
    def setUp(self) -> None:
        self.push = load_rules().sketch.camera.push_in["missile"]
        self.cam = CameraPath(_shots(MISSILE_SHOTS), MISSILE_TOTAL, self.push, load_rules().sketch.camera.hold_min_sec)

    def test_matches_reviewed_missile_camera(self) -> None:
        """사용자 검토본 카메라와 전 프레임 동일(이식 회귀)."""
        for i in range(int(MISSILE_TOTAL * FPS)):
            t = i / FPS
            got, want = self.cam.at(t), _orig_camera(t, self.push)
            for g, w in zip(got, want):
                self.assertAlmostEqual(g, w, delta=1e-9, msg=f"t={t}")

    def test_move_starts_from_previous_end_state(self) -> None:
        """숏 경계에서 w 가 이어진다(앞 숏 푸시인 끝 → 이동 시작). 옛 방식(원래 w 에서 재시작)은 push_in 만큼 튄다."""
        eps = 1e-7
        for s in self.cam.shots[1:]:
            before, after = self.cam.at(s.t0 - eps)[2], self.cam.at(s.t0)[2]
            self.assertLess(abs(math.log(after / before)), 1e-4, f"숏 {s.t0} 경계")
        prev = self.cam.shots[0]
        jump_old = abs(math.log(prev.w / (prev.w * (1 - self.push))))
        self.assertGreater(jump_old, self.push * 0.9)    # 비교 기준: 옛 방식이었다면 이만큼 튐


def reviewed_paths() -> dict[str, CameraPath]:
    """사용자 검토본 두 카메라(R-0174 측정 대상)."""
    cam = load_rules().sketch.camera
    return {"missile": CameraPath(_shots(MISSILE_SHOTS), MISSILE_TOTAL, cam.push_in["missile"], cam.hold_min_sec),
            "campaign": CameraPath(_shots(URANUS_SHOTS), URANUS_TOTAL, cam.push_in["campaign"], cam.hold_min_sec)}


class _RestartPath(CameraPath):
    """옛 결함 재현(R-0174): 숏 사이 이동을 앞 숏의 '원래' w 에서 다시 시작한다 — 전환 첫 프레임에 줌이 push_in 만큼 튄다."""

    def at(self, t: float) -> tuple[float, float, float]:
        x, y, w = super().at(t)
        i = max(j for j, s in enumerate(self.shots) if t >= s.t0)
        cur = self.shots[i]
        if i > 0 and cur.t0 <= t < cur.t1:
            prev = self.shots[i - 1]
            k = ease_io(clamp01((t - cur.t0) / (cur.t1 - cur.t0)))
            lw_fixed = math.log(prev.w * (1 - self.push_in)) * (1 - k) + math.log(cur.w) * k
            lw_old = math.log(prev.w) * (1 - k) + math.log(cur.w) * k
            w *= math.exp(lw_old - lw_fixed)
        return x, y, w


class _Patched(CameraPath):
    """한 프레임 구간에만 (x, y, w) 를 바꾼 카메라(음성 주입)."""

    def __init__(self, base: CameraPath, t0: float, t1: float, dx: float = 0.0, w_mul: float = 1.0) -> None:
        super().__init__(base.shots, base.duration_sec, base.push_in, base.hold_min_sec)
        self.win, self.dx, self.w_mul = (t0, t1), dx, w_mul

    def at(self, t: float) -> tuple[float, float, float]:
        x, y, w = super().at(t)
        if self.win[0] <= t < self.win[1]:
            return x + self.dx * w, y, w * self.w_mul
        return x, y, w


class CameraCheckTest(unittest.TestCase):
    """SK-C1(D-0141): 1차 |Δ ln w| + 2차 |Δ² ln w|·|Δ² x|/w·|Δ² y|/w."""

    def setUp(self) -> None:
        self.th = load_rules().sketch.checks

    def _run(self, cam: CameraPath) -> CheckReport:
        r = CheckReport()
        check_camera(r, cam.track(FPS), FPS, self.th)
        return r

    def test_reviewed_cameras_pass(self) -> None:
        for name, cam in reviewed_paths().items():
            r = self._run(cam)
            self.assertEqual(r.hard, [], name)
            self.assertEqual(r.ran, ["SK-C1"])

    def test_old_restart_violates_second_difference(self) -> None:
        base = reviewed_paths()["missile"]
        r = self._run(_RestartPath(base.shots, base.duration_sec, base.push_in, base.hold_min_sec))
        self.assertTrue(r.hard)
        self.assertTrue(all("Δ² ln w" in f.message for f in r.hard), [f.message for f in r.hard])
        with self.assertRaises(SketchCheckError):
            r.raise_if_hard()

    def test_one_frame_zoom_jump_violates_first_difference(self) -> None:
        base = reviewed_paths()["missile"]
        r = self._run(_Patched(base, 40.0, 60.0, w_mul=0.85))     # 40초부터 끝까지 w 15 % 순간 축소 = 하드 컷
        self.assertTrue(any("|Δ ln w|" in f.message for f in r.hard), [f.message for f in r.hard])

    def test_center_jump_violates(self) -> None:
        base = reviewed_paths()["campaign"]
        r = self._run(_Patched(base, 20.0, 20.0 + 1 / FPS, dx=0.05))   # 한 프레임 중심이 화면 폭 5 % 튐
        self.assertTrue(any("Δ² x/w" in f.message for f in r.hard), [f.message for f in r.hard])
        self.assertFalse(any("ln w" in f.message for f in r.hard))


class SpecTest(unittest.TestCase):
    BASE = {"schema_version": 1, "kind": "missile", "title": "t", "date": "2022. 11. 18", "duration_sec": 56,
            "sources": [{"text": "합동참모본부 발표"}], "shots": [{"t0": 0, "t1": 0, "lon": 132.6, "lat": 36.6, "w": 37}]}

    def test_extra_key_rejected(self) -> None:
        SketchSpec.model_validate(self.BASE)
        with self.assertRaises(ValidationError):
            SketchSpec.model_validate({**self.BASE, "unknown_key": 1})
        with self.assertRaises(ValidationError):
            SketchSpec.model_validate({**self.BASE, "shots": [{"t0": 0, "t1": 0, "lon": 1, "lat": 1, "w": 1, "zoom": 2}]})

    def test_shot_order_rejected(self) -> None:
        bad = {**self.BASE, "shots": [{"t0": 0, "t1": 0, "lon": 1, "lat": 1, "w": 1},
                                      {"t0": 8, "t1": 12, "lon": 1, "lat": 1, "w": 1},
                                      {"t0": 10, "t1": 11, "lon": 1, "lat": 1, "w": 1}]}
        with self.assertRaises(ValidationError):
            SketchSpec.model_validate(bad)


class ChecksFrameworkTest(unittest.TestCase):
    def test_hard_raises_warning_records(self) -> None:
        r = CheckReport()
        r.add("SK-C2", "라벨 겹침")
        r.raise_if_hard()                       # warning 만으로는 멈추지 않는다
        r.add("SK-H3", "비공개 자산 기준점")
        with self.assertRaises(SketchCheckError):
            r.raise_if_hard()
        rec = r.record()
        self.assertEqual([f.id for f in rec.hard], ["SK-H3"])
        self.assertEqual([f.id for f in rec.warnings], ["SK-C2"])
        self.assertEqual(rec.ran, ["SK-C2", "SK-H3"])
        with self.assertRaises(KeyError):
            r.add("SK-X9", "모르는 검사")
        self.assertEqual(set(v for v in CHECK_IDS.values()), {"hard", "warning"})


class SketchRulesTest(unittest.TestCase):
    def test_rules_load_and_fonts_known(self) -> None:
        sk = load_rules().sketch
        self.assertEqual(set(sk.camera.push_in), {"missile", "campaign"})
        unknown = sorted(sk.fonts_used() - set(FONT))
        self.assertEqual(unknown, [], "rules sketch 글꼴 이름은 engine.style.FONT 키")

    def test_unknown_key_rejected(self) -> None:
        from schemas.rules_models import VideoRules
        raw = yaml.safe_load((REPO / "rules" / "video_rules.yaml").read_text(encoding="utf-8"))
        raw["sketch"]["camera"]["zoom_bump"] = 0.1
        with self.assertRaises(ValidationError):
            VideoRules.model_validate(raw)


class CliHelpTest(unittest.TestCase):
    def test_help_and_not_yet(self) -> None:
        for mod in ("sketch.missile", "sketch.campaign"):
            r = subprocess.run([sys.executable, "-m", mod, "--help"], cwd=REPO, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("--check", r.stdout)
            self.assertIn("--frames", r.stdout)
        r = subprocess.run([sys.executable, "-m", "sketch.missile", "--help"], cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertIn("--globe", r.stdout)


if __name__ == "__main__":
    unittest.main()

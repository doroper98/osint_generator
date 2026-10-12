"""v7.1.0 UF-99(recurs_of UF-02·UF-97, D-0220) — 카메라 꺾임의 진짜 원인 = 렌더 View 의 무대 경계 클램프.

- gulf v6.0.2 카메라 키(고정 자료, 전달본 그대로)로 hard camera_bounds 가 감독 실측 시각을 가리킨다.
- 같은 궤적을 요청 궤적으로 재면 camera_continuity·camera_speed 가 통과했다(장치가 못 잡은 이유) — 화면 궤적으로 재면 실패한다.
- 경계 안 키 두 개 사이 이동은 클램프 0(fixed_point 경로 + 볼록 집합, 드리프트·creep 포함).
- 카메라 제안(frame_points)은 경계 안 키만 낸다. 스케치 SK-C1 도 같은 식(한 트랙에만 걸지 않는다, C12-3).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from engine import checks as C
from engine.camera import CamKey, bounds_excess, build_camera, max_view_w, screen_track
from engine.style import FPS
from rules import load_rules
from sketch.common.camera import bounds_stage

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures" / "camera" / "gulf_v602_keys.json"
GULF = REPO / "projects" / "gulf_pact_2026"
TOL = load_rules().qa_checks.camera_bounds_rel_tol


def _gulf() -> SimpleNamespace:
    doc = json.loads(FIX.read_text(encoding="utf-8"))
    keys = [CamKey(**k) for k in doc["keys"]]
    cams = build_camera(keys, doc["n_frames"], FPS, creep=[tuple(r) for r in doc["creep"]])
    return SimpleNamespace(cams=cams, keys=keys, events=[], plan=SimpleNamespace(cards=[]), n_frames=doc["n_frames"],
                           R=SimpleNamespace(stage=bounds_stage(GULF), cache={}))


def _starts(out: list[str]) -> list[float]:
    return [float(s.split("t=")[1].split("~")[0]) for s in out]


class GulfClampTest(unittest.TestCase):
    def test_camera_bounds_fails_at_measured_times(self) -> None:
        """감독 광류 실측(D-0220 §0): 29.71·132.50·288.62초 = 경계에 닿는 시각(±1프레임). 0초 오프닝도 경계 밖에서 시작."""
        out = C.check_camera_bounds(_gulf())
        self.assertIn("camera_bounds", C.HARD)
        st = _starts(out)
        self.assertEqual(len(st), 4, out)
        for want in (0.0, 29.71, 132.50, 288.62):
            self.assertTrue(any(abs(s - want) <= 1.5 / FPS + 0.01 for s in st), (want, st))
        self.assertTrue(all("허용 최대 w 54.0" in s for s in out), out)

    def test_requested_track_passed_screen_track_fails(self) -> None:
        """재는 것 ≠ 보이는 것 — 요청 궤적(옛 측정)은 통과, 화면 궤적(새 측정)은 같은 영상에서 꺾임을 잡는다."""
        P = _gulf()   # noqa: N806
        wide = SimpleNamespace(**{**vars(P), "R": SimpleNamespace(stage=SimpleNamespace(bounds=(-1e6, -1e6, 1e6, 1e6), name="mercator"))})
        self.assertEqual(C.check_camera_continuity(wide), [])
        self.assertEqual(C.check_camera_speed(wide), [])
        cont = C.check_camera_continuity(P)
        self.assertTrue(cont and any("꺾임" in s for s in cont), cont)
        sp = screen_track(P.R.stage, np.asarray(P.cams))
        jump = np.abs(np.diff(np.diff(np.log(sp[:, 2])))) * FPS * FPS   # 줌 가속도(/초²)
        i = int(np.argmax(jump))
        self.assertTrue(any(abs(i / FPS - t) < 0.2 for t in (29.71, 30.04, 61.67, 132.92, 192.83, 288.96, 300.38)), i / FPS)


class ConvexityTest(unittest.TestCase):
    def test_in_bounds_keys_never_clamp(self) -> None:
        """fixed_point 경로에서 (x, y, w) 는 이동 한 번 동안 직선 위 + 경계 안 집합은 볼록 → 두 키가 경계 안이면 이동 전체가 경계 안.
        드리프트·creep 은 w 를 줄이는 쪽이라 경계를 넘지 않는다."""
        st = bounds_stage(GULF)
        bx0, by0, bx1, by1 = st.bounds
        wmax = max_view_w(st)
        rng = np.random.default_rng(7)
        for _ in range(40):
            keys, t = [], 0.0
            for j in range(4):
                w = float(rng.uniform(2.0, wmax - 0.05))
                h = w * 480 / 854
                x = float(rng.uniform(bx0 + w / 2, bx1 - w / 2))
                y = float(rng.uniform(by0 + h / 2, by1 - h / 2))
                keys.append(CamKey(t=t, x=x, y=y, w=w, dur=0 if j == 0 else float(rng.uniform(2.6, 7.0)), mode="cut" if j == 0 else "move"))
                t += float(rng.uniform(4.0, 12.0))
            n = int((t + 15) * FPS)
            cams = build_camera(keys, n, FPS, creep=[(t * 0.2, t * 0.8)])
            self.assertEqual(int((bounds_excess(st, cams).max(axis=1) > TOL).sum()), 0)


class SuggestTest(unittest.TestCase):
    def test_frame_points_in_bounds(self) -> None:
        """장소가 경계 가장자리에 있어도 제안 카메라는 경계 안(받아들여도 클램프 0). 실패 틀도 경계 안."""
        from engine.framing import FramePoint, frame_points  # noqa: PLC0415

        st = bounds_stage(GULF)
        bx0, by0, bx1, by1 = st.bounds
        cases = [[FramePoint(x=bx0 + 0.3, y=(by0 + by1) / 2, up=20, down=20, side=20)], [FramePoint(x=bx0 + 1, y=by0 + 1, up=20, down=20, side=20), FramePoint(x=bx1 - 1, y=by1 - 1, up=20, down=20, side=20)]]
        for pts in cases:
            r = frame_points(pts, bounds=st.bounds)
            d = bounds_excess(st, np.array([[r.x, r.y, r.w]]))
            self.assertLessEqual(float(d.max()), TOL, (r, d))


class DirectorInputTest(unittest.TestCase):
    def test_geo_text_max_w_from_bounds(self) -> None:
        """연출 입력 지오 역량의 w 상한 = 무대 경계(옛 고정 문구 '2.5~96' 이 gulf 경계 54 보다 넓은 키를 허용했다)."""
        from workers.direction_io import geo_text  # noqa: PLC0415

        txt = geo_text(GULF)
        self.assertIn("2.5~54.0", txt)
        self.assertNotIn("~96", txt)
        self.assertEqual(sum("[camera-bounds]" in g for g in load_rules().direction_grammar), 1)


class SketchTest(unittest.TestCase):
    def test_sk_c1_bounds_same_rule(self) -> None:
        """스케치 SK-C1 도 경계 밖 궤적을 실패로(같은 함수·같은 키) — 한 트랙에만 걸린 장치 = 미보호(UF-02 교훈)."""
        from sketch.common.checks import CheckReport, check_camera  # noqa: PLC0415

        st = bounds_stage(GULF)
        doc = json.loads(FIX.read_text(encoding="utf-8"))
        tr = build_camera([CamKey(**k) for k in doc["keys"]], doc["n_frames"], FPS)
        rep = CheckReport()
        check_camera(rep, tr, FPS, load_rules().sketch.checks, st)
        self.assertTrue(any("경계" in f.message for f in rep.hard), [f.message for f in rep.hard])


class TimelineDemoTest(unittest.TestCase):
    def test_fed_timeline_demo_in_bounds(self) -> None:
        pd = REPO / "projects" / "fed_timeline_demo"
        if not (pd / "plan.json").exists():
            self.skipTest("fed_timeline_demo plan 없음")
        from engine.project import load_project  # noqa: PLC0415

        self.assertEqual(C.check_camera_bounds(load_project(pd)), [])


if __name__ == "__main__":
    unittest.main()

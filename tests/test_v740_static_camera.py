"""v7.4.0 back_and_forth D-0241·D-0242(사용자 의견 UF-120·122·123·125) — 정지 카메라 [static-camera]·drift 등속 이동·항로 속도 [route-too-fast]·
바다만 보이는 프레임 [sea-only-frame]·화면 단위 [unit-ton-glyph]. D-0244 — 뱃지 원 안전 영역 [badge-clipped]."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from engine import checks as C
from engine.camera import build_camera, cam
from engine.stage import make_stage

FPS = 24


def _fake_project(track: np.ndarray, events: list[dict], total: float) -> SimpleNamespace:
    st = make_stage("mercator")
    st._bounds = (0.0, 0.0, 180.0, 80.0)   # 시험 무대 경계(월드) — 클램프가 시험 카메라를 바꾸지 않게
    tb = SimpleNamespace(in_fullcard=lambda t: False)
    return SimpleNamespace(cams=track, n_frames=len(track), events=events, keys=[], plan=SimpleNamespace(total=total),
                           R=SimpleNamespace(stage=st, tb=tb, cache={}), root=None)


class StaticCameraTest(unittest.TestCase):
    def _times(self, total: float) -> list[float]:
        return [k * 0.5 for k in range(int(total / 0.5))]

    def test_static_25s_is_hard(self) -> None:
        ts = self._times(30)
        tr = [(130.0, 45.0, 10.0)] * len(ts)
        self.assertEqual(len(C.static_windows(ts, tr, [], lambda t: False)), 1)
        self.assertIn("static_camera", C.HARD)

    def test_drift_passes(self) -> None:
        ts = self._times(30)
        tr = [(130.0 + 0.02 * t, 45.0, 10.0) for t in ts]   # 화면 폭 0.2 %/초 — 느리지만 정지 아님
        self.assertEqual(C.static_windows(ts, tr, [], lambda t: False), [])

    def test_new_element_passes(self) -> None:
        ts = self._times(30)
        tr = [(130.0, 45.0, 10.0)] * len(ts)
        self.assertEqual(C.static_windows(ts, tr, [12.0], lambda t: False), [])   # 12초에 카드가 뜬다 → 20초 창이 없다

    def test_drift_mode_is_linear(self) -> None:
        keys = [cam(0.0, 0.0, 0.0, 10.0, 0.0, "cut"), cam(1.0, 10.0, 0.0, 10.0, 10.0, "drift")]
        tr = build_camera(keys, 11 * FPS, FPS)
        v = np.diff(tr[FPS + 1:10 * FPS, 0])
        self.assertLess(float(v.max() - v.min()), 1e-6)   # 등속(이징 없음)


class RouteSpeedTest(unittest.TestCase):
    def test_fast_route_hard(self) -> None:
        tr = np.tile([125.0, 40.0, 20.0], (24 * 20, 1))
        route = {"type": "route", "t0": 1.0, "t1": 10.0, "grow": 1.0, "label": "레일라호", "world_pts": [(118.0, 40.0), (132.0, 40.0)]}
        P = _fake_project(tr, [route], 20.0)   # noqa: N806
        self.assertEqual(len(C.check_route_speed(P)), 1)
        route["grow"] = 30.0
        self.assertEqual(C.check_route_speed(P), [])
        self.assertIn("route_speed", C.HARD)


class UnitTonTest(unittest.TestCase):
    def test_t_after_number(self) -> None:
        ev = [{"type": "card", "bigs": [["약 2만 6천 t", "옮겨 받은 연료"]], "mid": "x_t"}, {"type": "card", "lines": ["약 5만 7천 ton"]},
              {"type": "marker", "label": "Port 3 terminal"}]
        hits = C.unit_ton_hits(ev)
        self.assertEqual([s for _, s in hits], ["약 2만 6천 t"])
        self.assertIn("unit_ton_glyph", C.HARD)


class SeaOnlyTest(unittest.TestCase):
    def test_sea_center_low_coast_high(self) -> None:
        from engine.projection import View

        st = make_stage("mercator")
        st._bounds = (0.0, 0.0, 180.0, 80.0)
        land = C._land_world((), st.to_world, st.from_world)
        from shapely.geometry import box

        def ratio(lon: float, lat: float, w: float) -> float:
            x, y = st.to_world(lon=lon, lat=lat)
            v = View(st, (x, y, w))
            r = box(v.x0, v.y1 - v.h, v.x0 + v.w, v.y1)
            return land.intersection(r).area / r.area

        lim = C.R_.camera.land_min_ratio
        self.assertLess(ratio(134.5, 40.5, 7.0), lim)       # 동해 한가운데
        self.assertGreater(ratio(128.4, 36.0, 7.0), lim)    # 울산·포항 해안선 서쪽
        self.assertIn("sea_only_frame", C.HARD)


class BadgeClippedTest(unittest.TestCase):
    """D-0244 — 앵커가 화면 위끝에 걸쳐 위 가장자리 보정(edge_nudge)으로만 화면 안에 붙은 국기 = hard. 안쪽 국기·날짜 배지 위 국기."""

    def _run(self, sx: float, sy: float) -> list[str]:
        P = _fake_project(np.tile([90.0, 40.0, 20.0], (24 * 12, 1)), [], 12.0)   # noqa: N806
        from engine.projection import View

        v = View(P.R.stage, tuple(P.cams[0]))
        wx = v.x0 + sx / 854 * v.w
        wy = v.y1 - sy / 854 * v.w
        P.events.append({"type": "badge", "kind": "flag", "flag": "ru", "label": "러시아", "world": (wx, wy), "t0": 1.0, "t1": 10.0})
        return C.check_badge_clipped(P)

    def test_inside_ok(self) -> None:
        self.assertEqual(self._run(427.0, 200.0), [])
        self.assertIn("badge_clipped", C.HARD)

    def test_top_edge_nudge_is_hard(self) -> None:   # 디젤 v2 act2_14 원래 자리(앵커 y≈3) 재현
        hits = self._run(427.0, 3.0)
        self.assertEqual(len(hits), 1)
        self.assertIn("위 가장자리 보정", hits[0])

    def test_on_date_badge_is_hard(self) -> None:
        self.assertEqual(len(self._run(800.0, 60.0)), 1)


class BannedPersonifyTest(unittest.TestCase):
    def test_policy_subject_verbs(self) -> None:   # UF-124 — 제도·법 주어의 겨누다·겨냥하다·노리다
        import re

        from rules import load_rules

        pats = [re.compile(p) for p in load_rules().banned_phrases.patterns]
        bad = "즉 이 제도가 겨누는 것은 러시아가 파는 석유이지, 러시아가 사들이는 연료가 아닙니다."
        good = "즉 이 제도에서 제재 대상은 러시아가 파는 석유이고, 러시아가 사들이는 연료는 비제재 대상입니다."
        self.assertTrue(any(p.search(bad) for p in pats))
        self.assertFalse(any(p.search(good) for p in pats))


if __name__ == "__main__":
    unittest.main()

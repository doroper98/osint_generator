"""v4.11.0 G10 — 정적 구간 검사 `[static-window]`·느린 푸시인·변화 사다리 (back_and_forth D-0118 §1)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import numpy as np
import yaml

from engine.camera import CamKey, build_camera
from engine.checks import HARD, WARN, check_static_window, profile_skips
from engine.pacing import change_times, creep_factor, creep_ranges, map_segments, static_windows
from engine.project import pacing_check
from engine.shots import ShotStage
from rules import RULES_PATH, load_rules
from schemas.rules_models import VideoRules
from workers.prompt_loader import load_prompt

SW = load_rules().pacing.static_window


def _ch(*ts: float, kind: str = "marker") -> list[tuple[float, str]]:
    return [(t, kind) for t in ts]


class WindowTest(unittest.TestCase):
    def test_closed_window_edge_counts(self) -> None:
        """창은 닫힌 구간 [s, s+W] — 창 끝에 딱 붙은 변화도 센다. 0.05초 밖이면 걸린다."""
        self.assertEqual(static_windows([(0.0, 45.0)], _ch(0, 22.5, 45.0), 45, 3), [])
        w = static_windows([(0.0, 45.0)], _ch(0, 22.5, 45.05), 45, 3)
        self.assertEqual([(x["t0"], x["t1"], x["changes"]) for x in w], [(0.0, 45.0, 2)])

    def test_overlapping_windows_merge_into_one_range(self) -> None:
        """5초 간격 변화 사이의 100초 공백 → 걸린 창들이 겹쳐 한 범위. 경계는 창 시작 격자(0.1초)로."""
        ts = [float(t) for t in range(0, 55, 5)] + [float(t) for t in range(150, 205, 5)]
        w = static_windows([(0.0, 200.0)], _ch(*ts), 45, 3)
        self.assertEqual(len(w), 1)
        self.assertAlmostEqual(w[0]["t0"], 40.1, places=2)    # s=40 → 40·45·50 = 3(통과), 40.1 → 45·50 = 2
        self.assertAlmostEqual(w[0]["t1"], 159.9, places=2)   # s+W=160 → 150·155·160 = 3
        self.assertEqual(w[0]["changes"], 0)
        self.assertEqual(w[0]["kinds"], ["marker"])

    def test_short_segment_has_no_window_and_segments_do_not_bridge(self) -> None:
        """W 보다 짧은 지도 구간은 창이 없다 — 패널·전면 카드로 끊긴 두 구간을 이어 세지 않는다."""
        self.assertEqual(static_windows([(0.0, 44.9), (60.0, 100.0)], [], 45, 3), [])
        segs = map_segments(100.0, lambda t: "mercator", lambda t: 40 <= t <= 50)
        self.assertEqual(segs, [(0.0, 39.9), (50.1, 100.0)])
        self.assertEqual(map_segments(10.0, lambda t: "timeline", lambda t: False), [])   # 지도 무대만

    def test_min_changes_boundary(self) -> None:
        seg = [(0.0, 45.0)]
        self.assertEqual(static_windows(seg, _ch(5, 20), 45, 2), [])            # 2 ≥ 2 통과
        self.assertEqual(len(static_windows(seg, _ch(5, 20), 45, 3)), 1)        # 2 < 3 경고
        self.assertEqual(SW.window_sec, 45)
        self.assertEqual(SW.min_changes, 3)

    def test_change_kinds_camera_and_registry(self) -> None:
        ch = change_times([{"type": "marker", "t0": 3.0}, {"type": "tanker_loop", "t0": 4.0}, {"type": "route", "t0": 9.0}],
                          [0.0, 12.0], SW.change_kinds)
        self.assertEqual(ch, [(3.0, "marker"), (9.0, "route"), (12.0, "camera")])   # 첫 키(t=0)·목록 밖 종류는 세지 않는다
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
        raw["pacing"]["static_window"]["change_kinds"] = ["marker", "stamp"]
        with self.assertRaisesRegex(ValueError, "stamp"):
            VideoRules.model_validate(raw)


class CreepTest(unittest.TestCase):
    def test_factor_only_inside_range_then_held(self) -> None:
        rg = [(100.0, 145.0)]
        self.assertEqual(creep_factor(50.0, 0.0, rg, 0.96), 1.0)       # 창 전
        self.assertEqual(creep_factor(100.0, 0.0, rg, 0.96), 1.0)      # 창 시작
        self.assertAlmostEqual(creep_factor(122.5, 0.0, rg, 0.96), 0.98)
        self.assertAlmostEqual(creep_factor(145.0, 0.0, rg, 0.96), 0.96)
        self.assertAlmostEqual(creep_factor(170.0, 0.0, rg, 0.96), 0.96)   # 창 뒤 유지(같은 숏)
        self.assertEqual(creep_factor(170.0, 160.0, rg, 0.96), 1.0)     # 다음 키 이동 뒤 = 흡수
        self.assertEqual(creep_factor(120.0, 125.0, rg, 0.96), 1.0)     # 이동 중(키 도착 전)
        self.assertEqual(creep_ranges([{"t0": 0.0, "t1": 44.0}, {"t0": 50.0, "t1": 95.0}]), [(50.0, 95.0)])   # min_window_sec

    def test_build_camera_creep_scope(self) -> None:
        keys = [CamKey(t=0, x=10, y=20, w=30, dur=3.0), CamKey(t=160, x=12, y=20, w=30, dur=3.0)]
        fps, n = 10, 2000
        base = build_camera(keys, n, fps)
        self.assertTrue(np.array_equal(base, build_camera(keys, n, fps, creep=[])))   # 창 없음 = 바이트 동일(골든)
        cr = build_camera(keys, n, fps, creep=[(100.0, 145.0)])
        self.assertTrue(np.array_equal(cr[:1001], base[:1001]))                   # 창 전·시작 무변경
        self.assertTrue(np.array_equal(cr[:, :2], base[:, :2]))                   # 위치는 그대로 — w 만
        self.assertAlmostEqual(cr[1450, 2] / base[1450, 2], SW.creep.w_ratio, places=6)
        self.assertAlmostEqual(cr[1599, 2] / base[1599, 2], SW.creep.w_ratio, places=6)   # 다음 키 전까지 유지
        self.assertLess(abs(cr[1601, 2] - cr[1600, 2]), 0.05)                      # 이동이 줄어든 w 에서 출발(끊김 없음)
        self.assertTrue(np.allclose(cr[1640:, 2], base[1640:, 2]))                 # 이동 도착 뒤 = 원래 경로


class CheckTest(unittest.TestCase):
    def test_warning_and_animatic_profile(self) -> None:
        self.assertIn("static_window", WARN)
        self.assertNotIn("static_window", HARD)
        self.assertNotIn("static_window", load_rules().animatic.checks_skip)       # 콘티 판에서도 돈다(D-0108 자리)
        self.assertNotIn("static_window", profile_skips(NS(animatic=True)))
        P = NS(R=NS(cache={"pacing": {"window_sec": 45, "min_changes": 3,
                                      "static_windows": [{"t0": 60.0, "t1": 110.5, "changes": 1, "kinds": ["marker"]}]}}))
        self.assertEqual(check_static_window(P), ["[static-window] 60.0-110.5 changes=1 (창 45초, 기준 ≥ 3; 종류 marker)"])

    def test_pacing_check_uses_map_stage_and_covers(self) -> None:
        tb = NS(in_fullcard=lambda t: t < 5.0)
        shots = [ShotStage(t=0.0, mode="cut", stage="mercator", x=0, y=0, w=10), ShotStage(t=120.0, mode="dip", stage="timeline", x=0, y=0, w=10)]
        keys = [CamKey(t=0, x=0, y=0, w=10), CamKey(t=120, x=0, y=0, w=10, dur=0, mode="cut")]
        ev = [{"type": "panel", "t0": 60.0, "t1": 70.0}, {"type": "marker", "t0": 10.0}]
        pc = pacing_check(200.0, tb, shots, ev, keys, "mercator")
        self.assertEqual(pc["segments"], [[5.0, 59.9], [70.1, 119.9]])
        self.assertEqual([(w["t0"], w["t1"]) for w in pc["static_windows"]], [(5.0, 59.9), (70.1, 119.9)])
        self.assertEqual(pc["creep"], [[5.0, 59.9], [70.1, 119.9]])


class PromptTest(unittest.TestCase):
    def test_ladder_uses_rule_values(self) -> None:
        R = load_rules()  # noqa: N806
        for name in ("director", "revise_direction"):
            t = load_prompt(name, R)
            self.assertIn("변화 사다리", t)
            self.assertIn(f"같은 뷰가 {SW.window_sec:g}초를 넘으면", t)
            self.assertIn(f"{SW.min_changes}개 미만", t)
            self.assertNotIn("{{RULES.pacing", t)
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
        raw["pacing"]["static_window"]["window_sec"] = 50
        t = load_prompt("director", VideoRules.model_validate(raw))
        self.assertIn("같은 뷰가 50초를 넘으면", t)   # 옛 상수가 아니라 규칙 값


if __name__ == "__main__":
    unittest.main()

"""v5.21.14 D-0195·D-0197·D-0199 — 이동·공격 문장의 경로 누락(route_missing)·문장이 부르는 지명 화면 밖(frame_missing)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from engine.checks import HARD, WARN, story_geo_report
from engine.events import MarkerEvent
from engine.stage import MercatorStage
from rules import load_rules


def _P(sentences: list, events: list, cam: tuple[float, float, float] = (45.0, 20.0, 20.0)) -> SimpleNamespace:  # noqa: N802
    st = MercatorStage.__new__(MercatorStage)
    st.countries = []
    st.assets = None
    st._bounds = (-180.0, -80.0, 180.0, 80.0)
    n = 24 * 20
    return SimpleNamespace(plan=SimpleNamespace(sentences=sentences), events=events, cams=np.tile(np.array(cam), (n, 1)),
                           n_frames=n, R=SimpleNamespace(cache={}, stage=st, tb=SimpleNamespace(in_fullcard=lambda t: False)))


def _s(sid: str, t0: float, t1: float, text: str) -> SimpleNamespace:
    return SimpleNamespace(sid=sid, t0=t0, t1=t1, text=text)


def _mk(label: str, x: float, y: float) -> dict:
    return {"type": "marker", "label": label, "world": (x, y), "t0": 0.0, "t1": 10.0}


def _rt(p0: tuple, p1: tuple) -> dict:
    return {"type": "route", "world_pts": [p0, p1], "t0": 0.0, "t1": 10.0}


S = [_s("t_7", 1.0, 5.0, "파키스탄이 수송기 4대를 예멘 아덴에 보냈다고 보도했습니다.")]


class TestRouteMissing(unittest.TestCase):
    def test_registered(self) -> None:
        self.assertIn("route_missing_other", HARD)
        self.assertIn("frame_missing_target", HARD)
        self.assertIn("route_missing", WARN)
        self.assertIn("frame_missing", WARN)
        self.assertIn("route_missing", MarkerEvent.model_fields["label"].description)

    def test_gulf_aden_other_route_only_is_hard(self) -> None:
        """gulf troop_numbers_7 — 아덴 마커, 파키스탄→사우디 경로만."""
        r = story_geo_report(_P(S, [_mk("아덴", 45.0, 12.8), _rt((67.0, 25.0), (45.0, 24.0))]))
        self.assertEqual(len(r["route_missing_other"]), 1)
        self.assertIn("'아덴'", r["route_missing_other"][0])

    def test_route_to_marker_passes(self) -> None:
        r = story_geo_report(_P(S, [_mk("아덴", 45.0, 12.8), _rt((67.0, 25.0), (45.2, 12.9))]))
        self.assertEqual(r["route_missing"] + r["route_missing_other"], [])

    def test_no_routes_is_warning(self) -> None:
        r = story_geo_report(_P(S, [_mk("아덴", 45.0, 12.8)]))
        self.assertEqual((len(r["route_missing"]), len(r["route_missing_other"])), (1, 0))

    def test_no_verb_no_check(self) -> None:
        s = [_s("x", 1.0, 5.0, "아덴은 예멘 남부의 항구 도시입니다.")]
        r = story_geo_report(_P(s, [_mk("아덴", 45.0, 12.8)]))
        self.assertEqual(r["route_missing"], [])

    def test_attack_verb(self) -> None:
        s = [_s("r_0", 1.0, 5.0, "후티는 탄도미사일로 킹칼리드 국제공항을 공격했다고 밝혔습니다.")]
        r = story_geo_report(_P(s, [_mk("킹칼리드 국제공항", 46.7, 25.0)]))
        self.assertEqual(len(r["route_missing"]), 1)


class TestFrameMissing(unittest.TestCase):
    def test_target_offscreen_is_hard(self) -> None:
        """이동 대상 마커가 문장 내내 화면 밖 → hard."""
        r = story_geo_report(_P(S, [_mk("아덴", 120.0, 12.8), _rt((67.0, 25.0), (120.0, 12.8))]))
        self.assertEqual(len(r["frame_missing_target"]), 1)

    def test_onscreen_passes(self) -> None:
        r = story_geo_report(_P(S, [_mk("아덴", 45.0, 20.0), _rt((40.0, 22.0), (45.0, 20.0))]))
        self.assertEqual(r["frame_missing"] + r["frame_missing_target"], [])

    def test_rule_keys(self) -> None:
        q = load_rules().qa_checks
        self.assertIn("보냈", q.route_missing.move_verbs)
        self.assertIn("공격", q.route_missing.attack_verbs)


if __name__ == "__main__":
    unittest.main()

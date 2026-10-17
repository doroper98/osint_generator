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
        self.assertIn("route_missing", HARD)   # v5.22.1 D-0205 — 둘 다 hard
        self.assertIn("frame_missing", HARD)
        self.assertNotIn("route_missing", WARN)
        self.assertIn("route_missing", MarkerEvent.model_fields["label"].description)

    def test_gulf_aden_other_route_only_is_hard(self) -> None:
        """gulf troop_numbers_7 — 아덴 마커, 파키스탄→사우디 경로만."""
        r = story_geo_report(_P(S, [_mk("아덴", 45.0, 12.8), _rt((67.0, 25.0), (45.0, 24.0))]))
        self.assertEqual(len(r["route_missing_other"]), 1)
        self.assertIn("'아덴'", r["route_missing_other"][0])

    def test_route_to_marker_passes(self) -> None:
        r = story_geo_report(_P(S, [_mk("아덴", 45.0, 12.8), _rt((67.0, 25.0), (45.2, 12.9))]))
        self.assertEqual(r["route_missing"] + r["route_missing_other"], [])

    def test_flight_to_marker_passes(self) -> None:
        """v7.3.0 D-0206 — 출발점에서 마커로 가는 flight 는 그 문장의 경로다(diesel_road_2026 act1_3 키리시)."""
        s = [_s("act1_3", 1.0, 5.0, "우크라이나 국방부는 최근 키리시의 정유소를 타격했다고 밝혔습니다.")]
        fl = {"type": "flight", "world_origin": (34.6, 50.6), "world": (32.02, 59.45), "t0": 1.5, "t1": 7.0}
        r = story_geo_report(_P(s, [_mk("키리시", 32.02, 59.45), fl], cam=(33.0, 55.0, 30.0)))
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

    def test_flag_badge_counts_as_shown(self) -> None:
        """v5.22.1 D-0205 — 이란이 화면 밖이어도 이란 국기 뱃지가 문장 구간에 있으면 표시."""
        P = _P([_s("m_2", 1.0, 3.0, "후티와 이란은 이를 부인했습니다.")], [])
        P.R.stage.countries = [("IR", {"ko": "이란"}, (53.0, 32.0))]
        self.assertEqual(len(story_geo_report(P)["frame_missing"]), 1)
        P2 = _P([_s("m_2", 1.0, 3.0, "후티와 이란은 이를 부인했습니다.")], [{"type": "badge", "flag": "ir", "t0": 1.1, "t1": 4.0}])
        P2.R.stage.countries = P.R.stage.countries
        self.assertEqual(story_geo_report(P2)["frame_missing"], [])

    def test_exempt_only_golden(self) -> None:
        import subprocess

        from tests.anti_inertia._ast_util import REPO
        files = subprocess.run(["git", "ls-files", "projects/*/direction*.yaml"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        import re

        # 값이 있는 면제만 센다 — AI 검수 루프 판은 모든 필드를 직렬화해 `story_geo_exempt: null` 을 남긴다(면제 아님)
        hits = [f for f in files if re.search(r"^story_geo_exempt:[ \t]*(?!null[ \t]*$)\S", (REPO / f).read_text(encoding="utf-8"), re.M)]
        self.assertEqual(hits, ["projects/hormuz_korea/direction.yaml"])
        P = _P(S, [_mk("아덴", 120.0, 12.8)])
        P.R.cache["story_geo_exempt"] = {"reason": "r", "decision": "D-0205"}
        self.assertEqual(sum(len(v) for v in story_geo_report(P).values()), 0)

    def test_rule_keys(self) -> None:
        q = load_rules().qa_checks
        self.assertIn("보냈", q.route_missing.move_verbs)
        self.assertIn("공격", q.route_missing.attack_verbs)


if __name__ == "__main__":
    unittest.main()

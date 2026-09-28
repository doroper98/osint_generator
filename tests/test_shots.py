"""engine/shots — 숏 규칙 검사기 하나 + 전환 자동 선택 (v3.3.0, 05 §7-2·§7-3, D-0056 작업 3·4)."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from engine.camera import CamKey
from engine.projection import ym
from engine.shots import choose_transition, shot_issues
from rules import load_rules

SG = load_rules().shot_grammar
REPO = Path(__file__).resolve().parent.parent


def _k(t: float, dur: float = 3.0, mode: str = "move") -> CamKey:
    return CamKey(t=t, x=56.0, y=ym(26.0), w=14.0, dur=dur, mode=mode)


class TransitionTest(unittest.TestCase):
    def test_near_same_scale_is_move(self) -> None:
        self.assertEqual(choose_transition((56.0, ym(26.0), 14.0), (58.0, ym(25.0), 16.0)), "move")

    def test_far_is_dip(self) -> None:
        self.assertEqual(choose_transition((56.0, ym(26.0), 14.0), (127.0, ym(37.0), 8.0)), "dip")

    def test_big_zoom_ratio_is_dip(self) -> None:
        w = 14.0 * SG.auto_transition.dip_if_w_ratio_over
        self.assertEqual(choose_transition((56.0, ym(26.0), 14.0), (56.0, ym(26.0), w)), "dip")
        self.assertEqual(choose_transition((56.0, ym(26.0), 14.0), (56.0, ym(26.0), w * 0.9)), "move")


class ShotIssuesTest(unittest.TestCase):
    def _sents(self) -> list:
        return [NS(scene="a", t0=0.0), NS(scene="b", t0=30.0)]

    def test_short_hold_warned(self) -> None:
        out = shot_issues([_k(0, 0, "cut"), _k(4.0)], self._sents(), [], 60.0)
        self.assertTrue(any("머무름" in x for x in out))

    def test_two_moves_in_scene_warned(self) -> None:
        out = shot_issues([_k(0, 0, "cut"), _k(8.0), _k(20.0)], self._sents(), [], 60.0)
        self.assertTrue(any("카메라 이동 2" in x for x in out))

    def test_dip_rate_warned(self) -> None:
        dips = [{"type": "dip", "t0": t, "t1": t + 1} for t in (5, 15, 25)]
        self.assertTrue(any("암전" in x for x in shot_issues([_k(0, 0, "cut")], self._sents(), dips, 60.0)))

    def test_one_checker_code_path(self) -> None:
        """숏 규칙 수치는 engine/shots.py 에서만 읽는다 — checks 는 호출만(D-0047 §0-4)."""
        hits = [p.relative_to(REPO).as_posix() for p in (REPO / "engine").glob("*.py")
                if ".shot_min_hold_sec" in p.read_text(encoding="utf-8") and p.name != "shots.py"]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()

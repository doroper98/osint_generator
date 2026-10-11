"""v5.22.0 D-0200 — 원장 UF-08·UF-10 의 장치: battle_geo(전황 문장 지명·경로 없음)·portrait_unused(초상 있는 인물 미표시), 둘 다 warning."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine.checks import WARN, check_battle_geo, check_portrait_unused
from engine.stage import MercatorStage


def _s(sid: str, t0: float, t1: float, text: str) -> SimpleNamespace:
    return SimpleNamespace(sid=sid, t0=t0, t1=t1, text=text)


def _P(sentences: list, events: list) -> SimpleNamespace:  # noqa: N802
    st = MercatorStage.__new__(MercatorStage)
    return SimpleNamespace(plan=SimpleNamespace(sentences=sentences), events=events,
                           R=SimpleNamespace(cache={}, stage=st, tb=SimpleNamespace(in_fullcard=lambda t: False)))


S = [_s("yemen_front_0", 1.0, 5.0, "사우디 주도 연합군과 예멘 정부군이 10월 초 후티 점령지 탈환 공세를 시작했습니다.")]


class TestBattleGeo(unittest.TestCase):
    def test_registered_warning(self) -> None:
        self.assertIn("battle_geo", WARN)
        self.assertIn("portrait_unused", WARN)

    def test_battle_sentence_without_marker_warns(self) -> None:
        """UF-08 — 예멘 공세 장면에 뱃지·카드만 있고 도시·전선이 없었다."""
        ev = [{"type": "badge", "t0": 0.0, "t1": 6.0}, {"type": "card", "t0": 1.0, "t1": 5.0}]
        out = check_battle_geo(_P(S, ev))
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[battle-geo] yemen_front_0"))

    def test_marker_passes(self) -> None:
        ev = [{"type": "marker", "t0": 2.0, "t1": 6.0}]
        self.assertEqual(check_battle_geo(_P(S, ev)), [])

    def test_covered_sentence_skipped(self) -> None:
        ev = [{"type": "article", "t0": 0.0, "t1": 6.0}]
        self.assertEqual(check_battle_geo(_P(S, ev)), [])


class TestPortraitUnused(unittest.TestCase):
    T = [_s("riyadh_airport_8", 1.0, 6.0, "타임은 트럼프 대통령이 지금까지 후티에 대한 미국의 직접 타격 요청을 거절해 왔다고 보도했습니다.")]

    def test_name_without_badge_warns(self) -> None:
        """UF-10 — 트럼프가 나오는데 초상이 없었다(공용 라이브러리 trump)."""
        out = check_portrait_unused(_P(self.T, []))
        self.assertEqual(len(out), 1)
        self.assertIn("(trump)", out[0])

    def test_badge_or_panel_node_passes(self) -> None:
        badge = [{"type": "badge", "t0": 1.2, "t1": 6.0, "kind": "person", "pid": "trump"}]
        panel = [{"type": "panel", "t0": 0.0, "t1": 9.0, "data": {"nodes": [{"pid": "trump"}]}}]
        self.assertEqual(check_portrait_unused(_P(self.T, badge)), [])
        self.assertEqual(check_portrait_unused(_P(self.T, panel)), [])


if __name__ == "__main__":
    unittest.main()

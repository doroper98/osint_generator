"""v7.4.0 back_and_forth D-0229 §2.7(UF-107) — 위성 인셋 유지: 명시 hold_until, 같은 장소 연속 문장(rules flight.inset.hold_same_place), 대각 자리."""

from __future__ import annotations

import types
import unittest

from pydantic import ValidationError

from engine.direction import hold_same_place
from engine.events import FlightEvent
from engine.layers import flight as fl
from rules import load_rules

F = load_rules().flight


def _tb() -> types.SimpleNamespace:
    S = lambda sid, t0, t1, text: types.SimpleNamespace(sid=sid, t0=t0, t1=t1, text=text)  # noqa: E731, N806
    sent = {"cold_0": S("cold_0", 1.0, 6.0, "러시아 랴잔의 정유소에 불길이 올랐습니다."),
            "cold_1": S("cold_1", 6.5, 11.0, "러시아 국방부는 랴잔에서 격추한 무인기 파편이라고 밝혔습니다."),
            "cold_2": S("cold_2", 11.5, 16.0, "이에 대해 우크라이나 당국자는 공격을 확인했습니다."),
            "cold_3": S("cold_3", 16.5, 22.0, "랴잔 공격으로 휴전이 끝났습니다.")}
    return types.SimpleNamespace(order=list(sent), sent=sent)


def _ev(**ins: object) -> dict:
    return dict(type="flight", t0=0.5, t1=0.5 + F.dur_sec + F.impact_sec + F.inset.hold_sec + 0.5, kind="drone",
                origin={"lon": 35.0, "lat": 50.5}, lon=39.74, lat=54.63, inset=dict(mid="ins", **ins))


class SamePlaceTest(unittest.TestCase):
    def test_extends_over_consecutive_mentions(self) -> None:
        d = _ev(place="랴잔")
        hold_same_place(d, _tb())
        self.assertEqual(d["inset"]["hold_until"], 11.0)   # cold_0·cold_1 은 랴잔, cold_2 에서 끊김(cold_3 은 이어지지 않음)
        self.assertGreaterEqual(d["t1"], 11.0)
        FlightEvent.model_validate(d)

    def test_explicit_wins(self) -> None:
        d = _ev(place="랴잔", hold_until=22.0)
        d["t1"] = 22.5
        hold_same_place(d, _tb())
        self.assertEqual(d["inset"]["hold_until"], 22.0)

    def test_alpha_held(self) -> None:
        d = _ev(hold_until=20.0)
        d["t1"] = 21.0
        self.assertGreater(fl.inset_alpha(19.0, d), 0.9)
        self.assertEqual(fl.inset_alpha(23.0, d), 0.0)

    def test_hold_beyond_t1_is_error(self) -> None:
        with self.assertRaises(ValidationError):
            FlightEvent.model_validate(_ev(hold_until=99.0))


class DiagonalSideTest(unittest.TestCase):
    def test_down_left(self) -> None:
        x, y, w, h = fl.inset_box({"inset": {"side": "down_left"}}, 400.0, 120.0)   # v7.4.0 D-0300 — 지름 190: 아래 자리가 맞는 표적 높이
        self.assertLess(x + w, 400.0)
        self.assertGreater(y, 120.0)


if __name__ == "__main__":
    unittest.main()

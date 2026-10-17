"""v7.3.0 back_and_forth D-0206 — 비행 이벤트(flight): 착탄 시각·길이 검증·착탄 링 재사용·인셋 종류·세 아이콘 렌더."""

from __future__ import annotations

import types
import unittest
from unittest import mock

import cairo

from engine.credits import RightsError
from engine.events import FlightEvent
from engine.layers import flight as fl
from engine.layers.media import validate_media
from engine.registry import MAP_LAYER_ORDER, validate_events
from rules import load_rules

F = load_rules().flight


def _ev(**kw: object) -> dict:
    e = dict(type="flight", t0=10.0, t1=10.0 + F.dur_sec + F.impact_sec + 0.5, kind="drone",
             origin={"lon": 35.0, "lat": 50.5}, lon=39.74, lat=54.63)
    e.update(kw)
    return e


def _view() -> types.SimpleNamespace:
    return types.SimpleNamespace(stage=types.SimpleNamespace(theme_name=None), to_screen=lambda x, y: (x, y))


def _drawn(e: dict, t: float) -> tuple[cairo.ImageSurface, types.SimpleNamespace]:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 200)
    R = types.SimpleNamespace(reserved=[])  # noqa: N806
    d = dict(e, world=(150.0, 60.0), world_origin=(30.0, 160.0))
    fl.draw_flight(cairo.Context(surf), R, _view(), t, d, inset_drawer=lambda *a: None)
    return surf, R


def _ink(surf: cairo.ImageSurface) -> int:
    surf.flush()
    return sum(1 for b in bytes(surf.get_data())[3::4] if b)


class FlightModelTest(unittest.TestCase):
    def test_hit_time_is_code(self) -> None:
        """(a) 착탄 시각 = t0 + rules flight.dur_sec — 연출은 쓰지 않는다(P8)."""
        self.assertAlmostEqual(fl.hit_time(_ev()), 10.0 + F.dur_sec)

    def test_too_short_is_error(self) -> None:
        """(b) [flight-too-short] — 비행 + 착탄 링(+ 인셋) 보다 짧으면 렌더 전 오류(잘라 그리지 않는다, P6)."""
        with self.assertRaisesRegex(ValueError, r"\[flight-too-short\]"):
            FlightEvent.model_validate(_ev(t1=10.0 + F.dur_sec))
        with self.assertRaisesRegex(ValueError, r"\[flight-too-short\]"):
            FlightEvent.model_validate(_ev(inset={"mid": "x"}))
        FlightEvent.model_validate(_ev(t1=10.0 + F.dur_sec + F.impact_sec + F.inset.hold_sec, inset={"mid": "x"}))

    def test_inset_dropped_when_absent(self) -> None:
        d = validate_events([_ev()])[0]
        self.assertNotIn("inset", d)
        self.assertEqual(d["origin"], {"lon": 35.0, "lat": 50.5})

    def test_layer_order(self) -> None:
        """링 위·컷아웃 아래(D-0206 §4)."""
        self.assertEqual(MAP_LAYER_ORDER.index("flight"), MAP_LAYER_ORDER.index("boom") + 1)

    def test_impact_sec_matches_boom(self) -> None:
        """rules flight.impact_sec = effects.draw_boom 링 수명(1.6초, v3 합격 값) — 링을 다시 만들지 않는다."""
        import inspect  # noqa: PLC0415

        from engine.layers import effects  # noqa: PLC0415

        self.assertIn(f"lt / {F.impact_sec}", inspect.getsource(effects.draw_boom))


class FlightRenderTest(unittest.TestCase):
    def test_boom_reused_and_impact_false(self) -> None:
        """(c) 착탄 뒤 draw_boom 을 그대로 부른다. impact False 면 부르지 않는다."""
        th = 10.0 + F.dur_sec
        with mock.patch.object(fl, "draw_boom") as b:
            _drawn(_ev(), th + 0.3)
            self.assertEqual(b.call_count, 1)
            self.assertEqual(b.call_args.args[4]["t0"], th)
        with mock.patch.object(fl, "draw_boom") as b:
            _drawn(_ev(impact=False), th + 0.3)
            b.assert_not_called()

    def test_three_icons_render(self) -> None:
        """(e) 세 종류 렌더 1프레임 smoke — 비행 중 아이콘·꼬리선이 그려진다."""
        for kind in ("drone", "missile", "jet"):
            surf, _ = _drawn(_ev(kind=kind), 10.0 + F.dur_sec / 2)
            self.assertGreater(_ink(surf), 0, kind)

    def test_origin_glow_before_launch(self) -> None:
        surf, _ = _drawn(_ev(), 10.0 - F.origin.pulse_sec / 2)
        self.assertGreater(_ink(surf), 0)

    def test_inset_reserved(self) -> None:
        e = _ev(t1=30.0, inset={"mid": "x"})
        _, R = _drawn(e, 10.0 + F.dur_sec + 1.0)  # noqa: N806
        self.assertEqual(len(R.reserved), 1)


class InsetKindTest(unittest.TestCase):
    def test_inset_mid_kind_checked(self) -> None:
        """(d) 인셋 mid 의 레지스트리 kind 가 inset 이 아니면 RightsError(렌더 전)."""
        reg = {"p": types.SimpleNamespace(kind="photo", press_of=None, rights_status="rights_clear")}
        with self.assertRaises(RightsError):
            validate_media({"type": "inset", "mid": "p", "t0": 0}, reg)
        reg = {"s": types.SimpleNamespace(kind="inset", press_of=None, rights_status="rights_clear")}
        self.assertIs(validate_media({"type": "inset", "mid": "s", "t0": 0}, reg), reg["s"])


if __name__ == "__main__":
    unittest.main()

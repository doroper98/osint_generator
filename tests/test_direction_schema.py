"""engine/direction — direction.yaml 스키마·앵커·로더 (v3.1.0, 17 §2, back_and_forth D-0047 작업 2·9)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.direction import Direction, DirectionError, build, is_anchor, load_direction_doc, resolve_anchor, yaml_load
from engine.stage import MercatorStage
from engine.timebase import Timebase
from script.schema import Plan

REPO = Path(__file__).resolve().parent.parent
MINIMAL = REPO / "tests" / "fixtures" / "direction" / "minimal.yaml"


def _plan() -> Plan:
    rows = []
    t = 0.0
    for sid, scene, dur in (("s_0", "a", 4.0), ("s_1", "a", 5.0), ("s_2", "b", 3.0)):
        rows.append(dict(sid=sid, scene=scene, date="2026", text="문장", tts="문장", segments=[], mp3="/nope.mp3",
                         npy="/nope.npy", dur=dur, t0=t, t1=t + dur))
        t += dur + 0.5
    return Plan.model_validate(dict(sentences=rows, cards=[dict(kind="title", t0=0.0, t1=0.0), dict(kind="end", t0=t, t1=t + 5)],
                                    scene_start={"a": 0.0, "b": 9.0}, total=t + 5, voice="v", title="t", subtitle="s", date="2026"))


class AnchorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tb = Timebase(_plan())

    def test_all_anchor_forms(self) -> None:
        tb = self.tb
        self.assertEqual(resolve_anchor({"sid": "s_1", "off": 0.2}, tb), tb.S("s_1", 0.2))
        self.assertEqual(resolve_anchor({"sid": "s_1", "off": -0.4, "edge": "end"}, tb), tb.E("s_1", -0.4))
        self.assertEqual(resolve_anchor({"scene_start": "b", "off": -0.2}, tb), tb.SC("b") - 0.2)
        self.assertEqual(resolve_anchor({"scene_end": "a"}, tb), tb.SC_END("a"))
        self.assertEqual(resolve_anchor({"card": "end", "edge": "end", "off": 1.0}, tb), tb.card("end").t1 + 1.0)
        self.assertEqual(resolve_anchor({"total": True, "off": 0.5}, tb), tb.total + 0.5)
        self.assertEqual(resolve_anchor({"span": [{"sid": "s_1", "off": 0.6}, {"sid": "s_1", "off": -0.4, "edge": "end"}]}, tb),
                         tb.E("s_1", -0.4) - tb.S("s_1", 0.6))
        self.assertEqual(resolve_anchor(3.5, tb), 3.5)

    def test_offset_list_keeps_float_order(self) -> None:
        # 옛 연출 `(SC - 0.2) + 0.8` 을 비트 단위로 재현하려면 off 를 차례로 더한다
        tb = self.tb
        self.assertEqual(resolve_anchor({"scene_start": "b", "off": [-0.2, 0.8]}, tb), (tb.SC("b") - 0.2) + 0.8)

    def test_word_anchor_uses_at_word(self) -> None:
        tb = self.tb
        t = resolve_anchor({"word": {"sid": "s_0", "text": "장"}}, tb)
        self.assertEqual(tb.word_anchors[-1]["word"], "장")
        self.assertGreaterEqual(t, tb.S("s_0"))

    def test_bad_refs_are_errors(self) -> None:
        for a in ({"sid": "zz"}, {"scene_start": "zz"}, {"sid": "s_0", "edge": "middle"}, {"span": [1]}, True):
            with self.subTest(a=a), self.assertRaises(DirectionError):
                resolve_anchor(a, self.tb)

    def test_is_anchor_does_not_eat_data_dicts(self) -> None:
        self.assertTrue(is_anchor({"sid": "a", "off": 1}))
        self.assertFalse(is_anchor({"id": "trump", "group": "source"}))
        self.assertFalse(is_anchor({"sid": "a", "scene_start": "b"}))
        self.assertFalse(is_anchor({"text": "x", "t": 1}))


class DocTest(unittest.TestCase):
    def test_minimal_builds(self) -> None:
        doc = load_direction_doc(MINIMAL)
        keys, events, sound = build(doc, Timebase(_plan()), MercatorStage())
        self.assertEqual([k.mode for k in keys], ["cut", "move", "cut"])      # dip = 한가운데 cut
        self.assertEqual([e["type"] for e in events], ["marker", "route", "card", "dip"])
        self.assertEqual((events[0]["lon"], events[0]["lat"]), (56.35, 26.55))  # at_place
        self.assertEqual(events[1]["pts"][0], (56.2, 26.45))                     # {path: lane}
        self.assertAlmostEqual(events[3]["t1"] - events[3]["t0"], 1.0)
        assert sound is not None
        self.assertEqual(sound["cues"][0]["t"], 1.2)

    def test_off_key_survives_yaml(self) -> None:
        self.assertEqual(yaml_load("a: {sid: x, off: 0.2}")["a"], {"sid": "x", "off": 0.2})   # type: ignore[index]

    def test_schema_errors(self) -> None:
        base = yaml_load(MINIMAL.read_text(encoding="utf-8"))
        assert isinstance(base, dict)
        bad = [
            {**base, "events": [{"type": "marker", "t0": 0, "t1": 1, "start": 0, "end": 1}]},   # t0 금지
            {**base, "events": [{"type": "marker", "start": 0}]},                               # end 없음
            {**base, "events": [{"type": "marker", "start": 0, "end": 1, "at_place": "nowhere"}]},
            {**base, "shots": [{"at": {"sid": "s_0", "scene_start": "a"}, "mode": "cut", "camera": {"lon": 1, "lat": 2, "w": 3}}]},
            {**base, "shots": [{"at": 0, "mode": "zoom", "camera": {"lon": 1, "lat": 2, "w": 3}}]},
            {**base, "unknown": 1},
        ]
        for b in bad:
            with self.subTest(b=str(b)[:60]), self.assertRaises(ValueError):
                Direction.model_validate(b)

    def test_loader_never_executes_code(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "direction.yaml"
            p.write_text("!!python/object/apply:os.system ['echo pwned']\n", encoding="utf-8")
            with self.assertRaises(DirectionError):
                load_direction_doc(p)


if __name__ == "__main__":
    unittest.main()

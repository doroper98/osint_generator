"""v7.4.0 사용자 결정 UF-401 ③ — 뱃지 신호(영상 분석 D1 재언급 맥동 · D9 숙청 X · D10 물음표 말풍선).

뱃지는 머물고 신호만 더한다. 신호 시각은 뱃지 구간 안(밖 = 렌더 전 오류, P6). 신호를 쓰지 않은 뱃지 dict 는 옛 모양 그대로(DROP_NONE).
"""

from __future__ import annotations

import unittest

import cairo

from engine.layers.badges import CUE, draw_cues
from engine.registry import RegistryError, validate_events

BASE = {"type": "badge", "t0": 0.0, "t1": 10.0, "lon": 125.7, "lat": 39.0, "kind": "flag", "flag": "kp", "label": "북한"}


def _img(e: dict, t: float) -> bytes:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 120, 120)
    ctx = cairo.Context(surf)
    ctx.translate(60, 60)
    draw_cues(ctx, e, t, 30.0, (0.9, 0.7, 0.3), 1.0)
    return bytes(surf.get_data())


class BadgeCueDataTest(unittest.TestCase):
    def test_plain_badge_dict_unchanged(self) -> None:
        out = validate_events([BASE])[0]
        self.assertFalse({"pulse", "mark", "mark_t"} & set(out))

    def test_cue_fields_validated(self) -> None:
        ok = validate_events([{**BASE, "pulse": [2.0, 6.0], "mark": "question", "mark_t": 4.0}])[0]
        self.assertEqual(ok["pulse"], [2.0, 6.0])
        bad = {"pulse outside": {**BASE, "pulse": [12.0]}, "mark_t without mark": {**BASE, "mark_t": 3.0},
               "mark_t outside": {**BASE, "mark": "strike", "mark_t": 11.0}, "unknown mark": {**BASE, "mark": "cross"}}
        for why, e in bad.items():
            with self.subTest(why=why), self.assertRaises(RegistryError):
                validate_events([e])


class BadgeCueDrawTest(unittest.TestCase):
    def test_pulse_only_during_its_window(self) -> None:
        e = {**BASE, "pulse": [3.0]}
        blank = _img(BASE, 3.5)
        self.assertEqual(_img(e, 2.9), blank)
        self.assertNotEqual(_img(e, 3.0 + CUE.pulse_sec / 2), blank)
        last = 3.0 + CUE.pulse_sec + CUE.pulse_stagger_sec * (CUE.pulse_rings - 1) + 0.05
        self.assertEqual(_img(e, last), blank)

    def test_strike_draws_after_mark_t_and_stays(self) -> None:
        e = {**BASE, "mark": "strike", "mark_t": 4.0}
        blank = _img(BASE, 5.0)
        self.assertEqual(_img(e, 3.9), blank)
        half, full = _img(e, 4.0 + CUE.mark_draw_sec / 4), _img(e, 4.0 + CUE.mark_draw_sec * 2)
        self.assertNotEqual(half, full)
        self.assertEqual(full, _img(e, 9.0))

    def test_question_pops(self) -> None:
        e = {**BASE, "mark": "question"}
        self.assertNotEqual(_img(e, CUE.q_pop_sec * 2), _img(BASE, CUE.q_pop_sec * 2))


if __name__ == "__main__":
    unittest.main()

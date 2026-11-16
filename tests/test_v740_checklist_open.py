"""v7.4.0 사용자 결정 UF-401 ③-2 — checklist style open(영상 분석 D11 열린 가설 칸).

빈 번호 칸이 먼저 보이고 at[i] 에 i번 칸이 채워진다. 체크 표시는 그리지 않는다(가설 = 확인 아님). 안 쓰면 dict 옛 모양.
"""

from __future__ import annotations

import unittest

import cairo

from engine.panels.checklist import K, _draw_open
from engine.registry import RegistryError, validate_events

E = {"type": "panel", "kind": "checklist", "t0": 0.0, "t1": 12.0, "title": "세 가지 가설",
     "items": ["가설 하나", "가설 둘", "가설 셋"], "style": "open", "at": [3.0, 6.0, 9.0]}


def _img(e: dict, t: float) -> bytes:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    _draw_open(cairo.Context(surf), t, e, 1.0)
    return bytes(surf.get_data())


class ChecklistOpenTest(unittest.TestCase):
    def test_plain_checklist_dict_unchanged(self) -> None:
        d = validate_events([{k: v for k, v in E.items() if k not in ("style", "at")}])[0]
        self.assertFalse({"style", "at", "chart"} & set(d))   # 부모 _Panel.DROP_NONE(chart)도 지킨다

    def test_at_validated(self) -> None:
        bad = {"at without open": {**E, "style": "check"}, "count": {**E, "at": [3.0, 6.0]},
               "order": {**E, "at": [6.0, 3.0, 9.0]}, "outside": {**E, "at": [3.0, 6.0, 13.0]}}
        for why, e in bad.items():
            with self.subTest(why=why), self.assertRaises(RegistryError):
                validate_events([e])

    def test_slots_first_then_fill_at_time(self) -> None:
        reveal_done = K.open.reveal_start_sec + K.open.reveal_step_sec * 2 + K.open.reveal_fade_sec
        before = _img(E, reveal_done + 0.1)
        self.assertNotEqual(before, _img({**E, "items": ["x"], "at": [3.0]}, reveal_done + 0.1), "빈 칸 세 개가 먼저 보인다")
        other = {**E, "items": ["가설 하나", "다른 문구", "가설 셋"]}
        self.assertEqual(_img(E, 5.9), _img(other, 5.9), "2번 칸 문구는 at[1] 전에는 보이지 않는다")
        self.assertNotEqual(_img(E, 6.0 + K.open.fill_fade_sec), _img(other, 6.0 + K.open.fill_fade_sec))


if __name__ == "__main__":
    unittest.main()

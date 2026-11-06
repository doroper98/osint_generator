"""[island-pin-collision] 점 ↔ 점(v7.4.0 back_and_forth D372, RENDER-AP-034).

showcase_econ 콘티 판 v4 127초: 7.29 동결 핀과 소비자물가 핀(2026-08-01)의 점이 붙어 '●●' 로 보였다. 라벨끼리는 안 닿아서
기존 판정(라벨 ↔ 라벨·점·선)은 통과했다. 같은 레인 위 두 핀의 점이 닿으면 라벨과 무관하게 겹침으로 센다.
중심이 같은 두 점(같은 날짜 = 한 사건에 단 두 라벨)은 화면에 점 하나라 겹침이 아니다.
실측(이 커밋): v4 연출(a10ca246) = 1건(t=125.42~130.00), v4.1 연출(08-15) = 0건.
"""

from __future__ import annotations

import unittest

from engine.pin_labels import DOT_PX, dot_box, dots_touch, pin_label_check


class _Scene:
    """pin_label_check 입력 흉내 — 핀 둘, 라벨 상자 없음(점만)."""

    def __init__(self, x2: float) -> None:
        self.pins = [{"label": "7월 29일 동결", "t0": 0.0, "t1": 2.0}, {"label": "8월 소비자물가 +3.4%", "t0": 0.0, "t1": 2.0}]
        self.x2 = x2

    def frame(self, t: float, rows_of):  # noqa: ANN001, ANN201, ARG002
        return [(self.pins[0], None, dot_box(100.0, 50.0), []), (self.pins[1], None, dot_box(self.x2, 50.0), [])]


class PinDotCollisionTest(unittest.TestCase):
    def test_touching_dots_fail(self) -> None:   # v4 127초 — 3일 차(≈ 3.5px)
        rows = pin_label_check(_Scene(103.5))
        self.assertTrue(rows)
        self.assertIn("점과 점이 겹침", rows[0]["b"])

    def test_separated_dots_pass(self) -> None:   # v4.1 — 8월 가운데(≈ 20px)
        self.assertEqual(pin_label_check(_Scene(100.0 + 2 * DOT_PX + 6.0)), [])

    def test_coincident_dots_are_one_dot(self) -> None:   # 같은 날짜 두 라벨(act2_2~3 '반대 3인' + '7월 29일 동결')
        self.assertEqual(pin_label_check(_Scene(100.0)), [])
        self.assertFalse(dots_touch(dot_box(100.0, 50.0), dot_box(100.3, 50.0)))
        self.assertTrue(dots_touch(dot_box(100.0, 50.0), dot_box(100.0 + 2 * DOT_PX - 1, 50.0)))


if __name__ == "__main__":
    unittest.main()

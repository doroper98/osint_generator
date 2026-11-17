"""v7.4.0 D935 — statement 패널 서명국 자리(signer_xs). 8개국까지는 v3 좌표, 9개국 이상은 같은 좌우 여백 안에서 간격을 줄인다.

nvidia-chips-china-2026 프리뷰: 서명국 9곳(샌프란시스코 선언)의 아홉째 뱃지가 화면 오른쪽 밖으로 잘렸다(110 + 8 × 92 = 846 > 854 − 여백).
"""

from __future__ import annotations

import unittest

from engine.panels.statement import SIGNER_PITCH, SIGNER_PITCH_MIN, SIGNER_X0, StatementOverflowError, signer_xs
from engine.style import W_OUT


class SignerXsTest(unittest.TestCase):
    def test_up_to_eight_keep_v3_coordinates(self) -> None:
        for n in range(1, 9):
            self.assertEqual(signer_xs(n), [float(SIGNER_X0 + i * SIGNER_PITCH) for i in range(n)], n)

    def test_nine_and_more_stay_inside_margins(self) -> None:
        for n in (9, 10):
            xs = signer_xs(n)
            self.assertEqual(len(xs), n)
            self.assertAlmostEqual(xs[0], SIGNER_X0)
            self.assertLessEqual(xs[-1], W_OUT - SIGNER_X0 + 1e-6, n)
            gaps = {round(b - a, 6) for a, b in zip(xs, xs[1:])}
            self.assertEqual(len(gaps), 1, "서명국 간격은 고르게")
            self.assertGreaterEqual(gaps.pop(), SIGNER_PITCH_MIN)

    def test_too_many_is_error_not_silent_clip(self) -> None:
        with self.assertRaises(StatementOverflowError):
            signer_xs(14)


if __name__ == "__main__":
    unittest.main()

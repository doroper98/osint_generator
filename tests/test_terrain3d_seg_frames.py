"""v7.4.0 D-0634 §3-5 — terrain3d 구간 프레임 [i0, i1) = t_in ≤ i/fps < t_out 인 프레임만(컷 직전 프레임을 3D 로 넣지 않는다)."""

from __future__ import annotations

import unittest

from engine.stage_terrain3d import seg_frames


class SegFramesTest(unittest.TestCase):
    def test_cannae_seg00_excludes_pre_cut_frame(self) -> None:
        i0, i1 = seg_frames(113.4704761904762, 143.4919727891157, 24)
        self.assertEqual(i0, 2724)            # 옛 round = 2723(113.458초 — 컷 앞)
        self.assertGreaterEqual(i0 / 24, 113.4704761904762)
        self.assertLess((i0 - 1) / 24, 113.4704761904762)

    def test_membership_matches_time_rule(self) -> None:
        for t_in, t_out in ((10.0, 12.5), (113.4704761904762, 143.4919727891157), (0.02, 0.5), (5.0 + 1e-12, 6.0)):
            i0, i1 = seg_frames(t_in, t_out, 24)
            for i in range(max(0, i0 - 3), i1 + 3):
                self.assertEqual(i0 <= i < i1, t_in - 1e-9 <= i / 24 < t_out - 1e-9, (t_in, t_out, i))


if __name__ == "__main__":
    unittest.main()

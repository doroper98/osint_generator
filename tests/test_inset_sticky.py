"""위성 인셋 자리 고정·보간 이동 (v7.4.0, back_and_forth D-0300, 사용자 의견 UF-146).

UF-146 원문: "geo 콘티판 v2 첫 시작에 라쟌 위성사진을 보여주는 동그라미가 한순간 위치를 옮기고 사라져. 위성 사진 크기도 좀 키워야하고
갑자기 위치를 바꿔버리는것도 조정해"
- 자리는 등장 첫 프레임에 한 번 정해 유지(sticky), 안전 영역을 벗어나면 다음 적합 자리로 move_sec 보간 — 한 프레임 점프 금지.
- [inset-jump] hard: 원 중심 프레임 간 이동 > jump_px_max.
"""

from __future__ import annotations

import math
import unittest
from types import SimpleNamespace as NS
from unittest import mock

import numpy as np

from engine import checks
from engine.layers.flight import F, build_inset_track, inset_box, inset_clear, inset_fits
from engine.style import FPS


def _ev() -> dict:
    # 착탄 = 0초 — 0~2.5초 동안 인셋이 보인다
    return {"type": "flight", "t0": -F.dur_sec, "t1": 4.0, "world": (0.0, 0.0), "inset": {"mid": "inset_ryazan_esri", "side": "up_right"}}


def _frames(n: int) -> list[tuple[int, float, float]]:
    """표적이 화면 오른쪽으로 이동 — up_right 가 45프레임쯤 안전 영역(오른쪽 끝)을 벗어난다."""
    return [(i, 300.0 + 7.0 * i, 300.0 - 1.0 * i, []) for i in range(n)]


class InsetStickyTest(unittest.TestCase):
    def test_rule_values(self) -> None:
        self.assertEqual((F.inset.w_px, F.inset.gap_px, F.inset.caption_size, F.inset.frame.width, tuple(F.inset.fade)), (190, 14, 10, 1.2, (0.55, 1.2)))   # fade = v7.4.0 UF-159 ×1.5(옛 0.35·0.8)
        self.assertTrue(F.inset.sticky_side)
        self.assertEqual((F.inset.move_sec, F.inset.jump_px_max), (0.6, 24))

    def test_track_interpolates_no_jump(self) -> None:
        e = _ev()
        fr = _frames(60)
        with mock.patch.object(F.inset, "predict_keyframes", False):   # 보간 경로를 본다(예측이 고정 자리를 찾으면 옮김 0)
            build_inset_track(e, fr)
        tr = e["inset_track"]
        self.assertGreaterEqual(len(tr["moves"]), 1)   # 이 경로는 자리를 한 번 이상 옮긴다
        prev = None
        for i, x, y, _ in fr:
            bx, by, w, h = inset_box(e, x, y, i / FPS)
            c = (bx + w / 2, by + h / 2)
            if prev is not None:
                self.assertLessEqual(math.hypot(c[0] - prev[0], c[1] - prev[1]), F.inset.jump_px_max, i)
            prev = c

    def test_jump_is_hard(self) -> None:
        """궤적 없이(옛 동작) 프레임마다 다시 고르면 자리가 바뀌는 프레임에 점프 → [inset-jump]."""
        e = _ev()
        fr = _frames(60)
        cams = np.array([[0.0, 0.0, 1.0]] * 60)

        class V:   # 표적 화면 좌표를 프레임 번호로 돌려주는 가짜 뷰
            def __init__(self, stage: object, cam: np.ndarray) -> None:
                self.i = int(cam[0])

            def to_screen(self, *_: float) -> tuple[float, float]:
                return fr[self.i][1], fr[self.i][2]

        for i in range(60):
            cams[i, 0] = i
        P = NS(events=[e], cams=cams, n_frames=60, R=NS(stage=NS(name="mercator")))
        orig_view, orig_map = checks.View, checks._map_main
        checks.View, checks._map_main = V, (lambda P: True)
        try:
            out = checks.check_inset_jump(P)
            self.assertTrue(out and out[0].startswith("[inset-jump]"), out)
            with mock.patch.object(F.inset, "predict_keyframes", False):
                build_inset_track(e, fr)
            self.assertEqual(checks.check_inset_jump(P), [])
            self.assertTrue(checks.check_inset_side_change(P)[0].startswith("[inset-side-change]"))
        finally:
            checks.View, checks._map_main = orig_view, orig_map
        self.assertIn("inset_jump", checks.HARD)
        self.assertIn("inset_side_change", checks.WARN)

    def test_predicted_side_fixed_from_start(self) -> None:
        """D-0305 ② — 생애 전 구도에 맞는 자리가 있으면 처음부터 그 자리(옮김 0, basis predicted)."""
        e = _ev()
        e["inset"]["side"] = "right"
        fr = [(i, 300.0 + 8.0 * i, 280.0, []) for i in range(50)]   # 연출 자리(right)는 오른쪽 끝을 벗어나지만 up_right 등은 내내 맞는다
        self.assertFalse(all(inset_clear("right", x, y, o) for _, x, y, o in fr))
        build_inset_track(e, fr)
        tr = e["inset_track"]
        self.assertEqual((tr["basis"], tr["moves"]), ("predicted", []))
        self.assertTrue(all(inset_clear(tr["side"], x, y, o) for _, x, y, o in fr))
        self.assertTrue(F.inset.predict_keyframes)

    def test_target_label_is_obstacle(self) -> None:
        """D-0305 ① — 표적 표지 라벨 상자와 겹치는 자리는 고르지 않는다(geo 9~11초 '랴잔 정유소' 라벨을 원이 덮던 것)."""
        from engine.layers.flight import _inset_box_at, first_fit_side  # noqa: PLC0415

        e = {"inset": {"side": "right"}}
        x, y = 400.0, 240.0
        b = _inset_box_at("right", x, y)
        label = (b[0] + 10, y - 16, b[0] + 120, y + 26)   # 표적 오른쪽 라벨 = right 자리와 겹침
        self.assertEqual(first_fit_side(e, x, y), "right")
        self.assertNotEqual(first_fit_side(e, x, y, obstacles=[label]), "right")

    def test_fits_after_resize(self) -> None:
        self.assertTrue(inset_fits(inset_box(_ev(), 427.0, 240.0)))   # 화면 가운데 표적이면 새 지름으로도 어딘가 맞는다


if __name__ == "__main__":
    unittest.main()

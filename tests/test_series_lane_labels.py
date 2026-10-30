"""한 레인에 레코드 둘 이상 — 끝값 라벨 세로 분산·띠 라벨 없음·레인당 출처 한 줄 (v7.4.0, back_and_forth D-0256).

showcase_econ 콘티 판 v1 에서 금리 레인(목표 범위 띠 + 실효금리 계단) 오른쪽 끝 라벨이 "3.'3.63%" 로 겹치고 출처 줄 두 줄이 겹쳤다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine.layers import series as S
from engine.style import TIMELINE


class EndLabelSpreadTest(unittest.TestCase):
    def test_two_labels_in_one_lane_do_not_cross(self) -> None:
        """레코드 둘의 끝값 라벨 기준선이 같은 자리면 값 순으로 갈라져 간격 ≥ end_label_min_gap_px(작은 값이 아래)."""
        gap = TIMELINE.series.end_label_min_gap_px
        R = NS(cache={})  # noqa: N806
        y1 = S.place_end_label(R, 1.0, "policy_rate", 100.0, 4.0)
        R.cache["series_end_labels"]["lanes"]["policy_rate"].append((y1, 4.0, (0, y1 - 12, 40, y1)))
        y2 = S.place_end_label(R, 1.0, "policy_rate", 102.0, 3.63)
        self.assertGreaterEqual(abs(y2 - y1), gap)
        self.assertGreater(y2, y1)   # 작은 값 = 화면 아래(y 큼)
        y3 = S.place_end_label(R, 1.0, "inflation", 101.0, 3.35)   # 다른 레인은 그대로
        self.assertEqual(y3, 101.0)
        y4 = S.place_end_label(R, 2.0, "policy_rate", 100.0, 4.0)   # 다음 프레임은 새로 센다
        self.assertEqual(y4, 100.0)

    def test_lane_source_single_line(self) -> None:
        """레인 출처 줄은 load_project 가 붙인 lane_source(레인 전체) — 없으면 이벤트 자신의 출처."""
        self.assertEqual(S.lane_source_text({"lane_source": "A · 2026년 9월 기준 · B"}), "A · 2026년 9월 기준 · B")

    def test_rules_key(self) -> None:
        self.assertGreaterEqual(TIMELINE.series.end_label_min_gap_px, TIMELINE.series.value_size)

    def test_check_is_hard(self) -> None:
        from engine import checks

        self.assertIn("series_label_overlap", checks.HARD)


if __name__ == "__main__":
    unittest.main()


class EndLabelPlateTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0277 §2 — 끝값 라벨 뒤 판(강조 띠 위 대비, preview_v9 94초 "3.63 %"). 판 없는 끝값 라벨 = [series-label-overlap] hard."""

    def test_plate_drawn_behind_label(self) -> None:
        import cairo  # noqa: PLC0415

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 120, 60)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(1.0, 0.4, 0.1)   # 강조 띠 색 바탕
        ctx.paint()
        box = (40.0, 20.0, 80.0, 32.0)
        r = S.draw_end_label_plate(ctx, box, 1.0)
        pd = TIMELINE.series.end_label_plate.pad_px
        self.assertEqual(r[:3], (box[0] - pd, box[1] - pd, box[2] + pd))
        surf.flush()
        px = surf.get_data()[(int(r[1]) + 2) * surf.get_stride() + (int(r[0]) + 2) * 4 + 2]   # 판 안 빨강 채널(BGRA)
        self.assertLess(px, 255 * 0.5)   # 바탕(bg_rgb) 쪽으로 어두워졌다
        self.assertEqual(TIMELINE.series.end_label_plate.alpha, 0.72)

    def test_unplated_label_is_hard(self) -> None:
        from engine import checks  # noqa: PLC0415

        box = (40.0, 20.0, 80.0, 32.0)
        self.assertEqual(checks.unplated_end_labels(1.0, "policy_rate", [(32.0, 3.63, box, S.end_label_plate_rect(box))]), [])
        out = checks.unplated_end_labels(1.0, "policy_rate", [(32.0, 3.63, box, None)])
        self.assertTrue(out and "[series-label-overlap]" in out[0] and "판 없음" in out[0])


class EndLabelPinRingTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0283 §2 — 끝값 라벨 판이 핀 맥동 고리를 덮지 않는다(preview_v10 94초 "3.63 %" ↔ 9월 16일 핀 재현)."""

    def _R(self, pins: list) -> NS:  # noqa: N802
        return NS(cache={"value_pins": pins})

    def test_moves_off_ring(self) -> None:
        from engine.pin_labels import RING_PX  # noqa: PLC0415

        view = NS(to_screen=lambda x, y: (x, y))
        sx, sy, lw = 300.0, 200.0, 40.0
        h = TIMELINE.series.value_size
        by = sy + TIMELINE.series.value_dy
        box = (sx + TIMELINE.series.value_dx, by - h, sx + TIMELINE.series.value_dx + lw, by)
        R = self._R([("policy_rate", sx + 20.0, sy, 0.0, 10.0)])   # 끝점 바로 오른쪽에 핀(고리 24px)
        nb, covered = S.clear_pin_rings(R, view, 5.0, "policy_rate", box, sx, sy, lw)
        self.assertFalse(covered)
        ring = (sx + 20.0 - RING_PX, sy - RING_PX, sx + 20.0 + RING_PX, sy + RING_PX)
        self.assertFalse(S._hits(S.end_label_plate_rect(nb), ring))
        self.assertNotEqual(nb, box)
        same, cov = S.clear_pin_rings(self._R([]), view, 5.0, "policy_rate", box, sx, sy, lw)   # 핀 없으면 그대로
        self.assertEqual((same, cov), (box, False))

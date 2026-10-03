"""G7 인물 뱃지 머리 예약 = 초상 실측 + 화면 가장자리 보정 (v4.8.0, back_and_forth D-0112 A)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import cairo
from PIL import Image

from engine.layers import badges
from engine.layers.badges import badge_box, edge_nudge, portrait_head_top
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
B = load_rules().layout_480p.badge


def portraits() -> list[Path]:
    return sorted(REPO.glob("projects/*/assets/portraits/*.png")) + sorted((REPO / "assets/library/people").glob("*.png"))


class HeadReserveTest(unittest.TestCase):
    def test_rules(self) -> None:
        self.assertEqual((B.head_reserve, B.edge_nudge, B.reserve_top_factor), ("measured", True, 2.2))

    def test_measured_head_top_within_cap(self) -> None:
        """저장소 초상 전부(라이브러리 24장 + 프로젝트 초상) — 실측 머리 1~상한(2.2R), 실제로는 1.0~1.13R."""
        ps = portraits()
        self.assertGreaterEqual(len([p for p in ps if "library" in p.parts]), 24)
        for p in ps:
            with self.subTest(portrait=p.name):
                ht = portrait_head_top(Image.open(p).convert("RGBA"))
                self.assertTrue(1.0 <= ht <= B.reserve_top_factor, ht)
                self.assertLess(ht, 1.2, ht)

    def test_tall_portrait_capped(self) -> None:
        tall = Image.new("RGBA", (100, 300), (255, 255, 255, 255))   # 1.72 × 3 − 1.02 = 4.14R → 상한
        self.assertEqual(portrait_head_top(tall), B.reserve_top_factor)

    def test_box_uses_head_top_and_factor_fallback(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = dict(type="badge", kind="person", pid="p", flag="us", R=34, t0=0, t1=5, label="", head_top=1.08)
        self.assertAlmostEqual(badge_box(ctx, e, 400, 240)[1], 240 - (34 + 7))           # max(1.08R, R + 그림자)
        with mock.patch.object(badges.BADGE, "head_popout", True):   # v3 동작(머리가 원 위로) — 실측·상한 예약
            with mock.patch.object(badges.BADGE, "head_reserve", "factor"):
                self.assertAlmostEqual(badge_box(ctx, e, 400, 240)[1], 240 - 34 * B.reserve_top_factor)
            e2 = {k: v for k, v in e.items() if k != "head_top"}
            self.assertAlmostEqual(badge_box(ctx, e2, 400, 240)[1], 240 - 34 * B.reserve_top_factor)   # 초상 실측 없음 = 상한
        # v5.5.0 head_popout false(RENDER-AP-006) — 머리가 원 안이라 예약 = 원 + 그림자뿐
        self.assertFalse(B.head_popout)
        e.pop("head_top")
        self.assertAlmostEqual(badge_box(ctx, e, 400, 240)[1], 240 - (34 + 7))

    def test_edge_nudge(self) -> None:
        self.assertEqual(edge_nudge((-13, 50, 100, 200), 43, 150), (13, 0))
        self.assertEqual(edge_nudge((780, -20, 870, 100), 820, 60), (-16, 20))
        self.assertEqual(edge_nudge((-500, 50, -300, 200), -400, 150), (0, 0))     # 앵커가 화면 밖 = 보정 없음(카메라가 떠남)
        with mock.patch.object(badges.BADGE, "edge_nudge", False):
            self.assertEqual(edge_nudge((-13, 50, 100, 200), 43, 150), (0, 0))

    def test_hormuz_edge_recorded(self) -> None:
        """hormuz 이재명(t 243.5 — solo 원 왼쪽 13px)은 보정되고 provenance reserved.avoidance 에 edge 로 남는다."""
        from engine.project import load_project
        from engine.reserved import avoidance_report
        P = load_project(REPO / "projects" / "hormuz_korea")
        rows = [r for r in avoidance_report(P) if r["badge"] == "이재명"]
        self.assertTrue(any("edge" in r["strategy"] for r in rows), rows)
        self.assertTrue(all(h["head_top"] < 1.2 for h in P.R.cache["badge"]["head_top"]))


if __name__ == "__main__":
    unittest.main()

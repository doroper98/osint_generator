"""v5.21.11 D-0191 §1-3·D-0192 — 경로 라벨 자리(선이 글자를 지나가지 않게)·light 모양·검사 등록."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import cairo
import numpy as np

from engine.checks import HARD
from engine.layers.markers import marker_text_boxes
from engine.layers.routes import RL, label_candidates, place_route_label, segs_cross_box
from rules import load_rules

CTX = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
DARK = SimpleNamespace(theme=load_rules().geo.themes.dark.map)
LIGHT = SimpleNamespace(theme=load_rules().geo.themes.light.map)


def _line(p0: tuple[float, float], p1: tuple[float, float], n: int = 40) -> np.ndarray:
    return np.linspace(p0, p1, n)


class TestGeometry(unittest.TestCase):
    def test_segs_cross_box(self) -> None:
        box = (100.0, 100.0, 140.0, 120.0)
        self.assertTrue(segs_cross_box(_line((80, 110), (160, 110)), box))
        self.assertFalse(segs_cross_box(_line((80, 130), (160, 130)), box))
        self.assertTrue(segs_cross_box(_line((80, 123), (160, 123)), box, pad=4))   # 여유 안
        self.assertTrue(segs_cross_box(_line((120, 50), (120, 200)), box))         # 세로선

    def test_candidates_start_with_legacy_spot(self) -> None:
        S = _line((100, 200), (500, 200))  # noqa: N806
        x, y = S[len(S) // 2]
        self.assertEqual(label_candidates(S, 80.0)[0], (float(x), float(y - RL.legacy_dy)))


class TestPlace(unittest.TestCase):
    def test_free_legacy_spot_kept(self) -> None:
        """수평선 — 옛 자리(선 위 11px)가 선과 안 걸리면 그대로(골든 보존)."""
        S = _line((100, 200), (500, 200))  # noqa: N806
        cx, by, b, ok = place_route_label(CTX, DARK, "합의된 군사력", S, [], [S])
        self.assertTrue(ok)
        self.assertEqual((cx, by), label_candidates(S, b[2] - b[0])[0])

    def test_steep_line_moves_label_off_line(self) -> None:
        """가파른 선은 옛 자리 글자 상자를 지나간다 → 다른 후보, 어떤 선도 상자를 안 지난다."""
        S = _line((300, 80), (330, 330))  # noqa: N806
        x, y = S[len(S) // 2]
        w = 120.0
        legacy = (x - w / 2, y - RL.legacy_dy - RL.route_size, x + w / 2, y - RL.legacy_dy + RL.route_size * 0.3)
        self.assertTrue(segs_cross_box(S, legacy))
        _, _, b, ok = place_route_label(CTX, DARK, "상호방위협정 · 2025", S, [], [S])
        self.assertTrue(ok)
        self.assertFalse(segs_cross_box(S, b, RL.line_clear_px))

    def test_obstacles_and_other_lines_avoided(self) -> None:
        S = _line((100, 200), (500, 200))  # noqa: N806
        other = _line((250, 150), (450, 150))
        first = place_route_label(CTX, DARK, "라벨", S, [], [S])[2]
        _, _, b, ok = place_route_label(CTX, DARK, "라벨", S, [first], [S, other])
        self.assertTrue(ok)
        self.assertFalse(b[0] < first[2] and b[2] > first[0] and b[1] < first[3] and b[3] > first[1])
        self.assertFalse(segs_cross_box(other, b, RL.line_clear_px))

    def test_no_way_out_reports_not_ok(self) -> None:
        S = _line((100, 200), (500, 200))  # noqa: N806
        _, _, _, ok = place_route_label(CTX, DARK, "라벨", S, [(0.0, 0.0, 854.0, 480.0)], [S])
        self.assertFalse(ok)

    def test_light_label_wider_with_mark(self) -> None:
        S = _line((100, 200), (500, 200))  # noqa: N806
        bd = place_route_label(CTX, DARK, "라벨", S, [], [S])[2]
        bl = place_route_label(CTX, LIGHT, "라벨", S, [], [S])[2]
        st = LIGHT.theme.route_label
        self.assertAlmostEqual((bl[2] - bl[0]) - (bd[2] - bd[0]), st.mark_w + st.mark_gap)


class TestRules(unittest.TestCase):
    def test_theme_styles(self) -> None:
        r = load_rules()
        self.assertIsNone(r.geo.themes.dark.map.route_label)   # dark = 경로 색 글자(종전, 골든)
        self.assertEqual(r.geo.themes.light.map.route_label.style, "ink")
        self.assertGreater(r.geo.themes.light.map.route_label.mark_w, 0)

    def test_checks_registered(self) -> None:
        self.assertIn("route_label_cross", HARD)
        self.assertIn("route_label_overlap", HARD)

    def test_marker_text_boxes(self) -> None:
        e = {"label": "리야드", "side": "right"}
        self.assertEqual(len(marker_text_boxes(CTX, e, 300, 200)), 1)
        e2 = {"label": "리야드", "sub": "10월 5일 긴급회의", "side": "left"}
        boxes = marker_text_boxes(CTX, e2, 300, 200)
        self.assertEqual(len(boxes), 2)
        self.assertTrue(all(b[2] <= 300 for b in boxes))   # 왼쪽 라벨은 점 왼쪽


class TestExemptScope(unittest.TestCase):
    """D-0203 — route_cross_exempt 는 골든 기준 프로젝트(hormuz_korea) 연출의 이벤트 하나에만, 연출가 필드 표에 없다."""

    GOLDEN = {"hormuz_korea": 1}

    def test_only_golden_project(self) -> None:
        import subprocess

        from tests.anti_inertia._ast_util import REPO

        files = subprocess.run(["git", "ls-files", "projects/*/direction*.yaml"], cwd=REPO, capture_output=True, text=True,
                               check=True).stdout.split()
        self.assertTrue(files)
        for f in files:
            n = (REPO / f).read_text(encoding="utf-8").count("route_cross_exempt")
            pid = f.split("/")[1]
            want = self.GOLDEN.get(pid, 0) if f.endswith("/direction.yaml") else 0
            self.assertEqual(n, want, f)

    def test_not_in_director_field_table(self) -> None:
        from workers.direction_io import event_fields_table

        self.assertNotIn("route_cross_exempt", event_fields_table())


if __name__ == "__main__":
    unittest.main()

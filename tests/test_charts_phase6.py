"""v2 차트 5종 + network 이식 (D-0032 작업 5·6, 08 §8·§9·§3.1)."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

from engine.events import PanelNetwork
from engine.panels import network
from engine.panels.base import prov_tag_text
from engine.provenance import panels_used
from engine.registry import validate_events
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
KINDS = ("dots", "gantt", "dual_line", "fork", "checklist", "network")


def _ex(kind: str) -> dict:
    return yaml.safe_load((REPO / "prompts" / "examples" / "panels" / f"{kind}.yaml").read_text(encoding="utf-8"))["event"]


class ExampleParityTest(unittest.TestCase):
    def test_examples_equal_fixtures_and_validate(self) -> None:
        """세 곳 동시(C7): 레지스트리·렌더러·예시. 프롬프트 예시 = 프리뷰 예제, 둘 다 모델 통과(P4)."""
        reg = set(load_rules().registries.panel_kinds)
        for k in KINDS:
            self.assertIn(k, reg)
            fx = yaml.safe_load((REPO / "tests" / "fixtures" / "preview" / f"panel_{k}.yaml").read_text(encoding="utf-8"))
            self.assertEqual(fx["event"], _ex(k), k)
            self.assertEqual(len(validate_events([_ex(k)])), 1)
            self.assertTrue((REPO / "docs" / "handoff" / "reports" / "phase6" / "panels" / f"{k}.png").exists(), k)

    def test_planned_empty(self) -> None:
        self.assertEqual(load_rules().registries.panel_kinds_planned, [])


class ProvTagTest(unittest.TestCase):
    def test_rules_08_9(self) -> None:
        self.assertIsNone(prov_tag_text(None))
        self.assertIsNone(prov_tag_text({"verification": "verified", "sources": ["a"]}))
        self.assertEqual(prov_tag_text({"verification": "verified", "sources": []}), "추정 · 출처 미기재")
        self.assertEqual(prov_tag_text({"verification": "estimated", "sources": ["a"]}), "추정")
        self.assertEqual(prov_tag_text({"verification": "estimated", "sources": []}), "추정 · 출처 미기재")

    def test_data_charts_require_provenance(self) -> None:
        for k in ("dots", "gantt", "dual_line", "network"):
            bad = _ex(k)
            bad.pop("provenance")
            with self.assertRaises(Exception):
                validate_events([bad])

    def test_provenance_panels_used(self) -> None:
        evs = validate_events([_ex("gantt"), _ex("network")])
        used = panels_used(evs)
        self.assertEqual([u["kind"] for u in used], ["gantt", "network"])
        self.assertEqual(used[0]["prov_tag"], "추정 · 출처 미기재")
        self.assertIsNone(used[1]["prov_tag"])


class ChartModelTest(unittest.TestCase):
    def test_dual_line_length_and_range(self) -> None:
        bad = _ex("dual_line")
        bad["series"][0]["values"] = [88.0, 90.0]
        with self.assertRaises(Exception):
            validate_events([bad])
        bad = _ex("dual_line")
        bad["series"][0]["values"][0] = 120.0
        with self.assertRaises(Exception):
            validate_events([bad])

    def test_network_no_text_circle(self) -> None:
        bad = _ex("network")
        bad["nodes"][1] = dict(id="kr", col="left", kind="org", label="백악관")   # v2 문자 원 — 금지(08 §3.1)
        with self.assertRaises(Exception):
            validate_events([bad])

    def test_network_same_column_edge_rejected(self) -> None:
        bad = _ex("network")
        bad["edges"].append(dict(src="kr", dst="jp", type="related"))
        with self.assertRaises(Exception):
            validate_events([bad])

    def test_network_edges_after_nodes_and_rule_timing(self) -> None:
        e = validate_events([_ex("network")])[0]
        last = max(p[3] for p in network.layout(e).values())
        self.assertGreater(network.edge_start(e), last)

    def test_network_too_many_edges_warns(self) -> None:
        e = validate_events([_ex("network")])[0]
        big = copy.deepcopy(e)
        big["edges"] = big["edges"] * 2
        self.assertEqual(network.lint(e), [])
        self.assertEqual(len(network.lint(big)), 1)

    def test_unknown_network_type(self) -> None:
        bad = _ex("network")
        bad["edges"][0]["type"] = "영향"   # v2 한글 키 → 규칙 키(influence…)만
        with self.assertRaises(ValidationError):
            PanelNetwork.model_validate(bad)


if __name__ == "__main__":
    unittest.main()


class ProvTagPlacementTest(unittest.TestCase):
    """D-0034(D37) — 태그는 제목 아래 가운데, 모서리 HUD 와 겹침 0, <미검증> 라벨과 별개로 둘 다 그린다."""

    def test_below_title_not_corner(self) -> None:
        import cairo

        from engine.panels.base import body_shift, tag_boxes
        from engine.style import DATE_BADGE, PANEL, W_OUT

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        for k in KINDS:
            e = validate_events([_ex(k)])[0]
            boxes = tag_boxes(ctx, e)
            if not boxes:
                self.assertEqual(body_shift(e), 0.0, k)   # 태그 없는 패널은 본문 무변경
                continue
            x0 = min(b[2][0] for b in boxes)
            x1 = max(b[2][2] for b in boxes)
            self.assertAlmostEqual((x0 + x1) / 2, W_OUT / 2, places=6)       # 가운데
            top = min(b[2][1] for b in boxes)
            self.assertGreater(top, (PANEL.subtitle_y if e.get("subtitle") else PANEL.title_y))   # 제목·부제 아래
            self.assertGreater(top, DATE_BADGE.underline_y)                   # 날짜 배지(모서리)와 겹침 0
            self.assertGreater(body_shift(e), 0.0)

    def test_claim_label_and_tag_both_drawn(self) -> None:
        import cairo

        from engine.panels.base import tag_boxes

        e = validate_events([_ex("gantt")])[0]
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertEqual([b[0] for b in tag_boxes(ctx, e)], ["<미검증>", "추정 · 출처 미기재"])
        # 갤러리 PNG 에 두 상자 모두 실제로 칠해졌다(ru·amber 테두리 픽셀)
        from PIL import Image

        from engine.style import C

        im = Image.open(REPO / "docs" / "handoff" / "reports" / "phase6" / "panels" / "gantt.png").convert("RGB")
        for _, cname, (x0, y0, x1, y1) in tag_boxes(ctx, e):
            want = tuple(round(v * 255) for v in C[cname])
            def dist(px: tuple) -> float:   # 1px 테두리는 두 줄로 번져 밝기가 준다 — 밝기를 맞춘 뒤 색만 비교
                k = max(px) / max(want)
                return sum(abs(px[i] - want[i] * k) for i in range(3)) if k > 0.3 else 999.0

            cols = range(int(x0) + 4, int(x1) - 4)
            best = [min(dist(im.getpixel((x, y))) for y in range(int(y0) - 1, int(y0) + 2)) for x in cols]
            self.assertGreater(sum(1 for d in best if d < 40), len(best) // 2, cname)   # 윗변이 그 색으로 칠해졌다

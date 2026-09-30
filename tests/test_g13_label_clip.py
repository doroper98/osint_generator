"""G13 §D(v5.2.0, back_and_forth D-0133 B) — 차트 아일랜드 마커 라벨 반전·클램프, `[island-label-clip]` hard·`[island-label-overlap]` warning.

- §1 렌더 규칙: 아일랜드 마커 라벨이 상자 가장자리 − island.chart.label_flip_pad 를 넘으면 점 반대쪽, 그래도 넘치면 클램프.
  아일랜드 마커에만 — 지도·시간축 무대 마커 경로는 island_label 을 부르지 않는다(hormuz 골든 바이트 동일, 기록 `phaseG13/hormuz_label_clip.json`).
- §2 검사: 반전·클램프 뒤에도 상자 밖이면 hard. §3 라벨 ↔ 같은 순간 시리즈 출처 줄 교차 = warning.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace as NS
from unittest import mock

import cairo

from engine import checks
from engine import island as isl_mod
from engine.island import label_check, label_clip_details, label_overlap_details
from engine.layers import markers
from engine.layers.markers import draw_marker, island_label, island_label_rect, label_w
from engine.style import ISLAND
from rules import load_rules
from tests.anti_inertia._ast_util import REPO
from workers.prompt_loader import load_prompt

PAD = ISLAND.chart.label_flip_pad
G13 = REPO / "docs" / "handoff" / "reports" / "phaseG13"


def _ctx() -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def _mk(label: str, **kw) -> dict:  # noqa: ANN003
    return {"type": "marker", "label": label, "t0": 0.0, "t1": 10.0, "world": (0.0, 0.0), "in_island": True, **kw}


class FlipRuleTest(unittest.TestCase):
    def test_rule_value(self) -> None:
        self.assertEqual(PAD, 12)   # 기본 = 점 ↔ 라벨 여백(markers._SIDE dx)
        self.assertEqual(markers._SIDE["right"][0], PAD)

    def test_right_edge_marker_flips_left(self) -> None:
        """차트 오른쪽 끝 마커(G12·G13 검수 "다음 FOMC" 잘림) → 라벨이 점 왼쪽, 글자 상자는 상자 안."""
        ctx, e, vw = _ctx(), _mk("다음 FOMC"), 540.0
        self.assertEqual(island_label(ctx, e, vw - 20, vw), ("left", 0.0, "flip"))
        x0, _, x1, _, how = island_label_rect(ctx, e, vw - 20, 150, vw)
        self.assertEqual(how, "flip")
        self.assertLessEqual(x1, vw - PAD)
        self.assertGreaterEqual(x0, PAD)

    def test_fits_unchanged_and_clamp(self) -> None:
        ctx = _ctx()
        e = _mk("8월 소비자물가 3.35%")
        self.assertEqual(island_label(ctx, e, 100, 540), ("right", 0.0, "none"))
        w = label_w(ctx, e)
        vw = w + 2 * PAD + 30   # 어느 쪽에 붙여도 넘치고, 상자 안에는 들어가는 폭
        side, shift, how = island_label(ctx, e, vw / 2, vw)
        self.assertEqual((side, how), ("left", "clamp"))
        x0, _, x1, _, _ = island_label_rect(ctx, e, vw / 2, 100, vw)
        self.assertGreaterEqual(round(x0, 6), PAD)
        self.assertLessEqual(round(x1, 6), vw - PAD)

    def test_non_island_marker_path_untouched(self) -> None:
        """지도·시간축 무대 마커(in_island 없음)는 island_label 을 부르지 않는다 — 골든 경로 무변경."""
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 100)
        view = NS(to_screen=lambda *w: (190.0, 50.0), vw=200, vh=100)
        R = NS(zones=[], reserved=[])  # noqa: N806
        e = _mk("오른쪽 끝 긴 라벨")
        del e["in_island"]
        with mock.patch.object(markers, "island_label", side_effect=AssertionError("island path")):
            draw_marker(cairo.Context(surf), R, view, 5.0, e)
        self.assertEqual(len(R.reserved), 1)
        with mock.patch.object(markers, "island_label", side_effect=AssertionError("island path")), self.assertRaises(AssertionError):
            draw_marker(cairo.Context(surf), NS(zones=[], reserved=[]), view, 5.0, {**e, "in_island": True})   # 아일랜드 마커만 새 경로


class LabelCheckTest(unittest.TestCase):
    def _chart(self, x: float, src_rect: bool = False) -> tuple[list[dict], dict]:
        isl = {"type": "island", "kind": "chart", "box": "left", "t0": 0.0, "t1": 10.0}
        marker = _mk("다음 FOMC 회의 예정일 긴 라벨 " * 8 if x < 0 else "다음 FOMC", t0=2.0, t1=4.0)
        stage = NS(lane_screen=lambda v, i: (0.0, 170.0), lane_index=lambda lane: 0)
        chart = {"stage": stage, "cams": [None], "events": [marker]}
        if src_rect:
            chart["events"].append({"type": "series", "lane": "cpi", "t0": 0.0, "t1": 10.0, "slot": 0})
        self._x = abs(x)
        return [isl, marker], chart

    def _run(self, events: list[dict], chart: dict, y: float = 150.0) -> dict:
        view = NS(to_screen=lambda *w: (self._x, y), vw=540.0, vh=298.0)
        with mock.patch.object(isl_mod, "chart_view", return_value=view), \
             mock.patch("engine.layers.series.source_line", return_value="미국 노동통계국 · 2026년 8월 기준"):
            return label_check(events, chart)

    def test_flip_no_clip(self) -> None:
        ev, chart = self._chart(530.0)
        out = self._run(ev, chart)
        self.assertEqual(out["label_clip"], [])
        self.assertEqual(out["label_flip"], ["다음 FOMC"])

    def test_too_wide_label_clip_hard(self) -> None:
        ev, chart = self._chart(-270.0)
        out = self._run(ev, chart)
        self.assertEqual(len(out["label_clip"]), 1)   # 연속 표본은 한 구간
        r = out["label_clip"][0]
        self.assertEqual((r["island"], r["box"]), ("left", [540, 298]))
        self.assertGreater(r["t1"], r["t0"])
        d = label_clip_details(out["label_clip"])[0]
        self.assertTrue(d.startswith("[island-label-clip] marker "), d)

    def test_source_line_overlap_warning(self) -> None:
        ev, chart = self._chart(20.0, src_rect=True)   # 왼쪽 레인 이름·출처 줄 자리(x 16~)에 라벨
        out = self._run(ev, chart, y=165.0)            # 라벨 기준선 169 ≈ 출처 줄 기준선 170 − 7
        self.assertEqual([r["lane"] for r in out["label_overlap"]], ["cpi"])
        self.assertTrue(label_overlap_details(out["label_overlap"])[0].startswith("[island-label-overlap] marker '다음 FOMC' ↔ 레인 cpi"))
        far = self._run(*self._chart(20.0, src_rect=True), y=60.0)
        self.assertEqual(far["label_overlap"], [])


class RegistryTest(unittest.TestCase):
    def test_checks_registry_and_cache(self) -> None:
        self.assertIn("island_label_clip", checks.HARD)
        self.assertIn("island_label_overlap", checks.WARN)
        P = NS(R=NS(cache={"island_check": {"label_clip": [{"label": "x", "island": "left", "box": [540, 298], "rect": [500, 1, 560, 20],  # noqa: N806
                                                             "t0": 1.0, "t1": 2.0}],
                                            "label_overlap": [{"label": "y", "lane": "cpi", "t0": 3.0, "t1": 4.0}]}}))
        self.assertEqual(len(checks.check_island_label_clip(P)), 1)
        self.assertEqual(checks.check_island_label_overlap(P), ["[island-label-overlap] marker 'y' ↔ 레인 cpi 출처 줄 t=3.00~4.00"])
        self.assertEqual(checks.check_island_label_clip(NS(R=NS(cache={}))), [])   # backdrop 무대 밖 = 0

    def test_grammar_in_prompts(self) -> None:
        """연출 문법 한 줄(C7) — 연출·수정 프롬프트 둘 다."""
        for name in ("director", "revise_direction"):
            p = load_prompt(name, load_rules())
            self.assertIn("[island-label-clip]", p, name)
            self.assertIn("라벨이 점 왼쪽에 붙는다", p, name)


class HormuzGoldenRecordTest(unittest.TestCase):
    def test_hormuz_25_bytes_same_as_g12(self) -> None:
        """hormuz --preview golden 25컷 = phaseG12 기준선(25_END 는 도장 가린 md5) — 지도 무대 마커 경로 무변경 증명."""
        rec = json.loads((G13 / "hormuz_label_clip.json").read_text(encoding="utf-8"))
        base = json.loads((REPO / "docs" / "handoff" / "reports" / "phaseG12" / "hormuz_baseline.json").read_text(encoding="utf-8"))
        want = {c["png"]: c.get("md5_masked") or c["md5"] for c in base["cuts"]}
        self.assertEqual(len(want), 25)
        self.assertEqual({c["png"]: c["md5"] for c in rec["cuts"]}, want)
        self.assertEqual(rec["same_as_g12"], 25)


if __name__ == "__main__":
    unittest.main()

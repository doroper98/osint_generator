"""차트 정직성 결정적 검사 (v4.3.0, docs/handoff/20 §5.3, back_and_forth D-0084 작업 5·9, D-0087).

① 위반 주입 9건(§5.3 표 한 줄에 하나) 전부 hard ② 실제 입력 경로 주입(시간축 무대·series 레인을 그려 화면 기록으로 판정):
압축 물결 누락·단위 없는 레인·%/%p 혼용·레인 계열 4개·출처 줄 누락 ③ 적용 범위(D-0087): 날짜 축 패널은 n/a 메모, 값 축 패널 판정.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cairo
import numpy as np
import yaml

from engine import typography
from engine.honesty import CHECK_IDS, ChartMeta, judge, project_metas
from engine.project import prepare_series
from engine.projection import View
from engine.registry import resolve, validate_events
from engine.stage import attach_world, make_stage
from engine.style import FPS, H_OUT, W_OUT
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
SYN = yaml.safe_load((REPO / "tests" / "fixtures" / "honesty" / "synthetic.yaml").read_text(encoding="utf-8"))
LANES = [{"id": "policy_rate", "label": "기준금리", "kind": "step", "unit": "%"},
         {"id": "inflation", "label": "물가상승률", "kind": "line", "unit": "% (전년 대비)"},
         {"id": "events", "label": "사건", "kind": "pins"}]
CFG = {"start": "2019-01-01", "end": "2026-10-01", "lanes": LANES,
       "compress": [{"from": "2019-01-01", "to": "2021-01-01", "factor": 0.4}]}
FED = {"type": "series", "t0": 0.0, "t1": 10.0, "lane": "policy_rate", "series_id": "FEDFUNDS", "style": "step", "grow": False}
CPI = {"type": "series", "t0": 0.0, "t1": 10.0, "lane": "inflation", "series_id": "CPIAUCSL", "style": "line", "grow": False, "col": "ru"}


def preview_like(cfg: dict, raw: list[dict], times: list[float]) -> tuple[SimpleNamespace, list[str], list]:
    """시간축 프로젝트 흉내 — 실제 무대·레이어로 컷을 그리며 그린 글자를 모은다(engine.render.preview 와 같은 GLYPH_LOG 경로)."""
    st = make_stage("timeline", config=cfg)
    ev = validate_events(raw)
    attach_world(ev, st)
    n = int(max(e["t1"] for e in ev) * FPS) + 1
    cams = np.tile(np.array([st.bounds[2] / 2, 1.5, st.bounds[2]]), (n, 1))
    R = SimpleNamespace(stage=st, cache={}, reserved=[], zones=[])  # noqa: N806
    prepare_series(R, ev, cams, n)
    P = SimpleNamespace(R=R, cams=cams, n_frames=n, events=ev)  # noqa: N806
    labels = [f"t={t:.2f}" for t in times]
    drawn = []
    for t, lab in zip(times, labels):
        v = View(st, cams[int(t * FPS)])
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT))
        typography.GLYPH_LOG = []
        try:
            st.render_base(ctx, v)
            for e in ev:
                if e["t0"] <= t <= e["t1"]:
                    resolve(e).render(ctx, R, v, t, e)
            st.draw_labels(ctx, v, [], 1.0)
        finally:
            log, typography.GLYPH_LOG = typography.GLYPH_LOG, None
        drawn += [(lab, size, role, s) for size, role, s in log]
    return P, labels, drawn


def verdict(cfg: dict, raw: list[dict]) -> tuple[dict, dict]:
    P, labels, drawn = preview_like(cfg, raw, [2.0, 8.0])  # noqa: N806
    return judge(project_metas(P, [2.0, 8.0], labels, drawn))


class SyntheticInjectionTest(unittest.TestCase):
    def test_base_passes(self) -> None:
        hard, _ = judge([ChartMeta(**SYN["base"])])
        self.assertEqual({k: v for k, v in hard.items() if v}, {})

    def test_nine_violations_each_hard(self) -> None:
        self.assertEqual(len(SYN["cases"]), 9)
        for c in SYN["cases"]:
            with self.subTest(rule=c["rule"]):
                hard, _ = judge([ChartMeta(**{**SYN["base"], **c["over"]})])
                self.assertTrue(hard[c["expect"]], c["rule"])
                self.assertEqual([k for k, v in hard.items() if v], [c["expect"]])


class RealPathTest(unittest.TestCase):
    def test_timeline_demo_like_passes(self) -> None:
        hard, _ = verdict(CFG, [FED, CPI])
        self.assertEqual({k: v for k, v in hard.items() if v}, {})

    def test_compress_without_wave_fails(self) -> None:
        with mock.patch("engine.stage_timeline.TimelineStage._draw_compress", lambda *a, **k: None):
            hard, _ = verdict(CFG, [FED])
        self.assertTrue(any("[compress-unmarked]" in s for s in hard["chart_honesty"]))

    def test_lane_without_unit_fails(self) -> None:
        lanes = [dict(LANES[0], unit=None), *LANES[1:]]
        hard, _ = verdict({**CFG, "lanes": lanes}, [FED])
        self.assertTrue(hard["units_visible"])

    def test_percent_point_label_on_percent_data_fails(self) -> None:
        lanes = [dict(LANES[0], unit="%p"), *LANES[1:]]
        hard, _ = verdict({**CFG, "lanes": lanes}, [FED])
        self.assertTrue(any("[unit-mismatch]" in s for s in hard["chart_honesty"]))

    def test_four_series_in_lane_fails(self) -> None:
        many = [dict(CPI, series_id=s, style="line") for s in ("FEDFUNDS", "CPIAUCSL", "FEDFUNDS", "CPIAUCSL")]
        hard, _ = verdict(CFG, many)
        self.assertTrue(any("계열 4 > 3" in s for s in hard["series_limit_3"]))

    def test_missing_source_line_fails(self) -> None:
        with mock.patch("engine.layers.series._draw_source", lambda *a, **k: None):
            hard, _ = verdict(CFG, [FED])
        self.assertTrue(any("[source-missing]" in s for s in hard["as_of_visible"]))


class ScopeTest(unittest.TestCase):
    def test_targets_table_in_rules(self) -> None:
        t = load_rules().qa_checks.chart_targets
        self.assertEqual(set(t["value"]), set(CHECK_IDS))
        self.assertEqual(t["date"], ["chart_honesty"])
        self.assertEqual(t["none"], [])

    def test_date_panel_is_na_not_silent(self) -> None:
        m = ChartMeta(ref="panel timeline", axis="date", kind="timeline")
        hard, notes = judge([m])
        self.assertEqual({k: v for k, v in hard.items() if v}, {})
        self.assertTrue(all(any("n/a(date 축)" in s for s in notes[k]) for k in ("series_limit_3", "units_visible", "as_of_visible")))

    def test_value_panels_judged(self) -> None:
        from engine.honesty import PANEL_META  # noqa: PLC0415

        ex = yaml.safe_load((REPO / "prompts" / "examples" / "panels" / "dual_line.yaml").read_text(encoding="utf-8"))["event"]
        e = validate_events([ex])[0]
        m = ChartMeta(ref="dual_line", axis="value", kind="dual_line", **PANEL_META["dual_line"](e))
        self.assertEqual({k: v for k, v in judge([m])[0].items() if v}, {})   # y_prefix "$" = 단위 표시(D-0087 보정 1)
        e2 = {**e, "y_prefix": ""}
        m2 = ChartMeta(ref="dual_line", axis="value", kind="dual_line", **PANEL_META["dual_line"](e2))
        self.assertTrue(judge([m2])[0]["units_visible"])

    def test_panel_chart_meta_override(self) -> None:
        """보정 2 — 패널 chart 메타(막대·이중 축·로그)가 실제 입력 경로로 들어온다."""
        ex = yaml.safe_load((REPO / "prompts" / "examples" / "panels" / "dual_line.yaml").read_text(encoding="utf-8"))["event"]
        e = validate_events([{**ex, "chart": {"log_scale": True}}])[0]
        P = SimpleNamespace(R=SimpleNamespace(stage=make_stage("mercator")), events=[e], cams=None, n_frames=0)  # noqa: N806
        hard, _ = judge(project_metas(P, [], [], []))
        self.assertTrue(any("[log-unlabeled]" in s for s in hard["chart_honesty"]))


if __name__ == "__main__":
    unittest.main()

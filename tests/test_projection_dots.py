"""v7.4.0 back_and_forth D-0260 §2·D-0264 — 점도표는 패널이 아니라 금리 레인 위의 전망 점이다.

- 열 x = 그 해 12월 31일, 장기 = 마지막 연도 열 + longer_run_gap_days(rules stage_timeline.projection).
- 같은 값 참가자 수만큼 점(가로로 나란히 — primitive.dot_plot 배치와 같은 규칙), 중앙값은 코드 계산.
- 레인 값 범위가 전망 점까지 본다(D-0263 §2①). 색 = 장르 color_semantics.forecast(기존 토큰 amber).
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from data.series import load_series
from engine.layers.series import column_date, lane_range, projection_dots, record_points
from engine.stage_timeline import TimelineStage
from engine.style import ISLAND, TIMELINE
from genres.load import load_genre

SEP = load_series("SEP_20260916")
EV = [{"type": "series", "lane": "policy_rate", "series_id": "SEP_20260916", "style": "projection", "t0": 0.0, "t1": 9.0}]


def _stage() -> TimelineStage:
    st = TimelineStage(config={"start": "2025-09-01", "end": "2031-06-30",
                               "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"}]})
    st.fit_frame(tuple(TIMELINE.frame.box), ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
    return st


class ProjectionDotsTest(unittest.TestCase):
    def test_column_dates(self) -> None:
        self.assertEqual(column_date("2027", SEP.columns), date(2027, 12, 31))
        last = max(int(c.label) for c in SEP.columns if c.label.isdigit())
        self.assertEqual(column_date("Longer run", SEP.columns), date(last, 12, 31) + timedelta(days=TIMELINE.projection.longer_run_gap_days))

    def test_dots_one_per_participant_spread_horizontally(self) -> None:
        st = _stage()
        rng = lane_range(EV, "policy_rate", st)
        cols = projection_dots(st, EV[0], SEP, rng)
        self.assertEqual([len(p) for _, _, _, p, _ in cols], [len(c.values) for c in SEP.columns])
        for (_, _, _, pts, _), c in zip(cols, SEP.columns):
            same = [dx for (dx, wy) in pts if wy == pts[0][1]]
            self.assertEqual(len(same), c.values.count(c.values[0]))   # 같은 값 = 같은 높이, 가로 오프셋만 다르다
            self.assertEqual(len(set(same)), len(same))
        xs = [x for _, _, x, _, _ in cols]
        self.assertEqual(xs, sorted(xs))

    def test_lane_range_includes_projection(self) -> None:
        lo, hi = lane_range(EV, "policy_rate", _stage())
        vals = [v for _, v in record_points(SEP)]
        self.assertLessEqual(lo, min(vals))
        self.assertGreaterEqual(hi, max(vals))

    def test_example_validates_and_matches_fixture(self) -> None:
        """C7 — 예제 정본(prompts/examples)과 프리뷰 예제(tests/fixtures/preview)가 같고 이벤트 모델을 통과한다(P4)."""
        import yaml  # noqa: PLC0415

        from engine.events import SeriesEvent  # noqa: PLC0415
        from tests.anti_inertia._ast_util import REPO  # noqa: PLC0415

        a = yaml.safe_load((REPO / "prompts/examples/events/series_projection.yaml").read_text(encoding="utf-8"))
        b = yaml.safe_load((REPO / "tests/fixtures/preview/series_projection.yaml").read_text(encoding="utf-8"))
        self.assertEqual(a, b)
        ev = SeriesEvent.model_validate(a["event"])
        self.assertEqual((ev.style, load_series(ev.series_id).kind), ("projection", "scatter"))

    def test_forecast_color_is_existing_token(self) -> None:
        self.assertEqual(load_genre("macro_monetary").color_semantics["forecast"], "amber")   # D-0264 — 새 hex 금지


if __name__ == "__main__":
    unittest.main()


class LaneSourceJoinTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0266 — 같은 매체는 한 번(B), 전망 출처·고정 문구는 레인 줄이 아니라 전망 띠 태그(C)."""

    def test_same_outlet_merged_and_projection_excluded(self) -> None:
        from engine.layers.series import lane_source_join  # noqa: PLC0415

        ev = [{"type": "series", "series_id": "DFEDTARL", "upper_id": "DFEDTARU", "style": "band"},
              {"type": "series", "series_id": "FEDFUNDS", "style": "step"},
              {"type": "series", "series_id": "SEP_20260916", "style": "projection"}]
        s = lane_source_join(ev)
        self.assertEqual(s, "FRED(세인트루이스 연은) · 원출처 연준 이사회·H.15 · 2026년 8·9월 기준")
        self.assertEqual(s.count("FRED"), 1)
        self.assertNotIn("SEP", s)

    def test_projection_tags_carry_source_and_fixed_note(self) -> None:
        import numpy as np  # noqa: PLC0415

        from engine.layers.series import projection_tag_lines  # noqa: PLC0415
        from engine.projection import View  # noqa: PLC0415

        st = _stage()
        v = View(st, np.array([st.x_of("2027-06-01"), 1.0, 420.0]))
        lines = [t for t, _ in projection_tag_lines(v, st, EV[0], SEP)]
        self.assertIn("SEP", lines[0])
        self.assertEqual(lines[1], "참가자별 전망이며 약속이 아님")

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
                               "lanes": [{"id": "policy_rate", "label": "연방기금금리", "kind": "step", "unit": "%"},
                                         {"id": "events", "label": "사건", "kind": "pins"}]})
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

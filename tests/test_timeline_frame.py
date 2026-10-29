"""시간축 세계 틀(frame) — 화면 가득 채우지 않는다 (v7.4.0, back_and_forth D-0257, 사용자 의견 UF-137).

UF-137 원문: "금리 차트가 화면 좌우에 다 꽉차서 만드는 UI는 UX 측면에서 최악인거 같아."
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import numpy as np

from engine import checks
from engine.projection import View
from engine.stage_timeline import TimelineStage
from engine.style import ISLAND, TIMELINE, W_OUT

CFG = {"start": "2019-01-01", "end": "2026-12-31",
       "lanes": [{"id": "policy_rate", "label": "연방기금금리 (목표 범위·실효)", "kind": "step", "unit": "%"},
                 {"id": "inflation", "label": "소비자물가 상승률 (전년 동월 대비)", "kind": "line", "unit": "%"},
                 {"id": "events", "label": "사건", "kind": "pins"}]}


def _stage(frame: bool = True) -> TimelineStage:
    st = TimelineStage(config=CFG)
    if frame:
        st.fit_frame(tuple(TIMELINE.frame.box), ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
    return st


def _P(st: TimelineStage) -> NS:  # noqa: N802
    cams = np.tile(np.array([st.bounds[2] / 2, 1.5, st.bounds[2] * 0.6]), (24 * 10, 1))
    sent = NS(t0=1.0, t1=3.0)
    return NS(R=NS(stage=st, cache={}), plan=NS(sentences=[sent]), cams=cams, n_frames=24 * 10, events=[])


class TimelineFrameTest(unittest.TestCase):
    def test_frame_inside_screen_and_above_subtitles(self) -> None:
        x, y, w, h = TIMELINE.frame.box
        self.assertGreater(x, 0)
        self.assertLess(x + w, W_OUT)
        sub = TIMELINE.frame.box   # 자막 띠(2줄) 위 끝보다 위
        from engine.style import SUBTITLE  # noqa: PLC0415
        from rules import load_rules  # noqa: PLC0415

        top_sub = SUBTITLE.last_line_y - (load_rules().script_schema.subtitle_max_lines - 1) * SUBTITLE.line_gap - SUBTITLE.size
        self.assertLess(y + h, top_sub)
        self.assertEqual(sub, TIMELINE.frame.box)

    def test_view_maps_world_into_frame(self) -> None:
        st = _stage()
        v = View(st, np.array([st.bounds[2] / 2, 1.5, 365.0]))
        fx, fy, fw, fh = st.frame
        self.assertEqual((v.ox, v.oy, v.vw, v.vh), (fx, fy, fw, fh))
        x0, _ = v.to_screen(v.x0, 0.0)
        x1, _ = v.to_screen(v.x0 + v.w, 0.0)
        self.assertAlmostEqual(x0, fx)
        self.assertAlmostEqual(x1, fx + fw)
        top, _ = st.lane_screen(v, 0)
        _, bot = st.lane_screen(v, st.n - 1)
        self.assertGreaterEqual(top, fy)
        self.assertLessEqual(bot, fy + fh)

    def test_no_frame_is_hard(self) -> None:
        """틀 없는 시간축 주 무대(옛 화면 가득) = [chart-edge-bleed]."""
        out = checks.check_chart_edge_bleed(_P(_stage(frame=False)))
        self.assertEqual(len(out), 1)
        self.assertIn("[chart-edge-bleed]", out[0])

    def test_text_outside_frame_is_hard(self) -> None:
        """틀이 레인 이름보다 좁으면 글자 상자가 틀 밖 → hard. 기본 틀은 통과."""
        self.assertEqual(checks.check_chart_edge_bleed(_P(_stage())), [])
        st = _stage()
        st.frame = (st.frame[0], st.frame[1], 120.0, st.frame[3])   # 레인 이름 폭보다 좁게
        self.assertTrue(any("레인 이름" in s for s in checks.check_chart_edge_bleed(_P(st))))

    def test_check_is_hard(self) -> None:
        self.assertIn("chart_edge_bleed", checks.HARD)


class TimelineFrameCoverTest(unittest.TestCase):
    """v7.4.0 back_and_forth D-0259(UF-129 "그래프 넣는 씬에서 오른쪽 상단 아일랜드가 그래프를 가리지 않도록 해" — 시간축 틀 경로)."""

    def _P(self) -> NS:  # noqa: N802
        P = _P(_stage())
        P.events = [{"type": "series", "lane": "policy_rate", "series_id": "FEDFUNDS", "t0": 0.0, "t1": 9.0}]
        return P

    def _lane(self, P: NS, lane: str) -> tuple:  # noqa: N803
        st = P.R.stage
        v = View(st, P.cams[0])
        top, bot = st.lane_screen(v, st.lane_index(lane))
        return st.frame[0] + 300, top + 2, st.frame[0] + 400, bot - 2

    def test_cover_on_series_lane_is_hard(self) -> None:
        P = self._P()
        card = {"type": "card", "tag": "수치", "t0": 2.0, "t1": 5.0}
        P.events.append(card)
        box = self._lane(P, "policy_rate")
        got = checks.timeline_lanes_covered(P, lambda e, t: [box])
        self.assertEqual([(g[0]["tag"], g[1]) for g in got], [("수치", "policy_rate")])
        self.assertIn("timeline_frame_cover_types", type(checks.R_.qa_checks.card_over_panel).model_fields)

    def test_cover_on_event_lane_passes(self) -> None:
        P = self._P()
        P.events.append({"type": "card", "tag": "핀 옆", "t0": 2.0, "t1": 5.0})
        box = self._lane(P, "events")   # 레코드 없는 사건 레인 — 허용
        self.assertEqual(checks.timeline_lanes_covered(P, lambda e, t: [box]), [])

    def test_cover_straddling_frame_is_edge_bleed(self) -> None:
        from unittest import mock  # noqa: PLC0415

        P = self._P()
        P.events.append({"type": "card", "tag": "걸침", "t0": 2.0, "t1": 5.0})
        fx, fy, fw, _ = P.R.stage.frame
        with mock.patch.object(checks, "timeline_cover_box", return_value=[(fx + fw - 40, fy + 20, fx + fw + 30, fy + 90)]):
            self.assertTrue(any("걸침" in s for s in checks.check_chart_edge_bleed(P)))
        with mock.patch.object(checks, "timeline_cover_box", return_value=[(fx + fw - 140, fy + 20, fx + fw - 10, fy + 90)]):
            self.assertEqual(checks.check_chart_edge_bleed(P), [])


if __name__ == "__main__":
    unittest.main()

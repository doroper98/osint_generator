"""시리즈 레이어 series (v4.3.0, docs/handoff/20 §5.1·§6, back_and_forth D-0084 작업 4·9, D-0086).

레코드에서 직접 그림·grow 앞끝(카메라와 함께, 되돌아가도 줄지 않음)·빈 달 끊김 + "자료 없음"·값 라벨 단위·배선 오류.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import cairo
import numpy as np

from engine import typography
from engine.layers.series import lane_range, segments, value_y
from engine.project import ProjectError, prepare_series
from engine.projection import View
from engine.registry import RegistryError, resolve, validate_events
from engine.stage import attach_world, make_stage
from engine.style import C, FPS, H_OUT, TIMELINE, W_OUT
from data.series import load_series

LANES = [{"id": "policy_rate", "label": "기준금리", "kind": "step", "unit": "%"},
         {"id": "inflation", "label": "물가상승률", "kind": "line", "unit": "% (전년 대비)"},
         {"id": "events", "label": "사건", "kind": "pins"}]
CFG = {"start": "2019-01-01", "end": "2026-10-01", "lanes": LANES}


def setup(events: list[dict], cams: np.ndarray | None = None, stage_name: str = "timeline") -> tuple:
    st = make_stage(stage_name, config=CFG if stage_name == "timeline" else None)
    ev = validate_events(events)
    R = SimpleNamespace(stage=st, cache={}, reserved=[], zones=[])  # noqa: N806
    n = int(max(e["t1"] for e in ev) * FPS) + 1
    if cams is None:
        cams = np.tile(np.array([st.bounds[2] / 2, 1.5, st.bounds[2]]), (n, 1)) if stage_name == "timeline" else np.zeros((n, 3))
    prepare_series(R, ev, cams, n)
    return st, ev, R, cams


def draw(st, ev, R, cam, t):  # noqa: ANN001, ANN201, N803
    v = View(st, np.asarray(cam, float))
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
    ctx = cairo.Context(surf)
    st.render_base(ctx, v)
    typography.GLYPH_LOG = []
    try:
        for e in ev:
            resolve(e).render(ctx, R, v, t, e)
    finally:
        drawn, typography.GLYPH_LOG = typography.GLYPH_LOG, None
    surf.flush()
    img = np.ndarray((H_OUT, W_OUT, 4), np.uint8, surf.get_data())[:, :, 2::-1].astype(int)
    return v, img, [s for _, _, s in drawn]


def near(img: np.ndarray, col: str, tol: int = 60) -> np.ndarray:
    return np.abs(img - np.array(C[col]) * 255).sum(axis=2) < tol


FED = {"type": "series", "t0": 0.0, "t1": 20.0, "lane": "policy_rate", "series_id": "FEDFUNDS", "style": "step", "grow": True, "col": "gold"}
CPI = {"type": "series", "t0": 0.0, "t1": 20.0, "lane": "inflation", "series_id": "CPIAUCSL", "style": "line", "grow": False, "col": "ru"}


class SeriesDataTest(unittest.TestCase):
    def test_lane_range_includes_zero(self) -> None:
        lo, hi = lane_range([FED], "policy_rate")
        self.assertEqual(lo, 0.0)
        self.assertEqual(hi, max(v for _, v in load_series("FEDFUNDS").values))

    def test_segments_break_at_missing(self) -> None:
        segs = segments(load_series("CPIAUCSL").values)
        self.assertEqual(len(segs), 2)
        self.assertEqual((segs[0][-1][0].isoformat(), segs[1][0][0].isoformat()), ("2025-09-01", "2025-11-01"))


class SeriesDrawTest(unittest.TestCase):
    def test_drawn_from_record_with_unit_and_source(self) -> None:
        st, ev, R, cams = setup([FED, CPI])   # noqa: N806
        _, img, texts = draw(st, ev, R, cams[-1], 19.0)
        self.assertTrue(near(img, "gold").sum() > 200)
        rec = load_series("FEDFUNDS")
        self.assertTrue(any(s.endswith("%") and s[:-1].replace(".", "").isdigit() for s in texts), texts)   # 값 라벨 = 단위 포함
        self.assertIn(f"{rec.source} · {rec.as_of_label()}", texts)                                          # 출처·기준 시점 줄

    def test_grow_front_follows_camera_and_never_shrinks(self) -> None:
        st = make_stage("timeline", config=CFG)
        n = int(20 * FPS) + 1
        xs = np.concatenate([np.linspace(300, 2000, n // 2), np.linspace(2000, 800, n - n // 2)])   # 오른쪽으로 갔다가 되돌아옴
        cams = np.column_stack([xs, np.full(n, 1.5), np.full(n, 400.0)])
        st, ev, R, _ = setup([FED], cams)  # noqa: N806
        fr = R.cache["series_front"][0]
        self.assertTrue(np.all(np.diff(fr[: n]) >= 0))
        mid = n // 2
        self.assertGreater(fr[mid], fr[int(TIMELINE.series.grow_in_sec * FPS) + 1])

    def test_missing_month_breaks_line_and_is_marked(self) -> None:
        st, ev, R, _ = setup([CPI])  # noqa: N806
        cam = [st.x_of("2025-10-15"), 1.5, 200.0]
        v, img, texts = draw(st, ev, R, cam, 10.0)
        self.assertIn(TIMELINE.missing_mark.label, texts)
        rng = R.cache["series_range"]["inflation"]
        x = int(round(v.to_screen(st.x_of("2025-10-16"), 0)[0]))
        ys = [v.to_screen(0, value_y(st, "inflation", rng, val))[1] for val in (2.5, 3.2)]
        band = img[int(min(ys)) - 4: int(max(ys)) + 5, x - 1: x + 2]
        self.assertFalse(near(band, "ru").any(), "빈 달 자리에 보간 선분이 있다")


class SeriesWiringTest(unittest.TestCase):
    def test_series_on_map_stage_is_error(self) -> None:
        with self.assertRaisesRegex(ProjectError, "시간축 무대 전용"):
            setup([FED], stage_name="mercator")

    def test_series_on_pins_lane_is_error(self) -> None:
        with self.assertRaisesRegex(ProjectError, "pins"):
            setup([{**FED, "lane": "events"}])

    def test_unknown_series_is_error(self) -> None:
        with self.assertRaisesRegex(ProjectError, "레코드 없음"):
            setup([{**FED, "series_id": "NOPE"}])

    def test_numbers_not_in_direction(self) -> None:
        with self.assertRaises(RegistryError):
            validate_events([{**FED, "values": [1, 2]}])

    def test_pin_marker_attaches(self) -> None:
        st = make_stage("timeline", config=CFG)
        ev = validate_events([{"type": "marker", "t0": 0, "t1": 5, "date": "2022-03-16", "lane": "events", "label": "첫 인상"}])
        attach_world(ev, st)
        self.assertEqual(ev[0]["world"], st.to_world(date="2022-03-16", lane="events"))
        self.assertNotIn("lon", ev[0])


if __name__ == "__main__":
    unittest.main()

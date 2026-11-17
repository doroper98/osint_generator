"""v7.4.0 C0.0 2a단계(D917·UF-908) — 차트 아일랜드 안(시간축 뷰포트)의 skin 모습(rules skin.chart).

- 규칙: 엄격(모르는 키 = 오류), 아래 차례(눈금 < 가는 선 < 출처 ≤ pad_bottom), 제목 기준선은 값 범위 위.
- 화소(엔진 경로 — projects/studio_showcase 합성 사본, load_project·render_frame): 카드 안은 흰색(회색 레인 띠 없음, 중앙값 휘도 ≥ 0.97),
  강조 아닌 막대 = 중립 회색(분홍·빨강 손실 막대 없음), 강조 막대 = 주황(R ≫ B), 막대 위 모서리 직각(모서리 화소 = 막대 색).
- 배치(그리기와 같은 함수): 출처 줄 상자 ∩ 값 라벨·날짜 눈금 상자 = 0, 제목 상자 ∩ 막대·값 라벨 = 0 — 정지·카메라 이동 사본 표본 프레임 전부.
- skin 꺼짐: chart_skin() None, value_y 는 종전 레인 비율 여백(바이트 동일은 감독 identity 스크립트가 맡는다).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cairo
import numpy as np
import yaml
from pydantic import ValidationError

from engine import skin
from engine.style import SKIN, apply_palette
from rules import load_rules
from schemas.rules_models import SkinChart
from tests.test_v740_skin import showcase_project


def _hits(a: tuple, b: tuple) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _fix(o: object) -> object:
    """YAML 1.1 'off' → False 키 되돌림."""
    if isinstance(o, dict):
        return {("off" if k is False else k): _fix(v) for k, v in o.items()}
    return [_fix(x) for x in o] if isinstance(o, list) else o


def _moving_copy(proj: Path) -> None:
    """카메라가 시간축을 따라 움직이는 사본(양 끝에서 막대가 뷰 가장자리에 걸린다)."""
    p = proj / "direction.yaml"
    d = _fix(yaml.safe_load(p.read_text(encoding="utf-8")))
    d["shots"] = [d["shots"][0], {"at": 0, "stage": "timeline", "mode": "cut", "dur": 0, "camera": {"date": "2025-12-01", "w": 420}},
                  {"at": 14.0, "stage": "timeline", "mode": "move", "dur": 6.0, "camera": {"date": "2026-06-15", "w": 420}}]
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


class RulesTest(unittest.TestCase):
    def test_strict_and_order(self) -> None:
        raw = load_rules().skin.chart.model_dump()
        SkinChart.model_validate(raw)
        with self.assertRaises(ValidationError):
            SkinChart.model_validate({**raw, "bogus": 1})
        with self.assertRaises(ValidationError):
            SkinChart.model_validate({**raw, "rule": {**raw["rule"], "dy": raw["source"]["dy"] + 1}})
        with self.assertRaises(ValidationError):
            SkinChart.model_validate({**raw, "title": {**raw["title"], "dy": raw["plot_pad_top"]}})
        self.assertEqual(raw["bar_radius"], 0)   # UF-908 — 직각


class OffTest(unittest.TestCase):
    def test_off_is_old_layout(self) -> None:
        from engine.layers.series import chart_skin, value_y  # noqa: PLC0415
        from engine.stage_timeline import TimelineStage  # noqa: PLC0415
        from engine.style import TIMELINE  # noqa: PLC0415

        _off()
        self.assertIsNone(chart_skin())
        st = TimelineStage(config={"start": "2025-01-01", "end": "2026-01-01", "lanes": [{"id": "a", "label": "A", "kind": "bars"}]})
        B = TIMELINE.bars  # noqa: N806
        self.assertAlmostEqual(value_y(st, "a", (0.0, 1.0), 0.0), B.lane_pad_bottom)
        self.assertAlmostEqual(value_y(st, "a", (0.0, 1.0), 1.0), 1 - B.lane_pad_top)


class _Base(unittest.TestCase):
    moving = False

    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project  # noqa: PLC0415

        cls.tmp = tempfile.TemporaryDirectory()
        proj = showcase_project(Path(cls.tmp.name) / "s")
        if cls.moving:
            _moving_copy(proj)
        cls.P = load_project(proj, animatic=True)
        cls.isl = next(e for e in cls.P.events if e["type"] == "island")
        cls.ser = next(e for e in cls.P.events if e["type"] == "series")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()
        _off()

    def layout(self, t: float) -> dict:
        """그 순간 차트 아일랜드 안 글자·막대 상자(설계 px, 내용 영역 원점) — 그리기와 같은 함수·토큰."""
        from engine.island import chart_view, island_box  # noqa: PLC0415
        from engine.layers.series import (_grow, bar_rects, fmt_value, lane_title_box, load_series,  # noqa: PLC0415
                                          plot_right, source_line_boxes, source_style)
        from engine.style import FPS  # noqa: PLC0415
        from engine.typography import tw  # noqa: PLC0415

        chart = self.P.R.cache["island_chart"]
        st = chart["stage"]
        v = chart_view(chart, t, island_box(self.isl))
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = self.ser
        rng = self.P.R.cache["series_range"][e["lane"]]
        K = SKIN.chart  # noqa: N806
        fr = self.P.R.cache["series_front"][e["key"]]
        front = float(fr[min(len(fr) - 1, max(0, int(t * FPS)))])
        pl, pr = v.ox + K.title.x, plot_right(ctx, v, st, e["lane"], rng, "")
        bars, labels = [], []
        for _d, val, x0, x1, y0, yv in bar_rects(st, e, rng, load_series(e["series_id"])):
            k = _grow(front, x0, x1)
            if k <= 0:
                continue
            sx0, sy0 = v.to_screen(x0, y0)
            sx1, sy1 = v.to_screen(x1, y0 + (yv - y0) * k)
            if sx1 < pl or sx0 > pr:
                continue
            bars.append((max(sx0, pl), min(sy0, sy1), min(sx1, pr), max(sy0, sy1)))
            if k >= 1.0:
                s = fmt_value(val, "")
                lw = tw(ctx, s, K.value.size, K.value.font)
                by = sy1 - K.value.gap if val >= 0 else sy1 + K.value.gap + K.value.size
                lx = (sx0 + sx1) / 2 - lw / 2
                if pl <= lx and lx + lw <= pr:
                    labels.append((lx, by - K.value.size, lx + lw, by))
        fs, ff = source_style()
        src = [(x, by - fs, x + tw(ctx, ln, fs, ff), by) for ln, x, by in source_line_boxes(ctx, v, st, e)]
        ticks = [b for _, b in st.tick_label_boxes(ctx, v)]
        title = lane_title_box(ctx, v, st, 0)
        return {"bars": bars, "labels": labels, "source": src, "ticks": ticks, "title": title, "view": v}


class LayoutTest(_Base):
    moving = False

    def test_no_overlap(self) -> None:
        self.assertTrue(skin.active())
        T0, T1 = self.isl["t0"] + 2.0, self.isl["t1"] - 0.5  # noqa: N806
        for t in np.linspace(T0, T1, 12):
            L = self.layout(float(t))  # noqa: N806
            self.assertTrue(L["source"] and L["ticks"])
            for s in L["source"]:
                for o in L["labels"] + L["ticks"] + L["bars"]:
                    self.assertFalse(_hits(s, o), f"t={t:.2f} 출처 {s} ↔ {o}")
                self.assertLessEqual(s[3], L["view"].vh, f"t={t:.2f} 출처가 내용 영역 밖")
            for o in L["labels"] + L["bars"]:
                self.assertFalse(_hits(L["title"], o), f"t={t:.2f} 제목 {L['title']} ↔ {o}")
            for tk in L["ticks"]:
                for o in L["labels"] + L["bars"]:
                    self.assertFalse(_hits(tk, o), f"t={t:.2f} 눈금 {tk} ↔ {o}")

    def test_pixels(self) -> None:
        from engine.island import inner_box, island_box  # noqa: PLC0415
        from engine.layers.series import DRAWN_BARS  # noqa: PLC0415
        from engine.render import render_frame  # noqa: PLC0415
        from engine.style import FPS  # noqa: PLC0415

        P = self.P  # noqa: N806
        t = (P.plan.sentences[4].t0 + P.plan.sentences[4].t1) / 2
        DRAWN_BARS.clear()
        _, buf = render_frame(P, int(t * FPS))
        w, h = P.R.out.width, P.R.out.height
        img = np.frombuffer(bytes(buf), np.uint8).reshape(h, w, 4)[..., [2, 1, 0]].astype(np.float64) / 255
        k, px = P.R.out.k, P.R.out.pad_x
        x, y, bw, bh = inner_box(island_box(self.isl))
        sub = img[int(y * k) + 2:int((y + bh) * k) - 2, int(px + x * k) + 2:int(px + (x + bw) * k) - 2]
        lum = 0.2126 * sub[..., 0] + 0.7152 * sub[..., 1] + 0.0722 * sub[..., 2]
        self.assertGreaterEqual(float(np.median(lum)), 0.97)   # 회색 레인 띠 없음
        rects = sorted(DRAWN_BARS)
        self.assertGreaterEqual(len(rects), 3)
        for i, (x0, y0, x1, y1) in enumerate(rects):
            cx, cy = int((x0 + x1) / 2), int((y0 + y1) / 2)
            c = img[cy, cx]
            if i == len(rects) - 1:   # 최신 = 강조
                self.assertGreater(c[0] - c[2], 0.5, f"강조 막대 {c}")
            else:
                self.assertLess(max(abs(c[0] - c[1]), abs(c[1] - c[2])), 0.04, f"중립 회색 아님(분홍·빨강 손실 막대?) {c}")
            for yy in (int(y0) + 1, int(y1) - 2):   # 위·아래 모서리 화소 = 같은 줄 가운데 색(직각, UF-908)
                for xx in (int(x0) + 1, int(x1) - 2):
                    self.assertLess(np.abs(img[yy, xx] - img[yy, cx]).max(), 0.03, f"모서리 {xx},{yy} 둥글다")


class MovingLayoutTest(LayoutTest):
    moving = True

    def test_pixels(self) -> None:   # 화소는 정지 사본만
        pass


if __name__ == "__main__":
    unittest.main()

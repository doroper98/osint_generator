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


# ---- v7.4.0 2b — 차트 안 두 번째 손질(레인 여럿·예상치·끝값·자료 없음·띠·전망·쌓임·가이던스·열 확대 인셋·압축)
# 내부 시험용 자료(CPI·실효금리 레코드)는 시험 사본에만 쓴다 — projects/studio_showcase* 에 넣지 않는다(UF-906).

def _variant(proj: Path, var: str) -> None:
    """showcase 사본의 direction 을 변형 — two(레인 둘, 자료 없음 포함) · est(미래 열 예상 — 무대 끝을 열 뒤로) · dumbbell(열 확대 인셋)."""
    p = proj / "direction.yaml"
    d = _fix(yaml.safe_load(p.read_text(encoding="utf-8")))
    end = d["events"][1]["end"]
    cam = lambda date, w: [d["shots"][0], {"at": 0, "stage": "timeline", "mode": "cut", "dur": 0, "camera": {"date": date, "w": w}}]  # noqa: E731
    isl = {"type": "island", "kind": "chart", "box": "left", "start": 0.2, "end": end}
    ser = lambda lane, sid, style, col="gold", **kw: {"type": "series", "start": 0.3, "end": end, "lane": lane,  # noqa: E731
                                                      "series_id": sid, "style": style, "col": col, **kw}
    if var == "two":
        d["stage_config"]["timeline"] = {"start": "2023-01-01", "end": "2026-06-30", "lanes": [
            {"id": "cpi", "label": "소비자물가 상승률", "kind": "line", "unit": "%"},
            {"id": "ff", "label": "실효 연방기금금리", "kind": "step", "unit": "%"}]}
        d["shots"] = cam("2024-10-01", 1300)
        d["events"] = [isl, ser("cpi", "CPIAUCSL", "line"), ser("ff", "FEDFUNDS", "step", "white")]
    elif var == "est":
        d["stage_config"]["timeline"]["lanes"] = [{"id": "op", "label": "조정 주당순이익", "kind": "bars", "unit": "달러"}]
        d["events"][1].update(series_id="INTC_EPS_Q", estimate_id="INTC_EPS_Q_EST")
        d["stage_config"]["timeline"]["end"] = "2027-02-15"
        d["shots"][1]["camera"]["date"] = "2026-05-01"
    elif var == "dumbbell":
        d["stage_config"]["timeline"]["lanes"] = [{"id": "rev", "label": "분기 매출", "kind": "bars", "unit": "십억 달러"}]
        d["events"] = [isl, ser("rev", "INTC_REV_Q", "bars"),
                       {"type": "island", "kind": "column_detail", "start": 0.5, "end": end, "lane": "rev", "style": "dumbbell",
                        "series_id": "INTC_SEG_DCAI_Q", "title": "2분기 → 3분기 부문 매출 · 십억 달러", "accent": "파운드리",
                        "parts": [{"ids": ["INTC_SEG_DCAI_Q"], "label": "DC"}, {"ids": ["INTC_SEG_CCG_Q"], "label": "PC"},
                                  {"ids": ["INTC_SEG_FOUNDRY_Q"], "label": "파운드리"}]}]
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _lum(a: np.ndarray) -> np.ndarray:
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


class Rules2bTest(unittest.TestCase):
    def test_strict_blocks(self) -> None:
        raw = load_rules().skin.chart.model_dump()
        for k in ("lane", "end", "estimate", "missing", "band", "projection", "wave", "detail"):
            with self.assertRaises(ValidationError, msg=k):
                SkinChart.model_validate({**raw, k: {**raw[k], "bogus": 1}})
        with self.assertRaises(ValidationError):   # 선 레인 머리는 제목 기준선 아래
            SkinChart.model_validate({**raw, "lane": {**raw["lane"], "line_pad_top": raw["title"]["dy"]}})
        self.assertEqual(SKIN.chart.detail.level in SKIN.shadow.model_dump(), True)


class _Var(unittest.TestCase):
    var = ""

    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project  # noqa: PLC0415

        cls.tmp = tempfile.TemporaryDirectory()
        proj = showcase_project(Path(cls.tmp.name) / "s")
        _variant(proj, cls.var)
        cls.P = load_project(proj, animatic=True)
        cls.isl = next(e for e in cls.P.events if e["type"] == "island" and e.get("kind") == "chart")
        cls.sers = [e for e in cls.P.events if e["type"] == "series" and not e.get("detail")]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()
        _off()

    def frame(self, t: float) -> np.ndarray:
        from engine.render import render_frame  # noqa: PLC0415
        from engine.style import FPS  # noqa: PLC0415

        _, buf = render_frame(self.P, int(t * FPS))
        w, h = self.P.R.out.width, self.P.R.out.height
        return np.frombuffer(bytes(buf), np.uint8).reshape(h, w, 4)[..., [2, 1, 0]].astype(np.float64) / 255

    def view(self, t: float) -> tuple:
        from engine.island import chart_view, island_box  # noqa: PLC0415

        chart = self.P.R.cache["island_chart"]
        return chart["stage"], chart_view(chart, t, island_box(self.isl)), cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def dev(self, img: np.ndarray, r: tuple) -> np.ndarray:
        """설계 px 사각형(내용 영역 원점, x0·y0·x1·y1) → 화면 화소 조각."""
        from engine.island import inner_box, island_box  # noqa: PLC0415

        k, px = self.P.R.out.k, self.P.R.out.pad_x
        bx, by, _, _ = inner_box(island_box(self.isl))
        return img[int((by + r[1]) * k):int((by + r[3]) * k) + 1, int(px + (bx + r[0]) * k):int(px + (bx + r[2]) * k) + 1]


class TwoLaneTest(_Var):
    var = "two"

    def test_layout(self) -> None:
        from engine.layers.series import (lane_title_box, missing_marks, plot_pads, source_line_boxes, source_prefix,  # noqa: PLC0415
                                          value_y)
        t = self.isl["t1"] - 1.0
        st, v, ctx = self.view(t)
        K = SKIN.chart  # noqa: N806
        self.assertEqual(plot_pads(st, "cpi"), (K.lane.gap, K.lane.line_pad_top))
        self.assertEqual(plot_pads(st, "ff"), (K.plot_pad_bottom, K.lane.line_pad_top))
        ticks = [b for _, b in st.tick_label_boxes(ctx, v)]
        fs = SKIN.chart.source.size
        rows = []
        for e in self.sers:
            for k, (ln, x, by) in enumerate(source_line_boxes(ctx, v, st, e)):
                rows.append((by, ln))
                self.assertGreater(by - fs, max(b[3] for b in ticks), "출처가 눈금 아래 한 덩이")
                self.assertLessEqual(by, v.vh, "출처가 내용 영역 안")
                if k == 0:
                    self.assertTrue(ln.startswith(source_prefix(st, e["lane"])) and ln.startswith(st.lanes[st.lane_index(e["lane"])].label))
        self.assertEqual([r[1].split()[0] for r in sorted(rows)][:1], ["소비자물가"], "레인 순서대로")
        # 첫 레인 플롯 = 레인 높이 − 머리 − 틈, 다음 레인 제목은 첫 레인 플롯 아래
        rng = self.P.R.cache["series_range"]["cpi"]
        bot0 = v.to_screen(0.0, value_y(st, "cpi", rng, rng[0]))[1]
        self.assertLess(bot0, lane_title_box(ctx, v, st, 1)[1], "다음 레인 제목이 플롯 아래")
        # 자료 없음 꺾쇠는 끊긴 구간 양 끝 값보다 위
        from engine.layers.series import load_series  # noqa: PLC0415

        rec = load_series("CPIAUCSL")
        mm = missing_marks(v, st, rec, self.sers[0], rng)
        self.assertTrue(mm)
        for sa, sb, y in mm:   # 선의 점(구간 양옆 한 칸까지)은 모두 꺾쇠보다 아래 — 라벨이 선 위에 놓이지 않는다
            w = sb - sa
            near = [v.to_screen(st.x_of(d_), value_y(st, "cpi", rng, val))[1] for d_, val in rec.values
                    if sa - w <= v.to_screen(st.x_of(d_), 0.0)[0] <= sb + w]
            self.assertTrue(near)
            self.assertLess(y, min(near))

    def test_pixels(self) -> None:
        img = self.frame(self.isl["t1"] - 1.0)
        reg = self.P.R.cache.get("series_end_labels") or {}
        plates = [p[3] for ls in (reg.get("lanes") or {}).values() for p in ls]
        self.assertGreaterEqual(len(plates), 2, "끝값 라벨 둘")
        for r in plates:
            self.assertGreaterEqual(float(_lum(self.dev(img, r)).mean()), 0.85, f"끝값 판이 어둡다 {r}")


class EstimateTest(_Var):
    var = "est"

    def test_marks(self) -> None:
        from engine.layers.series import _grow, bar_rects, estimate_marks, load_series, plot_right  # noqa: PLC0415
        from engine.typography import tw  # noqa: PLC0415

        t = self.isl["t1"] - 1.0
        st, v, ctx = self.view(t)
        e = next(x for x in self.sers if x.get("estimate_id"))
        rng = self.P.R.cache["series_range"][e["lane"]]
        act = {d: (val, x0, x1, yv, _grow(1e18, x0, x1)) for d, val, x0, x1, _y, yv in bar_rects(st, e, rng, load_series(e["series_id"]))}
        mk = estimate_marks(v, st, e, rng, act)
        K = SKIN.chart  # noqa: N806
        kinds = {m["kind"] for m in mk}
        self.assertEqual(kinds, {"tick", "future"})
        pr = plot_right(ctx, v, st, e["lane"], rng, "")
        for m in mk:
            if m["kind"] == "future":
                self.assertLessEqual(m["x1"], pr, "미래 열 예상 윤곽이 숫자 열 앞에서 끝난다")
            else:
                val = act[m["d"]][0]
                sy = v.to_screen(0.0, act[m["d"]][3])[1]
                vb = min(sy, m["y"] - K.estimate.tick_w) - K.value.gap
                vl = tw(ctx, f"{val}", K.value.size, K.value.font)
                cx = (m["x0"] + m["x1"]) / 2
                lab = (cx - 50, m["by"] - K.estimate.size, cx + 50, m["by"])
                self.assertFalse(_hits(lab, (cx - vl, vb - K.value.size, cx + vl, vb)), "예상 라벨 ↔ 값 라벨")
        img = self.frame(t)
        fut = next(m for m in mk if m["kind"] == "future")
        self.assertGreaterEqual(float(_lum(self.dev(img, (fut["x0"], fut["y"], fut["x1"], fut["y0"]))).mean()), 0.85, "예상 윤곽이 무겁다")


class DumbbellTest(_Var):
    var = "dumbbell"

    def test_inset_white_square(self) -> None:
        from engine.layers.series import DRAWN_INSETS  # noqa: PLC0415

        DRAWN_INSETS.clear()
        img = self.frame(self.isl["t1"] - 1.0)
        self.assertTrue(DRAWN_INSETS)
        x0, y0, x1, y1 = (round(c) for c in DRAWN_INSETS[-1])
        sub = img[y0 + 2:y1 - 2, x0 + 2:x1 - 2]
        self.assertGreaterEqual(float(_lum(sub).mean()), 0.85, "인셋이 어두운 판")
        self.assertGreaterEqual(float(np.median(_lum(sub))), 0.95)
        c, inner = img[y0 + 1, x0 + 1], img[y0 + 1, (x0 + x1) // 2]   # 직각 — 모서리 화소 = 위 변 가운데 화소
        self.assertLess(np.abs(c - inner).max(), 0.06, "인셋 모서리가 둥글다")


if __name__ == "__main__":
    unittest.main()

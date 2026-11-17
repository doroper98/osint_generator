"""v7.4.0 C0.0 3a(UF-906·UF-908) — 패널 11종 안쪽의 디자인 시스템 판(engine/panels/*, engine/panels/skin_panel.py, rules skin.panel).

- 규칙: 엄격 모델(모르는 키·x0 ≥ x1·versus/precedent 세로 차례 어김 = 오류).
- skin(studio): 11종 프리뷰 예제(tests/fixtures/preview/panel_*.yaml)를 실제 패널 렌더러(make_panel_renderer → 흰 카드 + 본문)로 그려
  · 패널 상자 평균 밝기 ≥ 0.85, 어두운 화소(밝기 < 0.35) 비율 작음(어두운 속 카드·채운 상자 없음 — precedent·versus·fork 의 옛 어두운 카드 자리 포함)
  · 제목 = 왼쪽 정렬 잉크(제목 줄 가장 어두운 화소 ≈ 잉크 primary, 첫 잉크 화소가 skin.panel.x0 근처)
  · 패널 상자 아래 끝 밖(자막 구역 쪽)에 패널 글자가 새지 않는다(gantt 연도·dual_line 가로 라벨)
  · 추정 태그: tag_boxes 가 보고하는 상자 = 그린 well 알약 자리
- 비 skin: 패널 모듈이 skin_panel 그리기를 부르지 않는다(바이트 동일은 감독 identity 스크립트가 HEAD 와 대조).
- versus 넘침은 skin 에서도 VersusOverflowError(자름 없음, P6).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

import cairo
import numpy as np
import yaml
from pydantic import ValidationError

from engine import registry, skin
from engine.panels import skin_panel
from engine.panels import versus as versus_mod
from engine.panels.base import tag_boxes
from engine.style import H_OUT, ISLAND, PANEL, SKIN, W_OUT, apply_palette, hexc
from rules import load_rules
from schemas.rules_models import SkinPanel
from tests.anti_inertia._ast_util import REPO

PREVIEW = REPO / "tests" / "fixtures" / "preview"
KINDS = ("relation", "statement", "timeline", "precedent", "versus", "dots", "gantt", "dual_line", "fork", "checklist", "network")
BADGE_MODULES = ("relation", "statement", "precedent", "network")
BG = 0.92


def _on() -> None:
    skin.apply("studio")
    apply_palette(SKIN.palette)


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


def _event(kind: str) -> dict:
    doc = yaml.safe_load((PREVIEW / f"panel_{kind}.yaml").read_text(encoding="utf-8"))
    return registry.validate_events([doc["event"]])[0]


def _render(kind: str) -> tuple[np.ndarray, dict]:
    """스튜디오 무대 이름의 R 로 실제 패널 렌더러를 부른다(뱃지는 자산 없이 — 뱃지 층은 다른 단계 몫이라 막는다). 밝기 배열(H×W)."""
    e = _event(kind)
    R = SimpleNamespace(stage=SimpleNamespace(name="studio"), cache={}, out=SimpleNamespace(k=1.0))  # noqa: N806
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    c = cairo.Context(s)
    c.set_source_rgb(BG, BG, BG)
    c.paint()
    patches = [mock.patch(f"engine.panels.{m}.badge_at", lambda *a, **k: None) for m in BADGE_MODULES]
    for p in patches:
        p.start()
    try:
        registry.FULL_LAYERS.resolve(e).render(c, R, e["t1"] - 1.2, e)
    finally:
        for p in patches:
            p.stop()
    s.flush()
    a = np.ndarray((H_OUT, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :W_OUT, 2::-1].astype(np.float64) / 255.0
    return a @ np.array([0.2126, 0.7152, 0.0722]), e


def _box() -> tuple[int, int, int, int]:
    x, y, w, h = ISLAND.panel_box
    return int(x), int(y), int(x + w), int(y + h)


class RulesTest(unittest.TestCase):
    def test_strict(self) -> None:
        raw = load_rules().skin.panel.model_dump()
        SkinPanel.model_validate(raw)
        for bad in ({**raw, "nope": 1}, {**raw, "x0": raw["x1"]},
                    {**raw, "versus": {**raw["versus"], "src_y": raw["versus"]["top"]}},
                    {**raw, "precedent": {**raw["precedent"], "title_dy": raw["precedent"]["year_dy"]}}):
            with self.assertRaises(ValidationError):
                SkinPanel.model_validate(bad)

    def test_content_inside_panel_box(self) -> None:
        x0, _, x1, _ = _box()
        self.assertTrue(x0 < SKIN.panel.x0 < SKIN.panel.x1 < x1)


class SkinPanelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _on()
        cls.out = {k: _render(k) for k in KINDS}

    @classmethod
    def tearDownClass(cls) -> None:
        _off()

    def test_light_card_no_dark_boxes(self) -> None:
        x0, y0, x1, y1 = _box()
        for k, (lum, _) in self.out.items():
            reg = lum[y0:y1, x0:x1]
            with self.subTest(kind=k):
                self.assertGreaterEqual(reg.mean(), 0.85)
                self.assertLess(float((reg < 0.35).mean()), 0.03)

    def test_old_dark_card_areas_light(self) -> None:
        """옛 어두운 카드 자리(precedent 연도 카드·versus 기둥·fork 갈래 카드) — 속이 밝다(UF-906, 1단계 보고의 저대비 지적)."""
        from engine.panels import precedent  # noqa: PLC0415
        from rules import load_rules as _lr  # noqa: PLC0415

        F = _lr().panels.charts.fork  # noqa: N806
        areas = {"precedent": (precedent.CARD_X0, SKIN.panel.precedent.top, precedent.CARD_X0 + precedent.CARD_W, SKIN.panel.precedent.bottom),
                 "versus": (versus_mod._COLS[0][1], SKIN.panel.versus.top, versus_mod._COLS[0][1] + versus_mod.BOX_W, SKIN.panel.versus.bottom),
                 "fork": (F.card_x, F.card_y0 - F.card_h / 2, F.card_x + F.card_w, F.card_y0 + F.card_h / 2)}
        for k, (ax0, ay0, ax1, ay1) in areas.items():
            with self.subTest(kind=k):
                self.assertGreater(self.out[k][0][int(ay0):int(ay1), int(ax0):int(ax1)].mean(), 0.9)

    def test_title_left_ink(self) -> None:
        ink = float(np.array(hexc(SKIN.ink.primary)) @ np.array([0.2126, 0.7152, 0.0722]))
        y = int(PANEL.title_y)
        for k, (lum, _) in self.out.items():
            band = lum[y - int(SKIN.panel.title.size * 0.8):y + 2, :]
            dark = np.where(band.min(axis=0) < 0.3)[0]
            with self.subTest(kind=k):
                self.assertLess(band.min(), ink + 0.12)
                self.assertLessEqual(abs(int(dark[0]) - SKIN.panel.x0), 3)

    def test_nothing_below_card(self) -> None:
        """패널 상자 아래 끝 ~ 자막 구역 위(옛 gantt 연도·dual_line 라벨이 새던 띠) — 패널 글자 없음. relation 아래 인용(quote_bottom)은 규칙상 자리라 뺀다."""
        _, _, _, y1 = _box()
        for k, (lum, _) in self.out.items():
            if k == "relation":
                continue
            with self.subTest(kind=k):
                self.assertGreater(lum[y1 + 2:y1 + 8, :].min(), 0.6)

    def test_tag_box_matches_pill(self) -> None:
        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        lum, e = self.out["gantt"]
        boxes = tag_boxes(c, e)
        self.assertEqual(len(boxes), 1)
        _, _, (bx0, by0, bx1, by1) = boxes[0]
        self.assertAlmostEqual(bx1, SKIN.panel.x1)
        well = float(np.array(hexc(SKIN.surface.well)) @ np.array([0.2126, 0.7152, 0.0722]))
        edge = lum[int((by0 + by1) / 2), int(bx0) + 3]
        self.assertLess(abs(edge - well), 0.03)
        self.assertGreater(lum[int(by1) + 3, int(bx0) + 3], well)   # 알약 바로 아래 = 흰 카드


class OffPathTest(unittest.TestCase):
    def test_off_never_calls_skin_panel(self) -> None:
        _off()
        boom = mock.Mock(side_effect=AssertionError("비 skin 에서 skin_panel 호출"))
        with mock.patch.multiple(skin_panel, title=boom, hline=boom, vline=boom, dot=boom, stroke_path=boom, meta=boom, label=boom,
                                 draw_tag=boom, quote=boom, tag_box=boom):
            for k in KINDS:
                with self.subTest(kind=k):
                    _render(k)


class OverflowTest(unittest.TestCase):
    def tearDown(self) -> None:
        _off()

    def test_versus_overflow_raises_under_skin(self) -> None:
        _on()
        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertEqual(versus_mod.item_font(), SKIN.panel.versus.item_font)
        with self.assertRaises(versus_mod.VersusOverflowError):
            versus_mod.item_lines(c, "아주 긴 문장 " * 12)


if __name__ == "__main__":
    unittest.main()

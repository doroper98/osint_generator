"""v7.4.0 C0.0 2c단계(D917) — skin 무대의 전면 카드(engine/fullcards.py, rules skin.title_card·skin.end_card).

- 규칙: 엄격 모델(모르는 키·잘못된 잉크 단계·기준선 순서 = 오류).
- 타이틀: 카드가 다 들어온 프레임 평균 밝기 ≥ 0.9(어두운 장막 없음), 제목 글자 화소는 잉크로 짙다, 강조선은 주황·가운데,
  장르 template_label 이 머리 줄로 그려진다(부제 앞에 붙지 않는다).
- 엔딩: 판 평균 밝기 ≥ 0.9, 카드 뒤 홀드는 밝은 판(검정 없음), 가장 작은 글자까지 대비 ≥ 4.5, 넘침·롤 함수는 skin 과 무관.
- 엔진 경로: projects/studio_showcase 합성 plan 사본 → load_project·render_frame.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from pydantic import ValidationError

from engine import fullcards, skin
from engine.style import FPS, H_OUT, SKIN, W_OUT, hexc
from rules import load_rules
from schemas.rules_models import SkinEndCard, SkinTitleCard
from tests.test_v740_skin import _off, showcase_project


def _lum(rgb: np.ndarray) -> np.ndarray:
    """sRGB(0~1) → 상대 휘도(WCAG)."""
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def _contrast(fg: tuple[float, float, float], bg_lum: float) -> float:
    lf = float(_lum(np.asarray(fg, float)))
    hi, lo = max(lf, bg_lum), min(lf, bg_lum)
    return (hi + 0.05) / (lo + 0.05)


class RulesTest(unittest.TestCase):
    def test_strict(self) -> None:
        r = load_rules().skin
        tc, ec = r.title_card.model_dump(), r.end_card.model_dump()
        with self.assertRaises(ValidationError):
            SkinTitleCard.model_validate({**tc, "extra": 1})
        with self.assertRaises(ValidationError):
            SkinEndCard.model_validate({**ec, "meta_ink": "quaternary"})
        bad = {**tc, "date": {**tc["date"], "y": tc["kicker"]["y"] - 1}}   # 기준선 순서
        with self.assertRaises(ValidationError):
            SkinTitleCard.model_validate(bad)
        with self.assertRaises(ValidationError):
            SkinEndCard.model_validate({**ec, "head_ink": "orange"})

    def test_fonts_exist(self) -> None:
        from engine.style import FONT  # noqa: PLC0415

        t = SKIN.title_card
        for f in (t.kicker.font, t.subtitle.font, t.date.font):
            self.assertIn(f, FONT)


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project  # noqa: PLC0415

        cls.tmp = tempfile.TemporaryDirectory()
        cls.P = load_project(showcase_project(Path(cls.tmp.name) / "s"), animatic=True)
        cls.cards = {c.kind: c for c in cls.P.plan.cards}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()
        _off()

    def setUp(self) -> None:
        self.assertTrue(skin.active())

    def _frame(self, t: float, log: bool = False) -> tuple[np.ndarray, list[str]]:
        from engine import typography  # noqa: PLC0415
        from engine.render import render_frame  # noqa: PLC0415

        old = typography.GLYPH_LOG
        typography.GLYPH_LOG = [] if log else old
        try:
            surf, buf = render_frame(self.P, min(self.P.n_frames - 1, int(round(t * FPS))))
            drawn = [s for _z, _r, s in typography.GLYPH_LOG] if log else []
        finally:
            typography.GLYPH_LOG = old
        a = np.frombuffer(bytes(buf), np.uint8).reshape(surf.get_height(), surf.get_width(), 4)[..., 2::-1].astype(np.float64) / 255.0
        return a, drawn

    def test_title_light(self) -> None:
        c = self.cards["title"]
        img, drawn = self._frame(c.t0 + 3.0, log=True)
        self.assertGreaterEqual(float(img.mean()), 0.9)                      # 어두운 장막 없음
        k = img.shape[0] / H_OUT
        T = SKIN.title_card  # noqa: N806
        size = fullcards.TITLE_CARD.title_size
        band = img[int((T.title.y - size * 0.7) * k):int(T.title.y * k)]
        dark = band[_lum(band) < 0.05]
        self.assertGreater(len(dark), 1000)                                  # 제목 글자 화소
        ink = np.asarray(hexc(SKIN.ink.primary))
        self.assertLess(float(np.abs(dark.mean(0) - ink).max()), 0.06)       # 잉크(흰 글자 아님)
        ry = int((T.rule.top + T.rule.h / 2) * k)
        row = img[ry]
        acc = np.asarray(skin.ACCENT_SHAPE)
        xs = np.where(np.abs(row - acc).sum(-1) < 0.12)[0]
        self.assertGreater(len(xs), 0)                                       # 주황 강조선
        cx = (xs.min() + xs.max()) / 2 / k
        self.assertAlmostEqual(cx, W_OUT / 2, delta=1.0)                     # 가운데
        self.assertAlmostEqual((xs.max() - xs.min() + 1) / k, T.rule.w, delta=1.5)
        lab = fullcards.template_label(self.P.R)
        self.assertTrue(lab)
        self.assertIn(lab.upper(), drawn)                                    # 머리 줄
        self.assertIn(self.P.plan.subtitle, drawn)                           # 부제는 라벨 없이
        self.assertFalse(any(s.startswith(lab) and s != lab.upper() and self.P.plan.subtitle in s for s in drawn))

    def test_end_light_page(self) -> None:
        c = self.cards["end"]
        img, drawn = self._frame((c.t0 + c.t1) / 2, log=True)
        self.assertGreaterEqual(float(img.mean()), 0.9)
        self.assertIn("자료 및 출처", drawn)
        page = float(np.median(_lum(img)))
        E = SKIN.end_card  # noqa: N806
        for name, col in (("meta", fullcards.skin_ink(E.meta_ink)), ("item", fullcards.skin_ink(E.item_ink)),
                          ("head", hexc(E.head_ink)), ("heading", fullcards.skin_ink(E.heading_ink))):
            self.assertGreaterEqual(_contrast(col, page), 4.5, name)        # 가장 작은 7.8px 줄까지
        self.assertEqual(E.stamp_alpha, 1.0)                                 # 도장도 meta 잉크 그대로(알파로 옅게 하지 않는다)

    def test_hold_is_light(self) -> None:
        """카드 뒤 홀드 = 밝은 판(엔딩 카드 그리기만 — 영상 전체 페이드 FADE 는 render 몫)."""
        import cairo  # noqa: PLC0415

        c = self.cards["end"]
        s = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
        ctx = cairo.Context(s)
        ctx.set_source_rgb(0.5, 0.5, 0.5)
        ctx.paint()
        fullcards.draw_fullcards(ctx, self.P.R, c.t1 + 0.3)
        s.flush()
        a = np.ndarray((H_OUT, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :W_OUT, :3] / 255.0
        self.assertGreaterEqual(float(a.mean()), 0.5 + 0.5 * SKIN.end_card.hold_alpha - 0.01)

    def test_roll_unchanged(self) -> None:
        R = self.P.R  # noqa: N806
        secs, place, rsv = fullcards.project_credit_sections(R), fullcards.credit_place(R), fullcards.notice_reserve(R)
        on = (fullcards.endcard_layout(secs, place), fullcards.endcard_roll(secs, place, rsv), fullcards.endcard_overflow(secs, place, rsv))
        skin.apply(None)
        try:
            off = (fullcards.endcard_layout(secs, place), fullcards.endcard_roll(secs, place, rsv), fullcards.endcard_overflow(secs, place, rsv))
        finally:
            skin.apply("studio")
        self.assertEqual(on, off)


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 C0.0·UF-906(D917)·UF-908(D918) — 디자인 시스템 바탕 코어(engine/skin.py, rules skin).

- 규칙: 엄격(모르는 키 = 오류), palette 는 palettes 안, stages ⊂ registries.stages, porcelain text·muted·accent = skin 잉크·강조.
- 상태: apply("studio") = 켜짐(잉크 모드·C["white"] = 잉크), 다른 무대·None = 종전(한 프로세스 여러 영상).
- 카드 면: 같은 입력 = 같은 바이트, 그림자는 바깥으로 부드럽게 옅어진다(계단 없음), 면 안은 흰색(어두운 판 없음), 모서리 직각(D918).
- 자막: 잉크 글자(짙다), 테두리 없음(같은 줄 테두리 그리기보다 어두운 화소가 훨씬 적다), 바탕 대비 ≥ 7.
- 날짜: 잉크, 왼쪽 강조 점, 금색 밑줄 없음.
- 글자: 잉크 모드의 기본 테두리 = 없음, halo_rgb 를 직접 준 글자는 테두리 그대로.
- 엔진 경로: projects/studio_showcase(인텔 3분기 원고 cold·act1, 금리 차트 아님 — UF-906) 합성 plan 사본 → load_project·render_frame.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import cairo
import numpy as np
from pydantic import ValidationError

from engine import skin, typography
from engine.style import C, H_OUT, SKIN, W_OUT, apply_palette, hexc
from rules import load_rules
from schemas.rules_models import SkinRules, VideoRules
from tests.anti_inertia._ast_util import REPO

SHOWCASE = REPO / "projects" / "studio_showcase"
K = 1080 / H_OUT


def showcase_project(dst: Path) -> Path:
    """projects/studio_showcase 원본 파일(생성물 제외)을 dst 로 복사 + 합성 plan.json(TTS 없음) — tests.test_g8_animatic.synthetic_project 와 같은 plan."""
    from script.plan import load_script  # noqa: PLC0415
    from script.schema import Plan  # noqa: PLC0415
    from script.timeline import layout, sentence_rows  # noqa: PLC0415
    from tests.test_g8_animatic import write_synthetic_alignment  # noqa: PLC0415

    shutil.copytree(SHOWCASE, dst, ignore=shutil.ignore_patterns("out", "tts", "plan.json", "assets", "__pycache__"))
    sc = load_script(dst)
    rows = sentence_rows(sc)
    for x in rows:
        x["mp3"] = str(dst / "tts" / f"{x['sid']}.mp3")
        x["npy"] = x["mp3"] + ".npy"
        x["dur"] = round(0.8 + 0.085 * len(x["text"]), 3)
        x["trim_offset"] = 0.0
    write_synthetic_alignment(rows)
    cards, ss, total = layout(rows)
    plan = Plan(sentences=rows, cards=cards, scene_start=ss, total=total, voice="synthetic", title=sc.title,
                subtitle=sc.subtitle, date=sc.date)
    (dst / "plan.json").write_text(plan.model_dump_json(), encoding="utf-8")
    return dst


def _on() -> None:
    skin.apply("studio")
    apply_palette(SKIN.palette)


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


def _canvas(bg: float | None = None, w: int = W_OUT, h: int = H_OUT, k: float = 1.0) -> tuple[cairo.ImageSurface, cairo.Context]:
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w * k), int(h * k))
    c = cairo.Context(s)
    if bg is not None:
        c.set_source_rgb(bg, bg, bg)
        c.paint()
    c.scale(k, k)
    return s, c


def _rgb(s: cairo.ImageSurface) -> np.ndarray:
    s.flush()
    h, w = s.get_height(), s.get_width()
    return np.ndarray((h, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :w, 2::-1].astype(np.float64) / 255.0


def _lum(rgb: np.ndarray) -> np.ndarray:
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def _rel(c: np.ndarray) -> np.ndarray:
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


class RulesTest(unittest.TestCase):
    def test_strict_and_cross_refs(self) -> None:
        r = load_rules()
        raw = r.skin.model_dump()
        SkinRules.model_validate(raw)
        with self.assertRaises(ValidationError):
            SkinRules.model_validate({**raw, "theme": "dark"})
        with self.assertRaises(ValidationError):
            SkinRules.model_validate({**raw, "hairline": {**raw["hairline"], "alpha": 1.5}})
        with self.assertRaises(ValidationError):
            SkinRules.model_validate({**raw, "shadow": {**raw["shadow"], "card": []}})
        with self.assertRaises(ValidationError):
            SkinRules.model_validate({**raw, "ink": {**raw["ink"], "primary": "black"}})
        full = r.model_dump()
        with self.assertRaises(ValidationError):
            VideoRules.model_validate({**full, "skin": {**raw, "palette": "nope"}})
        with self.assertRaises(ValidationError):
            VideoRules.model_validate({**full, "skin": {**raw, "stages": ["studio", "moon"]}})
        self.assertIn(r.skin.palette, r.palettes)
        self.assertTrue(set(r.skin.stages) <= set(r.registries.stages))

    def test_palette_matches_ink(self) -> None:
        p = load_rules().palettes[SKIN.palette]
        self.assertEqual(p.text.upper(), SKIN.ink.primary.upper())
        self.assertEqual(p.muted.upper(), SKIN.ink.tertiary.upper())
        self.assertEqual(p.accent.upper(), SKIN.accent.ink.upper())
        self.assertIsNone(p.surface)   # 표준 상자 아일랜드(무대 표면 아님)

    def test_square_corners_rule(self) -> None:
        self.assertEqual(SKIN.surface.radius, 0)   # UF-908·D918 — 카드 모서리 직각


class StateTest(unittest.TestCase):
    def tearDown(self) -> None:
        _off()

    def test_apply_and_reset(self) -> None:
        self.assertTrue(skin.apply("studio"))
        apply_palette(SKIN.palette)
        self.assertTrue(skin.active() and typography.INK_MODE)
        self.assertEqual(C["white"], hexc(SKIN.ink.primary))
        self.assertEqual(typography.ink_rgb(), hexc(SKIN.ink.primary))
        for other in ("backdrop", "timeline", None):
            self.assertFalse(skin.apply(other))
            apply_palette(None)
            self.assertFalse(skin.active() or typography.INK_MODE)
            self.assertEqual(C["white"], (1, 1, 1))
            self.assertEqual(typography.ink_rgb(), (1, 1, 1))

    def test_ink_rgb_ignores_palette_when_off(self) -> None:
        """잉크 모드가 아니면 팔레트(예: noturno text)와 무관하게 흰색 — 비디자인 무대 출력 바이트 동일."""
        apply_palette("noturno")
        self.assertEqual(typography.ink_rgb(), (1, 1, 1))


class SurfaceTest(unittest.TestCase):
    BOX = (60.0, 60.0, 300.0, 200.0)

    def _card(self, k: float = K) -> np.ndarray:
        s, c = _canvas(0.94, 420, 330, k)
        skin.surface(c, self.BOX)
        return _rgb(s)

    def test_deterministic(self) -> None:
        self.assertTrue(np.array_equal(self._card(), self._card()))
        s1, c1 = _canvas(None, 420, 330, K)
        s2, c2 = _canvas(None, 420, 330, K)
        skin.soft_shadow(c1, self.BOX, 0, SKIN.shadow.card)
        skin.soft_shadow(c2, self.BOX, 0, SKIN.shadow.card)
        self.assertEqual(bytes(s1.get_data()), bytes(s2.get_data()))

    def test_soft_falloff_and_white_interior(self) -> None:
        img = _lum(self._card())
        x, y, w, h = (int(round(v * K)) for v in self.BOX)
        inner = img[y + 4:y + h - 4, x + 4:x + w - 4]
        self.assertGreaterEqual(float(inner.min()), 0.97)     # 면 안 = 흰색
        self.assertGreaterEqual(float(img[y:y + h, x:x + w].mean()), 0.9)   # 어두운 판 없음
        below = img[y + h + 1:y + h + int(60 * K), x + w // 2]   # 아래로 그림자 띠
        self.assertLess(float(below[2]), float(below[-1]))     # 가장자리 바로 밖 < 먼 바깥(그림자)
        self.assertLess(float(below[-1]), 0.94 + 0.005)
        self.assertLess(float(np.abs(np.diff(below)).max()), 0.02)   # 계단 없음 — 이웃 화소 차 작음
        side = img[y + h // 2, x + w + 1:x + w + int(40 * K)]
        self.assertLess(float(np.abs(np.diff(side)).max()), 0.02)

    def test_square_corner(self) -> None:
        """UF-908·D918 — 상자 모서리 안쪽 1 장치 px 가 카드 흰색(둥근 모서리면 바탕이 보인다)."""
        img = _lum(self._card())
        x, y, w, h = (v * K for v in self.BOX)
        for cx, cy in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
            self.assertGreaterEqual(float(img[int(cy), int(cx)]), 0.96, (cx, cy))

    def test_rounded_radius_still_works(self) -> None:
        s, c = _canvas(0.94, 420, 330, K)
        skin.surface(c, self.BOX, radius=14)
        img = _lum(_rgb(s))
        x, y = int(self.BOX[0] * K), int(self.BOX[1] * K)
        self.assertLess(float(img[y + 1, x + 1]), 0.95)   # 둥근 모서리 밖 = 바탕·그림자


class TypographyTest(unittest.TestCase):
    def tearDown(self) -> None:
        _off()

    def _draw(self, **kw: object) -> bytes:
        s, c = _canvas(0.94)
        typography.text(c, "테스트 Text 123", 40, 100, 30, "sansb", (0.1, 0.1, 0.1), 1.0, **kw)
        s.flush()
        return bytes(s.get_data())

    def test_default_halo_dropped_in_ink_mode(self) -> None:
        _on()
        self.assertEqual(self._draw(halo=3.0), self._draw(halo=0.0))
        self.assertNotEqual(self._draw(halo=3.0, halo_rgb=(0.02, 0.03, 0.05)), self._draw(halo=0.0))   # 직접 준 테두리색 = 그대로
        _off()
        self.assertNotEqual(self._draw(halo=3.0), self._draw(halo=0.0))   # 꺼지면 종전 테두리

    def test_default_colour(self) -> None:
        _on()
        s, c = _canvas(1.0)
        typography.text(c, "가", 10, 60, 50, "sansb")
        self.assertLess(float(_lum(_rgb(s)).min()), 0.2)   # 기본색 = 잉크


class SubtitleDateTest(unittest.TestCase):
    """스튜디오 바탕(밝은 회색 0.94) 위 자막·날짜 — engine.subtitles·engine.hud 를 가짜 타임베이스로."""

    def tearDown(self) -> None:
        _off()

    @staticmethod
    def _tb(date: str = "2026.10.29") -> SimpleNamespace:
        sent = SimpleNamespace(t0=0.0, t1=5.0, segments=[("회사 기준 조정 주당순이익은 ", 0), ("0.52달러", 1), ("였습니다.", 0)], date=date, role=None)
        return SimpleNamespace(order=["a"], sent={"a": sent}, hold_at=lambda t: None, cur_sentence=lambda t: "a", in_fullcard=lambda t: False)

    def _sub(self, on: bool) -> np.ndarray:
        from engine.subtitles import draw_subtitle  # noqa: PLC0415

        (_on if on else _off)()
        s, c = _canvas(0.94, k=K)
        draw_subtitle(c, SimpleNamespace(tb=self._tb()), 2.0)
        return _rgb(s)

    def test_subtitle_ink_no_outline(self) -> None:
        from engine.subtitles import subtitle_boxes  # noqa: PLC0415

        img = self._sub(True)
        lum = _lum(img)
        x0, y0, x1, y1 = (int(v * K) for v in subtitle_boxes(cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)), self._tb(), 2.0)[0])
        glyph = lum[y0:y1, x0:x1]
        self.assertLess(float(glyph.min()), 0.2)                             # 잉크(짙다)
        dark_skin = int((lum < 0.5).sum())
        dark_halo = int((_lum(self._halo_line()) < 0.5).sum())
        self.assertLess(dark_skin, dark_halo * 0.6)                          # 테두리 없음 — 같은 줄을 잉크 + 굵은 테두리로 그린 것보다 훨씬 적다
        ink = np.asarray(hexc(SKIN.ink.primary))
        bg = np.percentile(img[y0:y1, x0:x1].reshape(-1, 3), 95, axis=0)    # 글자 둘레 바탕(번짐 포함)
        ratio = (float(_rel(bg)) + 0.05) / (float(_rel(ink)) + 0.05)
        self.assertGreaterEqual(ratio, 7.0)

    def _halo_line(self) -> np.ndarray:
        """대조군 — 같은 문자열을 잉크 + 종전 테두리(SUBTITLE.halo)로(잉크 모드 끔)."""
        from engine.style import SUBTITLE  # noqa: PLC0415

        _off()
        s, c = _canvas(0.94, k=K)
        x = W_OUT / 2 - typography.tw(c, "회사 기준 조정 주당순이익은 0.52달러였습니다.", SUBTITLE.size, "sansm") / 2
        typography.text(c, "회사 기준 조정 주당순이익은 0.52달러였습니다.", x, SUBTITLE.last_line_y, SUBTITLE.size, "sansm",
                        hexc(SKIN.ink.primary), 1.0, SUBTITLE.halo, "l", halo_a=SUBTITLE.halo_alpha)
        return _rgb(s)

    def test_subtitle_off_unchanged_white(self) -> None:
        img = self._sub(False)
        self.assertGreater(float(_lum(img).max()), 0.99)                     # 종전: 흰 글자 + 짙은 테두리
        self.assertLess(float(_lum(img).min()), 0.2)

    def test_date(self) -> None:
        from engine.hud import draw_date  # noqa: PLC0415
        from engine.style import DATE_BADGE  # noqa: PLC0415

        _on()
        s, c = _canvas(0.94, k=K)
        draw_date(c, SimpleNamespace(tb=self._tb()), 3.0)
        img = _rgb(s)
        lum = _lum(img)
        ys, xs = np.nonzero(lum < 0.3)
        self.assertGreater(len(xs), 50)                                      # 잉크 글자
        acc = np.asarray(hexc(SKIN.accent.shape))
        hit = np.nonzero(np.abs(img - acc).sum(-1) < 0.12)
        self.assertGreater(len(hit[0]), 4)                                   # 강조 점
        self.assertLess(float(hit[1].max()), float(xs.min()))                # 글자 왼쪽
        gold = np.asarray(hexc(load_rules().colors.gold))
        self.assertEqual(int((np.abs(img - gold).sum(-1) < 0.15).sum()), 0)   # 금색 없음
        uy = int(DATE_BADGE.underline_y * K)
        self.assertGreater(float(lum[uy:uy + 3].min()), 0.9)                 # 밑줄 자리 비었음


class EnginePathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.proj = showcase_project(Path(cls.tmp.name) / "s")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()
        _off()

    def test_load_and_render(self) -> None:
        from engine.project import load_project  # noqa: PLC0415
        from engine.render import render_frame  # noqa: PLC0415
        from engine.style import FPS  # noqa: PLC0415

        P = load_project(self.proj, animatic=True)  # noqa: N806
        self.assertEqual(P.R.stage.name, "studio")
        self.assertEqual(P.R.cache["palette"], SKIN.palette)                  # 장르(earnings → noturno)보다 skin.palette
        self.assertEqual(P.R.cache["skin"], {"name": SKIN.palette, "stage": "studio"})
        self.assertTrue(skin.active())
        s = P.plan.sentences[3]
        _, buf = render_frame(P, int((s.t0 + s.t1) / 2 * FPS))
        self.assertEqual(len(bytes(buf)), P.R.out.width * P.R.out.height * 4)


if __name__ == "__main__":
    unittest.main()

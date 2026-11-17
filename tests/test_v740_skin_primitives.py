"""v7.4.0 C0.0 3c(UF-906) — 프리미티브 6종 skin 판(rules skin.primitives, engine/primitives/*).

skin 무대(engine.skin.active())면: 어두운 상자 없음(요소 상자 평균 밝기 ≥ 0.85), 글자 = 잉크(테두리 없음), 카드는 직각,
상자 함수(primitive_box)가 그리기와 같은 상자를 돌려준다. 꺼지면 기하 토큰이 rules primitives 그대로(종전 바이트 —
전 화면 대조는 감독 identity 스크립트). 규칙 모델은 엄격(모르는 키 = 오류), layout 덮어쓰기 키는 rules primitives 키만.
"""

from __future__ import annotations

import unittest
from typing import Any

import cairo
import numpy as np
from pydantic import ValidationError

from engine import skin, typography
from engine.primitives import PrimitiveError, _check_skin_layout, geo, module, primitive_box, style_for
from engine.style import PRIMITIVES, SKIN, apply_palette
from genres.load import load_genre
from schemas.rules_models import SkinPrimitives

GENRE = {"statement_diff": "macro_monetary", "dot_plot": "macro_monetary", "site_diagram": "geopolitics",
         "process_lane": "political_history", "doc_excerpt": "political_history", "era_numeral": "political_history"}
CARDS = ("statement_diff", "dot_plot", "site_diagram", "process_lane", "doc_excerpt")
BG = 0.90   # 무대 대신 칠하는 밝은 회색(카드 직각 판정 — 카드 안쪽 모서리 화소는 이보다 밝다)
K = 2.0


def _on() -> None:
    skin.apply("studio")
    apply_palette(SKIN.palette)


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


def _event(pid: str) -> dict:
    return dict(module(pid).PREVIEW_FIXTURE)


def _time(e: dict) -> float:
    return e["t1"] - 1.0   # 등장·표시가 다 나온 뒤(퇴장 페이드 전)


def _render(pid: str) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    e = _event(pid)
    st = style_for(pid, load_genre(GENRE[pid]).color_semantics)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(854 * K), int(480 * K))
    c = cairo.Context(s)
    c.set_source_rgb(BG, BG, BG)
    c.paint()
    c.scale(K, K)
    box = module(pid).draw(c, None, _time(e), e, st)
    s.flush()
    a = np.ndarray((s.get_height(), s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :s.get_width(), :3]
    return a[..., ::-1].astype(np.float32) / 255, box


def _luma(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


class SkinPrimitiveRulesTest(unittest.TestCase):
    def test_strict_model(self) -> None:
        d = SKIN.primitives.model_dump()
        d["statement_diff"]["glow"] = 1
        with self.assertRaises(ValidationError):
            SkinPrimitives.model_validate(d)
        d = SKIN.primitives.model_dump()
        d["process_lane"]["title"]["ink"] = "gold"
        with self.assertRaises(ValidationError):
            SkinPrimitives.model_validate(d)

    def test_layout_keys_are_primitive_keys(self) -> None:
        blk = SKIN.primitives.statement_diff
        old = dict(blk.layout)
        blk.layout["no_such_key"] = 1.0
        try:
            with self.assertRaisesRegex(PrimitiveError, "no_such_key"):
                _check_skin_layout()
        finally:
            blk.layout.clear()
            blk.layout.update(old)
        _check_skin_layout()

    def test_geo_off_is_rules_primitives(self) -> None:
        _off()
        for pid in GENRE:
            self.assertIs(geo(pid), PRIMITIVES[pid])
        _on()
        try:
            G = geo("statement_diff")  # noqa: N806
            for k, v in SKIN.primitives.statement_diff.layout.items():
                self.assertEqual(getattr(G, k), v)
        finally:
            _off()


class SkinPrimitiveDrawTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()

    def tearDown(self) -> None:
        _off()

    def test_no_dark_box(self) -> None:
        for pid in CARDS:
            with self.subTest(primitive=pid):
                img, (x0, y0, x1, y1) = _render(pid)
                part = _luma(img[int(y0 * K):int(y1 * K), int(x0 * K):int(x1 * K)])
                self.assertGreaterEqual(float(part.mean()), 0.85, f"{pid} 상자 평균 밝기")

    def test_square_card_corners(self) -> None:
        for pid in CARDS:
            with self.subTest(primitive=pid):
                img, (x0, y0, x1, _) = _render(pid)
                corner = _luma(img[int(y0 * K) + 2, int(x0 * K) + 2])
                self.assertGreater(float(corner), BG + 0.04, f"{pid} 카드 왼쪽 위 안쪽 화소가 무대색 — 둥근 모서리(UF-908)")

    def test_era_numeral_bare_text(self) -> None:
        img, box = _render("era_numeral")
        self.assertEqual(box[0], box[2])   # 예약 상자 = 점(배경 글자)
        x, y = box[0], box[1]
        size = PRIMITIVES["era_numeral"].size
        ring = [img[int((y - size * 1.2) * K), int(x * K)], img[int((y + size * 0.6) * K), int((x - size * 2.4) * K)]]
        for px in ring:
            self.assertGreater(float(_luma(px)), BG - 0.01, "숫자 둘레에 상자·판 없음")
        glyph = _luma(img[int((y - size) * K):int(y * K), int((x - size) * K):int((x + size) * K)])
        self.assertLess(float(glyph.min()), 0.2, "숫자 = 짙은 잉크")

    def test_ink_text_without_outline(self) -> None:
        calls: list[tuple[str, Any, float, str]] = []
        orig = typography.text

        def spy(ctx: cairo.Context, s: str, x: float, y: float, size: float, name: str = "sansm", col: Any = None, a: float = 1.0,
                halo: float = 3.0, *args: Any, **kw: Any) -> float:
            if s.strip():
                calls.append((s, col, halo, name))
            return orig(ctx, s, x, y, size, name, col, a, halo, *args, **kw)

        mods = [module(pid) for pid in GENRE]
        saved = [(m, getattr(m, "text", None)) for m in mods]
        typography.text = spy  # type: ignore[assignment]
        for m in mods:
            if hasattr(m, "text"):
                m.text = spy
        try:
            for pid in GENRE:
                _render(pid)
        finally:
            typography.text = orig  # type: ignore[assignment]
            for m, f in saved:
                if f is not None:
                    m.text = f
        self.assertTrue(calls)
        limit = float(_luma(np.array(skin.INK3)))
        for s, col, halo, _ in calls:
            with self.subTest(text=s):
                self.assertEqual(halo, 0, "테두리 없는 잉크 글자(C0.0)")
                self.assertIsNotNone(col)
                if s.isdigit() and len(s) == 1:   # process_lane 번호 원 안 흰 숫자
                    continue
                self.assertLessEqual(float(_luma(np.array(col[:3]))), limit + 1e-6, f"{s!r} 글자색이 잉크 3단보다 밝다")

    def test_box_function_matches_draw(self) -> None:
        for pid in GENRE:
            with self.subTest(primitive=pid):
                e = _event(pid)
                _, drawn = _render(pid)
                self.assertEqual(tuple(round(v, 6) for v in primitive_box(e)), tuple(round(v, 6) for v in drawn))

    def test_skin_box_follows_layout_override(self) -> None:
        e = _event("statement_diff")
        on = primitive_box(e)
        _off()
        off = primitive_box(e)
        _on()
        self.assertEqual(on[0], off[0])
        self.assertNotEqual(on[3] - on[1], off[3] - off[1], "skin 기하(layout 덮어쓰기)가 상자 높이에 반영")


if __name__ == "__main__":
    unittest.main()

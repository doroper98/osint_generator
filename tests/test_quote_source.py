"""고대 사료 인용 카드(quote.source, v7.4.0 back_and_forth D-0617 ①) — 모델·문구·렌더(세 곳 동시, 15 P10)."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import cairo
import yaml
from pydantic import ValidationError

from engine.events import QuoteEvent
from engine.quote import QuoteError, draw_quote, quote_box, source_credit, source_orig_lines

FIX = Path(__file__).resolve().parent / "fixtures" / "preview" / "war" / "quote_source.yaml"


def _ev() -> dict:
    return yaml.safe_load(FIX.read_text(encoding="utf-8"))["event"]


class QuoteSourceTest(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        e = QuoteEvent.model_validate(_ev())
        self.assertIsNone(e.flag)
        self.assertEqual(e.source.locator, "III.117.1")

    def test_source_and_flag_together_is_error(self) -> None:
        for extra in ({"flag": "it"}, {"pid": "x"}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                QuoteEvent.model_validate({**_ev(), **extra})

    def test_neither_is_error(self) -> None:
        e = _ev()
        e.pop("source")
        with self.assertRaises(ValidationError):
            QuoteEvent.model_validate(e)

    def test_credit_line(self) -> None:
        self.assertEqual(source_credit(_ev()["source"]), "폴리비오스 『역사』 III.117.1 · W. R. Paton 영역(1922, 퍼블릭 도메인)에서 옮김")

    def test_original_overflow_is_error(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = _ev()
        e["source"]["original"] = " ".join(["conspicuous bravery"] * 60)
        with self.assertRaises(QuoteError):
            source_orig_lines(ctx, e)

    def test_renders_without_badge(self) -> None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
        ctx = cairo.Context(surf)
        e = _ev()
        draw_quote(ctx, NS(cache={}), 5.0, e)   # 초상·국기 없음 — badge_at 를 부르지 않는다(R 은 덮개 기록만)
        surf.flush()
        b = quote_box(ctx, e)
        self.assertLess(b[1], b[3])
        self.assertTrue(any(v for v in bytes(surf.get_data())[:: 4 * 97]))


if __name__ == "__main__":
    unittest.main()

"""프리미티브 doc_excerpt — 1차 문서 발췌 (v7.4.0, 사용자 의견 UF-400 · 영상 분석 보고 §4 D6).

불변 층: 기관·문서 이름·문서 날짜·출처·번역 필수, 원문 ≤ 인용 상한, 밑줄 구절은 원문 안에 그대로(없으면 오류).
밑줄은 highlight_t 전에는 없다. 번역은 trans_delay_sec 뒤에 떠오른다. 상자는 매 프레임 같은 자리.
"""

from __future__ import annotations

import copy
import unittest

import cairo
from pydantic import ValidationError

from engine.primitives import event_model, module, style_for
from engine.style import PRIMITIVES, QUOTE_MAX_CHARS
from genres.load import load_genre

MOD = module("doc_excerpt")
FX = MOD.PREVIEW_FIXTURE
L = PRIMITIVES["doc_excerpt"]


def _data(**over: object) -> dict:
    d = {k: copy.deepcopy(v) for k, v in FX.items() if k not in ("type", "id", "t0", "t1")}
    d.update(over)
    return d


def _render(t: float, e: dict) -> bytes:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    MOD.draw(cairo.Context(surf), None, t, e, style_for("doc_excerpt", load_genre("political_history").color_semantics))
    return bytes(surf.get_data())


class DocExcerptDataTest(unittest.TestCase):
    def test_fixture_passes_schema(self) -> None:
        event_model("doc_excerpt", MOD.SCHEMA).model_validate(FX)

    def test_invalid_data_is_error(self) -> None:
        bad = {
            "empty translation": _data(translation=" "),
            "empty source": _data(source=""),
            "bad date": _data(doc_date="1982-02"),
            "too long": _data(original="word " * (QUOTE_MAX_CHARS // 5 + 1)),
            "highlight not in original": _data(highlight="officially introduced"),
            "unknown field": _data(scan="page.png"),
        }
        for why, d in bad.items():
            with self.subTest(why=why), self.assertRaises(ValidationError):
                MOD.SCHEMA.model_validate(d)


class DocExcerptMotionTest(unittest.TestCase):
    def test_underline_waits_for_its_time(self) -> None:
        ht = FX["highlight_t"]
        no_hl = {**FX, "highlight": None}
        self.assertEqual(_render(ht - 0.1, FX), _render(ht - 0.1, no_hl))
        self.assertNotEqual(_render(ht + L.underline_grow_sec, FX), _render(ht + L.underline_grow_sec, no_hl))

    def test_translation_rises_after_delay(self) -> None:
        early = _render(FX["t0"] + L.trans_delay_sec - 0.05, FX)
        other = _render(FX["t0"] + L.trans_delay_sec - 0.05, {**FX, "translation": "다른 번역 문장"})
        self.assertEqual(early, other)

    def test_box_is_fixed(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        st = style_for("doc_excerpt", load_genre("political_history").color_semantics)
        boxes = {MOD.draw(ctx, None, t, FX, st) for t in (0.1, 3.0, 8.9, 20.0)}
        self.assertEqual(len(boxes), 1)
        self.assertLessEqual(boxes.pop()[3], 400, "자막 구역 위에 끝나야 한다")


if __name__ == "__main__":
    unittest.main()

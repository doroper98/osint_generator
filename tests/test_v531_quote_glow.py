"""v5.3.1 시안 두 가지(사용자 제안 2026-10-02, valdai-2026 한정) — 인물 발언 중앙 인용(quote)·국경선 글로우(border_glow)."""

from __future__ import annotations

import unittest

import cairo
import yaml

from engine.events import QuoteEvent
from engine.quote import QuoteError, quote_lines
from engine.stage import MercatorStage, StageError
from engine.style import BORDER_GLOW, QUOTE
from tests._fonts import NO_FONTS_REASON, fonts_ready
from tests.anti_inertia._ast_util import REPO


def _q(text: str) -> dict:
    return dict(type="quote", t0=1.0, t1=5.0, pid="putin", flag="ru", speaker="블라디미르 푸틴", role="러시아 대통령", text=text,
                src="로이터", date="2026. 10. 01", accent="ru")


class PrototypeStatusTest(unittest.TestCase):
    def test_prototype_until_user_judges(self) -> None:
        """사용자 판정 전 = prototype(마음에 들면 규약 승격 — 사용자 지시 2026-10-02)."""
        self.assertEqual(QUOTE.status, "prototype")
        self.assertEqual(BORDER_GLOW.status, "prototype")


class QuoteModelTest(unittest.TestCase):
    def test_marks_drawn_by_code(self) -> None:
        """따옴표는 코드가 그린다 — text 에 넣으면 모델 오류(이중 따옴표 방지)."""
        QuoteEvent.model_validate(_q("모든 것이 올바르게 쓰였다"))
        with self.assertRaises(ValueError):
            QuoteEvent.model_validate(_q("“모든 것이 올바르게 쓰였다”"))

    @unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
    def test_overflow_is_error(self) -> None:
        """quote_max_lines 를 넘으면 QuoteError — 자름·말줄임 없음(15 P6)."""
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertLessEqual(len(quote_lines(ctx, _q("금지와 제재 때문에 세계시장에 나가지 못할 것"))), QUOTE.quote_max_lines)
        with self.assertRaises(QuoteError):
            quote_lines(ctx, _q(" ".join(["아주 긴 인용문이 이어집니다"] * 12)))


class BorderGlowConfigTest(unittest.TestCase):
    def test_mercator_config_only_border_glow(self) -> None:
        """지도 무대 stage_config 는 border_glow(bool) 하나 — 그 밖 키 = 오류(P10). 기본 꺼짐(골든 무설정)."""
        self.assertFalse(MercatorStage().border_glow)
        self.assertTrue(MercatorStage(config={"border_glow": True}).border_glow)
        with self.assertRaises(StageError):
            MercatorStage(config={"glow": True})
        with self.assertRaises(StageError):
            MercatorStage(config={"border_glow": "yes"})

    def test_only_valdai_opts_in(self) -> None:
        """이번 영상만 적용(사용자 지시) — 저장소에서 border_glow·quote 를 쓰는 연출은 valdai-2026 하나."""
        users = {"glow": set(), "quote": set()}
        for f in sorted((REPO / "projects").glob("*/direction.yaml")):
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            if ((d.get("stage_config") or {}).get("mercator") or {}).get("border_glow"):
                users["glow"].add(f.parent.name)
            if any(e.get("type") == "quote" for e in d.get("events") or []):
                users["quote"].add(f.parent.name)
        self.assertEqual(users, {"glow": {"valdai-2026"}, "quote": {"valdai-2026"}})


if __name__ == "__main__":
    unittest.main()

"""v7.4.0 RENDER-AP-033 — 글리프 검사·전수 검사가 미디어 레지스트리 문자열(기사 헤드라인·번역 줄·캡션)도 본다.

예산안 완성본 345초: 기사 카드 번역 줄(레지스트리 headline)의 '與' 가 산스 글꼴에 없어 두부(▯)로 찍혔다.
이벤트에는 mid 만 있어 glyph_sweep 이 그 카드 시각을 그리지 않았고, 프리뷰 표본(340.42초)도 카드 전이었다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks, render


def _P(headline: str, original: str | None = "국힘 vs. 與") -> NS:  # noqa: N802
    a = NS(headline=headline, headline_original=original, sub=None, caption="SBS Biz", file_note="2026. 10. 30")
    e = {"type": "article", "mid": "art", "t0": 343.0, "t1": 349.0}
    return NS(R=NS(assets=NS(media_assets={"art": a})), events=[e], n_frames=24 * 400)


class EventStringsTest(unittest.TestCase):
    def test_registry_strings_included(self) -> None:
        P = _P("국힘 vs. 與")
        got = checks.event_strings(P, P.events[0])
        self.assertIn("국힘 vs. 與", got)
        self.assertIn("SBS Biz", got)

    def test_no_registry_context_is_event_only(self) -> None:
        self.assertEqual(checks.event_strings(NS(), {"type": "photo", "mid": "x", "for": "국회"}), ["국회"])


class SweepRendersRegistryCardTest(unittest.TestCase):
    def _frames(self, headline: str, original: str | None = "국힘 vs. 與") -> list[int]:
        seen: list[int] = []
        with mock.patch.object(render, "render_frame", side_effect=lambda P, f: seen.append(f)):
            render.glyph_sweep(_P(headline, original))
        return seen

    def test_completed_state_sweeps_article_time(self) -> None:
        """예산안 완성본 상태(번역 줄 '與') — 기사 카드가 뜬 시각을 그려 실제 글꼴로 대조한다."""
        seen = self._frames("국힘 vs. 與")
        self.assertEqual(len(seen), 1)
        self.assertTrue(343 * 24 <= seen[0] <= 349 * 24)

    def test_registry_text_reaches_sweep_trigger(self) -> None:
        """레지스트리 문자열이 없으면(옛 경로 = 이벤트 필드만) 이 카드는 그려지지 않았다 — 지금은 레지스트리 문자열로 걸린다."""
        self.assertEqual(checks._strings(_P("국힘 vs. 與").events[0]), [])   # 옛 경로(이벤트 필드만) = 문자열 없음 → 그리지 않았다
        self.assertTrue(self._frames("국힘 vs. 與", None))   # 번역 줄 하나만으로도 그 시각을 그린다


if __name__ == "__main__":
    unittest.main()


class FinalGlyphGateTest(unittest.TestCase):
    """감독 D623 — 전편 렌더 전 관문. 與 + 산스 = 오류(전달본 사고 재현), 막히면 render_full 을 부르지 않는다."""

    def test_sans_lacks_yeo_serif_has_it(self) -> None:
        from engine import typography  # noqa: PLC0415
        from tests._fonts import fonts_ready  # noqa: PLC0415

        if not fonts_ready():
            self.skipTest("표준 글꼴 없음")
        self.assertNotIn(ord("與"), typography.font_cmap("sans"))
        self.assertIn(ord("與"), typography.font_cmap("serif"))

    def test_gate_lists_sweep_miss(self) -> None:
        miss = [("sweep article t=344.38", "sans", "與", "국힘 vs. 與")]
        with mock.patch.object(render, "glyph_sweep", return_value=miss), \
             mock.patch("engine.checks.check_glyphs", return_value=[]):
            out = render.final_glyph_gate(NS())
        self.assertEqual(len(out), 1)
        self.assertIn("與", out[0])
        self.assertIn("sans", out[0])

    def test_main_refuses_final_render(self) -> None:
        with mock.patch.object(render, "load_project", return_value=NS(warnings=[], R=NS(out=NS(name="final")))), \
             mock.patch.object(render, "final_glyph_gate", return_value=["[glyphs] x"]), \
             mock.patch.object(render, "render_full") as rf, \
             mock.patch("sys.stdout", new_callable=__import__("io").StringIO) as so:
            rc = render.main(["projects/budget_2027", "--res", "final"])
        self.assertEqual(rc, 1)
        self.assertIn("글리프 관문", so.getvalue())
        rf.assert_not_called()

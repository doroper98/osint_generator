"""v4.5.0 D85(C9 개정) — 검증 라벨은 자막에 그리지 않는다(v3.3.0 NB12 접두 폐지) · F6 auto 프리뷰 본편 컷 최소 수."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import cairo
import numpy as np

from engine.checks import missing_fonts
from engine.style import H_OUT, W_OUT
from engine.subtitles import draw_subtitle
from rules import load_rules


def _frame(label: str | None) -> np.ndarray:
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
    ctx = cairo.Context(surf)
    sent = NS(t0=1.0, t1=4.0, segments=[("대만해협은 바다입니다.", 0)])
    R = NS(tb=NS(order=["a_0"], sent={"a_0": sent}), cache={"sentence_labels": {"a_0": label} if label else {}})  # noqa: N806
    draw_subtitle(ctx, R, 2.0)
    surf.flush()
    return np.frombuffer(surf.get_data(), np.uint8).reshape(H_OUT, W_OUT, 4)[..., [2, 1, 0]]


_MISSING_FONTS = missing_fonts()


class SubtitleLabelTest(unittest.TestCase):
    # 렌더 경로(engine.typography)는 글꼴이 없으면 fontconfig 대체 글꼴로 그린다 — 라벨 픽셀 수가 달라진다(D-0057 §2 NB14).
    # 렌더 경로 글꼴 검사(P6)는 Phase 10 후보. 지금은 글리프 검사(test_checks)와 같은 사유 있는 skip.
    @unittest.skipIf(bool(_MISSING_FONTS), f"프로젝트 글꼴 없음 {_MISSING_FONTS} — `python tools/fetch_data.py fonts` 필요(D-0057 NB14)")
    def test_label_sentence_frame_equals_unlabeled(self) -> None:
        """라벨이 붙은 문장도 자막 픽셀이 라벨 없는 문장과 같다 — 라벨 글리프 0."""
        for lab in (v for v in load_rules().script_schema.labels.values() if v):
            self.assertTrue(np.array_equal(_frame(lab), _frame(None)), lab)

    def test_label_text_never_passed_to_text(self) -> None:
        """text() 호출 기록(typography.GLYPH_LOG)에 라벨 문구가 없다 — 글꼴과 무관한 판정."""
        from engine import typography  # noqa: PLC0415

        for lab in (v for v in load_rules().script_schema.labels.values() if v):
            typography.GLYPH_LOG = []
            try:
                _frame(lab)
                drawn = [s for _, _, s in typography.GLYPH_LOG]
            finally:
                typography.GLYPH_LOG = None
            self.assertTrue(drawn)
            self.assertFalse([s for s in drawn if lab in s or s in lab], lab)


class AutoPreviewBodyCutsTest(unittest.TestCase):
    def test_short_video_gets_min_body_cuts(self) -> None:
        from engine.render import auto_preview_times  # noqa: PLC0415

        sents = {"o_0": NS(t0=1.2, t1=4.7), "o_1": NS(t0=5.2, t1=9.4)}
        tb = NS(scenes=["o"], SC=lambda s: 0.0, SC_END=lambda s: 22.6, sent=sents,
                in_fullcard=lambda t: t >= 11.0)
        P = NS(R=NS(tb=tb), plan=NS(cards=[NS(t0=11.1, t1=22.1)]))  # noqa: N806
        ts = auto_preview_times(P)
        body = [t for t in ts if t < 11.0 and any(s.t0 <= t <= s.t1 for s in sents.values())]
        self.assertGreaterEqual(len(body), load_rules().preview.min_body_cuts)


if __name__ == "__main__":
    unittest.main()

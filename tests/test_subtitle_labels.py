"""NB12(v3.3.0, C9) — 검증 라벨 자막 접두 · F6 auto 프리뷰 본편 컷 최소 수."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import cairo
import numpy as np

from engine.checks import missing_fonts
from engine.style import C, H_OUT, SUBTITLE, W_OUT
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


def _amber_px(img: np.ndarray) -> int:
    col = np.array(C[SUBTITLE.label_style.color]) * 255
    band = img[int(SUBTITLE.last_line_y) - 20: int(SUBTITLE.last_line_y) + 4]
    return int((np.abs(band.astype(float) - col).sum(-1) < 60).sum())


_MISSING_FONTS = missing_fonts()


class SubtitleLabelTest(unittest.TestCase):
    # 렌더 경로(engine.typography)는 글꼴이 없으면 fontconfig 대체 글꼴로 그린다 — 라벨 픽셀 수가 달라진다(D-0057 §2 NB14).
    # 렌더 경로 글꼴 검사(P6)는 Phase 10 후보. 지금은 글리프 검사(test_checks)와 같은 사유 있는 skip.
    @unittest.skipIf(bool(_MISSING_FONTS), f"프로젝트 글꼴 없음 {_MISSING_FONTS} — `python tools/fetch_data.py fonts` 필요(D-0057 NB14)")
    def test_label_drawn_in_rule_color(self) -> None:
        lab = load_rules().script_schema.labels["unverified"]
        self.assertGreater(_amber_px(_frame(lab)), 20)
        self.assertEqual(_amber_px(_frame(None)), 0)

    def test_no_label_frame_unchanged_by_feature(self) -> None:
        """라벨 없는 문장은 기능 전과 같다(hormuz 25컷 MAD 0 의 단위 근거) — 두 번 그려도 같은 픽셀."""
        self.assertTrue(np.array_equal(_frame(None), _frame(None)))


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

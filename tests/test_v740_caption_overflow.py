"""v7.4.0 back_and_forth D-0333 — 사진·영상 캡션 바 글자는 바 폭(− 좌우 pad_x) 안. 캡션 줄 = 줄임표, 출처 줄 = 두 줄 접기(권리 표기 보존, C9).
접힌 줄마다 바(와 media_box) 높이 + source_line_px. 그래도 넘치면 [caption-overflow] hard. 발견: showcase_geo 구석 영상(300px) 출처 줄
'… · U.S. Central Command · Public domain' 의 'domain' 이 바 밖 지도 위에 떠 있었다(옛 caption_width 넘침 허용 설계)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine import checks
from engine.layers.media import BAR, MC, caption_bar_h, caption_layout
from engine.media_plan import media_box

CR_GEO = "자료 영상 · 2026. 07. 07 촬영 · U.S. Central Command · Public domain"
CR_ECON = "자료사진 · 2012. 09 · 미 연준 이사회 · United States Government Work"


class LayoutTest(unittest.TestCase):
    def test_fits_unchanged(self) -> None:
        self.assertEqual(caption_layout("짧은 캡션", "자료사진 · 2020", 376), ("짧은 캡션", ["자료사진 · 2020"], True))
        self.assertEqual(caption_bar_h("짧은 캡션", "자료사진 · 2020", 376), BAR)   # 넘치지 않으면 옛 그림 그대로(골든 불변)

    def test_source_wraps_keeps_license(self) -> None:
        for cr, w in ((CR_GEO, 300), (CR_ECON, 236)):
            c, src, ok = caption_layout("캡션", cr, w)
            self.assertTrue(ok)
            self.assertEqual(len(src), 2)
            self.assertEqual(" · ".join(src), cr)   # 마디 경계에서 접는다 — 글자를 버리지 않는다
            self.assertEqual(caption_bar_h("캡션", cr, w), BAR + MC.overflow.source_line_px)

    def test_caption_ellipsis(self) -> None:
        c, _, ok = caption_layout("아주 긴 캡션 " * 12, "자료사진", 236)
        self.assertTrue(ok)
        self.assertTrue(c.endswith("…"))

    def test_too_long_is_not_ok(self) -> None:
        self.assertFalse(caption_layout("캡션", " · ".join([CR_ECON] * 3), 236)[2])

    def test_media_box_follows_bar(self) -> None:
        a = {"m": NS(caption="캡션", credit="x", file="f", tool=NS(params={"scale": [16, 9]}))}
        e = {"mid": "m", "x": 0, "y": 0, "w": 236}
        import engine.media_registry as mr  # noqa: PLC0415

        orig = mr.credit_line
        try:
            mr.credit_line = lambda m: CR_ECON
            self.assertAlmostEqual(media_box(e, a)[3], 236 * 9 / 16 + BAR + MC.overflow.source_line_px)
        finally:
            mr.credit_line = orig


class CheckTest(unittest.TestCase):
    def test_hard_registered_and_flags(self) -> None:
        self.assertIn("caption_overflow", checks.HARD)
        import engine.media_registry as mr  # noqa: PLC0415

        orig = mr.credit_line
        try:
            mr.credit_line = lambda m: m.credit
            assets = {"ok": NS(caption="캡션", credit=CR_GEO), "bad": NS(caption="캡션", credit=" · ".join([CR_ECON] * 3))}
            P = NS(events=[{"type": "clip", "mid": "ok", "w": 300, "t0": 1.0}, {"type": "photo", "mid": "bad", "w": 236, "t0": 2.0}],  # noqa: N806
                   R=NS(assets=NS(media_assets=assets)))
            out = checks.check_caption_overflow(P)
        finally:
            mr.credit_line = orig
        self.assertEqual(len(out), 1)
        self.assertIn("[caption-overflow] photo bad", out[0])

    def test_rule_keys(self) -> None:
        ov = MC.overflow
        self.assertEqual((ov.caption, ov.source, ov.source_max_lines, ov.source_line_px), ("ellipsis", "wrap", 2, 12))


if __name__ == "__main__":
    unittest.main()

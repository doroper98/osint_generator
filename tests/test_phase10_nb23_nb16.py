"""Phase 10 §0 차단 항목 (v3.6.0, back_and_forth D-0066 §0 · D-0065 §2).

NB23: 카드 자신이 모서리 날짜·하단 자막 영역과 겹치면 `checks overlap`(hard)이 잡는다 — Phase 9 랫클리프 p_0191.86 카드
      `y: 0.56`(비율로 쓴 값)이 픽셀로 읽혀 날짜 자리에 떴는데 검사기는 사진·영상만 봐서 hard 0 이었다(P6 검사기 구멍).
NB16: 렌더 경로의 글꼴 선택(`typography.font`)도 대체 글꼴을 오류로 — 글리프 검사(checks._cmap)와 같은 판정 함수.
"""

from __future__ import annotations

import unittest
from unittest import mock

import cairo

from engine import checks, typography
from engine.hud import date_box
from engine.media_plan import card_zone_warnings, placement_warnings
from engine.style import CARD, DATE_BADGE, FONT, W_OUT
from rules import load_rules

SUB_Y = load_rules().layout_480p.reserved_zones.subtitle.y_from
_MISSING = checks.missing_fonts()


def _ctx() -> cairo.Context:
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def _card(**k: object) -> dict:
    return {"type": "card", "t0": 10.0, "t1": 14.0, "tag": "여러 매체가 확인", "lines": ["미 공군 수송기, 리가 경유 · 브누코보 착륙"],
            "accent": "gold", **k}


@unittest.skipIf(_MISSING, f"글꼴 없음 {_MISSING} — 카드 폭은 글자 폭으로 계산(`python tools/fetch_data.py fonts`)")
class CardZoneTest(unittest.TestCase):
    def test_ratio_y_hits_date(self) -> None:
        """Phase 9 재현: y 0.56 은 480p 픽셀 0.56 → 카드가 날짜 상자와 겹친다 → [card-over-date]."""
        w = card_zone_warnings(_ctx(), [_card(y=0.56)])
        self.assertEqual(len(w), 1)
        self.assertIn("[card-over-date]", w[0])
        self.assertIn("480p 픽셀", w[0])

    def test_default_y_clear(self) -> None:
        self.assertEqual(card_zone_warnings(_ctx(), [_card()]), [])
        self.assertGreater(CARD.y, date_box()[3])   # 기본 카드 자리는 날짜 아래(규칙 값끼리의 관계)

    def test_low_card_hits_subtitle(self) -> None:
        w = card_zone_warnings(_ctx(), [_card(y=SUB_Y - 20)])
        self.assertTrue(any("[card-over-subtitle]" in x for x in w), w)

    def test_post_box_checked(self) -> None:
        post = {"type": "post", "t0": 1.0, "t1": 2.0, "src": "src_x_0001", "post_box": (W_OUT - 200, 10, 180, 120)}
        self.assertTrue(any("[card-over-date]" in x for x in card_zone_warnings(_ctx(), [post])))

    def test_in_placement_warnings(self) -> None:
        """checks overlap(hard)의 입력 함수가 카드 판정을 포함한다 — 사진·영상이 없어도."""
        self.assertTrue(any("[card-over-date]" in x for x in placement_warnings([_card(y=0.56)], {})))
        self.assertIn("overlap", checks.HARD)


class DateBoxTest(unittest.TestCase):
    def test_one_definition(self) -> None:
        """날짜 상자 정의는 engine.hud.date_box 하나 — 배치 슬롯 후보·checks 가 같은 상자를 본다."""
        b = date_box()
        self.assertEqual(b, (W_OUT - DATE_BADGE.x_right - DATE_BADGE.size * 8, 0, W_OUT, DATE_BADGE.underline_y + 2))
        import inspect  # noqa: PLC0415

        from engine import media_plan, placement  # noqa: PLC0415

        for mod in (media_plan, placement):
            self.assertNotIn("DATE_BADGE", inspect.getsource(mod), mod.__name__)


class RenderFontTest(unittest.TestCase):
    def test_require_family_loud(self) -> None:
        with self.assertRaises(typography.FontMissingError):
            typography.require_family("NoSuchFamily Zz9")

    def test_font_entry_checks(self) -> None:
        """렌더 경로 `font()` 가 대체 글꼴로 조용히 그리지 않는다(15 P6, NB16)."""
        with mock.patch.dict(FONT, {"sansm": ("NoSuchFamily Zz9", 0)}):
            with self.assertRaises(typography.FontMissingError):
                typography.font(_ctx(), "sansm", 12)
            with self.assertRaises(typography.FontMissingError):
                typography.text(_ctx(), "가나다", 0, 0, 12, "sansm")

    def test_same_error_class(self) -> None:
        self.assertIs(checks.FontMissingError, typography.FontMissingError)

    @unittest.skipIf(_MISSING, f"글꼴 없음 {_MISSING} — 설치 환경에서만 통과 확인(`python tools/fetch_data.py fonts`)")
    def test_project_fonts_pass(self) -> None:
        for fam, _ in FONT.values():
            typography.require_family(fam)


if __name__ == "__main__":
    unittest.main()

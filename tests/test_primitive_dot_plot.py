"""프리미티브 dot_plot·statement_diff 단어 비교 개선 (v4.4.0, back_and_forth D-0090 작업 3·8, docs/handoff/20 §4.2·§5.2·§10).

dot_plot: 레코드에서만(연출 값 없음), 고정 문구 "참가자별 전망이며 약속이 아님", 중앙값 = 코드 계산, 출처·기준 시점 줄,
판독 최소 크기, 정직성 메타(AXIS value), 데이터 오류 = 렌더 전 오류(P6).
"""

from __future__ import annotations

import copy
import unittest

import cairo

from engine import typography
from engine.honesty import PRIMITIVE_AXIS, ChartMeta, judge
from engine.primitives import module, primitive_box, style_for
from engine.primitives.dot_plot import chart_meta, columns, value_range
from engine.primitives.statement_diff import diff_tokens
from engine.registry import RegistryError, validate_events
from engine.style import PRIMITIVES
from genres.load import load_genre
from rules import load_rules

FX = module("dot_plot").PREVIEW_FIXTURE
L = PRIMITIVES["dot_plot"]


def ev(**over: object) -> dict:
    d = copy.deepcopy(FX)
    d.update(over)
    return d


def render(e: dict, t: float) -> list[tuple[str, float]]:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    ctx = cairo.Context(surf)
    typography.GLYPH_LOG = []
    try:
        module("dot_plot").draw(ctx, None, t, validate_events([e])[0], style_for("dot_plot", load_genre("macro_monetary").color_semantics))
    finally:
        drawn, typography.GLYPH_LOG = typography.GLYPH_LOG, None
    return [(s, size) for size, _, s in drawn]


class DotPlotDataTest(unittest.TestCase):
    def test_fixture_and_registered(self) -> None:
        self.assertIn("dot_plot", load_rules().registries.primitives)
        self.assertNotIn("dot_plot", load_rules().registries.primitives_planned)
        self.assertEqual(validate_events([FX])[0]["id"], "dot_plot")

    def test_invalid_is_error(self) -> None:
        bad = {"not scatter": ev(record="FEDFUNDS"), "no record": ev(record="NOPE"), "bad column": ev(columns=["2031"]),
               "empty tag": ev(tag=" "), "values from direction": ev(values=[4.0]), "note override": ev(note="약속")}
        for why, e in bad.items():
            with self.subTest(why=why), self.assertRaises(RegistryError):
                validate_events([e])

    def test_columns_and_range(self) -> None:
        e = validate_events([ev(columns=["2026", "Longer run"])])[0]
        cs = columns(e)
        self.assertEqual([c.label for c in cs], ["2026", "Longer run"])
        lo, hi = value_range(cs)
        self.assertLess(lo, min(min(c.values) for c in cs))
        self.assertGreater(hi, max(max(c.values) for c in cs))


class DotPlotDrawTest(unittest.TestCase):
    def test_fixed_note_source_and_labels(self) -> None:
        texts = [s for s, _ in render(FX, FX["t1"] - 0.5)]
        self.assertIn(L.note, texts)
        self.assertTrue(any(s.startswith("연준 FOMC") and s.endswith("2026년 9월 기준") for s in texts))
        self.assertIn("장기", texts)
        self.assertTrue(any(s.endswith("%") for s in texts))   # 단위 표시

    def test_glyph_size(self) -> None:
        sizes = [size for _, size in render(FX, 7.0)]
        self.assertGreaterEqual(min(sizes), load_rules().layout_480p.min_font_px)

    def test_box_is_reserved(self) -> None:
        e = validate_events([FX])[0]
        x0, y0, x1, y1 = primitive_box(e)
        self.assertAlmostEqual(x1 - x0, L.w)
        self.assertLessEqual(x1, 854)
        self.assertLessEqual(y1, 480)

    def test_honesty_meta(self) -> None:
        self.assertEqual(PRIMITIVE_AXIS["dot_plot"], "value")
        self.assertEqual(PRIMITIVE_AXIS["statement_diff"], "none")
        m = ChartMeta(ref="primitive dot_plot", axis="value", kind="dot_plot", **chart_meta(validate_events([FX])[0]))
        hard, _ = judge([m])
        self.assertEqual(sum(len(v) for v in hard.values()), 0)
        hard, _ = judge([m.model_copy(update={"units": [], "unit_label": None})])
        self.assertTrue(hard["units_visible"])   # 단위를 빼면 hard


class StatementDiffWordsTest(unittest.TestCase):
    def test_punctuation_does_not_split_same_word(self) -> None:
        left, right = diff_tokens("Inflation remains elevated relative to the goal.", "Inflation remains elevated. Today the goal.")
        self.assertEqual(left[:3], [("Inflation", "same"), ("remains", "same"), ("elevated", "same")])
        self.assertEqual(right[2], ("elevated.", "same"))   # 표시는 원문(마침표 유지)
        self.assertIn(("relative", "removed"), left)
        self.assertEqual(right[-2:], [("the", "same"), ("goal.", "same")])

    def test_common_prefix_suffix(self) -> None:
        left, right = diff_tokens("a b c x d e", "a b c y z d e")
        self.assertEqual([o for _, o in left], ["same", "same", "same", "removed", "same", "same"])
        self.assertEqual([o for _, o in right], ["same", "same", "same", "added", "added", "same", "same"])

    def test_real_fomc_sentences(self) -> None:
        jul = "Inflation remains elevated relative to the Committee's 2 percent goal, in part reflecting supply shocks"
        sep = "Inflation remains elevated. Today's policy action will support a timelier return to the Committee's 2 percent goal."
        left, right = diff_tokens(jul, sep)
        self.assertEqual(" ".join(w for w, o in right if o == "added"), "Today's policy action will support a timelier return")
        self.assertIn(("goal,", "same"), left)


if __name__ == "__main__":
    unittest.main()

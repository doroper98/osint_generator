"""G13(v5.2.0, back_and_forth D-0129, 사용자 판정 D113) — 배경 사진 가독·주 아일랜드 상시·카드 ↔ 아일랜드 교차.

- §A: stage_backdrop 블러·덮개·채도 값(6·0.38·0.15). 기사 프레스 폴백은 분리(18·0.55 — hormuz 기사 골든 불변).
- §B: `[backdrop-main-missing]` hard — 주 아일랜드 없는 구간 > card_only_max_sec(경계·타이틀/엔딩·기사 제외·무대).
- §B: 연출·수정 프롬프트에 주 아일랜드 상시·보도 인용 = article 문법(규칙 값으로 채움).
- §C: `[card-island]` warning — 카드 제자리 상자 ∩ 같은 순간 아일랜드 상자 > 0.
"""

from __future__ import annotations

import ast
import unittest
from unittest import mock

from engine import checks
from engine.island import card_overlap, card_overlap_details, is_main, main_missing, main_missing_details
from engine.style import ARTICLE, BACKDROP, ISLAND
from rules import load_rules
from tests.anti_inertia._ast_util import REPO
from workers.prompt_loader import load_prompt

MAXS = ISLAND.card_only_max_sec


def _ev(typ: str, t0: float, t1: float, **kw) -> dict:  # noqa: ANN003
    return {"type": typ, "t0": t0, "t1": t1, **kw}


class RulesValueTest(unittest.TestCase):
    def test_backdrop_values_d0129(self) -> None:
        self.assertEqual((BACKDROP.blur_px, BACKDROP.dim, BACKDROP.desaturate), (6, 0.38, 0.15))
        self.assertEqual(ISLAND.fill_alpha, 0.78)   # 아일랜드 가독은 그대로
        self.assertTrue(ISLAND.main_required)
        self.assertEqual(ISLAND.main_kinds, ["chart", "primitive", "photo", "clip", "article", "panel"])   # panel = D-0130 Q3 B
        self.assertEqual(MAXS, 3.0)

    def test_article_fallback_separate_from_backdrop(self) -> None:
        """기사 프레스 폴백 블러는 배경 사진 값과 분리 — hormuz(mercator) 기사 컷은 G12 값 그대로."""
        self.assertEqual((ARTICLE.press_fallback.blur_px, ARTICLE.press_fallback.dim), (18, 0.55))
        src = (REPO / "engine" / "layers" / "article.py").read_text(encoding="utf-8")
        names = {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)}
        self.assertNotIn("BACKDROP", names)


class MainMissingTest(unittest.TestCase):
    def test_boundary_equal_passes_over_fails(self) -> None:
        chart = [_ev("island", 0, 10, kind="chart"), _ev("island", 10 + MAXS, 30, kind="chart")]
        self.assertEqual(main_missing(chart, 30, [], "backdrop"), [])
        late = [_ev("island", 0, 10, kind="chart"), _ev("island", 10 + MAXS + 0.01, 30, kind="chart")]
        gaps = main_missing(late, 30, [], "backdrop")
        self.assertEqual(len(gaps), 1)
        self.assertEqual((gaps[0]["t0"], gaps[0]["t1"]), (10, 13.01))

    def test_card_only_segment_is_missing(self) -> None:
        """카드만 있는 구간(사용자 판정 D113) — 카드는 주 아일랜드가 아니다. 앞·끝 구간도 잡는다."""
        ev = [_ev("card", 0, 20, tag="a"), _ev("island", 5, 12, kind="chart")]
        gaps = main_missing(ev, 20, [], "backdrop")
        self.assertEqual([(g["t0"], g["t1"]) for g in gaps], [(0, 5), (12, 20)])
        d = main_missing_details(gaps)
        self.assertTrue(d[0].startswith("[backdrop-main-missing] 0.00-5.00 5s"))

    def test_fullcards_and_article_excluded(self) -> None:
        ev = [_ev("island", 6, 42, kind="chart"), _ev("article", 44, 50, mid="x"), _ev("photo", 52, 60, mid="p")]
        cards = [(0, 5.5), (60, 70)]   # 타이틀·엔딩(± 0.3 은 호출부)
        self.assertEqual(main_missing(ev, 70, cards, "backdrop"), [])
        self.assertTrue(all(is_main(e) for e in ev))
        self.assertFalse(is_main(_ev("island", 0, 1, kind="other")))
        self.assertFalse(is_main(_ev("card", 0, 1, tag="x")))

    def test_panel_only_segment_passes(self) -> None:
        """D-0130 Q3 B — backdrop 패널(panel_box)만 있는 구간은 "카드만 있는 구간"이 아니다."""
        self.assertTrue(is_main(_ev("panel", 0, 1, kind="table")))
        ev = [_ev("island", 0, 10, kind="chart"), _ev("panel", 10, 25, kind="table"), _ev("card", 10, 25, tag="t"),
              _ev("island", 25, 30, kind="chart")]
        self.assertEqual(main_missing(ev, 30, [], "backdrop"), [])

    def test_other_stage_or_rule_off(self) -> None:
        ev = [_ev("card", 0, 20, tag="a")]
        self.assertEqual(main_missing(ev, 20, [], "mercator"), [])
        self.assertEqual(main_missing(ev, 20, [], "timeline"), [])
        with mock.patch.object(ISLAND, "main_required", False):
            self.assertEqual(main_missing(ev, 20, [], "backdrop"), [])

    def test_check_registered_hard_and_reads_cache(self) -> None:
        self.assertIn("backdrop_main_missing", checks.HARD)
        self.assertIn("card_island", checks.WARN)
        from types import SimpleNamespace as NS

        P = NS(R=NS(cache={"island_check": {"main_missing": [{"t0": 1.0, "t1": 9.0, "sec": 8.0}],  # noqa: N806
                                             "card_overlap": [{"card": "card:x", "island": "island chart left", "t0": 2.0,
                                                               "t1": 3.0, "px2": 120}]}}))
        self.assertEqual(len(checks.check_main_missing(P)), 1)
        self.assertEqual(checks.check_card_island(P), ["[card-island] card:x ↔ island chart left t=2.00~3.00 교차 120px²"])
        self.assertEqual(checks.check_main_missing(NS(R=NS(cache={}))), [])   # backdrop 무대 밖 = 0


class CardIslandTest(unittest.TestCase):
    def test_overlap_same_time_only(self) -> None:
        boxes = [("island chart left", 0.0, 10.0, (24.0, 56.0, 540.0, 298.0))]
        cards = [_ev("card", 2, 5, tag="in"), _ev("card", 12, 15, tag="later"), _ev("card", 2, 5, tag="clear")]
        geo = {"in": (500.0, 60.0, 700.0, 160.0), "later": (500.0, 60.0, 700.0, 160.0), "clear": (600.0, 60.0, 800.0, 160.0)}
        with mock.patch("engine.reserved.card_box", side_effect=lambda ctx, e: geo[e["tag"]]):
            rows = card_overlap(cards, boxes)
        self.assertEqual([r["card"] for r in rows], ["card:in"])
        self.assertEqual(rows[0]["px2"], 64 * 100)
        self.assertEqual((rows[0]["t0"], rows[0]["t1"]), (2, 5))
        self.assertTrue(card_overlap_details(rows)[0].startswith("[card-island] card:in ↔ island chart left"))
        self.assertEqual(card_overlap(cards, []), [])   # 아일랜드 없는 무대 = 0


class PromptTest(unittest.TestCase):
    def test_grammar_in_director_and_revise(self) -> None:
        R = load_rules()  # noqa: N806
        for name in ("director", "revise_direction"):
            t = load_prompt(name, R)
            self.assertIn("주 아일랜드 상시", t, name)
            self.assertIn(f"{MAXS:g}초 이하", t, name)
            self.assertIn("·".join(ISLAND.main_kinds), t, name)
            self.assertIn("article 이벤트로", t, name)
            self.assertIn("오프닝 첫 문장부터", t, name)
            self.assertNotIn("{card_only_max}", t, name)
            self.assertNotIn("{main_kinds}", t, name)
        self.assertTrue(any("기사(article) 이벤트로" in g for g in R.direction_grammar))

    def test_field_table_shows_schema_constraints(self) -> None:
        """LLM-AP-011 — 필드 표가 statement_diff 의 날짜 형식·인용 상한(규칙 값)을 보인다."""
        from engine.style import QUOTE_MAX_CHARS  # noqa: PLC0415
        from workers.direction_io import event_fields_table  # noqa: PLC0415

        row = next(ln for ln in event_fields_table().splitlines() if ln.startswith("- primitive:statement_diff:"))
        self.assertIn("date*: str (YYYY | YYYY.MM | YYYY.MM.DD", row)
        self.assertIn(f"before*: str (원문 ≤ {QUOTE_MAX_CHARS}자", row)


class RedirectTest(unittest.TestCase):
    def test_redirect_moves_not_deletes(self) -> None:
        """D-0131 — --redirect 없으면 기존 direction.yaml 유지, 있으면 prev/direction_{시각}.yaml 로 이동(내용 그대로)."""
        import tempfile  # noqa: PLC0415
        from datetime import datetime  # noqa: PLC0415
        from pathlib import Path  # noqa: PLC0415

        from tools.ai_direction_run import redirect  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            self.assertIsNone(redirect(pdir))   # 없으면 아무 일 없음
            (pdir / "direction.yaml").write_text("version: 1\n", encoding="utf-8")
            moved = redirect(pdir, datetime(2026, 9, 30, 18, 40, 5))
            self.assertEqual(moved, pdir / "prev" / "direction_260930_184005.yaml")
            self.assertFalse((pdir / "direction.yaml").exists())
            self.assertEqual(moved.read_text(encoding="utf-8"), "version: 1\n")


if __name__ == "__main__":
    unittest.main()

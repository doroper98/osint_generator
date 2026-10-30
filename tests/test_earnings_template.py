"""v7.4.0 T4 — 실적 발표 장르(D-0278 §4.3) · 템플릿 표시 줄(UF-147, D-0302 ⑤) · 투자 고지 · 기업 엔티티 · 장르 막 구성.

렌더 경로(타이틀 부제·엔딩 카드에 실제로 그려졌나)는 engine.checks check_template_label·check_invest_notice 가 프레임을 그려 본다.
여기서는 그 검사가 읽는 함수(fullcards.title_subtitle·last_notice)·검사 등록·장르·스키마·프롬프트를 본다.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml
from pydantic import ValidationError

from engine.checks import HARD
from genres.load import load_genre
from rules import load_rules
from schemas.entity_models import Entity
from workers.prompt_loader import load_prompt

R_ = load_rules()


def _ctx(subtitle: str, label: str | None, invest: bool, labels: dict | None = None) -> SimpleNamespace:
    plan = SimpleNamespace(subtitle=subtitle)
    tb = SimpleNamespace(plan=plan, order=list((labels or {}).keys()))
    return SimpleNamespace(tb=tb, cache={"template_label": label, "invest_notice": invest, "sentence_labels": labels or {}})


class GenreEarningsTest(unittest.TestCase):
    def test_profile(self) -> None:
        g = load_genre("earnings")
        self.assertEqual((g.template_label, g.invest_notice, g.status), ("실적 발표 템플릿", True, "proposed"))
        n = g.narration
        self.assertTrue(n.company_metric_attribution and n.consensus_attribution and n.price_window_attribution)
        self.assertEqual(g.stage.primary, "backdrop")
        self.assertIn("mercator", g.stage.secondary)

    def test_other_genres_unchanged(self) -> None:
        for name in ("geopolitics", "macro_monetary"):
            g = load_genre(name)
            self.assertIsNone(g.template_label)
            self.assertFalse(g.invest_notice)

    def test_checks_registered_hard(self) -> None:
        self.assertIn("template_label", HARD)
        self.assertIn("invest_notice", HARD)


class CardTextTest(unittest.TestCase):
    def test_title_subtitle(self) -> None:
        from engine.fullcards import title_subtitle  # noqa: PLC0415

        self.assertEqual(title_subtitle(_ctx("삼성전자 2026년 3분기", "실적 발표 템플릿", True)), "실적 발표 템플릿 · 삼성전자 2026년 3분기")
        self.assertEqual(title_subtitle(_ctx("호르무즈", None, False)), "호르무즈")   # 라벨 없는 장르 = 종전 그대로

    def test_last_notice(self) -> None:
        from engine.fullcards import last_notice  # noqa: PLC0415

        inv = R_.layout_480p.end_card.notice_invest.text
        self.assertEqual(last_notice(_ctx("", None, True)), inv)
        self.assertIsNone(last_notice(_ctx("", None, False)))
        both = last_notice(_ctx("", None, True, {"s1": ["unverified"]}))
        self.assertTrue(both.startswith(inv + " · ") and "1건" in both, both)

    def test_invest_text_not_banned(self) -> None:
        import re  # noqa: PLC0415

        inv = R_.layout_480p.end_card.notice_invest.text
        for p in R_.banned_phrases.patterns:
            self.assertIsNone(re.search(p, inv), p)


class CompanyEntityTest(unittest.TestCase):
    BASE = {"id": "acme", "kind": "company", "names": ["시험 기업"], "flag": "us", "ticker": "TEST", "exchange": "NASDAQ",
            "rights": "flags.flag_icons"}

    def test_valid(self) -> None:
        self.assertEqual(Entity.model_validate(self.BASE).ticker, "TEST")

    def test_requires_flag_ticker_exchange(self) -> None:
        for k in ("flag", "ticker", "exchange"):
            with self.subTest(k=k), self.assertRaisesRegex(ValidationError, "기업 엔티티"):
                Entity.model_validate({**self.BASE, k: None})

    def test_ticker_only_company(self) -> None:
        with self.assertRaisesRegex(ValidationError, "기업"):
            Entity.model_validate({"id": "x", "kind": "country", "names": ["x"], "flag": "us", "ticker": "X", "rights": "flags.flag_icons"})

    def test_registry_has_both(self) -> None:
        from engine.entities import load_entities  # noqa: PLC0415

        r = load_entities()
        self.assertEqual((r.lookup("삼성전자").ticker, r.lookup("인텔").ticker), ("005930.KS", "INTC"))


class PromptActsTest(unittest.TestCase):
    def test_earnings_acts_and_switches(self) -> None:
        t = load_prompt("script", R_, load_genre("earnings"))
        self.assertIn(R_.genre_prompt.acts_head, t)
        for line in R_.genre_prompt.acts["earnings"]:
            self.assertIn(line, t)
        for k in ("company_metric_attribution", "consensus_attribution", "price_window_attribution"):
            self.assertIn(R_.genre_prompt.narration[k], t)
        self.assertIn(R_.genre_prompt.acts_head, load_prompt("director", R_, load_genre("earnings")))

    def test_macro_has_no_acts(self) -> None:
        self.assertNotIn(R_.genre_prompt.acts_head, load_prompt("script", R_, load_genre("macro_monetary")))


class IntakeGuidanceTest(unittest.TestCase):
    def test_genre_guidance_appended(self) -> None:
        import argparse  # noqa: PLC0415
        import json  # noqa: PLC0415

        from workers.intake_planner_worker import CATEGORY_GUIDANCE, IntakePlannerWorker  # noqa: PLC0415

        self.assertIn("earnings", CATEGORY_GUIDANCE)
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td) / "p1"
            pdir.mkdir()
            (pdir / "project_manifest.json").write_text(json.dumps({
                "schema_version": 2, "project_id": "p1", "title": "시험", "category": "economy", "target_duration_min": 3,
                "created_at": "2026-10-30T00:00:00Z"}), encoding="utf-8")
            w = IntakePlannerWorker()
            w.project_dir = lambda args: pdir  # type: ignore[method-assign]
            base = w.build_user_prompt(argparse.Namespace(), None)  # type: ignore[arg-type]
            self.assertNotIn(CATEGORY_GUIDANCE["earnings"], base)
            (pdir / "order.yaml").write_text(yaml.safe_dump({
                "topic": "시험", "genre": "earnings", "instructions": ["시험"], "data": {"series": []},
                "media": {"wanted": ["기사 카드"], "rights": "시험"}}, allow_unicode=True), encoding="utf-8")
            self.assertIn(CATEGORY_GUIDANCE["earnings"], w.build_user_prompt(argparse.Namespace(), None))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

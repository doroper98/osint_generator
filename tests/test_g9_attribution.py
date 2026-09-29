"""v4.10.0 G9 — 귀속 표현 "보도했" (back_and_forth D-0116 작업 3, G4 보류 D84).

규칙 `script_schema.attribution_markers` 한 곳 → 원고 린트·검증 판정(`orchestrator.source_verify.judge`)·프롬프트(`{{RULES.attribution_markers}}`).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from orchestrator import source_intake as si
from orchestrator import source_verify as sv
from rules import load_rules
from script.lint import lint, load_claims_for
from script.schema import Script
from tests.test_source_intake import _Proj
from tests.test_source_verify import _draft, _ev
from workers.prompt_loader import load_prompt

REPO = Path(__file__).resolve().parent.parent


def _script(text: str, sources: list[str]) -> Script:
    return Script.model_validate({"schema_version": 1, "title": "t", "subtitle": "s", "date": "2026.09.30",
                                  "scenes": [{"id": "s", "sentences": [{"date": "2026.09.30", "text": text, "sources": sources}]}]})


def _attrib(script: Script, claims: dict[str, str]) -> list[str]:
    return [i.sid for i in lint(script, claims).issues if i.kind == "attribution"]


class RuleAndPromptTest(_Proj):
    def test_rule_has_marker(self) -> None:
        self.assertIn("보도했", load_rules().script_schema.attribution_markers)

    def test_prompts_carry_rule_list(self) -> None:
        R = load_rules()  # noqa: N806
        for name in ("script", "verify_sources"):
            text = load_prompt(name, R)
            self.assertNotIn("{{RULES.attribution_markers}}", text, name)
            for m in R.script_schema.attribution_markers:
                self.assertIn(f'"{m}"', text, (name, m))

    def test_lint_accepts_reported(self) -> None:
        claims = {"clm_0001": "unverified"}
        self.assertEqual(_attrib(_script("ABC뉴스는 워시가 5월 연준 의장에 취임했다고 보도했습니다.", ["clm_0001"]), claims), [])
        self.assertEqual(_attrib(_script("워시가 5월 연준 의장에 취임했습니다.", ["clm_0001"]), claims), ["s_0"])


class JudgeReportedTest(_Proj):
    """"매체 X 가 보도했다" 인용 = 주장이 있었다는 근거(D-0054 B) — 두 매체여도 사실 corroborated 가 아니다."""

    def test_reported_quotes_are_attributed(self) -> None:
        a1 = si.add_article(self.pdir, publisher="가나일보", headline="h", published_at=date(2026, 9, 21),
                            body="외신은 유조선 두 척이 격침됐다고 보도했다. 확인되지 않았다.").id
        a2 = si.add_article(self.pdir, publisher="다라통신", headline="h", published_at=date(2026, 9, 21),
                            body="현지 방송은 유조선 두 척이 격침됐다고 보도했다.").id
        s = si.load_sources(self.pdir)
        c, _ = sv.judge(_draft({"text": "유조선 두 척 격침", "evidence": [_ev(a1, "유조선 두 척이 격침됐다고 보도했다"),
                                                                     _ev(a2, "유조선 두 척이 격침됐다고 보도했다")]}),
                        s, {r.id: si.body_text(self.pdir, r) for r in s.sources})
        cl = c.claims[0]
        self.assertTrue(cl.attributed_only)
        self.assertTrue(cl.contested)
        self.assertEqual(cl.status, "unverified")
        self.assertEqual(sorted(k for k in cl.checks if k.startswith("attributed:")), sorted([f"attributed:{a1}", f"attributed:{a2}"]))


class ProjectImpactTest(_Proj):
    def test_fed_policy_attribution_warnings_cleared(self) -> None:
        """R-0110 의 원고 린트 경고 8("…라고 보도했습니다")이 0 이 된다."""
        pd = REPO / "projects" / "fed_policy_2026"
        sc = Script.model_validate(yaml.safe_load((pd / "script.yaml").read_text(encoding="utf-8")))
        self.assertEqual([i.sid for i in lint(sc, load_claims_for(pd)).issues if i.kind == "attribution"], [])

    def test_judged_claims_cannot_change(self) -> None:
        """추적된 verify draft 가 없어 판정을 재실행할 수 없다. 대신 인용 = 본문의 부분 문자열이므로 supports 근거 소스 본문에
        "보도했" 이 없으면 새 표지가 판정을 바꿀 수 없다 — 이것을 확인한다(fed_policy·랫클리프, 본문 없으면 건너뜀)."""
        checked = 0
        for proj in ("fed_policy_2026", "ratcliffe2026"):
            pd = REPO / "projects" / proj
            recs = si.load_sources(pd).by_id()
            for c in sv.load_claims(pd).claims:
                for k in c.checks:
                    if not k.startswith("quote_match:"):
                        continue
                    sid = k.split(":", 1)[1]
                    try:
                        body = si.body_text(pd, recs[sid])
                    except (OSError, ValueError):
                        continue
                    if body:
                        checked += 1
                        self.assertNotIn("보도했", body, (proj, c.claim_id, sid))
        if checked == 0:
            self.skipTest("소스 본문 없음 — artifacts phaseG4 복원 필요")

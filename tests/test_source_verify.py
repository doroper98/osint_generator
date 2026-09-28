"""orchestrator/source_verify — 인용 대조 판정(v3.2.0, 18 §3, back_and_forth D-0051 작업 6, D-0052 D50)."""

from __future__ import annotations

import json
import os
from datetime import date, datetime

from orchestrator import source_intake as si
from orchestrator import source_verify as sv
from rules import load_official_accounts
from schemas.source_models import VerifyDraft
from tests.test_source_intake import _Proj

OFF = load_official_accounts().accounts[0]


def _draft(*claims: dict) -> VerifyDraft:
    return VerifyDraft.model_validate({"schema_version": 1, "claims": list(claims)})


def _ev(src: str, q: str, stance: str = "supports") -> dict:
    return {"source_id": src, "quote": q, "stance": stance}


class JudgeTest(_Proj):
    def setUp(self) -> None:
        super().setUp()
        p = self.pdir
        self.x_off = si.add_x_text(p, account_name=OFF.name, handle=OFF.handle, text="Two tankers were escorted through the strait today.",
                                   lang="en", posted_at=datetime(2026, 9, 20, 14, 0)).id
        self.x_anon = si.add_x_text(p, account_name="Some Watcher", handle="@watcher_1", text="Iran says the escort violated its waters.",
                                    lang="en", posted_at=datetime(2026, 9, 20, 15, 0)).id
        self.a1 = si.add_article(p, publisher="가나일보", headline="유조선 2척 호위 통항", published_at=date(2026, 9, 21),
                                 body="20일 유조선 두 척이 해군 호위를 받으며 해협을 지났다. 이란은 영해 침범이라고 주장했다.").id
        self.a2 = si.add_article(p, publisher="다라통신", headline="호위 통항 재개", published_at=date(2026, 9, 21),
                                 body="유조선 두 척이 호위 속에 해협을 통과했다고 당국이 밝혔다.").id
        self.a3 = si.add_article(p, publisher="마바신문", headline="호위 통항", published_at=date(2026, 9, 21),
                                 body="다라통신에 따르면 유조선 두 척이 호위 속에 해협을 통과했다.", note="재인용 기사").id

    def _judge(self, d: VerifyDraft):  # noqa: ANN202
        s, b = si.load_sources(self.pdir), {r.id: si.body_text(self.pdir, r) for r in si.load_sources(self.pdir).sources}
        return sv.judge(d, s, b)

    def test_two_independent_articles_corroborated(self) -> None:
        c, drops = self._judge(_draft({"text": "유조선 두 척 호위 통항", "evidence": [
            _ev(self.a1, "유조선 두 척이 해군 호위를 받으며"), _ev(self.a2, "유조선 두 척이 호위 속에 해협을 통과했다")]}))
        self.assertEqual(drops, [])
        self.assertEqual(c.claims[0].status, "corroborated")
        self.assertEqual(c.claims[0].claim_id, "clm_0001")
        self.assertIn("independent_origins:2", c.claims[0].checks)

    def test_reprint_not_independent(self) -> None:
        c, _ = self._judge(_draft({"text": "호위 통항", "evidence": [
            _ev(self.a2, "유조선 두 척이 호위 속에 해협을 통과했다고"), _ev(self.a3, "유조선 두 척이 호위 속에 해협을 통과했다")]}))
        self.assertEqual(c.claims[0].status, "unverified")

    def test_official_needs_user_confirmation(self) -> None:
        d = _draft({"text": "호위 통항", "evidence": [_ev(self.x_off, "Two tankers were escorted")]})
        self.assertEqual(self._judge(d)[0].claims[0].status, "unverified")      # 확인 전
        si.confirm(self.pdir, self.x_off, "user")
        c, _ = self._judge(d)
        self.assertEqual(c.claims[0].status, "verified")
        self.assertIn(f"official:{self.x_off}", c.claims[0].checks)

    def test_contradiction_disputed(self) -> None:
        c, _ = self._judge(_draft({"text": "호위는 합법이었다", "evidence": [
            _ev(self.a2, "유조선 두 척이 호위 속에"), _ev(self.x_anon, "Iran says the escort violated its waters", "contradicts")]}))
        self.assertEqual(c.claims[0].status, "disputed")

    def test_quote_not_in_body_or_too_long_dropped(self) -> None:
        long_q = "유조선 " * 60
        c, drops = self._judge(_draft(
            {"text": "a", "evidence": [_ev(self.a1, "유조선 세 척이"), _ev(self.a2, "유조선 두 척이 호위 속에")]},
            {"text": "b", "evidence": [_ev(self.a1, long_q)]}))
        self.assertEqual(len(c.claims), 1)
        self.assertEqual(c.claims[0].status, "unverified")                       # 남은 근거 1개 origin
        self.assertTrue(any("본문에 없음" in d for d in drops))
        self.assertTrue(any("자 >" in d for d in drops))
        self.assertTrue(any("후보 버림" in d for d in drops))

    def test_whitespace_normalized_match(self) -> None:
        c, drops = self._judge(_draft({"text": "a", "evidence": [_ev(self.a1, "유조선   두 척이\n해군 호위를")]}))
        self.assertEqual(drops, [])

    def test_contested_without_sides_unverified(self) -> None:
        c, drops = self._judge(_draft({"text": "영해 침범", "contested": True, "evidence": [
            _ev(self.a1, "이란은 영해 침범이라고 주장했다"), _ev(self.x_anon, "Iran says the escort violated")],
            "sides": [{"party": "이란", "text": "영해 침범", "source_ids": [self.x_anon]}]}))
        self.assertEqual(c.claims[0].status, "unverified")

    def test_source_verification_rollup(self) -> None:
        c, _ = self._judge(_draft({"text": "호위", "evidence": [_ev(self.a1, "유조선 두 척이"), _ev(self.a2, "유조선 두 척이 호위")]}))
        s = sv.source_verification(si.load_sources(self.pdir), c)
        st = {r.id: r.verification.status for r in s.sources}  # type: ignore[union-attr]
        self.assertEqual(st[self.a1], "corroborated")
        self.assertEqual(st[self.x_anon], "unverified")


class RunVerifyTest(_Proj):
    def test_unconfirmed_blocks(self) -> None:
        si.add_x_text(self.pdir, account_name="A", handle="@abc", text="t", lang="en", posted_at=datetime(2026, 9, 1))
        res = sv.run_verify(self.pdir)
        self.assertFalse(res.ok)
        self.assertIn("확인 안 된", res.errors[0])
        self.assertIsNone(sv.load_claims(self.pdir))

    def test_stub_worker_to_claims(self) -> None:
        a = si.add_article(self.pdir, publisher="가", headline="h", published_at=date(2026, 9, 1), body="해협이 다시 열렸다.")
        b = si.add_article(self.pdir, publisher="나", headline="h", published_at=date(2026, 9, 1), body="당국은 해협이 다시 열렸다고 밝혔다.")
        for s in (a, b):
            si.confirm(self.pdir, s.id, "user")
        os.environ["OSINT_LLM_STUB"] = "1"
        os.environ["OSINT_LLM_STUB_RESPONSE"] = json.dumps({"schema_version": 1, "claims": [
            {"text": "해협 재개방", "evidence": [_ev(a.id, "해협이 다시 열렸다"), _ev(b.id, "해협이 다시 열렸다고")]}]})
        res = sv.run_verify(self.pdir)
        self.assertTrue(res.ok, res.errors)
        self.assertEqual(sv.load_claims(self.pdir).claims[0].status, "corroborated")  # type: ignore[union-attr]

    def test_bad_quote_is_contract_violation(self) -> None:
        a = si.add_article(self.pdir, publisher="가", headline="h", published_at=date(2026, 9, 1), body="해협이 다시 열렸다.")
        si.confirm(self.pdir, a.id, "user")
        os.environ["OSINT_LLM_STUB"] = "1"
        os.environ["OSINT_LLM_STUB_RESPONSE"] = json.dumps({"schema_version": 1, "claims": [
            {"text": "x", "evidence": [_ev(a.id, "해협이 닫혔다")]}]})
        res = sv.run_verify(self.pdir)
        self.assertFalse(res.ok)
        self.assertIsNone(sv.load_claims(self.pdir))

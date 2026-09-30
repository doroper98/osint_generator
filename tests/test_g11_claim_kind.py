"""v5.0.0 G11 — GOAL G4-21 · claims `claim_kind: fact | statement` (back_and_forth D-0119, 사용자 결정 D103).

귀속 인용("~라고 보도했다/주장했다")은 "그런 발언이 있었다"의 근거일 뿐, 내용의 교차 확인이 아니다(fact 는 D-0054 B 그대로).
statement 후보는 귀속 인용을 supports 로 세어 independent_min 이상이면 corroborated. kind 확정은 코드(judge), LLM 은 후보만.
"""

from __future__ import annotations

from datetime import date, datetime

from orchestrator import source_intake as si
from orchestrator import source_verify as sv
from schemas.source_models import Claim, ClaimCandidate, VerifyDraft
from tests import test_source_verify as tsv
from tests.test_source_intake import _Proj
from tests.test_source_verify import _draft, _ev

D = date(2026, 9, 21)


class _Base(_Proj):
    """tests.test_source_verify.JudgeTest 와 같은 소스(가나일보·다라통신·익명 X) — 그 클래스를 상속하면 기존 테스트가 다시 돈다."""

    def setUp(self) -> None:
        super().setUp()
        p = self.pdir
        self.x_anon = si.add_x_text(p, account_name="Some Watcher", handle="@watcher_1", text="Iran says the escort violated its waters.",
                                    lang="en", posted_at=datetime(2026, 9, 20, 15, 0)).id
        self.a1 = si.add_article(p, publisher="가나일보", headline="유조선 2척 호위 통항", published_at=D,
                                 body="20일 유조선 두 척이 해군 호위를 받으며 해협을 지났다. 이란은 영해 침범이라고 주장했다.").id
        self.a2 = si.add_article(p, publisher="다라통신", headline="호위 통항 재개", published_at=D,
                                 body="유조선 두 척이 호위 속에 해협을 통과했다고 당국이 밝혔다.").id

    _judge = tsv.JudgeTest._judge


def _stmt(text: str, *evidence: dict, **kw: object) -> dict:
    return {"text": text, "claim_kind": "statement", "evidence": list(evidence), **kw}


class ClaimKindSchemaTest(_Base):
    def test_kind_defaults_to_fact(self) -> None:
        self.assertEqual(ClaimCandidate.model_validate({"text": "t", "evidence": [_ev(self.a1, "q")]}).claim_kind, "fact")
        self.assertEqual(Claim.model_validate({"claim_id": "clm_0001", "text": "t", "source_ids": [self.a1],
                                               "status": "unverified"}).claim_kind, "fact")
        c, _ = self._judge(_draft({"text": "두 척 통과", "evidence": [_ev(self.a1, "유조선 두 척이 해군 호위를")]}))
        self.assertEqual(c.claims[0].claim_kind, "fact")
        self.assertIn('"claim_kind":"fact"', c.model_dump_json())                   # claims.json 에 기록

    def test_unknown_kind_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ClaimCandidate.model_validate({"text": "t", "claim_kind": "opinion", "evidence": [_ev(self.a1, "q")]})


class StatementJudgeTest(_Base):
    def setUp(self) -> None:
        super().setUp()
        p = self.pdir
        self.b1 = si.add_article(p, publisher="사아일보", headline="이란 반발", published_at=D, body="이란 외무부는 호위가 영해 침범이라고 밝혔다.").id
        self.b2 = si.add_article(p, publisher="자차통신", headline="이란 외무부", published_at=D, body="이란 외무부는 이번 호위를 영해 침범이라고 주장했다.").id
        self.b3 = si.add_article(p, publisher="카타뉴스", headline="침범", published_at=D, body="호위 함대가 이란 영해를 침범했다.").id

    def test_statement_two_attributed_outlets_corroborated(self) -> None:
        c, drops = self._judge(_draft(_stmt("이란 외무부가 호위를 영해 침범이라고 말했다",
                                            _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"),
                                            _ev(self.b2, "이란 외무부는 이번 호위를 영해 침범이라고 주장했다"))))
        cl = c.claims[0]
        self.assertEqual(drops, [])
        self.assertEqual((cl.claim_kind, cl.status, cl.contested), ("statement", "corroborated", False))
        self.assertIn("independent_origins:2", cl.checks)
        self.assertIn(f"attributed:{self.b1}", cl.checks)

    def test_fact_with_same_quotes_stays_contested(self) -> None:
        """같은 두 귀속 인용이라도 fact(“침범했다”) 면 D-0054 B 그대로 — 교차 확인 아님(G4-21 의 핵심)."""
        c, _ = self._judge(_draft({"text": "호위가 이란 영해를 침범했다", "evidence": [
            _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"), _ev(self.b2, "이란 외무부는 이번 호위를 영해 침범이라고 주장했다")]}))
        cl = c.claims[0]
        self.assertEqual((cl.claim_kind, cl.status, cl.contested, cl.attributed_only), ("fact", "unverified", True, True))

    def test_statement_asserted_quote_rejected(self) -> None:
        """statement 인데 귀속 없이 내용을 단정한 인용 → 근거 폐기 + drops[] + checks asserted(경고)."""
        c, drops = self._judge(_draft(_stmt("이란 외무부가 호위를 영해 침범이라고 말했다",
                                            _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"),
                                            _ev(self.b3, "호위 함대가 이란 영해를 침범했다"))))
        cl = c.claims[0]
        self.assertEqual((cl.claim_kind, cl.status), ("statement", "unverified"))   # 남은 귀속 origin 1
        self.assertNotIn(self.b3, cl.source_ids)
        self.assertIn(f"asserted:{self.b3}", cl.checks)
        self.assertIn("independent_origins:1", cl.checks)
        self.assertTrue(any(self.b3 in d and "단정" in d and "G4-21" in d for d in drops))

    def test_statement_without_attributed_evidence_falls_back_to_fact(self) -> None:
        c, drops = self._judge(_draft(_stmt("두 척 통과", _ev(self.a1, "유조선 두 척이 해군 호위를 받으며 해협을 지났다"),
                                            _ev(self.a2, "유조선 두 척이 호위 속에 해협을 통과했다"))))
        cl = c.claims[0]
        self.assertEqual((cl.claim_kind, cl.status), ("fact", "corroborated"))
        self.assertEqual(drops, [])                                                 # 후보 불채택은 근거 폐기가 아니다
        self.assertIn("kind_candidate:statement", cl.checks)

    def test_statement_official_confirmed_verified_and_contradiction_disputed(self) -> None:
        d = _draft(_stmt("이란이 호위를 침범이라고 말했다", _ev(self.x_anon, "Iran says the escort violated its waters"),
                         _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다")))
        self.assertEqual(self._judge(d)[0].claims[0].status, "corroborated")
        d2 = _draft(_stmt("이란이 호위를 침범이라고 말했다", _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"),
                          _ev(self.b3, "호위 함대가 이란 영해를 침범했다", "contradicts")))
        self.assertEqual(self._judge(d2)[0].claims[0].status, "disputed")         # 반박은 fact 와 같게

    def test_judge_deterministic(self) -> None:
        d = _draft(_stmt("이란 외무부 발언", _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"),
                         _ev(self.b3, "호위 함대가 이란 영해를 침범했다")),
                   {"text": "침범", "evidence": [_ev(self.b2, "이번 호위를 영해 침범이라고 주장했다")]})
        a, b = self._judge(d), self._judge(VerifyDraft.model_validate_json(d.model_dump_json()))
        self.assertEqual(a[0].model_dump_json(), b[0].model_dump_json())
        self.assertEqual(a[1], b[1])

    def _apply(self, d: VerifyDraft):  # noqa: ANN202
        for r in si.load_sources(self.pdir).sources:
            si.confirm(self.pdir, r.id, "user")
        s, b = sv.verify_inputs(self.pdir)
        return sv.apply_draft(self.pdir, d, s, b)

    def test_apply_draft_asserted_fails_with_drops_and_writes_nothing(self) -> None:
        """단정 인용 폐기 = drops[] 사유 → StageResult 계약대로 실패, claims.json 을 쓰지 않는다(P6). 경고에 claim·소스."""
        res = self._apply(_draft(_stmt("이란 외무부 발언", _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"),
                                       _ev(self.b3, "호위 함대가 이란 영해를 침범했다"))))
        self.assertFalse(res.ok)
        self.assertTrue(any(self.b3 in d["reason"] and "G4-21" in d["reason"] for d in res.drops))
        self.assertTrue(any("clm_0001" in w and self.b3 in w for w in res.warnings))
        self.assertIsNone(sv.load_claims(self.pdir))

    def test_apply_draft_statement_ok_records_kind(self) -> None:
        res = self._apply(_draft(_stmt("이란 외무부 발언", _ev(self.b1, "이란 외무부는 호위가 영해 침범이라고 밝혔다"),
                                       _ev(self.b2, "이란 외무부는 이번 호위를 영해 침범이라고 주장했다")),
                                 _stmt("통과", _ev(self.a2, "유조선 두 척이 호위 속에 해협을 통과했다"))))
        self.assertTrue(res.ok, res.errors)
        self.assertIn("claim_kind {'fact': 1, 'statement': 1}", res.warnings)
        self.assertTrue(any("clm_0002" in w and "fact 로 판정" in w for w in res.warnings))
        got = {c.claim_id: (c.claim_kind, c.status) for c in sv.load_claims(self.pdir).claims}  # type: ignore[union-attr]
        self.assertEqual(got, {"clm_0001": ("statement", "corroborated"), "clm_0002": ("fact", "unverified")})


class PromptKindTest(_Proj):
    def test_prompt_defines_kind_and_example_passes_schema(self) -> None:
        """P4 — verify_sources 예시가 VerifyDraft 를 통과하고 fact·statement 를 둘 다 보여 준다. 규칙 목록이 삽입된다."""
        from rules import load_rules  # noqa: PLC0415
        from tests.anti_inertia.test_prompt_schema_parity import examples  # noqa: PLC0415
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        kinds = set()
        for data in examples("verify_sources"):
            d = VerifyDraft.model_validate(data)
            kinds |= {c.claim_kind for c in d.claims}
        self.assertEqual(kinds, {"fact", "statement"})
        text = load_prompt("verify_sources", load_rules())
        self.assertIn("G4-21", text)
        self.assertIn('"statement"', text)
        self.assertNotIn("{{RULES", text)


class RejudgeToolTest(_Proj):
    """§5 재판정 도구(tools/g11_rejudge.py) — 읽기만, 결정적, 기존 draft(kind 없음 = fact) 재판정은 status 무변경."""

    def _tool(self):  # noqa: ANN202
        import importlib.util  # noqa: PLC0415
        from pathlib import Path  # noqa: PLC0415

        path = Path(__file__).resolve().parent.parent / "tools" / "g11_rejudge.py"
        spec = importlib.util.spec_from_file_location("g11_rejudge", path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod

    def test_old_draft_rejudge_unchanged_and_deterministic(self) -> None:
        a1 = si.add_article(self.pdir, publisher="가나일보", headline="h", published_at=D, body="유조선 두 척이 해협을 지났다. 이란은 침범이라고 주장했다.").id
        a2 = si.add_article(self.pdir, publisher="다라통신", headline="h", published_at=D, body="유조선 두 척이 해협을 지났다고 밝혔다.").id
        for s in (a1, a2):
            si.confirm(self.pdir, s, "user")
        d = _draft({"text": "두 척 통과", "evidence": [_ev(a1, "유조선 두 척이 해협을 지났다"), _ev(a2, "유조선 두 척이 해협을")]},
                   {"text": "침범", "evidence": [_ev(a1, "이란은 침범이라고 주장했다")]})
        s, b = sv.verify_inputs(self.pdir)
        self.assertTrue(sv.apply_draft(self.pdir, d, s, b).ok)
        # 옛 draft 모양(claim_kind 필드 없음) 그대로 저장 → 재판정
        raw = d.model_dump(mode="json")
        for c in raw["claims"]:
            c.pop("claim_kind")
        (self.pdir / "intake" / "verify_draft.json").write_text(__import__("json").dumps(raw, ensure_ascii=False), encoding="utf-8")
        before = (self.pdir / "intake" / "claims.json").read_bytes()
        t = self._tool()
        r1, r2 = t.rejudge(self.pdir), t.rejudge(self.pdir)
        self.assertEqual(r1, r2)
        self.assertEqual((r1["mode"], r1["changed"]), ("rejudge", 0))
        self.assertEqual({r["kind"] for r in r1["rows"]}, {"fact"})
        self.assertEqual((self.pdir / "intake" / "claims.json").read_bytes(), before)       # 읽기만

    def test_v3_migrated_not_applicable_and_report_copy_no_bodies(self) -> None:
        from pathlib import Path  # noqa: PLC0415

        t = self._tool()
        e2e = Path(__file__).resolve().parent.parent / "docs/handoff/reports/phase6_95/e2e/project"
        self.assertEqual(t.rejudge(e2e)["mode"], "no_bodies")
        (self.pdir / "intake").mkdir(parents=True, exist_ok=True)
        (self.pdir / "intake" / "claims.json").write_text(
            '{"schema_version": 1, "claims": [{"claim_id": "clm_0001", "text": "t", "source_ids": ["src_art_0001"], '
            '"status": "corroborated", "checks": ["v3_user_approved", "credits.yaml"]}]}', encoding="utf-8")
        self.assertEqual(t.rejudge(self.pdir)["mode"], "not_applicable")
        self.assertTrue(t.statement_shaped("합참은 조사 중이라고 밝혔다"))
        self.assertFalse(t.statement_shaped("폭발 원인은 확인되지 않았다"))


class PrimaryStatementTest(_Proj):
    """D-0122 ② B(좁게) — 발언 주체 본인의 공식·사용자 확인 소스 원문은 statement supports. 제3자·미확인은 폐기."""

    def setUp(self) -> None:
        super().setUp()
        from rules import load_official_accounts  # noqa: PLC0415

        off = load_official_accounts().accounts[0]
        p = self.pdir
        self.x_off = si.add_x_text(p, account_name=off.name, handle=off.handle, text="We will continue escort operations in the strait.",
                                   lang="en", posted_at=datetime(2026, 9, 20, 14, 0)).id
        self.x_3rd = si.add_x_text(p, account_name="Some Watcher", handle="@watcher_1", text="We will continue escort operations in the strait.",
                                   lang="en", posted_at=datetime(2026, 9, 20, 15, 0)).id
        self.a1 = si.add_article(p, publisher="가나일보", headline="h", published_at=D, body="당국은 호위를 계속하겠다고 밝혔다.").id

    def _judge(self, d: VerifyDraft):  # noqa: ANN202
        s = si.load_sources(self.pdir)
        return sv.judge(d, s, {r.id: si.body_text(self.pdir, r) for r in s.sources})

    def _d(self, speaker: str) -> VerifyDraft:
        return _draft(_stmt("당국이 호위를 계속하겠다고 밝혔다", _ev(speaker, "We will continue escort operations"),
                            _ev(self.a1, "당국은 호위를 계속하겠다고 밝혔다"), speaker_source_ids=[speaker]))

    def test_own_confirmed_official_original_counts(self) -> None:
        si.confirm(self.pdir, self.x_off, "user")
        c, drops = self._judge(self._d(self.x_off))
        cl = c.claims[0]
        self.assertEqual(drops, [])
        self.assertEqual((cl.claim_kind, cl.status, cl.attributed_only), ("statement", "verified", False))
        self.assertIn(f"primary:{self.x_off}", cl.checks)
        self.assertIn(f"official:{self.x_off}", cl.checks)

    def test_third_party_account_original_dropped(self) -> None:
        si.confirm(self.pdir, self.x_3rd, "user")
        c, drops = self._judge(self._d(self.x_3rd))
        self.assertEqual((c.claims[0].claim_kind, c.claims[0].status), ("statement", "unverified"))
        self.assertTrue(any(self.x_3rd in d and "본인 공식 소스 아님" in d for d in drops))

    def test_unconfirmed_official_original_dropped(self) -> None:
        c, drops = self._judge(self._d(self.x_off))                         # 사용자 확인 전
        self.assertNotIn(f"primary:{self.x_off}", c.claims[0].checks)
        self.assertTrue(any(self.x_off in d and "본인 공식 소스 아님" in d for d in drops))

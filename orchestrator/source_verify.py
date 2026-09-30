"""소스 검증 — 인용 대조로 claim status 를 코드가 정한다 (v3.2.0, docs/handoff/18 §3, back_and_forth D-0051 작업 6, D-0052 D50).

흐름: 사용자 확인된 소스 전부 → 검증 워커(verify_sources, LLM: claim 후보 + 소스별 짧은 인용 + stance)
→ `judge()`(코드) → `intake/claims.json` + 소스별 `verification` 갱신 + drops.

코드 판정(D50):
1. 인용은 `rules verification.quote_max_chars` 이하, 그 소스 본문의 **연속 부분 문자열**(공백 정규화 후). 아니면 근거 폐기 + drop.
2. origin 정규화: x_post = handle, article = publisher, document = issuer. 재인용(기사 note 의 `reprint_markers`, 또는
   기사 요지가 다른 소스의 인용을 그대로 담음)은 독립 origin 에서 뺀다. 삭제된 게시물(18 §3-4)도 세지 않는다.
0. (D-0054) 인용이 귀속 표현(`script_schema.attribution_markers` — "~라고 주장했다"·said·called…)을 담으면 그 근거는
   "주장이 있었다"만 뒷받침한다 — 사실의 supports 에서 뺀다. 그런 근거만 있으면 contested 로 승격(`attributed_only`).
   contested 면 **sides ≥ 2 → disputed, 아니면 unverified** — corroborated·verified 금지.
3. (contested 아닐 때) status 순서: 독립 origin 의 contradicts 근거 → **disputed** / 공식 1차 출처(official_* 계정·document)가 supports
   + 그 소스 사용자 확인 → **verified** / supports 독립 origin ≥ `independent_min` → **corroborated** / 나머지 **unverified**.
4. contested 인데 sides < 2 → unverified(스키마). 사용자 확인 안 된 소스가 있으면 단계 자체를 시작하지 않는다(18 §7).
5. (v5.0.0 GOAL G4-21, D-0119) `claim_kind` 는 LLM 이 후보만 낸다. **statement**(“그런 발언·보도가 있었다”) 후보는 귀속 인용
   supports 가 하나라도 있으면 채택 — 귀속 인용을 supports 로 세어 ③ 그대로(independent_min 이상 → corroborated), 귀속만이라는
   이유로 contested 로 올리지 않는다. 귀속 표현 없이 내용을 단정하는 인용은 statement 의 근거가 아니다 → 근거 폐기 + drops[]
   + checks `asserted:<src>`(경고). 예외(D-0122 ② B, 좁게): LLM 이 `speaker_source_ids` 로 댄 발언 주체 **본인** 소스가
   `is_official` + 사용자 확인이면 그 비귀속 원문은 발언의 supports(checks `primary:<src>`) — 매체 인용이 아니라 발언 그 자체다.
   아니면 폐기 + drops "본인 공식 소스 아님". 귀속 인용·본인 원문이 하나도 없으면 후보 불채택 → fact(checks `kind_candidate:statement`, 경고).
   **fact** 는 ⓪ 그대로.
   fact 후보를 코드가 statement 로 올리지 않는다(“침범했다”가 보도 둘로 corroborated 가 되는 것을 막는 것이 G4-21).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

from orchestrator.source_intake import Source, body_text, load_sources, save_sources, unconfirmed
from rules import load_rules
from schemas.engine_models import StageResult
from schemas.source_models import (ArticleSource, Claim, ClaimCandidate, ClaimsFile, DocumentSource, EvidenceQuote, SourcesFile,
                                   SourceVerification, VerifyDraft, XPostSource, check_claim_sources)

CLAIMS = Path("intake") / "claims.json"
DRAFT = Path("intake") / "verify_draft.json"
_WS = re.compile(r"\s+")
_STRENGTH = {"disputed": 0, "unverified": 1, "corroborated": 2, "verified": 3}


def claims_path(pdir: Path) -> Path:
    return pdir / CLAIMS


def load_claims(pdir: Path) -> Optional[ClaimsFile]:
    p = claims_path(pdir)
    return ClaimsFile.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


def _norm(s: str) -> str:
    return _WS.sub(" ", s).strip().lower()


def origin(rec: Source) -> str:
    if isinstance(rec, XPostSource):
        return "x:" + rec.handle.lower()
    if isinstance(rec, ArticleSource):
        return "pub:" + _norm(rec.publisher)
    return "doc:" + _norm(rec.issuer)


def is_official(rec: Source) -> bool:
    return isinstance(rec, DocumentSource) or (isinstance(rec, XPostSource) and rec.account_class.startswith("official"))


def _attributed(quote: str, markers: list[str]) -> bool:
    q = quote.lower()
    return any(m in q for m in markers)


def _reprint(rec: Source, other_quotes: list[str], markers: list[str]) -> bool:
    if not isinstance(rec, ArticleSource):
        return False
    if any(m in rec.note for m in markers):
        return True
    facts = _norm(" ".join(rec.key_facts))
    return any(q and q in facts for q in other_quotes)


def judge(draft: VerifyDraft, sources: SourcesFile, bodies: dict[str, str]) -> tuple[ClaimsFile, list[str]]:
    """LLM 후보 → 코드 판정 claims + drops(버린 근거·후보 기록). 결정적이다(같은 입력 = 같은 출력)."""
    R_ = load_rules()
    V = R_.verification  # noqa: N806
    markers = [m.lower() for m in R_.script_schema.attribution_markers]
    recs = sources.by_id()
    norm_body = {k: _norm(v) for k, v in bodies.items()}
    drops: list[str] = []
    claims: list[Claim] = []
    for k, cand in enumerate(draft.claims, 1):
        cid = f"clm_{k:04d}"
        good = []
        for ev in cand.evidence:
            q = _norm(ev.quote)
            if ev.source_id not in recs:
                drops.append(f"{cid}: 없는 소스 {ev.source_id} — 근거 폐기")
            elif len(ev.quote) > V.quote_max_chars:
                drops.append(f"{cid}: {ev.source_id} 인용 {len(ev.quote)}자 > {V.quote_max_chars} — 근거 폐기")
            elif q not in norm_body.get(ev.source_id, ""):
                drops.append(f"{cid}: {ev.source_id} 인용이 본문에 없음({ev.quote[:40]!r}) — 근거 폐기")
            else:
                good.append(ev)
        sup_all = [e for e in good if e.stance == "supports"]
        con = [e for e in good if e.stance == "contradicts"]
        if not sup_all:
            drops.append(f"{cid}: 본문과 맞는 supports 근거 없음 — 후보 버림({cand.text[:40]!r})")
            continue
        att = [e for e in sup_all if _attributed(e.quote, markers)]
        primary = [e for e in sup_all if e not in att and e.source_id in cand.speaker_source_ids
                   and is_official(recs[e.source_id]) and recs[e.source_id].confirmed]   # D-0122 B — 본인 공식 원문
        kind = "fact"
        kind_checks: list[str] = []
        if cand.claim_kind == "statement":                     # G4-21 — 후보 채택은 귀속 인용·본인 원문 근거가 있을 때만
            if att or primary:
                kind = "statement"
            else:                                               # 후보 불채택은 근거 폐기가 아니다 — checks 에 남기고 경고로(apply_draft)
                kind_checks = ["kind_candidate:statement"]
        asserted: list[EvidenceQuote] = []
        if kind == "statement":                                 # 귀속 없는 단정 인용은 "발언이 있었다"의 근거가 아니다
            asserted = [e for e in sup_all if e not in att and e not in primary]
            for e in asserted:
                why = "본인 공식 소스 아님" if e.source_id in cand.speaker_source_ids else "statement 근거 아님"
                drops.append(f"{cid}: {e.source_id} 인용이 귀속 표현 없이 내용을 단정 — {why}, 근거 폐기(G4-21)")
            good = [e for e in good if e not in asserted]
            sup_all = att + primary
            sup = sup_all                                       # G4-21 — 귀속 인용·본인 원문을 발언의 supports 로 센다
        else:
            sup = [e for e in sup_all if e not in att]          # D-0054 B — 귀속 인용은 사실의 근거가 아니다
        attributed_only = not [e for e in sup_all if e not in att]   # statement 에 본인 원문이 있으면 False(귀속만이 아니다)
        quotes_by_src = {e.source_id: _norm(e.quote) for e in good}

        def counted(e) -> bool:  # noqa: ANN001
            r = recs[e.source_id]
            others = [q for s, q in quotes_by_src.items() if s != e.source_id]
            return not (isinstance(r, XPostSource) and r.deleted) and not _reprint(r, others, V.reprint_markers)

        contested = cand.contested or (attributed_only and kind == "fact")   # 귀속 인용만 있는 사실 = 분쟁으로 승격(LLM 누락 보완)
        sup_orig = {origin(recs[e.source_id]) for e in sup if counted(e)}
        con_orig = {origin(recs[e.source_id]) for e in con if counted(e)}
        if not contested:
            con_orig -= sup_orig                               # 반박 origin 제거는 분쟁이 아닐 때만(D-0054 A)
        checks = [f"quote_match:{e.source_id}" for e in good] + [f"independent_origins:{len(sup_orig)}"]
        checks += [f"attributed:{e.source_id}" for e in att]
        checks += [f"primary:{e.source_id}" for e in primary if kind == "statement"]
        checks += [f"asserted:{e.source_id}" for e in asserted] + kind_checks
        official = [e.source_id for e in sup if is_official(recs[e.source_id]) and recs[e.source_id].confirmed and counted(e)]
        checks += [f"official:{s}" for s in official]
        sides = cand.sides if contested else None
        if contested:                                          # 판정 ⓪ — 분쟁은 corroborated·verified 가 될 수 없다
            status = "disputed" if len(sides or []) >= 2 else "unverified"
        elif con_orig:
            status = "disputed"
        elif official:
            status = "verified"
        elif len(sup_orig) >= V.independent_min:
            status = "corroborated"
        else:
            status = "unverified"
        ids = list(dict.fromkeys(e.source_id for e in sup_all + con))
        claims.append(Claim(claim_id=cid, text=cand.text, source_ids=ids, status=status, contested=contested,  # type: ignore[arg-type]
                            sides=sides, event_date=cand.event_date, checks=checks, attributed_only=attributed_only, claim_kind=kind, notes=""))  # type: ignore[arg-type]
    out = ClaimsFile(claims=claims)
    errs = check_claim_sources(out, sources)
    if errs:   # sides 가 없는 소스를 가리킴 등 — 조용히 넘기지 않는다
        raise ValueError("claims 소스 참조 오류: " + "; ".join(errs))
    return out, drops


def source_verification(sources: SourcesFile, claims: ClaimsFile) -> SourcesFile:
    """소스별 verification = 그 소스가 supports 로 뒷받침한 claim 중 가장 강한 status(없으면 unverified)."""
    best: dict[str, str] = {}
    for c in claims.claims:
        for s in c.source_ids:
            if _STRENGTH[c.status] > _STRENGTH.get(best.get(s, "disputed"), -1) or s not in best:
                best[s] = c.status
    out = []
    for r in sources.sources:
        chk = (["official_account"] if isinstance(r, XPostSource) and r.account_class.startswith("official") else []) \
            + [f"claims:{sum(r.id in c.source_ids for c in claims.claims)}"]
        out.append(r.model_copy(update={"verification": SourceVerification(status=best.get(r.id, "unverified"), checks=chk)}))  # type: ignore[arg-type]
    return SourcesFile(sources=out)


def verify_inputs(pdir: Path) -> tuple[SourcesFile, dict[str, str]]:
    f = load_sources(pdir)
    if not f.sources:
        raise ValueError("소스가 없다 — intake/sources.json")
    pending = unconfirmed(pdir)
    if pending:
        raise ValueError(f"사용자 확인 안 된 소스 {pending} — 확인 전에는 검증하지 않는다(18 §7)")
    return f, {s.id: body_text(pdir, s) for s in f.sources}


def run_verify(pdir: Path, backend: str = "claude") -> StageResult:
    """SOURCE_VERIFY 단계: 워커 1회(재요청 1) → 코드 판정 → claims.json·sources.json. 실패면 파일을 쓰지 않는다(P6)."""
    try:
        sources, bodies = verify_inputs(pdir)
    except ValueError as ex:
        return StageResult(ok=False, stage="source_verify", errors=[str(ex)])
    from schemas.models import TaskQueueItem  # noqa: PLC0415
    from workers.verify_sources_worker import VerifySourcesWorker  # noqa: PLC0415

    w = VerifySourcesWorker()
    w.llm_backend = backend
    task = TaskQueueItem(task_id=f"verify_sources__{pdir.name}", task_type="verify_sources", assigned_worker="verify_sources",
                         description="소스 검증 1회", input_refs=["intake/sources.json"], output_refs=[DRAFT.as_posix()])
    args = argparse.Namespace(project_id=pdir.name, task_id=task.task_id, projects_root=str(pdir.parent))
    res = w.run(args, task)
    try:
        w.write_result(args, res)
    except OSError:
        pass
    status = res.status if isinstance(res.status, str) else res.status.value
    if status != "completed" or not (pdir / DRAFT).exists():
        return StageResult(ok=False, stage="source_verify", errors=list(res.errors) or [f"verify_sources 실패({status})"])
    draft = VerifyDraft.model_validate_json((pdir / DRAFT).read_text(encoding="utf-8"))
    return apply_draft(pdir, draft, sources, bodies)


def apply_draft(pdir: Path, draft: VerifyDraft, sources: SourcesFile, bodies: dict[str, str]) -> StageResult:
    try:
        claims, drops = judge(draft, sources, bodies)
    except ValueError as ex:
        return StageResult(ok=False, stage="source_verify", errors=[str(ex)])
    if not claims.claims:
        return StageResult(ok=False, stage="source_verify", errors=["판정 뒤 남은 claim 이 없다"], drops=[{"reason": d} for d in drops])
    kinds = {k: sum(c.claim_kind == k for c in claims.claims) for k in ("fact", "statement")}
    warns = [f"claim_kind {kinds}"]
    warns += [f"{c.claim_id}: statement 인데 귀속 없이 단정한 인용 {[x.split(':', 1)[1] for x in c.checks if x.startswith('asserted:')]} — 근거 폐기(G4-21)"
              for c in claims.claims if any(x.startswith("asserted:") for x in c.checks)]
    warns += [f"{c.claim_id}: statement 후보인데 귀속 인용·본인 원문 근거 없음 — fact 로 판정(G4-21)"
              for c in claims.claims if "kind_candidate:statement" in c.checks]
    if drops:   # StageResult 계약(drops 가 있으면 ok 아님, 15 P6) — 파일을 쓰지 않고 실패로 보고한다(v5.0.0 전에는 쓴 뒤 예외)
        return StageResult(ok=False, stage="source_verify", errors=[f"근거 폐기 {len(drops)}건 — drops 확인 후 재검증"],
                           drops=[{"reason": d} for d in drops], warnings=warns)
    p = claims_path(pdir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(claims.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    save_sources(pdir, source_verification(sources, claims))
    counts = {s: sum(c.status == s for c in claims.claims) for s in _STRENGTH}
    return StageResult(ok=True, stage="source_verify", artifacts={"claims": str(p)}, warnings=[f"status {counts}"] + warns)


__all__ = ["apply_draft", "claims_path", "is_official", "judge", "load_claims", "origin", "run_verify", "source_verification",
           "verify_inputs"]

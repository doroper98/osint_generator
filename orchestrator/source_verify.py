"""소스 검증 — 인용 대조로 claim status 를 코드가 정한다 (v3.2.0, docs/handoff/18 §3, back_and_forth D-0051 작업 6, D-0052 D50).

흐름: 사용자 확인된 소스 전부 → 검증 워커(verify_sources, LLM: claim 후보 + 소스별 짧은 인용 + stance)
→ `judge()`(코드) → `intake/claims.json` + 소스별 `verification` 갱신 + drops.

코드 판정(D50):
1. 인용은 `rules verification.quote_max_chars` 이하, 그 소스 본문의 **연속 부분 문자열**(공백 정규화 후). 아니면 근거 폐기 + drop.
2. origin 정규화: x_post = handle, article = publisher, document = issuer. 재인용(기사 note 의 `reprint_markers`, 또는
   기사 요지가 다른 소스의 인용을 그대로 담음)은 독립 origin 에서 뺀다. 삭제된 게시물(18 §3-4)도 세지 않는다.
3. status 순서: 독립 origin 의 contradicts 근거 → **disputed** / 공식 1차 출처(official_* 계정·document)가 supports
   + 그 소스 사용자 확인 → **verified** / supports 독립 origin ≥ `independent_min` → **corroborated** / 나머지 **unverified**.
4. contested 인데 sides < 2 → unverified(스키마). 사용자 확인 안 된 소스가 있으면 단계 자체를 시작하지 않는다(18 §7).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

from orchestrator.source_intake import Source, body_text, load_sources, save_sources, unconfirmed
from rules import load_rules
from schemas.engine_models import StageResult
from schemas.source_models import (ArticleSource, Claim, ClaimCandidate, ClaimsFile, DocumentSource, SourcesFile,
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


def _reprint(rec: Source, other_quotes: list[str], markers: list[str]) -> bool:
    if not isinstance(rec, ArticleSource):
        return False
    if any(m in rec.note for m in markers):
        return True
    facts = _norm(" ".join(rec.key_facts))
    return any(q and q in facts for q in other_quotes)


def judge(draft: VerifyDraft, sources: SourcesFile, bodies: dict[str, str]) -> tuple[ClaimsFile, list[str]]:
    """LLM 후보 → 코드 판정 claims + drops(버린 근거·후보 기록). 결정적이다(같은 입력 = 같은 출력)."""
    V = load_rules().verification  # noqa: N806
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
        sup = [e for e in good if e.stance == "supports"]
        con = [e for e in good if e.stance == "contradicts"]
        if not sup:
            drops.append(f"{cid}: 본문과 맞는 supports 근거 없음 — 후보 버림({cand.text[:40]!r})")
            continue
        quotes_by_src = {e.source_id: _norm(e.quote) for e in good}

        def counted(e) -> bool:  # noqa: ANN001
            r = recs[e.source_id]
            others = [q for s, q in quotes_by_src.items() if s != e.source_id]
            return not (isinstance(r, XPostSource) and r.deleted) and not _reprint(r, others, V.reprint_markers)

        sup_orig = {origin(recs[e.source_id]) for e in sup if counted(e)}
        con_orig = {origin(recs[e.source_id]) for e in con if counted(e)} - sup_orig
        checks = [f"quote_match:{e.source_id}" for e in good] + [f"independent_origins:{len(sup_orig)}"]
        official = [e.source_id for e in sup if is_official(recs[e.source_id]) and recs[e.source_id].confirmed and counted(e)]
        checks += [f"official:{s}" for s in official]
        if con_orig:
            status = "disputed"
        elif official:
            status = "verified"
        elif len(sup_orig) >= V.independent_min:
            status = "corroborated"
        else:
            status = "unverified"
        sides = cand.sides if cand.contested else None
        if cand.contested and len(sides or []) < 2:
            status = "unverified"
            drops.append(f"{cid}: 분쟁 사안인데 양측 입장 < 2 — unverified(18 §3-5)")
        ids = list(dict.fromkeys(e.source_id for e in sup + con))
        claims.append(Claim(claim_id=cid, text=cand.text, source_ids=ids, status=status, contested=cand.contested,  # type: ignore[arg-type]
                            sides=sides, event_date=cand.event_date, checks=checks, notes=""))
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
    p = claims_path(pdir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(claims.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    save_sources(pdir, source_verification(sources, claims))
    counts = {s: sum(c.status == s for c in claims.claims) for s in _STRENGTH}
    return StageResult(ok=True, stage="source_verify", artifacts={"claims": str(p)},
                       drops=[{"reason": d} for d in drops], warnings=[f"status {counts}"])


__all__ = ["apply_draft", "claims_path", "is_official", "judge", "load_claims", "origin", "run_verify", "source_verification",
           "verify_inputs"]

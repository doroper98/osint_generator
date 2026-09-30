"""G11 재판정 표 — claims `claim_kind` 도입(v5.0.0 GOAL G4-21) 전/후 status 변화 (back_and_forth D-0119 §5).

프로젝트마다 한 줄 JSON(jsonl). 파일을 쓰지 않는다(읽기만).
- `intake/verify_draft.json` 과 본문이 있으면 **실제 재판정**: 현재 `judge()` 로 다시 판정해 claims.json 과 status 를 비교.
- draft 가 없으면(과거 실행이 draft 를 남기지 않음) **기록 투영**: 기존 draft 에는 claim_kind 가 없으므로 전부 fact(기본) —
  fact 경로는 무변경이라 status 도 그대로다(`after = before`). 덧붙여 귀속 근거(checks `attributed:`)가 있는 claim 을
  statement 후보로 다시 뽑았을 때의 status 를 checks·sources.json 만으로 투영한다(`if_statement`, 재인용 판정은 인용이 없어 생략).
  투영은 **문장이 발언 모양인 claim**(본문에 `attribution_markers` 가 있는 문장)만 한다 — "폭발은 두 차례였다" 같은 사실 문장을
  statement 로 바꾸는 것은 LLM 의 새 후보(새 claim 문장)이지 재판정이 아니다. 과거 프롬프트는 귀속 인용뿐인 주장을 contested 로 달게
  했으므로 `status`(LLM contested 유지)와 `status_uncontested`(새 프롬프트에서 contested 를 달지 않았을 때)를 둘 다 적는다.
- v3 이관 claims(checks `v3_user_approved`, `tools/migrate_v3_claims.py`)는 판정 경로를 거치지 않았으므로 대상 아님.
- draft 는 있는데 본문 보관본이 없으면(보고서 사본 등) 인용 대조가 불가능 — `no_bodies` 로 적고 판정하지 않는다.

    python tools/g11_rejudge.py projects/hormuz_korea projects/ratcliffe2026 projects/fed_policy_2026
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from orchestrator import source_verify as sv  # noqa: E402
from orchestrator.source_intake import body_text, load_sources  # noqa: E402
from rules import load_rules  # noqa: E402
from schemas.source_models import Claim, ClaimsFile, SourcesFile, VerifyDraft, XPostSource  # noqa: E402


def _ids(c: Claim, prefix: str) -> list[str]:
    return [x.split(":", 1)[1] for x in c.checks if x.startswith(prefix)]


def project_statement(c: Claim, sources: SourcesFile) -> Optional[dict[str, object]]:
    """귀속 근거가 있는 claim 을 statement 로 판정했다면 — judge ③ 을 checks 로 재현(투영). 귀속 근거가 없으면 None."""
    att = _ids(c, "attributed:")
    if not att:
        return None
    recs = sources.by_id()
    live = [s for s in att if s in recs and not (isinstance(recs[s], XPostSource) and recs[s].deleted)]  # type: ignore[union-attr]
    origins = sorted({sv.origin(recs[s]) for s in live})
    asserted = [s for s in _ids(c, "quote_match:") if s not in att]        # statement 에선 폐기(반박 근거가 섞였을 수 있다)
    llm_contested = c.contested and not c.attributed_only                   # 귀속만이라 승격된 분쟁은 statement 에서 풀린다
    official = [s for s in live if sv.is_official(recs[s]) and recs[s].confirmed]
    plain = "verified" if official else "corroborated" if len(origins) >= load_rules().verification.independent_min else "unverified"
    st = ("disputed" if len(c.sides or []) >= 2 else "unverified") if llm_contested else plain
    return {"status": st, "status_uncontested": plain, "origins": origins, "asserted_dropped": asserted,
            "contested_kept": llm_contested}


def statement_shaped(text: str) -> bool:
    """문장에 귀속 표현이 있는가. "확인되지 않" 은 미확인을 스스로 밝히는 사실 문장이라(rules 주석) 발언 모양에서 뺀다."""
    t = text.lower()
    return any(m.lower() in t for m in load_rules().script_schema.attribution_markers if m != "확인되지 않")


def rejudge(pdir: Path) -> dict[str, object]:
    cp = pdir / "intake" / "claims.json"
    if not cp.exists():
        return {"project": pdir.name, "mode": "no_claims"}
    claims = ClaimsFile.model_validate_json(cp.read_text(encoding="utf-8"))
    if all("v3_user_approved" in c.checks for c in claims.claims):
        return {"project": pdir.name, "mode": "not_applicable", "claims": len(claims.claims),
                "reason": "v3 이관 claims(checks v3_user_approved) — 판정 경로를 거치지 않음"}
    sources = load_sources(pdir)
    dp = pdir / "intake" / "verify_draft.json"
    rows: list[dict[str, object]] = []
    missing = [s.id for s in sources.sources if not isinstance(s, XPostSource) and not (pdir / "intake" / "bodies" / f"{s.id}.txt").exists()]
    if dp.exists() and missing:
        return {"project": pdir.name, "mode": "no_bodies", "claims": len(claims.claims), "missing_bodies": missing}
    if dp.exists():
        draft = VerifyDraft.model_validate_json(dp.read_text(encoding="utf-8"))
        new, drops = sv.judge(draft, sources, {s.id: body_text(pdir, s) for s in sources.sources})
        after = {c.claim_id: c for c in new.claims}
        for c in claims.claims:
            a = after.get(c.claim_id)
            rows.append({"claim_id": c.claim_id, "before": c.status, "after": a.status if a else None,
                         "kind": a.claim_kind if a else None})
        return {"project": pdir.name, "mode": "rejudge", "claims": len(claims.claims), "drops": drops, "rows": rows,
                "changed": sum(r["before"] != r["after"] for r in rows)}
    for c in claims.claims:
        row: dict[str, object] = {"claim_id": c.claim_id, "before": c.status, "after": c.status, "kind": "fact", "text": c.text}
        proj = project_statement(c, sources) if statement_shaped(c.text) else None
        if proj is not None:
            row["if_statement"] = proj
        rows.append(row)
    return {"project": pdir.name, "mode": "projection", "claims": len(claims.claims), "changed": 0,
            "statement_candidates": sum("if_statement" in r for r in rows),
            "rows": [r for r in rows if "if_statement" in r]}


def main(argv: list[str]) -> int:
    for p in argv:
        print(json.dumps(rejudge(Path(p).resolve()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

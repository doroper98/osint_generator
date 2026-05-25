"""report_bundle 수신/검증 + research_dossier 변환 (외부 연동, 계약 v1).

agents_reviewer 가 emit 한 report_bundle.json 을 `ReportBundle`(extra="forbid")로
fail-closed 검증 로드하고, 우리 파이프라인의 사실 토대인 `ResearchDossier` 로 변환한다.
변환(`bundle_to_research_dossier`)은 순수 함수다 — 디스크 I/O 는 research_io 가 담당.

매핑 (계약 v1 §9)
-----------------
- report.headline           → dossier.topic
- report.deck (+ closing)   → dossier.summary
- claims[]                  → ResearchClaim (status/evidence/라벨 무손실 전파)
- evidence.quote_or_data    → Evidence.quote (필드명 매핑)
- signals[]                 → open_questions (전방위 관찰 항목)

차트/지도/테마는 시각 에셋 단계(Phase 7)에서 소비하며 본 변환(텍스트 슬라이드 seam)에선
사용하지 않는다.
"""

from __future__ import annotations

import json
from pathlib import Path

from schemas.models import (
    Evidence,
    ReportBundle,
    ResearchClaim,
    ResearchDossier,
)


def load_report_bundle(path: Path) -> ReportBundle:
    """report_bundle.json 을 로드 → `ReportBundle` (fail-closed 검증).

    raise
    -----
    FileNotFoundError
        파일 없음.
    json.JSONDecodeError / pydantic.ValidationError(=ValueError)
        손상/스키마 위반은 건너뛰지 않고 전파.
    """
    if not path.exists():
        raise FileNotFoundError(f"report_bundle 파일이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ReportBundle.model_validate(raw)


def bundle_to_research_dossier(bundle: ReportBundle, project_id: str) -> ResearchDossier:
    """`ReportBundle` → `ResearchDossier` (순수 변환, 계약 v1 §9)."""
    summary = bundle.report.deck
    if bundle.report.closing:
        summary = f"{summary} {bundle.report.closing}".strip()

    claims: list[ResearchClaim] = []
    for c in bundle.claims:
        evidence = [
            Evidence(
                source_id=e.source_id or None,
                quote=e.quote_or_data,
                locator=e.locator or None,
                stance=e.stance,
            )
            for e in c.evidence
        ]
        claims.append(
            ResearchClaim(
                claim_id=c.claim_id,
                statement=c.statement,
                status=c.status,
                evidence=evidence,
                cross_checked=c.cross_checked,
                confidence=c.confidence,
            )
        )

    open_questions: list[str] = []
    for s in bundle.signals:
        open_questions.append(
            f"{s.signal}: {s.description}" if s.description else s.signal
        )

    return ResearchDossier(
        project_id=project_id,
        topic=bundle.report.headline,
        summary=summary,
        seeds=[],
        claims=claims,
        open_questions=open_questions,
    )


__all__ = ["load_report_bundle", "bundle_to_research_dossier"]

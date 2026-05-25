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


def _claims_from_bundle_claims(bundle: ReportBundle) -> list[ResearchClaim]:
    """bundle.claims (v5.6+ prose→claim 그래프가 있을 때) 직매핑."""
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
    return claims


def _synthesize_claims_from_visuals(bundle: ReportBundle) -> list[ResearchClaim]:
    """bundle.claims 가 비었을 때(v5.5.0 현실) 라벨 척추를 charts/map/contradictions
    provenance 에서 합성한다 — 검증 상태(verification)가 영상 라벨로 전파되도록.
    """
    claims: list[ResearchClaim] = []

    for ch in bundle.charts:
        statement = ch.title
        if ch.note:
            statement = f"{statement} — {ch.note}"
        prov = ch.provenance
        evidence = [
            Evidence(
                source_id=s.source_id or None,
                quote=" ".join(p for p in (s.provider, s.code, s.unit) if p).strip(),
                stance="supports",
            )
            for s in prov.sources
        ]
        claims.append(
            ResearchClaim(
                claim_id=ch.chart_id,
                statement=statement or ch.chart_id,
                status=prov.verification,
                evidence=evidence,
                cross_checked=(prov.verification == "confirmed"),
                confidence=prov.confidence,
                notes=f"chart:{ch.type}",
            )
        )

    if bundle.map is not None:
        m = bundle.map
        names = [mk.name for mk in m.markers if mk.name]
        if names:
            claims.append(
                ResearchClaim(
                    claim_id=m.id or "map",
                    statement="지리적 배치: " + ", ".join(names),
                    status=m.provenance.verification if m.provenance else "inferred",
                    confidence=m.provenance.confidence if m.provenance else "medium",
                    notes="map",
                )
            )

    # 모순(contradictions)은 봉합하지 않고 disputed claim 으로 — <반박됨> 라벨 신호.
    for i, c in enumerate(bundle.contradictions, start=1):
        note = f"반론: {c.side_b}"
        if c.resolution:
            note = f"{note} / 판단: {c.resolution}"
        claims.append(
            ResearchClaim(
                claim_id=f"contradiction_{i}",
                statement=c.side_a,
                status="disputed",
                evidence=(
                    [Evidence(quote=c.evidence, stance="contextual")] if c.evidence else []
                ),
                confidence="medium",
                notes=note,
            )
        )

    return claims


def _narrative_summary(bundle: ReportBundle) -> str:
    """deck + (섹션 heading+prose) + closing 을 ScriptWorker 가 쓸 서사 원천으로 결합.

    v5.5.0 emit 은 알맹이가 sections[].prose 에 있으므로(계약 §6: prose=나레이션 원천),
    summary 에 실어 ScriptWorker 가 발화형으로 변환하도록 넘긴다.
    """
    parts: list[str] = []
    if bundle.report.deck:
        parts.append(bundle.report.deck)
    for s in bundle.sections:
        if s.prose:
            head = f"[{s.heading}] " if s.heading else ""
            parts.append(f"{head}{s.prose}")
    if bundle.report.closing:
        parts.append(bundle.report.closing)
    return "\n\n".join(parts).strip()


def bundle_to_research_dossier(bundle: ReportBundle, project_id: str) -> ResearchDossier:
    """`ReportBundle` → `ResearchDossier` (순수 변환, 계약 v1 §9).

    claims 분기:
    - bundle.claims 가 있으면(v5.6+ prose→claim) 그대로 매핑.
    - 비어 있으면(v5.5.0 현실) charts/map/contradictions provenance 에서 합성 —
      라벨 척추가 chart/map provenance 를 타게 한다(검증 상태 무손실 전파).
    서사(section prose)는 summary 로 실어 ScriptWorker 가 발화형으로 변환한다.
    """
    if bundle.claims:
        claims = _claims_from_bundle_claims(bundle)
    else:
        claims = _synthesize_claims_from_visuals(bundle)

    open_questions: list[str] = []
    for s in bundle.signals:
        open_questions.append(
            f"{s.signal}: {s.description}" if s.description else s.signal
        )

    return ResearchDossier(
        project_id=project_id,
        topic=bundle.report.headline,
        summary=_narrative_summary(bundle),
        seeds=[],
        claims=claims,
        open_questions=open_questions,
    )


__all__ = ["load_report_bundle", "bundle_to_research_dossier"]

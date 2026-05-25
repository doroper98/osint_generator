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
    SourceEntry,
    SourceRegistry,
)


def persisted_bundle_path(project_id: str, cfg=None) -> Path:
    """받은 bundle 의 영속 사본 경로 (`04_research/report_bundle.json`). render_io 가
    차트/지도 지오데이터를 scene 에 붙일 때 읽는다.
    """
    from orchestrator.research_io import research_dir

    return research_dir(project_id, cfg) / "report_bundle.json"


def persist_report_bundle(project_id: str, bundle: ReportBundle, cfg=None) -> Path:
    """받은 bundle 을 `04_research/report_bundle.json` 으로 영속화(tmp→replace)."""
    path = persisted_bundle_path(project_id, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def load_persisted_bundle(project_id: str, cfg=None) -> ReportBundle:
    """`04_research/report_bundle.json` → ReportBundle. 없으면 FileNotFoundError."""
    path = persisted_bundle_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"report_bundle.json 영속 사본이 없습니다: {path}")
    return ReportBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))


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


# 섹션당 prose 발췌 상한(자). 전체 보고서(수천 자)를 통째로 넘기면 ScriptWorker(LLM)가
# 5분 대본으로 압축하다 출력이 비대해져 응답을 쪼개고 형식이 깨진다(LLM-AP-005). 헤딩 +
# 앞 문장들의 '구조적 개요'를 넘기고 살은 ScriptWorker 가 붙이게 한다.
_SECTION_PROSE_CAP = 320


def _truncate_at_sentence(text: str, max_chars: int) -> str:
    """max_chars 근처의 문장 종결 지점에서 자른다(문장 중간 절단 방지)."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    best = -1
    for ender in ("다. ", "다.\n", "다.", ". ", ".\n", "? ", "! "):
        idx = cut.rfind(ender)
        if idx != -1:
            best = max(best, idx + len(ender.rstrip()))
    return (cut[:best] if best != -1 else cut).strip()


def _narrative_summary(bundle: ReportBundle) -> str:
    """deck + (섹션 heading + prose 발췌) + closing 을 ScriptWorker 가 쓸 서사 개요로 결합.

    v5.5.0 emit 은 알맹이가 sections[].prose 에 있으므로(계약 §6: prose=나레이션 원천),
    summary 에 실어 ScriptWorker 가 발화형으로 변환하도록 넘긴다. 단 섹션당 발췌 상한을
    둬 입력 비대화를 막는다(5분 대본은 어차피 응축이므로 개요로 충분, LLM-AP-005).
    """
    parts: list[str] = []
    if bundle.report.deck:
        parts.append(bundle.report.deck)
    for s in bundle.sections:
        if s.prose:
            head = f"[{s.heading}] " if s.heading else ""
            parts.append(f"{head}{_truncate_at_sentence(s.prose, _SECTION_PROSE_CAP)}")
    if bundle.report.closing:
        parts.append(bundle.report.closing)
    return "\n\n".join(parts).strip()


def bundle_to_source_registry(bundle: ReportBundle, project_id: str) -> SourceRegistry:
    """bundle 의 출처(top-level sources + 차트/지도 provenance.sources)를 SourceRegistry 로.

    화면 상단 출처 표기(영상 문법)를 위해 source_id → 표기명을 해소할 수 있게 한다.
    source_id 로 dedup(top-level sources 가 우선). 차트 provenance 의 데이터 출처
    (예: mkt-1=YAHOO/KRX)도 포함해야 chart-derived claim 의 출처가 해소된다.
    """
    by_id: dict[str, SourceEntry] = {}

    # 차트/지도 provenance.sources (데이터 시리즈 출처).
    provs = [c.provenance for c in bundle.charts]
    if bundle.map is not None and bundle.map.provenance is not None:
        provs.append(bundle.map.provenance)
    for prov in provs:
        for s in prov.sources:
            if not s.source_id or s.source_id in by_id:
                continue
            label = " ".join(p for p in (s.provider, s.code) if p).strip()
            by_id[s.source_id] = SourceEntry(
                source_id=s.source_id,
                platform=s.provider or "data",
                source_type="data_series",
                original_url=s.url or None,
                title=label or s.provider or s.source_id,
            )

    # top-level sources (보고서 인용 출처) — 우선(덮어쓰기).
    for s in bundle.sources:
        by_id[s.source_id] = SourceEntry(
            source_id=s.source_id,
            platform=s.publisher or "source",
            source_type="report_cited",
            original_url=s.url or None,
            title=s.title or s.publisher or s.source_id,
        )

    return SourceRegistry(project_id=project_id, sources=list(by_id.values()))


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


__all__ = [
    "load_report_bundle",
    "persist_report_bundle",
    "load_persisted_bundle",
    "persisted_bundle_path",
    "bundle_to_research_dossier",
    "bundle_to_source_registry",
]

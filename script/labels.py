"""문장 검증 라벨 — 코드가 도시어 claim status 로 계산한다 (v3.0.0, back_and_forth D-0043, D42, 15 P8).

원고 문장 `sources` = 도시어(`04_research/research_dossier.json`) claim_id 목록. 라벨 문구와 강약 순서는
`rules/video_rules.yaml script_schema.labels / label_strength_order` 에서만 읽는다.
한 문장이 여러 claim 을 인용하면 **가장 약한 status** 가 그 문장의 라벨이다.
저장: `projects/<pid>/script_labels.json`(파생값 — SSOT 는 도시어). 영상 렌더 표기는 6.95(18).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules
from script.schema import Script

LABELS_FILENAME = "script_labels.json"
DOSSIER_RELPATH = "04_research/research_dossier.json"


class LabelError(ValueError):
    """sources 에 도시어 밖 claim_id, 또는 저장된 라벨이 재계산과 다름."""


class SentenceLabel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = None       # 가장 약한 claim status. sources 가 비면 None
    label: Optional[str] = None        # 규칙 문구(confirmed 는 None)
    claim_ids: list[str] = Field(default_factory=list)


class ScriptLabels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    labels: dict[str, SentenceLabel]

    def counts(self) -> dict[str, int]:
        order = load_rules().script_schema.label_strength_order
        out = {k: 0 for k in reversed(order)}
        for sl in self.labels.values():
            if sl.status is not None:
                out[sl.status] += 1
        return out


def dossier_statuses(dossier_path: Path) -> dict[str, str]:
    """research_dossier.json → {claim_id: status}."""
    from schemas.models import ResearchDossier  # noqa: PLC0415

    d = ResearchDossier.model_validate_json(dossier_path.read_text(encoding="utf-8"))
    return {c.claim_id: (c.status if isinstance(c.status, str) else c.status.value) for c in d.claims}


def compute_labels(script: Script, statuses: dict[str, str]) -> ScriptLabels:
    rules = load_rules().script_schema
    rank = {s: i for i, s in enumerate(rules.label_strength_order)}
    out: dict[str, SentenceLabel] = {}
    unknown: list[str] = []
    for sc in script.scenes:
        for k, s in enumerate(sc.sentences):
            sid = f"{sc.id}_{k}"
            missing = [c for c in s.sources if c not in statuses]
            unknown += [f"{sid}:{c}" for c in missing]
            if missing or not s.sources:
                out[sid] = SentenceLabel(claim_ids=list(s.sources))
                continue
            weakest = min((statuses[c] for c in s.sources), key=lambda st: rank[st])
            out[sid] = SentenceLabel(status=weakest, label=rules.labels[weakest], claim_ids=list(s.sources))
    if unknown:
        raise LabelError(f"sources 에 도시어 밖 claim_id {len(unknown)}건: {', '.join(unknown[:8])}")
    return ScriptLabels(labels=out)


def check_project_labels(proj: Path, script: Script) -> Optional[ScriptLabels]:
    """도시어가 있으면 재계산하고 저장본과 대조한다. 도시어도 저장본도 없으면 None(라벨 없음)."""
    dossier = proj / DOSSIER_RELPATH
    saved = proj / LABELS_FILENAME
    if not dossier.exists():
        if saved.exists():
            raise LabelError(f"{saved.name} 은 있는데 도시어({DOSSIER_RELPATH})가 없다 — 라벨 근거 없음")
        return None
    labels = compute_labels(script, dossier_statuses(dossier))
    if saved.exists():
        stored = ScriptLabels.model_validate(json.loads(saved.read_text(encoding="utf-8")))
        if stored != labels:
            diff = [sid for sid in labels.labels if stored.labels.get(sid) != labels.labels[sid]]
            raise LabelError(f"{saved.name} 이 도시어 재계산과 다르다({len(diff)}문장: {', '.join(diff[:6])}) — 워커 재실행 필요")
    return labels


__all__ = ["LABELS_FILENAME", "LabelError", "ScriptLabels", "SentenceLabel", "check_project_labels",
           "compute_labels", "dossier_statuses"]

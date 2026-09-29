"""문장 검증 라벨 — 코드가 claims.json status 로 계산한다 (v3.0.0 D42 → v3.2.0 D-0051 작업 7, 15 P8).

원고 문장 `sources` = `intake/claims.json` claim_id 목록(18 §3-6). 라벨 문구와 강약 순서는
`rules/video_rules.yaml script_schema.labels / label_strength_order` 에서만 읽는다(`status_label` — 패널·post 카드도 같은 표).
한 문장이 여러 claim 을 인용하면 **가장 약한 status** 가 그 문장의 라벨이다.
저장: `projects/<pid>/script_labels.json`(파생값 — SSOT 는 claims.json).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules
from script.schema import Script

LABELS_FILENAME = "script_labels.json"
CLAIMS_RELPATH = "intake/claims.json"


class LabelError(ValueError):
    """sources 에 claims.json 밖 claim_id, 또는 저장된 라벨이 재계산과 다름."""


def status_label(status: Optional[str]) -> Optional[str]:
    """검증 status → 영상 라벨 문구(규칙 표, verified·corroborated = None). 모르는 status = KeyError(P10)."""
    if status is None:
        return None
    return load_rules().script_schema.labels[status]


class SentenceLabel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = None       # 가장 약한 claim status. sources 가 비면 None
    label: Optional[str] = None        # 규칙 문구(verified·corroborated 는 None)
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


def claim_statuses(claims_path: Path) -> dict[str, str]:
    """intake/claims.json → {claim_id: status}."""
    from schemas.source_models import ClaimsFile  # noqa: PLC0415

    return {c.claim_id: c.status for c in ClaimsFile.model_validate_json(claims_path.read_text(encoding="utf-8")).claims}


def compute_labels(script: Script, statuses: dict[str, str]) -> ScriptLabels:
    rules = load_rules().script_schema
    rank = {s: i for i, s in enumerate(rules.label_strength_order)}
    out: dict[str, SentenceLabel] = {}
    unknown: list[str] = []
    for sc in script.scenes:
        for k, s in enumerate(sc.sentences):
            sid = f"{sc.id}_{k}"
            cids = [c for c in s.sources if not c.startswith("series:")]   # v4.3.0 D-0088 — 데이터 레코드 참조는 claim 이 아니다(라벨 계산 밖)
            missing = [c for c in cids if c not in statuses]
            unknown += [f"{sid}:{c}" for c in missing]
            if missing or not cids:
                out[sid] = SentenceLabel(claim_ids=cids)
                continue
            weakest = min((statuses[c] for c in cids), key=lambda st: rank[st])
            out[sid] = SentenceLabel(status=weakest, label=rules.labels[weakest], claim_ids=cids)
    if unknown:
        raise LabelError(f"sources 에 claims.json 밖 claim_id {len(unknown)}건: {', '.join(unknown[:8])}")
    return ScriptLabels(labels=out)


def check_project_labels(proj: Path, script: Script) -> Optional[ScriptLabels]:
    """claims.json 이 있으면 재계산하고 저장본과 대조한다. claims 도 저장본도 없으면 None(라벨 없음)."""
    claims = proj / CLAIMS_RELPATH
    saved = proj / LABELS_FILENAME
    if not claims.exists():
        if saved.exists():
            raise LabelError(f"{saved.name} 은 있는데 {CLAIMS_RELPATH} 가 없다 — 라벨 근거 없음")
        return None
    labels = compute_labels(script, claim_statuses(claims))
    if saved.exists():
        stored = ScriptLabels.model_validate(json.loads(saved.read_text(encoding="utf-8")))
        if stored != labels:
            diff = [sid for sid in labels.labels if stored.labels.get(sid) != labels.labels[sid]]
            raise LabelError(f"{saved.name} 이 claims.json 재계산과 다르다({len(diff)}문장: {', '.join(diff[:6])}) — 워커 재실행 필요")
    return labels


__all__ = ["CLAIMS_RELPATH", "LABELS_FILENAME", "LabelError", "ScriptLabels", "SentenceLabel", "check_project_labels",
           "claim_statuses", "compute_labels", "status_label"]

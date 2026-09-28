"""import-bundle 오케스트레이션 (v3.5.0, back_and_forth D-0063 작업 2·5, D-0064) — 얇은 호출만(15 P1).

번들 어댑터(`bundle/`)의 순수 함수를 부르고, 6.95 인테이크 경로(`orchestrator.source_intake.add_article`)로 기록한다.
- 출처: `bundle.to_sources.resolve_sources`(가져오기 = `source_intake.fetch_article`, 차단 = `host_blocked`) →
  `intake/sources.json`(사용자 확인 전) + 못 만든 것은 `intake/bundle_import.json unresolved_sources[]`.
- claims 후보: `intake/bundle_claims.json`(검증 워커 `{bundle_hints}` 재료). claims.json 은 쓰지 않는다 — 판정은 verify_sources.
같은 번들을 다시 넣으면 이미 이관된 출처(note 의 번들 id·출처 id)는 건너뛴다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from bundle.load import load_report_bundle
from bundle.to_sources import BUNDLE_CLAIMS_FILE, NOTE_PREFIX, Unresolved, claim_hints, resolve_sources
from orchestrator import source_intake as si

IMPORT_FILE = "bundle_import.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportedSource(_Strict):
    bundle_source_id: str
    source_id: str
    filled_by: list[str]


class BundleImport(_Strict):
    """import-bundle 기록(`intake/bundle_import.json`) — 게이트 ①·소스 확인 화면·provenance 가 읽는다."""

    schema_version: Literal[1] = 1
    bundle_id: str
    bundle_file: str
    generated_at: Optional[str] = None
    producer: str
    fetch: bool
    imported_sources: list[ImportedSource] = Field(default_factory=list)
    skipped_existing: list[str] = Field(default_factory=list)
    unresolved_sources: list[Unresolved] = Field(default_factory=list)
    claim_hints: int = 0
    draft: dict[str, Any] = Field(default_factory=dict)      # 원고·연출 초안 요약(bundle_drafts 가 채운다)


def import_path(pdir: Path) -> Path:
    return pdir / "intake" / IMPORT_FILE


def load_import(pdir: Path) -> Optional[BundleImport]:
    p = import_path(pdir)
    return BundleImport.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


def import_sources(pdir: Path, bundle_file: Path, *, fetch: bool = True) -> BundleImport:
    """번들 → sources.json(기사 레코드, 확인 전) + bundle_claims.json + bundle_import.json."""
    b = load_report_bundle(bundle_file)
    existing = {s.note for s in si.load_sources(pdir).sources if s.note.startswith(NOTE_PREFIX)}
    ok, bad = resolve_sources(b, fetch=si.fetch_article if fetch else None, blocked=si.host_blocked)
    imported, skipped = [], []
    for a in ok:
        if a.note in existing:
            skipped.append(a.bundle_source_id)
            continue
        rec = si.add_article(pdir, publisher=a.publisher, headline=a.headline, published_at=a.published_at, body=a.body,
                             url=a.url, note=a.note, lang="en" if a.headline.isascii() else "ko")
        imported.append(ImportedSource(bundle_source_id=a.bundle_source_id, source_id=rec.id, filled_by=list(a.filled_by)))
    hints = claim_hints(b)
    (pdir / "intake").mkdir(parents=True, exist_ok=True)
    (pdir / "intake" / BUNDLE_CLAIMS_FILE).write_text(hints.model_dump_json(indent=2), encoding="utf-8")
    rec_ = BundleImport(bundle_id=b.report.report_id, bundle_file=str(bundle_file),
                        generated_at=b.generated_at.isoformat() if b.generated_at else None,
                        producer=f"{b.producer.system} {b.producer.version}", fetch=fetch, imported_sources=imported,
                        skipped_existing=skipped, unresolved_sources=bad, claim_hints=len(hints.hints))
    import_path(pdir).write_text(rec_.model_dump_json(indent=2), encoding="utf-8")
    return rec_


def write_drafts(pdir: Path, bundle_file: Path) -> dict[str, Any]:
    """작업 3·4 — `script.draft.yaml`·`script.draft.notes.json`·`intake/bundle_materials.json`·`direction.draft.yaml`.
    최종 `script.yaml`·`direction.yaml` 은 쓰지 않는다(원고는 ScriptWorker, 연출은 DirectorWorker — 15 P8)."""
    from bundle.entities import join_entities  # noqa: PLC0415
    from bundle.to_direction import MATERIALS_FILE, build_direction_draft, build_materials, dump_direction_draft  # noqa: PLC0415
    from bundle.to_script import build_draft, dump_draft_yaml  # noqa: PLC0415
    from engine.entities import load_entities  # noqa: PLC0415

    b = load_report_bundle(bundle_file)
    reg = load_entities()
    join = join_entities(b, reg)
    script, notes = build_draft(b, join, reg)
    (pdir / "script.draft.yaml").write_text(dump_draft_yaml(script, notes), encoding="utf-8")
    (pdir / "script.draft.notes.json").write_text(notes.model_dump_json(indent=2), encoding="utf-8")
    scene_of = {sec: bd.scene for bd in notes.boundaries for sec in bd.sections}
    by_scene: dict[str, list[str]] = {}
    for sid, ids in notes.mentions.items():
        seen = by_scene.setdefault(sid.rsplit("_", 1)[0], [])
        seen += [i for i in ids if i not in seen]
    mat = build_materials(b, join, reg, scene_of, by_scene)
    (pdir / "intake").mkdir(parents=True, exist_ok=True)
    (pdir / "intake" / MATERIALS_FILE).write_text(mat.model_dump_json(indent=2), encoding="utf-8")
    try:
        d = build_direction_draft(mat, [sc.id for sc in script.scenes])
        (pdir / "direction.draft.yaml").write_text(dump_direction_draft(d, mat), encoding="utf-8")
        ddraft = "direction.draft.yaml"
    except ValueError as ex:          # 지도 마커 없음 — 초안 없이 기록(연출가가 처음부터)
        ddraft = f"없음: {ex}"
    return {"sections": notes.sections, "scenes": notes.scenes, "rewrite_required": len(notes.rewrite_required),
            "unmatched": len(notes.unmatched), "date_timeline": sum(v == "timeline" for v in notes.date_sources.values()),
            "date_report": sum(v == "report" for v in notes.date_sources.values()), "panels": len(mat.panels),
            "unsupported_charts": len(mat.unsupported), "direction_draft": ddraft}


def import_bundle(pdir: Path, bundle_file: Path, *, fetch: bool = True) -> BundleImport:
    """import-bundle 전체(작업 1~4): 번들을 프로젝트에 보관 → 출처·claim 후보 → 원고·연출 초안. 게이트 ① 진입 조건
    (claims.json)은 사용자 확인 → verify_sources 뒤에 충족된다(18 §7 — 확인 없이 검증하지 않는다)."""
    kept = pdir / "intake" / "files" / bundle_file.name
    kept.parent.mkdir(parents=True, exist_ok=True)
    if kept.resolve() != bundle_file.resolve():
        kept.write_bytes(bundle_file.read_bytes())
    r = import_sources(pdir, kept, fetch=fetch)
    r = r.model_copy(update={"draft": write_drafts(pdir, kept)})
    import_path(pdir).write_text(r.model_dump_json(indent=2), encoding="utf-8")
    return r


def import_view_lines(pdir: Path) -> list[str]:
    """게이트 ①·소스 확인 화면의 번들 출처 줄 — 이관 수·못 만든 출처 사유(사용자가 add-source 로 채우는 입구, D-0064 쟁점 2)."""
    r = load_import(pdir)
    if r is None:
        return []
    d = r.draft
    out = [f"번들 {r.bundle_id} ({r.producer}) — 출처 이관 {len(r.imported_sources)}건 · 못 만든 출처 {len(r.unresolved_sources)}건"
           f" · claim 후보 {r.claim_hints}건 (fetch {'켬' if r.fetch else '끔'})"]
    if d:
        out.append(f"  초안 섹션 {d.get('sections')} → 장면 {d.get('scenes')} · rewrite_required {d.get('rewrite_required')}"
                   f" · 엔티티 unmatched {d.get('unmatched')} · 패널 {d.get('panels')} · 패널 없는 차트 {d.get('unsupported_charts')}")
    out += [f"  이관 {i.source_id} ← {i.bundle_source_id} ({'+'.join(i.filled_by)})" for i in r.imported_sources]
    out += [f"  미해결 {u.bundle_source_id}: {u.reason} — {u.raw[:80]}  → add-source 로 직접 넣을 수 있다" for u in r.unresolved_sources]
    return out


def dump(r: BundleImport) -> str:
    return json.dumps({"bundle": r.bundle_id, "imported": len(r.imported_sources), "unresolved": len(r.unresolved_sources),
                       "claim_hints": r.claim_hints, **r.draft}, ensure_ascii=False)


__all__ = ["BundleImport", "IMPORT_FILE", "import_bundle", "import_path", "import_sources", "import_view_lines", "load_import",
           "write_drafts"]

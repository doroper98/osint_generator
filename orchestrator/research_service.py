"""build-research 오케스트레이션 (v3.2.0, 17 §5.1, back_and_forth D-0051 작업 7·11).

SOURCE_VERIFY 에서 `intake/claims.json`(소스 검증 결과)이 있어야 ResearchWorker 1회 → `facts.json`(Facts) → RESEARCH 전이.
사용자 입출력은 호출자(CLI·Command Center) 몫, 본 모듈은 결과/예외로만 소통한다.
옛 ResearchDossier·research_io·source_completeness_report 진입 조건은 삭제(D52, P2).
"""

from __future__ import annotations

import argparse
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import resume_project, transition_state
from schemas.models import ProjectManifest, ProjectState, TaskQueueItem
from schemas.source_models import check_claim_sources


class ResearchError(RuntimeError):
    """build-research 흐름 실패. kind: state(상태·claims 없음) / worker / persist."""

    def __init__(self, message: str, *, kind: str, errors: Optional[list[str]] = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.errors = errors or []


def _state_str(state) -> str:  # noqa: ANN001
    return state.value if hasattr(state, "value") else str(state)


def run_research_worker(project_id: str, *, backend: str = "claude", force: bool = False,
                        cfg: Optional[AppConfig] = None) -> tuple[ProjectManifest, list[str], bool]:
    """SOURCE_VERIFY + 유효한 claims.json → Facts → RESEARCH. (manifest, outputs, skipped)."""
    from orchestrator.source_intake import load_sources  # noqa: PLC0415
    from orchestrator.source_verify import load_claims  # noqa: PLC0415
    from script.schema import Facts  # noqa: PLC0415
    from workers.research_worker import FACTS_FILENAME, ResearchWorker, check_facts  # noqa: PLC0415

    cfg = cfg or load_config()
    manifest = resume_project(project_id, cfg)
    current = _state_str(manifest.current_state)
    pdir = project_dir(project_id, cfg)
    if current != ProjectState.SOURCE_VERIFY.value:
        raise ResearchError(f"현재 상태 '{current}' 에서는 build-research 를 실행할 수 없습니다(허용: source_verify)", kind="state")
    try:
        claims = load_claims(pdir)
    except ValueError as ex:
        raise ResearchError(f"claims.json 손상: {ex}", kind="state") from ex
    if claims is None or not claims.claims:
        raise ResearchError("claims.json 이 없다 — verify-sources 먼저(18 §7)", kind="state")
    ref_errs = check_claim_sources(claims, load_sources(pdir))
    if ref_errs:
        raise ResearchError("claims.json 이 sources.json 과 맞지 않는다", kind="state", errors=ref_errs)

    facts_p = pdir / FACTS_FILENAME
    skipped = False
    if facts_p.exists() and not force:
        try:
            skipped = not check_facts(Facts.model_validate_json(facts_p.read_text(encoding="utf-8")), claims)
        except ValueError:
            skipped = False
    if skipped:
        outputs = [str(facts_p)]
    else:
        task = TaskQueueItem(task_id=f"research-{project_id}", task_type="research", assigned_worker="research",
                             description="ResearchWorker 1회(claims → facts)",
                             input_refs=["intake/sources.json", "intake/claims.json", "project_manifest.json"],
                             output_refs=[FACTS_FILENAME])
        worker = ResearchWorker()
        worker.llm_backend = backend
        wargs = argparse.Namespace(project_id=project_id, task_id=task.task_id, projects_root=str(pdir.parent))
        result = worker.run(wargs, task)
        try:
            worker.write_result(wargs, result)
        except OSError:
            pass
        st = _state_str(result.status)
        if st != "completed":
            raise ResearchError(f"ResearchWorker 실패: status={st}", kind="worker", errors=list(result.errors))
        outputs = list(result.outputs)
        try:
            errs = check_facts(Facts.model_validate_json(facts_p.read_text(encoding="utf-8")), claims)
        except (OSError, ValueError) as e:
            raise ResearchError(f"facts.json 영속화 검증 실패: {e}", kind="persist") from e
        if errs:
            raise ResearchError("facts.json 계약 위반", kind="persist", errors=errs)
    manifest = transition_state(manifest, ProjectState.RESEARCH,
                                reason="ResearchWorker 성공(facts.json)" if not skipped else "기존 facts.json 재사용", cfg=cfg)
    return manifest, outputs, skipped


__all__ = ["run_research_worker", "ResearchError"]

"""상태별 진행 (v3.0.0, docs/handoff/16 §2·§4·§5, back_and_forth D-0040 작업 6).

Command Center(TUI)와 CLI(`orchestrator.main advance/approve/reject`)가 같은 함수를 쓴다.
- 엔진 상태(VOICE_TIMELINE·ASSETS·DIRECTION·PREVIEW_QA·RENDER·AUDIO_MIX·DELIVER): `engine_service` 로
  단계를 돌리고, 전부 ok 면 다음 상태로 간다. **하나라도 ok 가 아니면(drops·errors) 그 상태에 머문다**(15 P6).
- 승인 게이트(SCRIPT_APPROVAL·PREVIEW_APPROVAL): 여기서 진행하지 않는다 — approve / reject 만.
- LLM·사람 상태(CREATED~SCRIPT_DRAFT): 해당 명령(plan-intake·submit-intake·build-source-registry·
  build-research-dossier·build-script)이 진행한다. `advance` 는 안내 오류를 낸다.
StageResult 전체는 `logs/stages/NN_<stage>.json`, 요약은 manifest `stage_records`(오케스트레이터 자기 기록 —
엔진 입력 파일이 아니다, 15 P1).
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from orchestrator import engine_service
from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import load_manifest, record_stage, transition_state
from orchestrator.state_machine import GATES, coerce, next_state
from schemas.engine_models import StageResult
from schemas.models import ProjectManifest, ProjectState, StageRecord

LLM_STATE_COMMANDS: dict[ProjectState, str] = {
    ProjectState.CREATED: "plan-intake",
    ProjectState.INTAKE: "plan-intake → submit-intake",
    ProjectState.SOURCE_VERIFY: "build-source-registry → build-research-dossier 또는 import-bundle",
    ProjectState.RESEARCH: "build-script",
    ProjectState.SCRIPT_DRAFT: "원고 확정 후 transition --to script_approval",
}


class PipelineError(RuntimeError):
    """지금 상태에서 advance 로 진행할 수 없을 때(게이트·LLM 단계·종료)."""


def next_action(state: ProjectState | str) -> str:
    st = coerce(state)
    if st == ProjectState.DONE:
        return "완료"
    if st in GATES:
        return f"승인 대기 — approve --gate {st.value} / reject --gate {st.value} --to …"
    if st in engine_service.STATE_STAGES:
        return f"advance — 엔진 {', '.join(engine_service.STATE_STAGES[st])}"
    return LLM_STATE_COMMANDS.get(st, "-")


def _log_path(pdir: Path, n: int, stage: str) -> Path:
    return pdir / "logs" / "stages" / f"{n:02d}_{stage}.json"


def advance(project_id: str, cfg: Optional[AppConfig] = None, *, jobs: Optional[int] = None,
            runner: Callable = subprocess.run,
            on_result: Optional[Callable[[StageResult], None]] = None,
            workers: Optional[dict] = None, backend: str = "claude") -> tuple[ProjectManifest, list[StageResult]]:
    """현재 상태의 단계를 돌리고, 전부 ok 면 다음 상태로 전이한다.
    DIRECTION·PREVIEW_QA 는 AI 연출·시각 검수 루프(orchestrator.ai_direction, v3.1.0)를 포함한다."""
    from orchestrator import ai_direction  # noqa: PLC0415

    cfg = cfg or load_config()
    manifest = load_manifest(project_id, cfg)
    st = coerce(manifest.current_state)
    if st == ProjectState.DONE:
        raise PipelineError("이미 done")
    if st in GATES:
        raise PipelineError(f"'{st.value}' 는 승인 게이트 — {next_action(st)}")
    stages = engine_service.stages_for(st)
    if not stages:
        raise PipelineError(f"'{st.value}' 는 LLM·사람 단계 — {next_action(st)}")
    pdir = project_dir(project_id, cfg)
    results: list[StageResult] = []
    box = {"m": manifest}

    def record(res: StageResult, stage: Optional[str] = None) -> None:
        stage = stage or res.stage
        results.append(res)
        log = _log_path(pdir, len(box["m"].stage_records) + 1, stage)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(json.dumps(res.model_dump(), ensure_ascii=False, indent=1), encoding="utf-8")
        box["m"] = record_stage(box["m"], StageRecord(
            state=st, stage=stage, ok=res.ok, artifacts=res.artifacts, errors=res.errors,
            drops=len(res.drops), log=str(log.relative_to(pdir))), cfg)
        if on_result is not None:
            on_result(res)

    def run_engine(stage: str) -> StageResult:
        res = engine_service.run_stage(pdir, stage, jobs=jobs if jobs is not None else cfg.engine.jobs, runner=runner)  # type: ignore[arg-type]
        return res.model_copy(update={"stage": stage})   # 기록 단계명 = 엔진 서비스 단계명

    if st == ProjectState.DIRECTION and not (pdir / "direction.yaml").exists():
        res = ai_direction.run_worker("director", pdir, backend, workers)   # 17 §5.3 — 연출 파일이 없을 때만
        record(res)
        if not res.ok:
            return box["m"], results
    if st == ProjectState.PREVIEW_QA:
        ok, summary = ai_direction.qa_loop(pdir, run_engine, record, backend, workers)
        if not ok:
            return box["m"], results                  # 머문다(15 P6)
        reason = f"preview ok · 검수 {len(summary['verdicts'])}회 · 수정 {summary['iterations']}회"
    else:
        for stage in stages:
            res = run_engine(stage)
            record(res, stage)
            if not res.ok:
                return box["m"], results              # 머문다(15 P6) — 폴백·다음 단계 없음
        reason = f"engine {', '.join(stages)} ok"
    nxt = next_state(st)
    assert nxt is not None
    manifest = transition_state(box["m"], nxt, reason=reason, cfg=cfg)
    return manifest, results


__all__ = ["PipelineError", "advance", "next_action", "LLM_STATE_COMMANDS"]

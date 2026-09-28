"""AI 연출·시각 검수 루프 (v3.1.0, docs/handoff/16 §2 DIRECTION → PREVIEW_QA, 17 §1, back_and_forth D-0047 작업 8).

- DIRECTION: 연출 파일이 없으면 DirectorWorker(LLM)가 쓴다. 사람이 쓴 direction.yaml 이 있으면 그대로 쓴다.
- PREVIEW_QA: preview(결정적 검사 checks.json 포함). AI 연출(direction.meta.json origin=ai)이면
    checks hard > 0 → ReviseDirectionWorker(검사 오류만) → 재검증·재프리뷰
    checks hard 0 → VisualQAWorker(시트 이미지) → revise 면 ReviseDirectionWorker → 재프리뷰 → 재검수
  를 **최대 rules qa_checks.visual_qa_loop_max 회** 돈다. 루프 제어·종료는 코드가 한다(AP-V6-2·5 — LLM 이 정하지 않음).
  사람 연출은 검수 루프를 돌지 않는다(골든 연출을 LLM 이 고치지 않게) — 사람이 게이트 ②에서 본다.
- 판정·코멘트는 manifest stage_records 와 prev/ 파일에만 남는다. 프롬프트·규칙 자동 반영 금지(15 P11).
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from rules import load_rules
from schemas.engine_models import StageResult
from schemas.models import TaskQueueItem

WorkerFactory = Callable[[], object]


def _workers() -> dict[str, WorkerFactory]:
    from workers.director_worker import DirectorWorker  # noqa: PLC0415
    from workers.revise_direction_worker import ReviseDirectionWorker  # noqa: PLC0415
    from workers.visual_qa_worker import VisualQAWorker  # noqa: PLC0415

    return {"director": DirectorWorker, "visual_qa": VisualQAWorker, "revise_direction": ReviseDirectionWorker}


def is_ai_direction(pdir: Path) -> bool:
    p = pdir / "direction.meta.json"
    return p.exists() and json.loads(p.read_text(encoding="utf-8")).get("origin") == "ai"


def _refs(name: str, pdir: Path) -> list[str]:
    from workers.direction_io import next_version  # noqa: PLC0415

    n = next_version(pdir, "direction", ".yaml")
    if name == "director":
        return ["direction.yaml", f"direction.v{n}.yaml", "direction.meta.json"]
    if name == "revise_direction":
        return ["direction.yaml", f"direction.v{n}.yaml", f"prev/revision.v{n}.json"]
    q = next_version(pdir / "prev", "qa_verdict", ".json")
    return [f"prev/qa_verdict.v{q}.json"]


def run_worker(name: str, pdir: Path, backend: str = "claude", workers: Optional[dict[str, WorkerFactory]] = None) -> StageResult:
    """워커 1회(재요청은 워커가 1회까지) → StageResult 모양으로(기록·전파를 엔진 단계와 같게)."""
    w = (workers or _workers())[name]()
    w.llm_backend = backend  # type: ignore[attr-defined]
    task = TaskQueueItem(task_id=f"{name}-{pdir.name}", task_type=name, assigned_worker=name, description=f"{name} 1회",
                         input_refs=[], output_refs=_refs(name, pdir))
    args = argparse.Namespace(project_id=pdir.name, task_id=task.task_id, projects_root=str(pdir.parent))
    try:
        res = w.run(args, task)  # type: ignore[attr-defined]
    except (OSError, ValueError, KeyError) as ex:        # 입력 부재 등 — 조용히 넘기지 않고 실패로 기록(15 P6)
        return StageResult(ok=False, stage=name, errors=[f"{name} 입력 오류: {type(ex).__name__}: {ex}"])
    try:
        w.write_result(args, res)  # type: ignore[attr-defined]
    except OSError:
        pass
    status = res.status if isinstance(res.status, str) else res.status.value
    ok = status == "completed"
    return StageResult(ok=ok, stage=name, artifacts={f"out{i}": o for i, o in enumerate(res.outputs)},
                       errors=[] if ok else list(res.errors) or [f"{name} 실패"])


def qa_loop(pdir: Path, run_engine: Callable[[str], StageResult], record: Callable[[StageResult], None],
            backend: str = "claude", workers: Optional[dict[str, WorkerFactory]] = None) -> tuple[bool, dict]:
    """PREVIEW_QA 한 번. (다음 상태로 가도 되는가, 요약). run_engine(stage) = engine_service 호출."""
    loop_max = load_rules().qa_checks.visual_qa_loop_max
    summary: dict = {"iterations": 0, "verdicts": [], "loop_max": loop_max}
    ai = is_ai_direction(pdir)
    for it in range(loop_max + 1):
        prev = run_engine("preview")
        record(prev)
        chk_path = pdir / "prev" / "checks.json"
        hard = json.loads(chk_path.read_text(encoding="utf-8"))["hard"] if chk_path.exists() else None
        if not prev.ok and hard in (None, 0):
            return False, summary                      # 검사 밖 오류(렌더·권리) — 머문다(15 P6)
        if not ai:
            return prev.ok, summary                     # 사람 연출: 검수 루프 없음
        if prev.ok:
            qa = run_worker("visual_qa", pdir, backend, workers)
            record(qa)
            if not qa.ok:
                return False, summary
            from workers.revise_direction_worker import latest  # noqa: PLC0415
            from engine.qa import QAVerdict  # noqa: PLC0415

            v = QAVerdict.model_validate_json(latest(pdir / "prev", "qa_verdict", ".json").read_text(encoding="utf-8"))  # type: ignore[union-attr]
            summary["verdicts"].append({"verdict": v.verdict, "hard": v.hard_count(), "issues": len(v.issues)})
            if v.verdict == "pass":
                return True, summary
        if it == loop_max:                               # 상한 — 잔여 이슈와 함께 게이트 ②로(hard 검사가 남으면 머묾)
            return prev.ok, summary
        rev = run_worker("revise_direction", pdir, backend, workers)
        record(rev)
        if not rev.ok:
            return False, summary
        summary["iterations"] += 1
        val = run_engine("validate")                    # 수정본을 렌더 입력 경로로 점검(17 §1 engine.validate)
        record(val)
        if not val.ok:
            return False, summary
    return False, summary


__all__ = ["is_ai_direction", "qa_loop", "run_worker"]

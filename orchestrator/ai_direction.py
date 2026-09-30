"""AI 연출·시각 검수 루프 (v3.1.0, docs/handoff/16 §2 DIRECTION → PREVIEW_QA, 17 §1, back_and_forth D-0047 작업 8).

- DIRECTION: 연출 파일이 없으면 DirectorWorker(LLM)가 쓴다. 사람이 쓴 direction.yaml 이 있으면 그대로 쓴다.
- PREVIEW_QA: preview(결정적 검사 checks.json 포함). AI 연출(direction.meta.json origin=ai)이면
    checks hard > 0 → ReviseDirectionWorker(검사 오류만) → 재검증·재프리뷰
    checks hard 0 → VisualQAWorker(시트 이미지) → revise 면 ReviseDirectionWorker → 재프리뷰 → 재검수
  를 **최대 rules qa_checks.visual_qa_loop_max 회** 돈다. 루프 제어·종료는 코드가 한다(AP-V6-2·5 — LLM 이 정하지 않음).
  사람 연출은 검수 루프를 돌지 않는다(골든 연출을 LLM 이 고치지 않게) — 사람이 게이트 ②에서 본다.
- 회차 기록 prev/qa_loop.json(판·checks·검수·수정, 판별 시트 prev/sheet.v{n}.jpg) — 수정 워커의 루프 이력 입력(D-0049 쟁점 2),
  게이트 ② 판 목록, provenance 가 함께 쓴다. 상한 도달 시 rules loop_pick_order 최선 판을 되돌린다(쟁점 3).
- 판정·코멘트는 manifest stage_records 와 prev/ 파일에만 남는다. 프롬프트·규칙 자동 반영 금지(15 P11).
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from rules import load_rules
from schemas.engine_models import StageResult
from schemas.models import TaskQueueItem

if TYPE_CHECKING:
    from engine.qa import QALoopRecord, QALoopRound

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


def _save_record(pdir: Path, rec: "QALoopRecord") -> None:
    (pdir / "prev" / "qa_loop.json").write_text(rec.model_dump_json(indent=1), encoding="utf-8")


def load_record(pdir: Path) -> Optional["QALoopRecord"]:
    from engine.qa import QALoopRecord  # noqa: PLC0415

    p = pdir / "prev" / "qa_loop.json"
    return QALoopRecord.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


def _archive_round(pdir: Path, version: int, hard: int) -> "QALoopRound":
    """이번 프리뷰의 checks·시트를 판 번호로 보관(prev/ 산출물 복사 — 엔진 입력은 건드리지 않음)."""
    from engine.qa import QALoopRound  # noqa: PLC0415

    prev = pdir / "prev"
    for src, dst in (("checks.json", f"checks.v{version}.json"), ("sheet.jpg", f"sheet.v{version}.jpg")):
        if (prev / src).exists():
            shutil.copyfile(prev / src, prev / dst)
    return QALoopRound(version=version, checks_hard=hard, checks_file=f"checks.v{version}.json", sheet=f"sheet.v{version}.jpg")


def qa_loop(pdir: Path, run_engine: Callable[[str], StageResult], record: Callable[[StageResult], None],
            backend: str = "claude", workers: Optional[dict[str, WorkerFactory]] = None,
            loop_max: Optional[int] = None) -> tuple[bool, dict]:
    """PREVIEW_QA 한 번. (다음 상태로 가도 되는가, 요약). run_engine(stage) = engine_service 호출.
    회차마다 prev/qa_loop.json 에 판·검사·검수·수정 기록(수정 워커 입력·게이트 ② 판 목록·provenance 공용, D-0049).
    상한 도달 시 rules qa_checks.loop_pick_order 사전식 최소 판을 direction.yaml 로 되돌리고 다시 프리뷰한다(D-0049 쟁점 3).
    loop_max = 이번 호출의 수정 회차 수(None = rules qa_checks.visual_qa_loop_max). 상한 밖 추가 회차는 감독 결정이 있을 때만(v5.2.0 D-0132 §3)."""
    from engine.qa import QALoopPick, QALoopRecord, QAVerdict, pick_best  # noqa: PLC0415
    from workers.direction_io import current_version, restore_version  # noqa: PLC0415
    from workers.revise_direction_worker import latest  # noqa: PLC0415

    qc = load_rules().qa_checks
    loop_max = qc.visual_qa_loop_max if loop_max is None else loop_max
    summary: dict = {"iterations": 0, "verdicts": [], "loop_max": loop_max}
    ai = is_ai_direction(pdir)
    rec = QALoopRecord()
    for it in range(loop_max + 1):
        prev = run_engine("preview")
        record(prev)
        chk_path = pdir / "prev" / "checks.json"
        hard = json.loads(chk_path.read_text(encoding="utf-8"))["hard"] if chk_path.exists() else None
        if not prev.ok and hard in (None, 0):
            return False, summary                      # 검사 밖 오류(렌더·권리) — 머문다(15 P6)
        if not ai:
            return prev.ok, summary                     # 사람 연출: 검수 루프 없음
        ver = current_version(pdir)
        rnd = _archive_round(pdir, ver if ver is not None else 0, hard or 0)
        rec.rounds.append(rnd)
        _save_record(pdir, rec)
        if prev.ok:
            qa = run_worker("visual_qa", pdir, backend, workers)
            record(qa)
            if not qa.ok:
                return False, summary
            vp = latest(pdir / "prev", "qa_verdict", ".json")
            v = QAVerdict.model_validate_json(vp.read_text(encoding="utf-8"))  # type: ignore[union-attr]
            rnd.qa, rnd.qa_hard, rnd.qa_soft = vp.name, v.hard_count(), len(v.issues) - v.hard_count()  # type: ignore[union-attr]
            _save_record(pdir, rec)
            summary["verdicts"].append({"verdict": v.verdict, "hard": v.hard_count(), "issues": len(v.issues)})
            if v.verdict == "pass":
                rec.selected = QALoopPick(version=rnd.version, by="code", reason="검수 pass")
                _save_record(pdir, rec)
                summary["selected"] = rnd.version
                return True, summary
        if it == loop_max:                               # 상한 — 최선 판을 골라 게이트 ②로(hard 검사가 남으면 머묾)
            best = pick_best(rec.rounds, list(qc.loop_pick_order))
            why = (f"상한 {loop_max}회 도달 — {'·'.join(qc.loop_pick_order)} 사전식 최소 "
                   f"(checks hard {best.checks_hard}, 검수 hard {best.qa_hard}, soft {best.qa_soft})")
            rec.selected = QALoopPick(version=best.version, by="code", reason=why)
            _save_record(pdir, rec)
            summary["selected"] = best.version
            if best.version != rnd.version and best.version > 0:
                restore_version(pdir, best.version)
                again = run_engine("preview")           # prev/ 가 고른 판을 보이게(시트·provenance·checks)
                record(again)
                return again.ok, summary
            return prev.ok, summary
        rev = run_worker("revise_direction", pdir, backend, workers)
        record(rev)
        if not rev.ok:
            return False, summary
        rp = latest(pdir / "prev", "revision", ".json")
        rnd.revision = rp.name if rp is not None else None
        _save_record(pdir, rec)
        summary["iterations"] += 1
        val = run_engine("validate")                    # 수정본을 렌더 입력 경로로 점검(17 §1 engine.validate)
        record(val)
        if not val.ok:
            return False, summary
    return False, summary


__all__ = ["is_ai_direction", "load_record", "qa_loop", "run_worker"]

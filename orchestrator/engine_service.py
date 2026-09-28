"""엔진 어댑터 (v3.0.0, docs/handoff/16 §4, 15 P1, back_and_forth D-0040 작업 4).

오케스트레이터는 엔진을 **서브프로세스 CLI** 로만 부른다. 각 CLI 는 표준 출력 마지막 줄에
`StageResult` JSON 을 낸다(`schemas/engine_models.py`). 이 모듈은
  1. 단계 → CLI 명령을 고르고(`STAGE_COMMANDS`),
  2. 실행해 마지막 줄 JSON 을 `StageResult` 로 검증하고,
  3. 종료 코드·단계 이름·JSON 이 서로 맞지 않으면 ok=False 로 돌려준다(15 P6 — 조용한 성공 없음).
**엔진 입력 파일(script.yaml·direction.yaml·plan.json·자산)을 만들거나 고치지 않는다**(15 P1,
`tests/test_engine_service.py` 가 AST 로 검사). 입력은 LLM 단계·사용자가 쓴 파일뿐이다.

16 §4 CLI 대응 (실측, v3.0.0):
| stage              | 명령                                   | 비고 |
| plan               | python -m script.plan <proj>           | plan.json, tts/ |
| assets             | python -m geo.prep <proj>              | 인물·국기·미디어는 tools/fetch_data(사람 준비) |
| direction_validate | python -m script.lint <proj>           | `engine.validate` 는 6.9(17 §2). 그 전까지 원고 Script 로드 + 린트. 연출·레지스트리·예약영역 검사는 preview 의 load_project |
| preview            | python -m engine.render <proj> --preview auto |
| render             | python -m engine.render <proj> --jobs N |
| mix                | python -m audio.mix <proj>             |
| deliver            | python -m engine.mux <proj>            | final.mp4·srt·description·provenance.json |
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from schemas.engine_models import StageResult
from schemas.models import ProjectState

REPO = Path(__file__).resolve().parent.parent

Stage = Literal["plan", "assets", "direction_validate", "preview", "render", "mix", "deliver"]

# 단계 → (모듈, CLI 가 StageResult.stage 에 적는 이름)
STAGE_COMMANDS: dict[str, tuple[str, str]] = {
    "plan": ("script.plan", "plan"),
    "assets": ("geo.prep", "geo"),
    "direction_validate": ("script.lint", "lint"),
    "preview": ("engine.render", "preview"),
    "render": ("engine.render", "render"),
    "mix": ("audio.mix", "mix"),
    "deliver": ("engine.mux", "mux"),
}

# 상태 → 그 상태에서 돌리는 엔진 단계(16 §2). 목록에 없는 상태는 LLM·사람 단계다.
STATE_STAGES: dict[ProjectState, tuple[str, ...]] = {
    ProjectState.VOICE_TIMELINE: ("plan",),
    ProjectState.ASSETS: ("assets",),
    ProjectState.DIRECTION: ("direction_validate",),
    ProjectState.PREVIEW_QA: ("preview",),
    ProjectState.RENDER: ("render",),
    ProjectState.AUDIO_MIX: ("mix",),
    ProjectState.DELIVER: ("deliver",),
}

Runner = Callable[..., subprocess.CompletedProcess]


def build_command(project_dir: Path, stage: str, *, jobs: int | None = None,
                  preview: str = "auto", extra: Sequence[str] = ()) -> list[str]:
    if stage not in STAGE_COMMANDS:
        raise ValueError(f"알 수 없는 엔진 단계 {stage!r} — 허용: {', '.join(STAGE_COMMANDS)}")
    module, _ = STAGE_COMMANDS[stage]
    cmd = [sys.executable, "-m", module, str(project_dir)]
    if stage == "preview":
        cmd += ["--preview", preview]
    elif stage == "render" and jobs is not None:
        cmd += ["--jobs", str(jobs)]
    return cmd + list(extra)


def parse_result(stage: str, returncode: int, stdout: str, stderr: str) -> StageResult:
    """마지막 줄 JSON → StageResult. 모순(종료 코드·단계 이름)은 ok=False 로(15 P6)."""
    tail = [ln for ln in stdout.splitlines() if ln.strip()]
    err_tail = stderr.strip().splitlines()[-5:]
    if not tail:
        return StageResult(ok=False, stage=stage, errors=[f"{stage}: StageResult JSON 없음 (exit {returncode})", *err_tail])
    try:
        res = StageResult.model_validate(json.loads(tail[-1]))
    except (json.JSONDecodeError, ValidationError) as ex:
        return StageResult(ok=False, stage=stage, errors=[f"{stage}: 마지막 줄이 StageResult 가 아님 — {ex}", *err_tail])
    expected = STAGE_COMMANDS[stage][1]
    problems: list[str] = []
    if res.stage != expected:
        problems.append(f"{stage}: CLI 가 stage={res.stage!r} 를 냈다(기대 {expected!r})")
    if res.ok and returncode != 0:
        problems.append(f"{stage}: ok=True 인데 종료 코드 {returncode}")
    if not res.ok and returncode == 0:
        problems.append(f"{stage}: ok=False 인데 종료 코드 0")
    if problems:
        return res.model_copy(update={"ok": False, "errors": [*res.errors, *problems]})
    return res


def run_stage(project_dir: Path, stage: Stage, *, jobs: int | None = None, preview: str = "auto",
              extra: Sequence[str] = (), runner: Runner = subprocess.run) -> StageResult:
    """엔진 단계 하나를 서브프로세스로 돌려 StageResult 를 돌려준다(16 §4)."""
    cmd = build_command(Path(project_dir).resolve(), stage, jobs=jobs, preview=preview, extra=extra)
    proc = runner(cmd, cwd=REPO, capture_output=True, text=True, check=False)
    return parse_result(stage, proc.returncode, proc.stdout or "", proc.stderr or "")


def stages_for(state: ProjectState | str) -> tuple[str, ...]:
    st = state if isinstance(state, ProjectState) else ProjectState(state)
    return STATE_STAGES.get(st, ())


__all__ = ["STAGE_COMMANDS", "STATE_STAGES", "Stage", "build_command", "parse_result", "run_stage", "stages_for"]

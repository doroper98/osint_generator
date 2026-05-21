"""orchestrator CLI 진입점.

서브커맨드
----------
- command-center --project {pid}            : Command Center TUI 진입
- new-project {pid} --title ... --category .: 새 프로젝트 생성
- resume {pid}                              : 기존 프로젝트 manifest 확인
- transition {pid} --to {state} [--reason]  : 상태 전이
- plan-intake {pid} [--backend claude|codex]: IntakePlannerWorker 호출 + 인테이크 상태 전이
- submit-intake {pid} --file path/to/source_intake.json
                                            : SourceIntake 영속화 + source_collecting 전이
- approve --project {pid} --gate ...        : Review Gate 승인 기록 (Phase 11)
- version                                   : 현재 버전 출력
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestrator import __version__
from orchestrator.command_center import run_command_center
from orchestrator.project_manager import (
    new_project,
    resume_project,
    transition_state,
)
from schemas.models import (
    Category,
    ProjectManifest,
    ProjectState,
    SourceIntake,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="longform-briefing-pipeline orchestrator CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    cc = sub.add_parser("command-center", help="Command Center TUI 진입")
    cc.add_argument("--project", required=True, help="project_id")

    npj = sub.add_parser("new-project", help="새 프로젝트 생성")
    npj.add_argument("project_id", help="project_id (영문 소문자/숫자/하이픈)")
    npj.add_argument("--title", required=True, help="프로젝트 제목")
    npj.add_argument(
        "--category",
        required=True,
        choices=[c.value for c in Category],
        help="주제 카테고리",
    )
    npj.add_argument("--duration-min", type=int, default=18, help="목표 영상 길이 (분)")
    npj.add_argument("--topic-summary", default="", help="주제 요약")

    rsm = sub.add_parser("resume", help="기존 프로젝트 manifest 출력")
    rsm.add_argument("project_id", help="project_id")

    tr = sub.add_parser("transition", help="상태 전이")
    tr.add_argument("project_id", help="project_id")
    tr.add_argument(
        "--to",
        required=True,
        choices=[s.value for s in ProjectState],
        help="목표 상태",
    )
    tr.add_argument("--reason", default="", help="전이 사유")

    pin = sub.add_parser(
        "plan-intake",
        help="IntakePlannerWorker 호출 + intake_planning → intake_pending_user 전이",
    )
    pin.add_argument("project_id", help="project_id")
    pin.add_argument(
        "--backend",
        choices=["claude", "codex"],
        default="claude",
        help="LLM backend (기본: claude)",
    )

    sin = sub.add_parser(
        "submit-intake",
        help="SourceIntake JSON 파일을 영속화 + source_collecting 전이",
    )
    sin.add_argument("project_id", help="project_id")
    sin.add_argument(
        "--file",
        required=True,
        help="검증된 source_intake.json 후보 파일 경로 (SourceIntake 스키마)",
    )
    sin.add_argument("--reason", default="CLI submit-intake", help="전이 사유")

    apv = sub.add_parser("approve", help="Review Gate 승인 기록 (Phase 11)")
    apv.add_argument("--project", required=True)
    apv.add_argument("--gate", required=True)
    apv.add_argument("--comment", default="")

    sub.add_parser("version", help="버전 출력")

    return parser


def _print_manifest_summary(manifest: ProjectManifest) -> None:
    state = manifest.current_state
    state_str = state.value if hasattr(state, "value") else state
    cat = manifest.category
    cat_str = cat.value if hasattr(cat, "value") else cat
    print(f"project_id     : {manifest.project_id}")
    print(f"title          : {manifest.title}")
    print(f"category       : {cat_str}")
    print(f"current_state  : {state_str}")
    print(f"duration_min   : {manifest.target_duration_min}")
    print(f"created_at     : {manifest.created_at}")
    print(f"updated_at     : {manifest.updated_at}")
    print(f"state_history  : {len(manifest.state_history)} entries")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "version":
        print(f"orchestrator v{__version__}")
        return 0

    if args.cmd == "command-center":
        run_command_center(project_id=args.project)
        return 0

    if args.cmd == "new-project":
        try:
            manifest = new_project(
                project_id=args.project_id,
                title=args.title,
                category=args.category,
                target_duration_min=args.duration_min,
                topic_summary=args.topic_summary,
            )
        except (FileExistsError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"새 프로젝트 생성 완료: {args.project_id}")
        _print_manifest_summary(manifest)
        return 0

    if args.cmd == "resume":
        try:
            manifest = resume_project(args.project_id)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"프로젝트 재개: {args.project_id}")
        _print_manifest_summary(manifest)
        return 0

    if args.cmd == "transition":
        try:
            manifest = resume_project(args.project_id)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        try:
            manifest = transition_state(manifest, args.to, reason=args.reason)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"상태 전이 완료: {args.project_id} → {args.to}")
        _print_manifest_summary(manifest)
        return 0

    if args.cmd == "plan-intake":
        return _cmd_plan_intake(args)

    if args.cmd == "submit-intake":
        return _cmd_submit_intake(args)

    if args.cmd == "approve":
        print("approve: Phase 11 에서 구현 예정입니다.")
        return 0

    parser.error("unknown command")
    return 2


def _cmd_plan_intake(args: argparse.Namespace) -> int:
    """plan-intake: IntakePlannerWorker 1회 호출 + 상태 전이.

    흐름:
    1. manifest 로딩.
    2. current_state 가 CREATED 이면 INTAKE_PLANNING 으로 전이 (이미 진행 중이면 skip).
    3. 합성 `TaskQueueItem` 생성 후 IntakePlannerWorker.run() 직접 호출 (Phase 4 의
       자동 task_queue 흐름은 도입 전).
    4. 성공 (status=completed) 이면 INTAKE_PENDING_USER 로 전이.
    5. 실패면 사용자에게 안내. state 는 INTAKE_PLANNING 그대로 유지.
    """
    # 지연 import: TUI / FastAPI 미설치 환경에서도 CLI 의 다른 서브커맨드는 동작해야 함.
    from schemas.models import TaskQueueItem
    from workers.intake_planner_worker import IntakePlannerWorker

    try:
        manifest = resume_project(args.project_id)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    current_str = manifest.current_state.value if hasattr(manifest.current_state, "value") else manifest.current_state
    if current_str == ProjectState.CREATED.value:
        try:
            manifest = transition_state(
                manifest,
                ProjectState.INTAKE_PLANNING,
                reason="plan-intake CLI 시작",
            )
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    elif current_str != ProjectState.INTAKE_PLANNING.value:
        print(
            f"error: 현재 상태 '{current_str}' 에서는 plan-intake 를 실행할 수 없습니다. "
            f"(허용: created 또는 intake_planning)",
            file=sys.stderr,
        )
        return 2

    task_id = f"intake-plan-{args.project_id}"
    task = TaskQueueItem(
        task_id=task_id,
        task_type="intake_planning",
        assigned_worker="intake_planner",
        description="Phase 3 IntakePlannerWorker 1회 실행",
        input_refs=["project_manifest.json"],
        output_refs=["01_intake/intake_plan.json"],
    )
    worker = IntakePlannerWorker()
    worker.llm_backend = args.backend  # type: ignore[misc]

    worker_args = argparse.Namespace(
        project_id=args.project_id,
        task_id=task_id,
        projects_root="projects",
    )
    result = worker.run(worker_args, task)
    result_status = result.status.value if hasattr(result.status, "value") else result.status

    if result_status != "completed":
        print(
            f"plan-intake 실패: status={result_status} errors={result.errors}",
            file=sys.stderr,
        )
        return 1

    try:
        manifest = transition_state(
            resume_project(args.project_id),
            ProjectState.INTAKE_PENDING_USER,
            reason="IntakePlannerWorker 성공",
        )
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    print(f"plan-intake 완료: {args.project_id} (backend={args.backend})")
    print(f"outputs : {result.outputs}")
    _print_manifest_summary(manifest)
    return 0


def _cmd_submit_intake(args: argparse.Namespace) -> int:
    """submit-intake: 검증된 SourceIntake 파일을 받아 영속화 + 상태 전이.

    웹 인테이크 페이지 (`web/intake_page_app.py`) 가 제출하는 흐름과 동일한 검증을
    CLI 에서도 사용할 수 있게 한 편의 명령. 입력 파일은 SourceIntake 스키마를 통과해야
    한다 (Pydantic v2 validation).
    """
    try:
        manifest = resume_project(args.project_id)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    src_path = Path(args.file)
    if not src_path.exists():
        print(f"error: 파일이 없습니다: {src_path}", file=sys.stderr)
        return 1

    try:
        raw = json.loads(src_path.read_text(encoding="utf-8"))
        intake = SourceIntake.model_validate(raw)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"error: SourceIntake 검증 실패 — {e}", file=sys.stderr)
        return 1

    # project_id 일치 검증
    if intake.project_id != args.project_id:
        print(
            f"error: project_id 불일치 — file={intake.project_id} cli={args.project_id}",
            file=sys.stderr,
        )
        return 1

    # 영속화 (덮어쓰기)
    out_path = manifest_intake_path(args.project_id) / "source_intake.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(intake.model_dump_json(indent=2), encoding="utf-8")

    try:
        manifest = transition_state(
            manifest,
            ProjectState.SOURCE_COLLECTING,
            reason=args.reason,
        )
    except ValueError as e:
        print(f"error: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    print(f"submit-intake 완료: {args.project_id}")
    print(f"saved   : {out_path}")
    print(f"decisions: {len(intake.user_decisions)}")
    _print_manifest_summary(manifest)
    return 0


def manifest_intake_path(project_id: str) -> Path:
    """`projects/{pid}/01_intake/` 디렉토리. project_manager 외부에서 쓰기 시 기본 경로."""
    from orchestrator.config import project_dir as _pdir

    return _pdir(project_id) / "01_intake"


if __name__ == "__main__":
    sys.exit(main())

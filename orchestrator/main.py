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
    pin.add_argument(
        "--force",
        action="store_true",
        help=(
            "이미 유효한 intake_plan.json 이 있어도 worker 를 재실행. "
            "기본 동작은 idempotent — intake_planning 상태에서 유효한 plan 이 있으면 "
            "재실행을 건너뛰고 intake_pending_user 로 전이만 진행 (v0.3.1 H3)."
        ),
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

    v0.3.1 (codex 4차 리뷰 흡수):
    - H3: idempotency 보강. current_state=intake_planning 이고 유효한 `01_intake/intake_plan.json`
      이 이미 있으면 worker 를 다시 돌리지 않고 intake_pending_user 로 전이만 진행 (재실행
      한 번이 LLM 호출 비용 + record 누적이라 idempotent 가 기본). `--force` 로 강제 재실행.
    - M2: worker.run() 결과를 `BaseWorker.write_result(args, result)` 로 task_result.json 까지
      영속화. Phase 4 의 정식 task_queue 흐름 도입 전까지의 C4 추적성 정합 stopgap.

    흐름:
    1. project_id 정책 검증.
    2. manifest 로딩 + state precondition.
    3. created → intake_planning 전이 (이미 planning 이면 skip).
    4. 기존 intake_plan.json 이 유효하고 `--force` 미지정이면 worker skip → step 6.
    5. 합성 TaskQueueItem + worker.run() + write_result (task_result.json 영속화).
    6. intake_planning → intake_pending_user 전이.
    """
    # 지연 import: TUI / FastAPI 미설치 환경에서도 CLI 의 다른 서브커맨드는 동작해야 함.
    from orchestrator.project_manager import validate_project_id
    from schemas.models import IntakePlan, TaskQueueItem
    from workers.intake_planner_worker import IntakePlannerWorker

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

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

    plan_path = manifest_intake_path(args.project_id) / "intake_plan.json"

    # v0.3.1 H3: 기존 plan 이 유효하면 worker skip.
    skip_worker = False
    if plan_path.exists() and not args.force:
        try:
            IntakePlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
            skip_worker = True
            print(
                f"plan-intake: 기존 intake_plan.json 발견 — worker 재실행 건너뜀 "
                f"(재실행 원하면 --force). path={plan_path}"
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(
                f"plan-intake: 기존 intake_plan.json 이 손상되어 worker 를 재실행합니다. "
                f"({type(e).__name__})",
                file=sys.stderr,
            )

    if not skip_worker:
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
        # v0.3.1 M2: task_result.json 영속화 — BaseWorker.main 의 표준 흐름 보강.
        try:
            worker.write_result(worker_args, result)
        except OSError as e:
            print(f"warning: task_result.json 영속화 실패 — {e}", file=sys.stderr)

        result_status = result.status.value if hasattr(result.status, "value") else result.status
        if result_status != "completed":
            print(
                f"plan-intake 실패: status={result_status} errors={result.errors}",
                file=sys.stderr,
            )
            return 1
        outputs_summary = result.outputs
    else:
        outputs_summary = [str(plan_path)]

    try:
        manifest = transition_state(
            resume_project(args.project_id),
            ProjectState.INTAKE_PENDING_USER,
            reason="IntakePlannerWorker 성공" if not skip_worker else "기존 intake_plan.json 재사용",
        )
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    print(f"plan-intake 완료: {args.project_id} (backend={args.backend}, skipped={skip_worker})")
    print(f"outputs : {outputs_summary}")
    _print_manifest_summary(manifest)
    return 0


def _cmd_submit_intake(args: argparse.Namespace) -> int:
    """submit-intake: 검증된 SourceIntake 파일을 받아 영속화 + 상태 전이.

    웹 인테이크 페이지 (`web/intake_page_app.py`) 가 제출하는 흐름과 동일한 검증을
    CLI 에서도 사용할 수 있게 한 편의 명령. 입력 파일은 SourceIntake 스키마를 통과해야
    한다 (Pydantic v2 validation).

    v0.3.1: project_id 정책 검증 (C1), state precondition 검증을 write 보다 먼저 수행 (M1).
    """
    from orchestrator.project_manager import validate_project_id

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        manifest = resume_project(args.project_id)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # v0.3.1 M1: state precondition 을 파일 쓰기 전에 확인.
    current_str = manifest.current_state.value if hasattr(manifest.current_state, "value") else manifest.current_state
    if current_str != ProjectState.INTAKE_PENDING_USER.value:
        print(
            f"error: 현재 상태 '{current_str}' 에서는 submit-intake 를 수행할 수 없습니다. "
            f"(허용: intake_pending_user)",
            file=sys.stderr,
        )
        return 2

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

    # v0.3.1 M1: tmp write → transition → atomic rename. 잘못된 상태에서 파일이 먼저
    # 덮어쓰이는 race 차단 + transition 실패 시 leftover 정리. precondition 검증은
    # 위에서 했지만 race 대비 두번째 게이트가 transition 자체.
    out_path = manifest_intake_path(args.project_id) / "source_intake.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(intake.model_dump_json(indent=2), encoding="utf-8")
    try:
        manifest = transition_state(
            manifest,
            ProjectState.SOURCE_COLLECTING,
            reason=args.reason,
        )
    except ValueError as e:
        # transition 실패 시 tmp 파일 best-effort cleanup. 원본 source_intake.json 은
        # 있다면 그대로 유지 (이전 시도의 산출물).
        try:
            tmp_path.unlink()
        except OSError:
            pass
        print(f"error: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2
    tmp_path.replace(out_path)

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

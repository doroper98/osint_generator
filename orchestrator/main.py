"""orchestrator CLI 진입점.

서브커맨드
----------
- command-center --project {pid}              : Command Center TUI 진입
- new-project {pid} --title ... --category ...: 새 프로젝트 생성 (Phase 2)
- resume {pid}                                : 기존 프로젝트 재개 (Phase 2)
- transition {pid} --to {state} [--reason ...]: 상태 전이 (Phase 2)
- approve --project {pid} --gate ...          : Review Gate 승인 기록 (Phase 11)
- version                                     : 현재 버전 출력
"""

from __future__ import annotations

import argparse
import sys

from orchestrator import __version__
from orchestrator.project_manager import (
    ProjectExistsError,
    ProjectNotFoundError,
    new_project,
    resume_project,
    transition_state,
)
from orchestrator.state_machine import InvalidTransitionError
from schemas.models import Category, ProjectState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="longform-briefing-pipeline orchestrator CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    cc = sub.add_parser("command-center", help="Command Center TUI 진입")
    cc.add_argument("--project", required=True, help="project_id")

    npj = sub.add_parser("new-project", help="새 프로젝트 매니페스트 생성")
    npj.add_argument("project_id", help="프로젝트 ID (디렉토리명)")
    npj.add_argument("--title", default=None, help="제목 (기본: project_id)")
    npj.add_argument(
        "--category",
        required=True,
        choices=[c.value for c in Category],
        help="주제 카테고리",
    )
    npj.add_argument("--duration-min", type=int, default=18)
    npj.add_argument("--topic-summary", default="")

    rsm = sub.add_parser("resume", help="기존 프로젝트 매니페스트 재개")
    rsm.add_argument("project_id", help="프로젝트 ID")

    trn = sub.add_parser("transition", help="프로젝트 상태 전이")
    trn.add_argument("project_id", help="프로젝트 ID")
    trn.add_argument(
        "--to",
        required=True,
        choices=[s.value for s in ProjectState],
        help="목표 상태",
    )
    trn.add_argument("--reason", default="")

    apv = sub.add_parser("approve", help="Review Gate 승인 기록 (Phase 11)")
    apv.add_argument("--project", required=True)
    apv.add_argument("--gate", required=True)
    apv.add_argument("--comment", default="")

    sub.add_parser("version", help="버전 출력")

    return parser


def _print_manifest_summary(manifest, prefix: str = "") -> None:
    state = manifest.current_state
    if hasattr(state, "value"):
        state = state.value
    print(f"{prefix}project_id     : {manifest.project_id}")
    print(f"{prefix}title          : {manifest.title}")
    print(f"{prefix}category       : {manifest.category}")
    print(f"{prefix}current_state  : {state}")
    print(f"{prefix}target_duration: {manifest.target_duration_min} min")
    print(f"{prefix}history entries: {len(manifest.state_history)}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "version":
        print(f"orchestrator v{__version__}")
        return 0

    if args.cmd == "command-center":
        # TUI 의존성(textual)을 비-TUI 커맨드에서 끌어오지 않도록 지연 import.
        from orchestrator.command_center import run_command_center

        run_command_center(project_id=args.project)
        return 0

    if args.cmd == "new-project":
        try:
            manifest = new_project(
                project_id=args.project_id,
                title=args.title or args.project_id,
                category=args.category,
                target_duration_min=args.duration_min,
                topic_summary=args.topic_summary,
            )
        except ProjectExistsError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"새 프로젝트 생성됨: projects/{manifest.project_id}/project_manifest.json")
        _print_manifest_summary(manifest, prefix="  ")
        return 0

    if args.cmd == "resume":
        try:
            manifest = resume_project(project_id=args.project_id)
        except ProjectNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"프로젝트 재개: projects/{manifest.project_id}/")
        _print_manifest_summary(manifest, prefix="  ")
        return 0

    if args.cmd == "transition":
        try:
            manifest = transition_state(
                project_id=args.project_id,
                next_state=args.to,
                reason=args.reason,
            )
        except ProjectNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except InvalidTransitionError as e:
            print(f"error: {e}", file=sys.stderr)
            return 3
        state = manifest.current_state
        if hasattr(state, "value"):
            state = state.value
        print(f"상태 전이 완료: {manifest.project_id} → {state}")
        return 0

    if args.cmd == "approve":
        print("approve: Phase 11 에서 구현 예정입니다.")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())

"""orchestrator CLI 진입점.

서브커맨드
----------
- command-center --project {pid}        : Command Center TUI 진입
- new-project --title ... --category ...: 새 프로젝트 생성 (Phase 2 본격화)
- approve --project {pid} --gate ...    : Review Gate 승인 기록 (Phase 11)
- version                               : 현재 버전 출력

Phase 1 MVP 에서는 command-center 와 version 만 동작합니다.
"""

from __future__ import annotations

import argparse
import sys

from orchestrator import __version__
from orchestrator.command_center import run_command_center


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="longform-briefing-pipeline orchestrator CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    cc = sub.add_parser("command-center", help="Command Center TUI 진입")
    cc.add_argument("--project", required=True, help="project_id")

    npj = sub.add_parser("new-project", help="새 프로젝트 생성 (Phase 2 본격화)")
    npj.add_argument("--title", required=True)
    npj.add_argument("--category", required=True)
    npj.add_argument("--duration-min", type=int, default=18)

    apv = sub.add_parser("approve", help="Review Gate 승인 기록 (Phase 11)")
    apv.add_argument("--project", required=True)
    apv.add_argument("--gate", required=True)
    apv.add_argument("--comment", default="")

    sub.add_parser("version", help="버전 출력")

    return parser


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
        print("new-project: Phase 2 에서 본격 구현 예정입니다.")
        print(f"  title: {args.title}")
        print(f"  category: {args.category}")
        print(f"  duration_min: {args.duration_min}")
        return 0

    if args.cmd == "approve":
        print("approve: Phase 11 에서 구현 예정입니다.")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())

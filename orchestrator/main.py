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
- build-source-registry {pid}               : partials → source_registry.json +
                                              source_completeness_report.json + 전이 (Phase 5)
- build-research-dossier {pid} [--backend]  : ResearchWorker 호출 → research_dossier.json
                                              + research_in_progress 전이 (Phase 6A)
- build-script {pid} [--backend]            : ScriptWorker 호출 → full_script.json
                                              + script_writing 전이 (Phase 6 Script)
- build-scene {pid}                         : full_script → scene_manifest.json (결정론적)
                                              + scene_planning 전이 (수직 슬라이스 V2)
- render-debug {pid}                         : scene_manifest+full_script → render_props.json
                                              → Remotion 으로 draft_debug.mp4 (수직 슬라이스 V3)
- build-audio {pid} [--backend]              : full_script → 나레이션 wav + audio_manifest.json
                                              (TTS 백엔드 교체 가능, 수직 슬라이스 V4)
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


def _tts_backend_choices() -> tuple[str, ...]:
    """TTS 백엔드 선택지 (지연 import — worker 의존성 격리)."""
    from workers.tts_backends import BACKEND_CHOICES

    return BACKEND_CHOICES


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
    npj.add_argument("--duration-min", type=int, default=18, help="목표 영상 길이 (분, 3~20)")
    npj.add_argument("--topic-summary", default="", help="주제 요약")
    npj.add_argument(
        "--link",
        action="append",
        default=None,
        metavar="URL",
        help="사용자 사전 제공 자료 링크 (반복 가능). IntakePlanner 가 참고.",
    )

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

    bsr = sub.add_parser(
        "build-source-registry",
        help=(
            "partials 합쳐 source_registry.json + source_completeness_report.json "
            "생성 후 source_completeness_review 전이 (Phase 5)"
        ),
    )
    bsr.add_argument("project_id", help="project_id")
    bsr.add_argument(
        "--lenient-input-item-id",
        action="store_true",
        help=(
            "input_item_id=None 을 허용 (builder 의 strict_input_item_id=False). "
            "기본은 strict — pipeline production path 에서는 source_collector 가 "
            "항상 input_item_id 를 set 하므로 None 자체가 drift 신호."
        ),
    )

    brd = sub.add_parser(
        "build-research-dossier",
        help=(
            "ResearchWorker 호출 → research_dossier.json 생성 후 "
            "research_in_progress 전이 (Phase 6A)"
        ),
    )
    brd.add_argument("project_id", help="project_id")
    brd.add_argument(
        "--backend",
        choices=["claude", "codex"],
        default="claude",
        help="LLM backend (기본: claude)",
    )
    brd.add_argument(
        "--force",
        action="store_true",
        help=(
            "이미 유효한 research_dossier.json 이 있어도 worker 를 재실행. "
            "기본 동작은 idempotent — 유효한 dossier 가 있으면 재실행을 건너뛰고 "
            "research_in_progress 로 전이만 진행."
        ),
    )

    bsc = sub.add_parser(
        "build-script",
        help=(
            "ScriptWorker 호출 → full_script.json 생성 후 script_writing 전이 "
            "(Phase 6 Script, blueprint 흡수)"
        ),
    )
    bsc.add_argument("project_id", help="project_id")
    bsc.add_argument(
        "--backend", choices=["claude", "codex"], default="claude",
        help="LLM backend (기본: claude)",
    )
    bsc.add_argument(
        "--force", action="store_true",
        help="유효한 full_script.json 이 있어도 worker 재실행 (기본은 idempotent skip).",
    )

    bsn = sub.add_parser(
        "build-scene",
        help=(
            "full_script → scene_manifest.json (결정론적, 텍스트 슬라이드) 생성 후 "
            "scene_planning 전이 (수직 슬라이스 V2)"
        ),
    )
    bsn.add_argument("project_id", help="project_id")

    rdg = sub.add_parser(
        "render-debug",
        help=(
            "render_props.json 생성 후 Remotion 으로 draft_debug.mp4 렌더 "
            "(수직 슬라이스 V3, 미리보기 — state 전이 없음)"
        ),
    )
    rdg.add_argument("project_id", help="project_id")
    rdg.add_argument(
        "--props-only",
        action="store_true",
        help="render_props.json 만 생성하고 Remotion 렌더는 건너뜀 (node 미설치 환경용).",
    )
    rdg.add_argument(
        "--browser-executable",
        default=None,
        help=(
            "Remotion 이 쓸 chrome-headless-shell 바이너리 경로. 미지정 시 "
            "OSINT_HEADLESS_SHELL 환경변수 또는 자동탐지 (RENDER-AP-001 — chromium "
            "자동 다운로드가 막힌 환경 대응)."
        ),
    )

    bad = sub.add_parser(
        "build-audio",
        help=(
            "full_script → 나레이션 wav + audio_manifest.json (TTS 백엔드 교체 가능: "
            "local/elevenlabs/stub, 수직 슬라이스 V4 — state 전이 없음)"
        ),
    )
    bad.add_argument("project_id", help="project_id")
    bad.add_argument(
        "--backend",
        choices=list(_tts_backend_choices()),
        default="local",
        help=(
            "TTS 백엔드. local(기본·프라이버시·OSINT_TTS_CMD) / elevenlabs(외부 API·"
            "ELEVENLABS_API_KEY) / stub(무음, 테스트)."
        ),
    )
    bad.add_argument("--voice", default=None, help="백엔드별 보이스 식별자(선택).")

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
                initial_links=args.link,
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

    if args.cmd == "build-source-registry":
        return _cmd_build_source_registry(args)

    if args.cmd == "build-research-dossier":
        return _cmd_build_research_dossier(args)

    if args.cmd == "build-script":
        return _cmd_build_script(args)

    if args.cmd == "build-scene":
        return _cmd_build_scene(args)

    if args.cmd == "render-debug":
        return _cmd_render_debug(args)

    if args.cmd == "build-audio":
        return _cmd_build_audio(args)

    if args.cmd == "approve":
        print("approve: Phase 11 에서 구현 예정입니다.")
        return 0

    parser.error("unknown command")
    return 2


def _cmd_plan_intake(args: argparse.Namespace) -> int:
    """plan-intake: IntakePlannerWorker 1회 호출 + 상태 전이.

    오케스트레이션 로직 자체는 `orchestrator.intake_service.run_intake_planner` 에
    있으며 (CLI 와 Web `POST /new` 가 공유), 본 핸들러는 thin wrapper — 입력 검증과
    사용자 출력/exit code 매핑만 담당한다.

    - idempotency: 유효한 기존 `intake_plan.json` 이 있고 `--force` 미지정이면 worker
      재실행을 건너뛰고 전이만 진행 (재실행은 LLM 호출 비용).
    - worker 실패 시 intake_planning 에서 멈춤 (pending_user 까지 전진하지 않음).
    """
    from orchestrator.intake_service import IntakePlanningError, run_intake_planner
    from orchestrator.project_manager import validate_project_id

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        manifest, outputs_summary, skipped = run_intake_planner(
            args.project_id, backend=args.backend, force=args.force
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except IntakePlanningError as e:
        if e.kind == "state":
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"plan-intake 실패: {e} errors={e.errors}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    if skipped:
        print("plan-intake: 기존 intake_plan.json 재사용 — worker 건너뜀 (재실행 원하면 --force).")
    print(f"plan-intake 완료: {args.project_id} (backend={args.backend}, skipped={skipped})")
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


def _cmd_build_source_registry(args: argparse.Namespace) -> int:
    """build-source-registry: partials → source_registry.json + completeness report + 전이.

    Phase 5 완료 게이트 (Review Gate 2, `source_completeness_review`) 의 두 입력을
    한 번에 만든다:
    1. project_id 정책 검증 (C1 path traversal 가드).
    2. manifest 로딩 + state precondition (source_collecting 에서만 허용).
    3. build_and_persist_source_registry — partials 로딩 → builder → 영속화.
    4. check_source_completeness — 부족 자료 식별 → source_completeness_report.json.
    5. source_collecting → source_completeness_review 전이.

    builder / checker 는 순수 함수 (디스크 I/O 없음). 로딩·쓰기는 source_registry_io
    가 담당하며 본 CLI 는 thin orchestration. registry/report 영속화 실패 시 전이
    하지 않는다 (게이트 입력이 갖춰진 뒤에만 전진).
    """
    from orchestrator.project_manager import validate_project_id
    from orchestrator.source_completeness_checker import check_source_completeness
    from orchestrator.source_registry_io import (
        build_and_persist_source_registry,
        persist_source_completeness_report,
    )

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

    current_str = (
        manifest.current_state.value
        if hasattr(manifest.current_state, "value")
        else manifest.current_state
    )
    if current_str != ProjectState.SOURCE_COLLECTING.value:
        print(
            f"error: 현재 상태 '{current_str}' 에서는 build-source-registry 를 실행할 수 "
            f"없습니다. (허용: source_collecting)",
            file=sys.stderr,
        )
        return 2

    try:
        registry, stats = build_and_persist_source_registry(
            args.project_id,
            strict_input_item_id=not args.lenient_input_item_id,
        )
    except (json.JSONDecodeError, ValueError, OSError) as e:
        # JSONDecodeError/ValidationError(=ValueError) : partial 손상·스키마 위반,
        # ValueError : builder fail-fast invariant, OSError : registry 디스크 영속화 실패.
        # report persist 의 OSError 처리와 대칭 — 영속화 단계가 어디서 깨지든 전이 금지.
        print(f"error: source_registry 빌드/영속화 실패 — {e}", file=sys.stderr)
        return 1

    report = check_source_completeness(registry)
    try:
        persist_source_completeness_report(args.project_id, report)
    except OSError as e:
        print(f"error: source_completeness_report 영속화 실패 — {e}", file=sys.stderr)
        return 1

    try:
        manifest = transition_state(
            resume_project(args.project_id),
            ProjectState.SOURCE_COMPLETENESS_REVIEW,
            reason="source_registry + completeness report 생성",
        )
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    sources_dir = manifest_sources_path(args.project_id)
    print(f"build-source-registry 완료: {args.project_id}")
    print(f"saved   : {sources_dir / 'source_registry.json'}")
    print(f"report  : {sources_dir / 'source_completeness_report.json'}")
    print(
        f"stats   : partials={stats['partial_count']} "
        f"(empty={stats['empty_partial_count']}) sources={stats['source_count']}"
    )
    print(
        f"report  : status={report.overall_status} usable={report.usable_sources}/"
        f"{report.total_sources} blocker={report.blocker_count} "
        f"warning={report.warning_count} info={report.info_count}"
    )
    _print_manifest_summary(manifest)
    return 0


def _cmd_build_research_dossier(args: argparse.Namespace) -> int:
    """build-research-dossier: ResearchWorker 1회 호출 + 상태 전이 (Phase 6A).

    오케스트레이션 로직은 `orchestrator.research_service.run_research_worker` 에 있으며,
    본 핸들러는 thin wrapper — 입력 검증과 사용자 출력/exit code 매핑만 담당한다.

    - precondition: source_completeness_review 상태에서만 실행 (Review Gate 2 통과 후).
    - idempotency: 유효한 기존 research_dossier.json 이 있고 `--force` 미지정이면 worker
      재실행을 건너뛰고 전이만 진행 (재실행은 LLM 호출 비용).
    - worker 실패 / 영속화 검증 실패 시 source_completeness_review 에서 멈춤.
    """
    from orchestrator.project_manager import validate_project_id
    from orchestrator.research_service import ResearchError, run_research_worker

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        manifest, outputs_summary, skipped = run_research_worker(
            args.project_id, backend=args.backend, force=args.force
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ResearchError as e:
        if e.kind == "state":
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"build-research-dossier 실패: {e} errors={e.errors}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    if skipped:
        print(
            "build-research-dossier: 기존 research_dossier.json 재사용 — "
            "worker 건너뜀 (재실행 원하면 --force)."
        )
    print(
        f"build-research-dossier 완료: {args.project_id} "
        f"(backend={args.backend}, skipped={skipped})"
    )
    print(f"outputs : {outputs_summary}")
    _print_manifest_summary(manifest)
    return 0


def _cmd_build_script(args: argparse.Namespace) -> int:
    """build-script: ScriptWorker 1회 호출 + 상태 전이 (Phase 6 Script).

    thin wrapper — 검증·출력·exit code 매핑만. 오케스트레이션은
    orchestrator.script_service.run_script_worker.
    """
    from orchestrator.project_manager import validate_project_id
    from orchestrator.script_service import ScriptError, run_script_worker

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        manifest, outputs_summary, skipped = run_script_worker(
            args.project_id, backend=args.backend, force=args.force
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ScriptError as e:
        if e.kind == "state":
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"build-script 실패: {e} errors={e.errors}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    if skipped:
        print("build-script: 기존 full_script.json 재사용 — worker 건너뜀 (재실행 원하면 --force).")
    print(f"build-script 완료: {args.project_id} (backend={args.backend}, skipped={skipped})")
    print(f"outputs : {outputs_summary}")
    _print_manifest_summary(manifest)
    return 0


def _cmd_build_scene(args: argparse.Namespace) -> int:
    """build-scene: full_script → scene_manifest.json (결정론적) + 상태 전이 (V2).

    scene_builder 는 순수 함수, scene_io 가 I/O. LLM 미사용. precondition 은
    script_writing 이며, 수직 슬라이스라 script_review(Gate 4)를 통과만 하고
    scene_planning 에 안착한다. 영속화 성공 후에만 전이.
    """
    from orchestrator.project_manager import validate_project_id
    from orchestrator.scene_io import build_and_persist_scene_manifest

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

    current_str = (
        manifest.current_state.value
        if hasattr(manifest.current_state, "value")
        else manifest.current_state
    )
    if current_str != ProjectState.SCRIPT_WRITING.value:
        print(
            f"error: 현재 상태 '{current_str}' 에서는 build-scene 을 실행할 수 없습니다. "
            f"(허용: script_writing)",
            file=sys.stderr,
        )
        return 2

    try:
        scene_manifest = build_and_persist_scene_manifest(args.project_id)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError, OSError) as e:
        print(f"error: scene_manifest 빌드/영속화 실패 — {e}", file=sys.stderr)
        return 1

    # script_review(Gate 4)를 통과만 하고 scene_planning 안착 (수직 슬라이스: gate 흡수).
    try:
        manifest = transition_state(
            manifest, ProjectState.SCRIPT_REVIEW, reason="script_review 흡수 (수직 슬라이스)",
        )
        manifest = transition_state(
            manifest, ProjectState.SCENE_PLANNING, reason="scene_manifest 생성",
        )
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    print(f"build-scene 완료: {args.project_id}")
    print(f"saved   : {manifest_scene_path(args.project_id) / 'scene_manifest.json'}")
    print(f"scenes  : {len(scene_manifest.scenes)}")
    _print_manifest_summary(manifest)
    return 0


def _cmd_build_audio(args: argparse.Namespace) -> int:
    """build-audio: full_script → 나레이션 wav + audio_manifest.json (V4).

    TTS 백엔드 교체 가능(local/elevenlabs/stub). state 전이 없는 산출물 생성(재생성 가능).
    full_script 가 있어야 한다.
    """
    from orchestrator.audio_io import audio_manifest_path
    from orchestrator.audio_service import build_audio
    from orchestrator.project_manager import validate_project_id
    from workers.tts_backends import TTSError

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        manifest = build_audio(
            args.project_id, backend=args.backend, voice=args.voice
        )
    except FileNotFoundError as e:
        print(f"error: {e} (먼저 build-script 로 full_script 를 만드십시오)", file=sys.stderr)
        return 1
    except TTSError as e:
        print(f"error: TTS 실패 — {e}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as e:
        print(f"error: audio 빌드/영속화 실패 — {e}", file=sys.stderr)
        return 1

    print(f"build-audio 완료: {args.project_id} (backend={args.backend})")
    print(f"saved   : {audio_manifest_path(args.project_id)}")
    print(
        f"segments: {len(manifest.segments)}  "
        f"total   : {manifest.total_duration_sec:.1f}s "
        f"({manifest.total_duration_sec / 60:.2f} min)"
    )
    return 0


def _detect_headless_shell() -> str | None:
    """chrome-headless-shell 바이너리 자동탐지 (RENDER-AP-001).

    Remotion 이 자체 다운로드를 못 하는 환경(네트워크 allowlist)에서, 머신에 이미
    있는 headless-shell 을 찾아 `--browser-executable` 로 넘기기 위함. full chrome 가
    아니라 headless_shell 만 채택한다 (full chrome 는 Remotion 의 old-headless 요구를
    충족 못 해 launch 실패). 못 찾으면 None — 호출자가 다운로드/안내로 폴백.
    """
    import glob

    patterns = [
        # Playwright 가 설치한 chromium headless shell.
        "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell",
        str(Path.home() / ".cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell"),
        # Puppeteer chrome-headless-shell.
        str(Path.home() / ".cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell"),
    ]
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[-1]  # 최신(정렬 마지막) 채택.
    return None


def _cmd_render_debug(args: argparse.Namespace) -> int:
    """render-debug: scene_manifest+full_script → render_props.json → Remotion mp4 (V3).

    수직 슬라이스의 최소 렌더(미리보기). precondition 은 scene_planning 이상이면
    충분하나(scene_manifest 존재), 단순히 scene_manifest/full_script 존재로 판정한다.
    상태 전이는 하지 않는다 — 현재 scene_manifest 로부터 언제든 다시 뽑는 미리보기.

    1. render_props.json 생성 (build_and_persist_render_props).
    2. --props-only 면 종료. 아니면 remotion/ 에서 `npx remotion render` 호출.
    """
    import os
    import subprocess

    from orchestrator.config import REPO_ROOT
    from orchestrator.project_manager import validate_project_id
    from orchestrator.render_io import (
        build_and_persist_render_props,
        draft_debug_path,
        render_props_path,
    )

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        props, props_path = build_and_persist_render_props(args.project_id)
    except FileNotFoundError as e:
        print(f"error: {e} (먼저 build-scene 으로 scene_manifest 를 만드십시오)", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError, OSError) as e:
        print(f"error: render_props 빌드/영속화 실패 — {e}", file=sys.stderr)
        return 1

    print(f"render_props 생성: {props_path} (scenes={len(props.scenes)})")

    if args.props_only:
        print("--props-only: Remotion 렌더 건너뜀.")
        return 0

    remotion_dir = REPO_ROOT / "remotion"
    if not (remotion_dir / "node_modules").exists():
        print(
            f"error: remotion 의존성 미설치. 먼저:\n"
            f"  cd {remotion_dir} && npm install\n"
            f"그 뒤 render-debug 를 다시 실행하거나, render_props.json 으로 로컬에서 렌더하십시오.",
            file=sys.stderr,
        )
        return 1

    out_path = draft_debug_path(args.project_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx", "remotion", "render", "src/index.ts", "Briefing",
        str(out_path.resolve()),
        f"--props={props_path.resolve()}",
    ]
    # RENDER-AP-001: Remotion 의 chromium headless-shell 자동 다운로드가 막힌 환경
    # (네트워크 allowlist) 을 위해, 기존 chrome-headless-shell 바이너리를 가리킨다.
    # 우선순위: --browser-executable 플래그 > OSINT_HEADLESS_SHELL 환경변수 > 자동탐지.
    # full chrome 가 아니라 headless_shell(old headless 구현)이어야 한다 (full chrome 는
    # old headless 미지원으로 launch 실패).
    shell = args.browser_executable or os.environ.get("OSINT_HEADLESS_SHELL") or _detect_headless_shell()
    if shell:
        cmd.append(f"--browser-executable={shell}")
    print(f"렌더 시작: {' '.join(cmd)} (cwd={remotion_dir})")
    try:
        proc = subprocess.run(cmd, cwd=str(remotion_dir), timeout=1800)
    except FileNotFoundError:
        print("error: npx/node 를 찾을 수 없습니다. Node.js 설치 필요.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("error: Remotion 렌더 타임아웃 (30분).", file=sys.stderr)
        return 1
    if proc.returncode != 0:
        print(f"error: Remotion 렌더 실패 (exit {proc.returncode}).", file=sys.stderr)
        return 1

    print(f"render-debug 완료: {out_path}")
    return 0


def manifest_scene_path(project_id: str) -> Path:
    """`projects/{pid}/06_scene/` 디렉토리."""
    from orchestrator.config import project_dir as _pdir

    return _pdir(project_id) / "06_scene"


def manifest_sources_path(project_id: str) -> Path:
    """`projects/{pid}/02_sources/` 디렉토리."""
    from orchestrator.config import project_dir as _pdir

    return _pdir(project_id) / "02_sources"


def manifest_intake_path(project_id: str) -> Path:
    """`projects/{pid}/01_intake/` 디렉토리. project_manager 외부에서 쓰기 시 기본 경로."""
    from orchestrator.config import project_dir as _pdir

    return _pdir(project_id) / "01_intake"


if __name__ == "__main__":
    sys.exit(main())

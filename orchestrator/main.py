"""orchestrator CLI 진입점.

서브커맨드
----------
- command-center --project {pid}            : Command Center TUI 진입
- new-project {pid} --title ... --category .: 새 프로젝트 생성
- resume {pid}                              : 기존 프로젝트 manifest 확인
- transition {pid} --to {state} [--reason]  : 상태 전이
- plan-intake {pid} [--backend claude|codex]: IntakePlannerWorker 호출 + 인테이크 상태 전이
- submit-intake {pid} --file path/to/source_intake.json
                                            : SourceIntake 영속화 + source_verify 전이
- build-source-registry {pid}               : partials → source_registry.json +
                                              source_completeness_report.json (Phase 5)
- build-research-dossier {pid} [--backend]  : ResearchWorker 호출 → research_dossier.json
                                              + research 전이 (Phase 6A)
- import-bundle {pid} --file <path>          : agents_reviewer report_bundle.json →
                                              research_dossier.json + research
                                              전이 (외부 연동, build-research-dossier 대체)
- build-script {pid} [--backend]            : ScriptWorker 호출 → full_script.json
                                              + script_draft 전이 (Phase 6 Script)
- build-scene / render-debug / build-audio / build-audio-demo
                                            : v2.0.0 에서 삭제 — LegacyRemovedError (docs/handoff/16 §4)
- advance --project {pid} [--jobs N]         : 현재 엔진 상태 단계 실행(engine_service) → ok 면 다음 상태 (v3.0.0)
- gate-view --project {pid}                  : 승인 게이트 화면 텍스트 (16 §5)
- approve --project {pid} --gate G [--comment]: 게이트 승인 → 다음 상태
- reject --project {pid} --gate G --to S --comment C : 게이트 반려 → 16 §2 역전이
- version                                   : 현재 버전 출력
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestrator import __version__
from orchestrator.command_center import run_command_center
from orchestrator.errors import LegacyRemovedError
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
        help="IntakePlannerWorker 호출 + created → intake 전이",
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
            "기본 동작은 idempotent — intake 상태에서 유효한 plan 이 있으면 "
            "재실행을 건너뛴다 (v0.3.1 H3)."
        ),
    )

    sin = sub.add_parser(
        "submit-intake",
        help="SourceIntake JSON 파일을 영속화 + source_verify 전이",
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
            "생성 (source_verify 에 머문다, v3.0.0)"
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
            "research 전이 (Phase 6A)"
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
            "research 로 전이만 진행."
        ),
    )

    imb = sub.add_parser(
        "import-bundle",
        help=(
            "agents_reviewer report_bundle.json → research_dossier.json 변환 후 "
            "research 전이 (외부 연동, build-research-dossier 드롭인 대체)"
        ),
    )
    imb.add_argument("project_id", help="project_id")
    imb.add_argument(
        "--file",
        required=True,
        help="report_bundle.json 경로 (ReportBundle 스키마, extra=forbid 검증)",
    )

    bsc = sub.add_parser(
        "build-script",
        help=(
            "ScriptWorker 호출 → full_script.json 생성 후 script_draft 전이 "
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

    # v2.0.0 삭제된 옛 영상 경로 — 서브커맨드는 남겨 시끄럽게 실패시킨다 (docs/handoff/15 P6).
    for legacy_cmd, arg_name in (
        ("build-scene", "project_id"),
        ("render-debug", "project_id"),
        ("build-audio", "project_id"),
        ("build-audio-demo", "props_path"),
    ):
        lp = sub.add_parser(legacy_cmd, help="[삭제됨 v2.0.0] LegacyRemovedError — docs/handoff/16 §4")
        lp.add_argument(arg_name)
        lp.add_argument("legacy_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    lsc = sub.add_parser(
        "lint-script",
        help="full_script narration 의 TTS-위험 표기(약어/기호/단위/URL 등) 검사",
    )
    lsc.add_argument("project_id", help="project_id")
    lsc.add_argument(
        "--strict", action="store_true",
        help="위험 표기가 하나라도 있으면 exit 1 (CI 게이트용).",
    )

    adv = sub.add_parser("advance", help="현재 엔진 상태의 단계를 돌리고 ok 면 다음 상태로 (v3.0.0, 16 §4)")
    adv.add_argument("--project", required=True)
    adv.add_argument("--jobs", type=int, default=None)

    gv = sub.add_parser("gate-view", help="승인 게이트 화면 텍스트 (16 §5)")
    gv.add_argument("--project", required=True)

    apv = sub.add_parser("approve", help="승인 게이트 승인 → 다음 상태 (16 §5)")
    apv.add_argument("--project", required=True)
    apv.add_argument("--gate", required=True, choices=["script_approval", "preview_approval"])
    apv.add_argument("--comment", default="")
    apv.add_argument("--by", default="user")

    rjt = sub.add_parser("reject", help="승인 게이트 반려 → 16 §2 역전이 (코멘트 필수)")
    rjt.add_argument("--project", required=True)
    rjt.add_argument("--gate", required=True, choices=["script_approval", "preview_approval"])
    rjt.add_argument("--to", required=True, choices=["script_draft", "direction", "assets"])
    rjt.add_argument("--comment", required=True)
    rjt.add_argument("--by", default="user")

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


def _load_env_file() -> None:
    """저장소 root 의 .env 를 자동 로딩(있으면).

    v0.32.1 도입. ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 등 secret 을 사용자가
    매 cmd 세션마다 입력하지 않게. **이미 환경에 같은 키가 있으면 override 하지 않는다**
    (`override=False`) — 운영 환경의 명시적 export 가 .env 보다 우선.

    .env 미존재 / `python-dotenv` 미설치는 silent no-op. CI / 테스트는 영향 없음.
    """
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except ImportError:
        return
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=False)


def _dump_effective_config(cmd: str) -> None:
    """서브커맨드 진입 시 유효 설정 1줄 덤프 (stderr, docs/handoff/19 §5.4 — agents_reviewer
    V5_ACTIVATION §4 교훈: 설정이 실제로 무엇으로 로드됐는지 매 실행 증명)."""
    from orchestrator.config import load_config
    from rules import rules_hash

    payload = {"cmd": cmd, "config": load_config().model_dump(mode="json"), "rules_hash": rules_hash()}
    print("effective_config " + json.dumps(payload, ensure_ascii=False), file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    _load_env_file()
    parser = build_parser()
    args = parser.parse_args(argv)
    _dump_effective_config(args.cmd)

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

    if args.cmd == "import-bundle":
        return _cmd_import_bundle(args)

    if args.cmd == "build-script":
        return _cmd_build_script(args)

    if args.cmd in ("build-scene", "render-debug", "build-audio", "build-audio-demo"):
        raise LegacyRemovedError(args.cmd)

    if args.cmd == "lint-script":
        return _cmd_lint_script(args)

    if args.cmd in ("advance", "gate-view", "approve", "reject"):
        return _cmd_pipeline(args)

    parser.error("unknown command")
    return 2


def _cmd_pipeline(args: argparse.Namespace) -> int:
    """advance / gate-view / approve / reject — Command Center 와 같은 함수(orchestrator.pipeline, v3.0.0)."""
    from orchestrator.config import project_dir
    from orchestrator.errors import ManifestError
    from orchestrator.gate_view import gate_view
    from orchestrator.pipeline import PipelineError, advance, next_action
    from orchestrator.project_manager import approve_gate, load_manifest, reject_gate

    try:
        manifest = load_manifest(args.project)
        pdir = project_dir(args.project)
        if args.cmd == "advance":
            def show(res: object) -> None:
                print(json.dumps(res.model_dump(), ensure_ascii=False))  # type: ignore[attr-defined]
            before = manifest.current_state
            manifest, results = advance(args.project, jobs=args.jobs, on_result=show)
            ok = all(r.ok for r in results)
            print(f"advance: {before} → {manifest.current_state} ({'ok' if ok else '실패 — 머묾'})")
            print(f"next   : {next_action(manifest.current_state)}")
            return 0 if ok else 1
        if args.cmd == "gate-view":
            text, _ = gate_view(pdir, manifest.current_state)
            print(text)
            return 0
        _, shown = gate_view(pdir, args.gate)
        if args.cmd == "approve":
            manifest = approve_gate(manifest, args.gate, by=args.by, comment=args.comment, shown=shown)
        else:
            manifest = reject_gate(manifest, args.gate, args.to, by=args.by, comment=args.comment, shown=shown)
    except (FileNotFoundError, ManifestError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (PipelineError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"{args.cmd}: {args.gate} → {manifest.current_state}")
    print(f"next   : {next_action(manifest.current_state)}")
    return 0


def _cmd_plan_intake(args: argparse.Namespace) -> int:
    """plan-intake: IntakePlannerWorker 1회 호출 + 상태 전이.

    오케스트레이션 로직 자체는 `orchestrator.intake_service.run_intake_planner` 에
    있으며 (CLI 와 Web `POST /new` 가 공유), 본 핸들러는 thin wrapper — 입력 검증과
    사용자 출력/exit code 매핑만 담당한다.

    - idempotency: 유효한 기존 `intake_plan.json` 이 있고 `--force` 미지정이면 worker
      재실행을 건너뛴다 (재실행은 LLM 호출 비용).
    - worker 실패 시 intake 에 머물고 plan 이 없으므로 submit-intake 가 막힌다.
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
    from orchestrator.intake_service import intake_plan_ready

    if current_str != ProjectState.INTAKE.value or not intake_plan_ready(args.project_id):
        print(
            f"error: 현재 상태 '{current_str}' 에서는 submit-intake 를 수행할 수 없습니다. "
            f"(허용: intake + 유효한 intake_plan.json — plan-intake 먼저)",
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
            ProjectState.SOURCE_VERIFY,
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

    Phase 5 완료 게이트 (Review Gate 2, `source_verify`) 의 두 입력을
    한 번에 만든다:
    1. project_id 정책 검증 (C1 path traversal 가드).
    2. manifest 로딩 + state precondition (source_verify 에서만 허용).
    3. build_and_persist_source_registry — partials 로딩 → builder → 영속화.
    4. check_source_completeness — 부족 자료 식별 → source_completeness_report.json.
    5. 전이 없음 — source_verify 에 머문다(v3.0.0, 16 §2). report 가 있으면 research 로 갈 수 있다.

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
    if current_str != ProjectState.SOURCE_VERIFY.value:
        print(
            f"error: 현재 상태 '{current_str}' 에서는 build-source-registry 를 실행할 수 "
            f"없습니다. (허용: source_verify)",
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

    manifest = resume_project(args.project_id)

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

    - precondition: source_verify 상태에서만 실행 (Review Gate 2 통과 후).
    - idempotency: 유효한 기존 research_dossier.json 이 있고 `--force` 미지정이면 worker
      재실행을 건너뛰고 전이만 진행 (재실행은 LLM 호출 비용).
    - worker 실패 / 영속화 검증 실패 시 source_verify 에서 멈춤.
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


def _cmd_import_bundle(args: argparse.Namespace) -> int:
    """import-bundle: report_bundle.json → research_dossier.json + 전이 (외부 연동).

    thin wrapper — 검증·출력·exit code 매핑만. 오케스트레이션은
    orchestrator.bundle_service.import_report_bundle. build-research-dossier 의
    드롭인 대체(LLM 대신 외부 bundle 흡수)이므로 이후 단계는 동일하다.
    """
    from orchestrator.bundle_service import BundleImportError, import_report_bundle
    from orchestrator.project_manager import validate_project_id

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        manifest, outputs = import_report_bundle(args.project_id, Path(args.file))
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except BundleImportError as e:
        if e.kind == "state":
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"import-bundle 실패: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2

    print(f"import-bundle 완료: {args.project_id}")
    print(f"outputs : {outputs}")
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
    _print_tts_lint_summary(args.project_id)
    _print_manifest_summary(manifest)
    return 0


def _print_tts_lint_summary(project_id: str) -> None:
    """생성된 full_script narration 의 TTS-위험 표기를 검사해 경고 출력 (재발 방지)."""
    from orchestrator.script_io import load_full_script
    from orchestrator.tts_lint import lint_full_script

    try:
        script = load_full_script(project_id)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return
    issues = lint_full_script(script)
    if not issues:
        print("TTS-lint : narration 깨끗 (위험 표기 없음)")
        return
    print(f"TTS-lint : 경고 {len(issues)}건 — narration 에 TTS 가 어색하게 읽을 표기:")
    for seg_id, issue in issues[:20]:
        print(f"  - [{seg_id}] {issue.category}: {issue.snippet!r} → {issue.hint}")
    if len(issues) > 20:
        print(f"  ... 외 {len(issues) - 20}건. `lint-script {project_id}` 로 전체 확인.")


def _cmd_lint_script(args: argparse.Namespace) -> int:
    """lint-script: full_script narration 의 TTS-위험 표기 리포트. --strict 면 issue 시 exit 1."""
    from orchestrator.project_manager import validate_project_id
    from orchestrator.script_io import load_full_script
    from orchestrator.tts_lint import lint_full_script

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        script = load_full_script(args.project_id)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError) as e:
        print(f"error: full_script 파싱 실패 — {e}", file=sys.stderr)
        return 1

    issues = lint_full_script(script)
    if not issues:
        print(f"lint-script: {args.project_id} narration 깨끗 (위험 표기 0건).")
        return 0
    print(f"lint-script: {args.project_id} — TTS-위험 표기 {len(issues)}건")
    for seg_id, issue in issues:
        print(f"  [{seg_id}] {issue.category}: {issue.snippet!r}\n      → {issue.hint}")
    return 1 if args.strict else 0


def manifest_sources_path(project_id: str) -> Path:
    """`projects/{pid}/02_sources/` 디렉토리."""
    from orchestrator.config import project_dir as _pdir

    return _pdir(project_id) / "02_sources"


def manifest_intake_path(project_id: str) -> Path:
    """`projects/{pid}/01_intake/` 디렉토리. project_manager 외부에서 쓰기 시 기본 경로."""
    from orchestrator.config import project_dir as _pdir

    return _pdir(project_id) / "01_intake"


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LegacyRemovedError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(3)

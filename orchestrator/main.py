"""orchestrator CLI 진입점.

서브커맨드
----------
- command-center --project {pid}            : Command Center TUI 진입
- new-project {pid} --title ... --category .: 새 프로젝트 생성
- resume {pid}                              : 기존 프로젝트 manifest 확인
- transition {pid} --to {state} [--reason]  : 상태 전이
- plan-intake {pid} [--backend claude|codex]: IntakePlannerWorker 호출 + 인테이크 상태 전이
- add-source {pid} --kind x-text|x-capture|article|document ...
                                            : 소스 레코드 추가 → intake/sources.json (v3.2.0, 18 §1). X 캡처는 판독 워커 초안
- confirm-source {pid} --id ID --by NAME [--posted-at ISO] : 사용자 확인(18 §7)
- list-sources {pid}                        : 소스 목록·확인 여부
- submit-intake {pid}                       : 확인된 소스로 source_verify 전이(미확인이 있으면 거부)
- verify-sources {pid} [--backend]          : 소스 검증(인용 대조) → intake/claims.json (source_verify 에 머문다, v3.2.0)
- build-research {pid} [--backend] [--force]: ResearchWorker → facts.json + research 전이 (v3.2.0, 17 §5.1)
- import-bundle {pid} --file <path> [--no-fetch] : v3.5.0 번들 어댑터 — 출처·claim 후보·원고/연출 초안(D-0063 작업 5)
- build-script {pid} [--backend]            : ScriptWorker 호출 → script.yaml + script_labels.json
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

    ads = sub.add_parser("add-source", help="소스 추가 → intake/sources.json (v3.2.0, 18 §1). x.com 은 열지 않는다")
    ads.add_argument("project_id", help="project_id")
    ads.add_argument("--kind", required=True, choices=["x-text", "x-capture", "article", "document"])
    ads.add_argument("--handle", help="X 핸들(@...) — x-text")
    ads.add_argument("--name", help="X 표시 이름 — x-text")
    ads.add_argument("--text", help="X 본문(x-text) 또는 기사·자료 본문(article·document, --text-file 대신)")
    ads.add_argument("--text-file", help="본문 파일(article·document)")
    ads.add_argument("--text-ko", help="X 본문 번역(x-text)")
    ads.add_argument("--lang", default=None, help="본문 언어 코드(기본: x-text en, 그 밖 ko)")
    ads.add_argument("--posted-at", help="X 게시 시각 ISO 8601")
    ads.add_argument("--image", help="X 캡처 이미지(png·jpg) — x-capture")
    ads.add_argument("--url", help="원문 URL(기록용 — X 링크는 열지 않는다. article 은 --fetch 로 가져오기)")
    ads.add_argument("--fetch", action="store_true", help="article: URL 에서 제목·본문 가져오기(X 호스트 거부)")
    ads.add_argument("--publisher", help="기사 매체")
    ads.add_argument("--headline", help="기사 제목(원문)")
    ads.add_argument("--headline-ko", help="기사 제목 번역")
    ads.add_argument("--pub-date", help="기사·자료 게시일 YYYY-MM-DD")
    ads.add_argument("--issuer", help="공문·자료 발행 기관")
    ads.add_argument("--title", help="공문·자료 제목")
    ads.add_argument("--fact", action="append", default=[], help="요지 한 줄(여러 번). 기사 원문 장문 복제 금지")
    ads.add_argument("--note", default="", help="사용자 메모")
    ads.add_argument("--backend", choices=["claude", "codex"], default="claude", help="x-capture 판독 LLM backend")

    cfs = sub.add_parser("confirm-source", help="소스 사용자 확인(계정·시각이 맞는지, 18 §7)")
    cfs.add_argument("project_id", help="project_id")
    cfs.add_argument("--id", required=True, help="소스 id(src_...)")
    cfs.add_argument("--by", required=True, help="확인한 사람")
    cfs.add_argument("--posted-at", help="게시 시각 고침(ISO 8601)")
    cfs.add_argument("--handle", help="핸들 고침")
    cfs.add_argument("--name", help="표시 이름 고침")
    cfs.add_argument("--text-ko", help="번역 고침")
    cfs.add_argument("--account-class", choices=["journalist", "public_figure", "private", "unknown"],
                     help="미등재 계정 분류(공식 여부는 목록으로만, 18 §3-1)")

    lss = sub.add_parser("list-sources", help="소스 목록·확인 여부")
    lss.add_argument("project_id", help="project_id")

    sin = sub.add_parser("submit-intake", help="확인된 소스로 intake → source_verify 전이(v3.2.0)")
    sin.add_argument("project_id", help="project_id")
    sin.add_argument("--reason", default="CLI submit-intake", help="전이 사유")

    # v3.2.0 삭제(D52) — 옛 소스 레지스트리 명령은 시끄럽게 실패
    lbs = sub.add_parser("build-source-registry", help="[삭제됨 v3.2.0] verify-sources 사용")
    lbs.add_argument("legacy_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    vsr = sub.add_parser("verify-sources", help="소스 검증(인용 대조) → intake/claims.json (source_verify, v3.2.0)")
    vsr.add_argument("project_id", help="project_id")
    vsr.add_argument("--backend", choices=["claude", "codex"], default="claude", help="LLM backend (기본: claude)")

    brs = sub.add_parser("build-research", help="ResearchWorker → facts.json 후 research 전이 (v3.2.0, 17 §5.1)")
    brs.add_argument("project_id", help="project_id")
    brs.add_argument("--backend", choices=["claude", "codex"], default="claude", help="LLM backend (기본: claude)")
    brs.add_argument("--force", action="store_true", help="유효한 facts.json 이 있어도 재실행(기본은 재사용)")

    imb = sub.add_parser("import-bundle", help="번들 → sources.json(확인 전)·bundle_claims·script.draft.yaml·bundle_materials (v3.5.0)")
    imb.add_argument("project_id", help="project_id")
    imb.add_argument("--file", required=True, help="report_bundle.json 경로")
    imb.add_argument("--no-fetch", action="store_true", help="번들 출처 기사를 가져오지 않는다(본문 없는 출처는 unresolved)")

    # v3.2.0 삭제(D52) — 옛 도시어 명령은 시끄럽게 실패
    lrd = sub.add_parser("build-research-dossier", help="[삭제됨 v3.2.0] build-research 사용")
    lrd.add_argument("legacy_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    bsc = sub.add_parser(
        "build-script",
        help=(
            "ScriptWorker 호출 → script.yaml·script_labels.json 생성 후 script_draft 전이 "
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
        help="유효한 script.yaml 이 있어도 worker 재실행 (기본은 idempotent skip).",
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
        help="script.yaml 원고 린트(script.lint — 금지 문구·발음 기호·강조어·출처·검증 라벨)",
    )
    lsc.add_argument("project_id", help="project_id")
    lsc.add_argument(
        "--strict", action="store_true",
        help="경고가 하나라도 있으면 exit 1 (CI 게이트용). 오류는 항상 exit 1.",
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
    apv.add_argument("--version", type=int, default=None, dest="chosen_version",
                     help="게이트 ② 에서 고를 AI 연출 판 번호(gate-view 판 목록, D-0049). 없으면 코드 선택 그대로")

    rjt = sub.add_parser("reject", help="승인 게이트 반려 → 16 §2 역전이 (코멘트 필수)")
    rjt.add_argument("--project", required=True)
    rjt.add_argument("--gate", required=True, choices=["script_approval", "preview_approval"])
    rjt.add_argument("--to", required=True, choices=["script_draft", "direction", "assets"])
    rjt.add_argument("--comment", required=True)
    rjt.add_argument("--by", default="user")

    rop = sub.add_parser("reopen", help="렌더 이후 사용자 피드백으로 연출을 다시 → direction (사유 필수, v4.7.0 D-0104 D4)")
    rop.add_argument("--project", required=True)
    rop.add_argument("--to", required=True, choices=["direction", "script_draft"])   # script_draft v5.6.0 PIPELINE-AP-017
    rop.add_argument("--reason", required=True)
    rop.add_argument("--by", default="user")

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

    if args.cmd == "add-source":
        return _cmd_add_source(args)

    if args.cmd == "confirm-source":
        return _cmd_confirm_source(args)

    if args.cmd == "list-sources":
        return _cmd_list_sources(args)

    if args.cmd == "submit-intake":
        return _cmd_submit_intake(args)

    if args.cmd == "build-source-registry":
        raise LegacyRemovedError("build-source-registry(v3.2.0 삭제 → verify-sources)")

    if args.cmd == "verify-sources":
        return _cmd_verify_sources(args)

    if args.cmd == "build-research":
        return _cmd_build_research(args)

    if args.cmd == "build-research-dossier":
        raise LegacyRemovedError("build-research-dossier(v3.2.0 삭제 → build-research)")

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
    if args.cmd == "reopen":
        return _cmd_reopen(args)

    parser.error("unknown command")
    return 2


def _cmd_reopen(args: argparse.Namespace) -> int:
    """reopen — 렌더 이후 → direction(v4.7.0 D-0104 D4). manifest.reopens 에 사유·연출 판 번호."""
    from orchestrator.errors import ManifestError
    from orchestrator.pipeline import next_action
    from orchestrator.project_manager import load_manifest, reopen

    try:
        before = load_manifest(args.project).current_state
        manifest = reopen(load_manifest(args.project), args.to, by=args.by, reason=args.reason)
    except (FileNotFoundError, ManifestError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    rec = manifest.reopens[-1]
    print(f"reopen: {before} → {manifest.current_state} (연출 판 v{rec.direction_version})")
    print(f"next   : {next_action(manifest.current_state)}")
    return 0


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
            manifest = approve_gate(manifest, args.gate, by=args.by, comment=args.comment, shown=shown,
                                    chosen_version=args.chosen_version)
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


def _source_pdir(project_id: str) -> Path:
    from orchestrator.config import project_dir
    from orchestrator.project_manager import validate_project_id

    validate_project_id(project_id)
    resume_project(project_id)          # 없으면 FileNotFoundError
    return project_dir(project_id)


def _cmd_import_bundle(args: argparse.Namespace) -> int:
    """import-bundle: 번들 어댑터(v3.5.0, D-0063 작업 5). 다음 단계: confirm-source → verify-sources → build-research → build-script."""
    from orchestrator import bundle_service as bs

    try:
        pdir = _source_pdir(args.project_id)
        r = bs.import_bundle(pdir, Path(args.file), fetch=not args.no_fetch)
    except (ValueError, FileNotFoundError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(bs.dump(r))
    return 0


def _cmd_add_source(args: argparse.Namespace) -> int:
    """add-source: 소스 레코드 한 건 → intake/sources.json (18 §1). 확인은 confirm-source 가 따로 한다."""
    from datetime import date, datetime

    from orchestrator import source_intake as si

    try:
        pdir = _source_pdir(args.project_id)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    def body() -> str:
        if args.text_file:
            return Path(args.text_file).read_text(encoding="utf-8")
        return args.text or ""

    try:
        if args.kind == "x-text":
            if not (args.handle and args.name and args.text):
                print("error: x-text 는 --handle --name --text 가 필요하다", file=sys.stderr)
                return 1
            rec = si.add_x_text(pdir, account_name=args.name, handle=args.handle, text=args.text, text_ko=args.text_ko,
                                lang=args.lang or "en", url=args.url, note=args.note,
                                posted_at=datetime.fromisoformat(args.posted_at) if args.posted_at else None)
        elif args.kind == "x-capture":
            if not args.image:
                print("error: x-capture 는 --image 가 필요하다", file=sys.stderr)
                return 1
            sid = si.stage_capture(pdir, Path(args.image))
            rec, errs = si.read_capture(pdir, sid, note=args.note, backend=args.backend)
            if rec is None:
                print(f"error: 캡처 판독 실패 — 레코드를 만들지 않았다: {errs}", file=sys.stderr)
                return 1
        elif args.kind == "article":
            text, headline, publisher, pub_day = body(), args.headline, args.publisher, args.pub_date
            if args.fetch:
                if not args.url:
                    print("error: --fetch 는 --url 이 필요하다", file=sys.stderr)
                    return 1
                got = si.fetch_article(args.url)
                text, headline = text or got["body"], headline or got["title"]
                publisher, pub_day = publisher or got["publisher"], pub_day or got["published_at"]
            if not (text and headline and publisher and pub_day):
                print("error: article 은 본문(--text/--text-file/--fetch)·--headline·--publisher·--pub-date 가 필요하다",
                      file=sys.stderr)
                return 1
            rec = si.add_article(pdir, publisher=publisher, headline=headline, headline_ko=args.headline_ko,
                                 published_at=date.fromisoformat(pub_day), body=text, url=args.url,
                                 key_facts=args.fact or None, lang=args.lang or "ko", note=args.note)
        else:
            if not (args.issuer and args.title and body()):
                print("error: document 는 --issuer --title 과 본문이 필요하다", file=sys.stderr)
                return 1
            rec = si.add_document(pdir, issuer=args.issuer, title=args.title, body=body(), key_facts=args.fact or None,
                                  published_at=date.fromisoformat(args.pub_date) if args.pub_date else None,
                                  url=args.url, lang=args.lang or "ko", note=args.note)
    except (si.SourceIntakeError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"id": rec.id, "type": rec.type, "confirmed": rec.confirmed,
                      **({"account_class": rec.account_class} if rec.type == "x_post" else {})}, ensure_ascii=False))
    return 0


def _cmd_confirm_source(args: argparse.Namespace) -> int:
    from datetime import datetime

    from orchestrator import source_intake as si

    try:
        pdir = _source_pdir(args.project_id)
        rec = si.confirm(pdir, args.id, args.by, posted_at=datetime.fromisoformat(args.posted_at) if args.posted_at else None,
                         handle=args.handle, account_name=args.name, text_ko=args.text_ko,
                         account_class=args.account_class)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"id": rec.id, "confirmed_by": rec.confirmed_by,
                      **({"account_class": rec.account_class} if rec.type == "x_post" else {})}, ensure_ascii=False))
    return 0


def _cmd_list_sources(args: argparse.Namespace) -> int:
    from orchestrator import source_intake as si

    try:
        pdir = _source_pdir(args.project_id)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for r in si.load_sources(pdir).sources:
        who = f"{r.account_name} {r.handle} [{r.account_class}]" if r.type == "x_post" else \
            (r.publisher if r.type == "article" else r.issuer)
        st = r.verification.status if r.verification else "-"
        print(f"{r.id}\t{r.type}\t{who}\t확인={'O' if r.confirmed else 'X'}\t검증={st}")
    print(si.dump(pdir))
    return 0


def _cmd_submit_intake(args: argparse.Namespace) -> int:
    """submit-intake(v3.2.0): 확인된 소스로 intake → source_verify. 미확인·소스 없음이면 거부(18 §7)."""
    from orchestrator.intake_service import SubmitSourcesError, submit_sources
    from orchestrator.project_manager import validate_project_id

    try:
        validate_project_id(args.project_id)
        manifest = submit_sources(args.project_id, reason=args.reason)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except SubmitSourcesError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"submit-intake 완료: {args.project_id}")
    _print_manifest_summary(manifest)
    return 0


def _cmd_verify_sources(args: argparse.Namespace) -> int:
    """verify-sources: SOURCE_VERIFY 에서 검증 워커 1회 + 코드 판정 → intake/claims.json. 전이 없음(다음은 build-research)."""
    from orchestrator.config import project_dir
    from orchestrator.project_manager import validate_project_id
    from orchestrator.source_verify import run_verify

    try:
        validate_project_id(args.project_id)
        manifest = resume_project(args.project_id)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    cur = manifest.current_state.value if hasattr(manifest.current_state, "value") else manifest.current_state
    if cur != ProjectState.SOURCE_VERIFY.value:
        print(f"error: 현재 상태 '{cur}' 에서는 verify-sources 를 실행할 수 없습니다(허용: source_verify)", file=sys.stderr)
        return 2
    res = run_verify(project_dir(args.project_id), backend=args.backend)
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


def _cmd_build_research(args: argparse.Namespace) -> int:
    """build-research: claims.json → ResearchWorker → facts.json + research 전이(orchestrator.research_service)."""
    from orchestrator.project_manager import validate_project_id
    from orchestrator.research_service import ResearchError, run_research_worker

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        manifest, outputs_summary, skipped = run_research_worker(args.project_id, backend=args.backend, force=args.force)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ResearchError as e:
        if e.kind == "state":
            print(f"error: {e} {e.errors or ''}", file=sys.stderr)
            return 2
        print(f"build-research 실패: {e} errors={e.errors}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"warning: 상태 전이 실패 — {e}", file=sys.stderr)
        return 2
    if skipped:
        print("build-research: 기존 facts.json 재사용 — worker 건너뜀 (재실행 원하면 --force).")
    print(f"build-research 완료: {args.project_id} (backend={args.backend}, skipped={skipped})")
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
        print("build-script: 기존 script.yaml 재사용 — worker 건너뜀 (재실행 원하면 --force).")
    print(f"build-script 완료: {args.project_id} (backend={args.backend}, skipped={skipped})")
    print(f"outputs : {outputs_summary}")
    _print_script_lint_summary(args.project_id)
    _print_manifest_summary(manifest)
    return 0


def _script_lint(project_id: str):  # noqa: ANN202 — StageResult
    """원고 린트는 엔진 CLI `script.lint`(engine_service direction_validate, v3.0.0). 금지 문구·발음 기호·강조어·출처·라벨."""
    from orchestrator.config import project_dir
    from orchestrator.engine_service import run_stage

    return run_stage(project_dir(project_id), "direction_validate")


def _print_script_lint_summary(project_id: str) -> None:
    """생성된 원고를 script.lint 로 검사해 요약 출력 (재발 방지)."""
    res = _script_lint(project_id)
    print(f"script-lint : 오류 {len(res.errors)} · 경고 {len(res.warnings)}")
    for line in (res.errors + res.warnings)[:20]:
        print(f"  - {line}")
    if len(res.errors) + len(res.warnings) > 20:
        print(f"  ... `lint-script {project_id}` 로 전체 확인.")


def _cmd_lint_script(args: argparse.Namespace) -> int:
    """lint-script: script.yaml 린트 리포트(script.lint CLI). 오류면 exit 1, --strict 면 경고도 exit 1."""
    from orchestrator.project_manager import validate_project_id

    try:
        validate_project_id(args.project_id)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    res = _script_lint(args.project_id)
    print(f"lint-script: {args.project_id} — 오류 {len(res.errors)} · 경고 {len(res.warnings)}")
    for line in res.errors:
        print(f"  오류 {line}")
    for line in res.warnings:
        print(f"  경고 {line}")
    if not res.ok:
        return 1
    return 1 if (args.strict and res.warnings) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LegacyRemovedError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(3)

"""Project Manager — ProjectManifest 의 생성·재개·전이 책임.

본 모듈은 `projects/{project_id}/project_manifest.json` 의 유일한 쓰기자입니다.
TUI / CLI 는 본 모듈을 통해서만 manifest 를 갱신합니다.

원칙
----
- `state_history` 는 append-only 입니다. 기존 항목 수정 금지.
- 모든 전이는 `state_machine.validate_transition` 을 통과해야 합니다.
- 디스크 쓰기는 항상 `updated_at` 을 갱신합니다.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.errors import ManifestCorruptError, ManifestVersionError
from orchestrator.state_machine import GATES, ROLLBACKS, coerce, is_rollback, next_state, validate_reopen, validate_transition
from schemas.models import (
    MANIFEST_SCHEMA_VERSION,
    Category,
    GateDecision,
    StageRecord,
    ProjectManifest,
    ProjectState,
    ReopenRecord,
    StateTransition,
)


logger = logging.getLogger(__name__)


MANIFEST_FILENAME = "project_manifest.json"

# project_id slug 정규식. 영문 소문자·숫자·하이픈·언더스코어를 허용하며,
# 첫 글자는 영문 소문자 또는 숫자여야 한다 (선두 `-` / `_` 차단).
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]*$")


def validate_project_id(project_id: str) -> str:
    """project_id slug 정책을 외부 호출 지점에서 강제하는 공개 가드.

    `new_project` 의 내부 검증을 web/CLI/외부 통합 코드에서 재사용할 수 있게 분리.
    v0.3.1: codex 4차 리뷰 C1 (web {project_id} path traversal) 의 구조적 조치.

    raises
    ------
    ValueError : project_id 가 _SLUG_RE 패턴에 맞지 않으면. 메시지에 사용자 입력 자체는
                 노출하지 않고 정책만 명시 (정찰 가치를 낮춤).
    """
    if not isinstance(project_id, str) or not _SLUG_RE.match(project_id):
        raise ValueError(
            "잘못된 project_id 입니다. "
            "영문 소문자·숫자·하이픈·언더스코어만 허용되며 첫 글자는 영숫자입니다."
        )
    return project_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 경로 헬퍼
# ---------------------------------------------------------------------------


def manifest_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return project_dir(project_id, cfg) / MANIFEST_FILENAME


# 16 §6 산출물 지도(프로젝트 기준 상대 경로). 오케스트레이터는 경로를 관리·표시할 뿐 엔진 입력을 쓰지 않는다(15 P1).
# direction 은 선언형 direction.yaml(17 §2, v3.1.0 — 옛 direction.py 삭제).
PROJECT_PATHS: dict[str, str] = {
    "sources": "intake/sources.json",          # v3.2.0 — 18 §2 소스 레코드
    "claims": "intake/claims.json",            # v3.2.0 — 18 §3-6 주장
    "screenshots": "intake/screenshots",       # X 캡처(비공개 보관)
    "script": "script.yaml",
    "script_labels": "script_labels.json",
    "plan": "plan.json",
    "tts": "tts",
    "assets": "assets",
    "media": "media",
    "direction": "direction.yaml",
    "prev": "prev",
    "prev_sheet": "prev/sheet.jpg",
    "prev_provenance": "prev/provenance.json",
    "out": "out",
    "final": "out/final.mp4",
    "provenance": "out/provenance.json",
}


def project_paths(project_id: str, cfg: Optional[AppConfig] = None) -> dict[str, Path]:
    """16 §6 산출물 절대 경로."""
    pdir = project_dir(project_id, cfg or load_config())
    return {k: pdir / v for k, v in PROJECT_PATHS.items()}


def artifact_status(project_id: str, cfg: Optional[AppConfig] = None) -> dict[str, bool]:
    """산출물 존재 여부(게이트·대시보드 표시용, 읽기만)."""
    return {k: p.exists() for k, p in project_paths(project_id, cfg).items()}


def _ensure_project_layout(project_id: str, cfg: AppConfig) -> Path:
    """프로젝트 디렉토리 골격을 만듭니다. 이미 존재하면 그대로 둡니다."""
    pdir = project_dir(project_id, cfg)
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks").mkdir(parents=True, exist_ok=True)
    (pdir / "03_tasks" / "task_results").mkdir(parents=True, exist_ok=True)
    (pdir / "logs" / "workers").mkdir(parents=True, exist_ok=True)
    return pdir


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _write_manifest(manifest: ProjectManifest, cfg: AppConfig) -> Path:
    """manifest 를 디스크에 직렬화. 항상 updated_at 을 현재시간으로 갱신.

    Atomic **visibility** vs **durability** 를 분리해 보장:

    - Visibility (외부 reader 가 half-written 상태를 보지 못함):
      tmp 파일에 먼저 write 한 뒤 `Path.replace` 로 교체. POSIX `rename(2)`
      와 Windows `os.replace` 는 동일한 inode/path 교체 의미에서 atomic.
      이 단계까지만 보장하면 TUI 의 라이브 manifest reload 같은 동시 reader
      가 깨진 JSON 을 잠깐도 볼 수 없다.

    - Durability (전원장애·강제종료에도 마지막 write 가 살아남음):
      tmp write 직후 `flush()` + `os.fsync()` 로 데이터가 디스크 매체에 도달함을
      보장한 뒤 rename. 추가로 부모 디렉토리도 fsync (POSIX 한정, Windows 는
      `O_DIRECTORY` 미지원이라 best-effort skip) 해 rename 사실 자체도 durable.

    - 예외 안전: write 중간 실패 시 tmp 파일을 best-effort cleanup. `replace`
      이후의 tmp 는 이미 path 로 옮겨졌으므로 잔존 없음.
    """
    manifest.updated_at = utc_now()
    path = manifest_path(manifest.project_id, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = manifest.model_dump_json(indent=2)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        # 실패 시 leftover tmp 정리 (best-effort, 실패해도 원본 예외만 전파).
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise
    # 부모 디렉토리 fsync — rename 사실 자체를 durable 하게 만든다 (POSIX).
    # Windows 는 directory fd open 이 막혀있어 best-effort skip.
    # 실패는 흡수하되 (rename 자체는 이미 visible) 운영자에게 신호하기 위해
    # platform · errno 를 포함해 warning 로그를 남긴다. docstring 의 durability
    # 보장 문구와 runtime 현실의 어긋남을 가시화.
    try:
        dir_fd = os.open(path.parent, getattr(os, "O_DIRECTORY", os.O_RDONLY))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as e:
        logger.warning(
            "dir fsync 실패 (rename durability 약화 가능): "
            "path=%s platform=%s errno=%s msg=%s",
            path.parent,
            os.name,
            e.errno,
            e,
        )
    return path


def load_manifest(project_id: str, cfg: Optional[AppConfig] = None) -> ProjectManifest:
    """디스크의 project_manifest.json 을 읽어 ProjectManifest 로 검증.

    손상 → ManifestCorruptError, schema_version ≠ 2 → ManifestVersionError (v3.0.0, 15 P6 — 폴백 없음).
    """
    cfg = cfg or load_config()
    path = manifest_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(f"project_manifest.json 이 없습니다: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ManifestCorruptError(path, f"JSON 아님 ({e})") from e
    if not isinstance(raw, dict):
        raise ManifestCorruptError(path, "최상위가 객체가 아님")
    found = raw.get("schema_version")
    if found != MANIFEST_SCHEMA_VERSION:
        raise ManifestVersionError(path, found, MANIFEST_SCHEMA_VERSION)
    try:
        return ProjectManifest.model_validate(raw)
    except ValidationError as e:
        raise ManifestCorruptError(path, f"스키마 불일치 ({e.error_count()}건: {e.errors()[0]['loc']})") from e


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


INITIAL_LINK_MAX_LEN: int = 2048
INITIAL_LINK_MAX_COUNT: int = 50


def _normalize_initial_links(links: Optional[list[str]]) -> list[str]:
    """사용자 제공 링크를 신뢰 경계에서 정규화.

    링크는 IntakePlanner 프롬프트에 삽입되므로 (trust boundary) 제어문자·개행으로
    프롬프트 구조를 깨거나 비-URL 텍스트로 prompt-injection 을 시도하지 못하게 한다.

    - 제어문자·공백을 모두 제거 (URL 에 내부 공백은 없음).
    - http:// 또는 https:// 로 시작하는 것만 유지 (그 외는 drop).
    - 링크당 최대 INITIAL_LINK_MAX_LEN, 최대 INITIAL_LINK_MAX_COUNT 개.
    """
    if not links:
        return []
    out: list[str] = []
    for raw in links:
        if raw is None:
            continue
        s = "".join(ch for ch in str(raw) if ch.isprintable() and not ch.isspace())
        if not (s.startswith("http://") or s.startswith("https://")):
            continue
        if len(s) > INITIAL_LINK_MAX_LEN:
            continue
        out.append(s)
        if len(out) >= INITIAL_LINK_MAX_COUNT:
            break
    return out


def new_project(
    project_id: str,
    title: str,
    category: Category | str,
    target_duration_min: int = 18,
    topic_summary: str = "",
    initial_links: Optional[list[str]] = None,
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """새 프로젝트 manifest 를 생성·저장하고 반환합니다.

    - 이미 동일 project_id 가 존재하면 FileExistsError.
    - project_id 는 영문 소문자/숫자/하이픈/언더스코어만 허용.
    - initial_links : 생성 시 사용자가 미리 제공한 자료 링크. IntakePlanner 가 참고.
    """
    cfg = cfg or load_config()

    validate_project_id(project_id)

    path = manifest_path(project_id, cfg)
    if path.exists():
        raise FileExistsError(
            f"이미 존재하는 프로젝트입니다: {project_id} (manifest: {path})"
        )

    cat = category if isinstance(category, Category) else Category(category)

    manifest = ProjectManifest(
        project_id=project_id,
        title=title,
        category=cat,
        target_duration_min=target_duration_min,
        topic_summary=topic_summary,
        initial_links=_normalize_initial_links(initial_links),
        current_state=ProjectState.CREATED,
        state_history=[],
        paths=dict(PROJECT_PATHS),   # v3.0.0 — 16 §6
    )

    _ensure_project_layout(project_id, cfg)
    _write_manifest(manifest, cfg)
    return manifest


def resume_project(
    project_id: str,
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """기존 프로젝트를 로드. manifest 가 없으면 FileNotFoundError.

    manifest 검증을 먼저 수행한 뒤 누락된 하위 폴더만 보강합니다
    (미존재 프로젝트로 resume 호출 시 빈 폴더가 생기는 것을 막기 위해).
    """
    cfg = cfg or load_config()
    manifest = load_manifest(project_id, cfg)
    _ensure_project_layout(project_id, cfg)
    return manifest


def transition_state(
    manifest: ProjectManifest,
    next_state: ProjectState | str,
    reason: str = "",
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """current_state 를 next_state 로 전이.

    잘못된 전이는 ValueError. state_history 에 append-only 로 기록 후 디스크 저장.
    승인 게이트(16 §5)에서 나가는 전이는 `approve_gate`·`reject_gate` 로만 한다 — 여기서는 ValueError.
    """
    cur = coerce(manifest.current_state)
    if cur in GATES:
        raise ValueError(
            f"'{cur.value}' 는 사용자 승인 게이트다 — approve / reject 로만 나간다(16 §5)"
        )
    return _apply_transition(manifest, next_state, reason, cfg or load_config())


def _apply_transition(
    manifest: ProjectManifest, next_state: ProjectState | str, reason: str, cfg: AppConfig, reopen: bool = False
) -> ProjectManifest:
    target = coerce(next_state)
    if reopen:
        validate_reopen(manifest.current_state, target)
    else:
        validate_transition(manifest.current_state, target)
    if target == ProjectState.SCRIPT_APPROVAL:   # v3.2.0 18 §7 — claim id 없는 주장 문장이 있으면 게이트 ① 전에 차단
        from orchestrator.source_completeness_checker import check_script_sources  # noqa: PLC0415

        blocked = check_script_sources(project_dir(manifest.project_id, cfg))
        if blocked:
            raise ValueError("원고 출처 미완결 — script_approval 로 갈 수 없다(18 §7):\n" + "\n".join(blocked[:20]))
    manifest.state_history.append(StateTransition(
        from_state=coerce(manifest.current_state), to_state=target, transitioned_at=utc_now(), reason=reason,
    ))
    manifest.current_state = target.value   # type: ignore[assignment] — 로드한 manifest 와 같은 모양(use_enum_values)
    _write_manifest(manifest, cfg)
    return manifest


def latest_direction_version(pdir: Path) -> Optional[int]:
    """direction.v{N}.yaml 중 가장 큰 N(없으면 None)."""
    ns = [int(m.group(1)) for f in pdir.glob("direction.v*.yaml") if (m := re.fullmatch(r"direction\.v(\d+)\.yaml", f.name))]
    return max(ns) if ns else None


def reopen(
    manifest: ProjectManifest,
    to: ProjectState | str,
    by: str,
    reason: str,
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """렌더 이후 → direction 되돌림(v4.7.0 back_and_forth D-0104 D4). 사유 필수, manifest.reopens 에 사유·판 번호 기록.
    사유는 이 프로젝트의 수정 지시로만 남긴다(규칙·프롬프트 자동 반영 금지, 15 P11)."""
    cfg = cfg or load_config()
    tgt = coerce(to)
    validate_reopen(manifest.current_state, tgt)
    if not reason.strip():
        raise ValueError("reopen 사유(reason)가 비었다 — 무엇을 왜 다시 연출하는지 적는다")
    ver = latest_direction_version(project_dir(manifest.project_id, cfg))
    manifest.reopens.append(ReopenRecord(from_state=coerce(manifest.current_state), to_state=tgt, by=by, reason=reason,
                                         direction_version=ver))
    return _apply_transition(manifest, tgt, f"reopen → {tgt.value} — {by}: {reason}", cfg, reopen=True)


def record_stage(manifest: ProjectManifest, record: StageRecord, cfg: Optional[AppConfig] = None) -> ProjectManifest:
    """엔진 단계 실행 요약을 append 하고 저장한다(상태는 바꾸지 않는다)."""
    manifest.stage_records.append(record)
    _write_manifest(manifest, cfg or load_config())
    return manifest


def _require_gate(manifest: ProjectManifest, gate: ProjectState | str) -> ProjectState:
    cur = coerce(manifest.current_state)
    g = coerce(gate)
    if g not in GATES:
        raise ValueError(f"'{g.value}' 는 승인 게이트가 아니다 — 게이트: {', '.join(sorted(x.value for x in GATES))}")
    if cur != g:
        raise ValueError(f"현재 상태 '{cur.value}' — '{g.value}' 게이트에 있지 않다")
    return g


def approve_gate(
    manifest: ProjectManifest,
    gate: ProjectState | str,
    by: str,
    comment: str = "",
    shown: Optional[dict[str, str]] = None,
    cfg: Optional[AppConfig] = None,
    chosen_version: Optional[int] = None,
) -> ProjectManifest:
    """게이트 승인 → 기록(누가·언제·코멘트·본 것) → 다음 상태.
    chosen_version(게이트 ② 전용, D-0049 쟁점 3): 사람이 고른 AI 연출 판을 direction.yaml 로 되돌리고 qa_loop.json 선택을 사람으로 기록."""
    cfg = cfg or load_config()
    g = _require_gate(manifest, gate)
    nxt = next_state(g)
    assert nxt is not None
    if g == ProjectState.PREVIEW_APPROVAL:   # 콘티 판 의무(WORKFLOWS W0, PIPELINE-AP-014) — 건너뛰면 게이트 ② 승인 불가
        shown = {**(shown or {}), "animatic": require_animatic(project_dir(manifest.project_id, cfg))}
    if chosen_version is not None:
        if g != ProjectState.PREVIEW_APPROVAL:
            raise ValueError("chosen_version 은 게이트 ②(preview_approval)에서만 쓴다")
        _choose_version(project_dir(manifest.project_id, cfg), chosen_version, by)
    manifest.gate_decisions.append(GateDecision(gate=g, decision="approved", by=by, comment=comment, shown=shown or {},
                                                chosen_version=chosen_version))
    return _apply_transition(manifest, nxt, f"{g.value} 승인 — {by}", cfg)


class AnimaticMissingError(ValueError):
    """게이트 ② 승인 전에 현재 음성 타임라인의 콘티 판(out/animatic.mp4)이 없다."""


ANIMATIC_TOTAL_TOL_SEC = 0.05   # 콘티 판 total_sec ↔ plan.json total 허용 차(같은 음성 타임라인인지)


def require_animatic(pdir: Path) -> str:
    """콘티 판이 현재 음성 타임라인(plan.json)으로 렌더됐는지 확인하고 게이트 기록용 한 줄을 돌려준다.
    없거나 옛 음성이면 AnimaticMissingError — 우회 플래그 없음(사용자 결정 2026-10-01, PIPELINE-AP-014)."""
    how = f"`python -m engine.render {pdir} --animatic` 로 콘티 판을 만들고 사용자 흐름 검토를 받은 뒤 승인한다(WORKFLOWS W0)"
    pp = pdir / "out" / "animatic_provenance.json"
    if not pp.exists():
        raise AnimaticMissingError(f"콘티 판 없음({pp}) — 게이트 ② 는 콘티 판 없이 승인할 수 없다. {how}")
    prov = json.loads(pp.read_text(encoding="utf-8"))
    run = prov.get("animatic_run")
    if not prov.get("animatic") or not isinstance(run, dict):
        raise AnimaticMissingError(f"{pp.name} 에 animatic_run 기록이 없다 — 콘티 판 렌더가 끝나지 않았다. {how}")
    plan = pdir / "plan.json"
    if plan.exists():
        total = float(json.loads(plan.read_text(encoding="utf-8"))["total"])
        if abs(float(prov.get("total_sec", -1.0)) - total) > ANIMATIC_TOTAL_TOL_SEC:
            raise AnimaticMissingError(f"콘티 판 길이 {prov.get('total_sec')}초 ≠ 현재 plan {total:.2f}초 — 옛 음성으로 만든 콘티 판이다. {how}")
    return f"{run.get('output')} · {prov.get('total_sec')}초 · direction {run.get('direction_sha1') or '기록 없음'}"


def _choose_version(pdir: Path, version: int, by: str) -> None:
    from engine.qa import QALoopPick, QALoopRecord  # noqa: PLC0415
    from workers.direction_io import restore_version  # noqa: PLC0415

    p = pdir / "prev" / "qa_loop.json"
    if not p.exists():
        raise ValueError("AI 검수 기록(prev/qa_loop.json)이 없다 — 고를 판이 없음")
    rec = QALoopRecord.model_validate_json(p.read_text(encoding="utf-8"))
    if version not in {r.version for r in rec.rounds}:
        raise ValueError(f"v{version} 은 판 목록에 없다: {[r.version for r in rec.rounds]}")
    restore_version(pdir, version)
    rec.selected = QALoopPick(version=version, by="human", reason=f"게이트 ② {by} 선택")
    p.write_text(rec.model_dump_json(indent=1), encoding="utf-8")


def reject_gate(
    manifest: ProjectManifest,
    gate: ProjectState | str,
    to: ProjectState | str,
    by: str,
    comment: str,
    shown: Optional[dict[str, str]] = None,
    cfg: Optional[AppConfig] = None,
) -> ProjectManifest:
    """게이트 반려 → 16 §2 역전이. 코멘트는 이 프로젝트의 수정 지시로만 남긴다(규칙·프롬프트 자동 반영 금지, 15 P11)."""
    cfg = cfg or load_config()
    g = _require_gate(manifest, gate)
    tgt = coerce(to)
    if not is_rollback(g, tgt):
        allowed = ", ".join(sorted(x.value for x in ROLLBACKS[g]))
        raise ValueError(f"'{g.value}' 반려는 {allowed} 로만 되돌린다(16 §2): {tgt.value}")
    if not comment.strip():
        raise ValueError("반려 사유(comment)가 비었다 — 16 §2 '반려 사유 첨부'")
    manifest.gate_decisions.append(GateDecision(gate=g, decision="rejected", by=by, comment=comment,
                                                rollback_to=tgt, shown=shown or {}))
    return _apply_transition(manifest, tgt, f"{g.value} 반려 → {tgt.value} — {by}: {comment}", cfg)

"""ProjectManifest 상태 전이 규칙 (v3.0.0, docs/handoff/16 §2).

전이 규칙:
- 앞으로는 `SEQUENCE` 의 바로 다음 상태로만 간다. 임의 점프는 금지(SCHEMA-AP-001).
- 뒤로는 `ROLLBACKS` 표의 반려 되돌림만 허용한다(16 §2 역전이).
  SCRIPT_APPROVAL → SCRIPT_DRAFT, PREVIEW_APPROVAL → DIRECTION·SCRIPT_DRAFT·ASSETS.
- 게이트 실패(권리·출처·린트)는 전이가 아니다 — 그 단계에 머문다. 폴백으로 다음 단계 진행 금지(15 P6).
- 동일 상태로의 재전이는 허용하지 않는다. DONE 은 종착이다.

본 모듈은 순수 함수만 제공합니다. 디스크 I/O 는 project_manager.py 가 담당합니다.
"""

from __future__ import annotations

from schemas.models import ProjectState


# 16 §2 의 앞 방향 순서.
SEQUENCE: list[ProjectState] = [
    ProjectState.CREATED,
    ProjectState.INTAKE,
    ProjectState.SOURCE_VERIFY,
    ProjectState.RESEARCH,
    ProjectState.SCRIPT_DRAFT,
    ProjectState.SCRIPT_APPROVAL,
    ProjectState.VOICE_TIMELINE,
    ProjectState.ASSETS,
    ProjectState.DIRECTION,
    ProjectState.PREVIEW_QA,
    ProjectState.PREVIEW_APPROVAL,
    ProjectState.RENDER,
    ProjectState.AUDIO_MIX,
    ProjectState.DELIVER,
    ProjectState.DONE,
]

# 16 §2 역전이 — 승인 게이트의 반려만 뒤로 간다.
ROLLBACKS: dict[ProjectState, frozenset[ProjectState]] = {
    ProjectState.SCRIPT_APPROVAL: frozenset({ProjectState.SCRIPT_DRAFT}),
    ProjectState.PREVIEW_APPROVAL: frozenset({
        ProjectState.DIRECTION,      # 연출 문제
        ProjectState.SCRIPT_DRAFT,   # 내용 문제
        ProjectState.ASSETS,         # 자료 교체
    }),
}

# 사용자 승인 게이트(16 §5). 게이트에서 앞으로 가는 전이는 승인 기록이 있어야 한다(project_manager).
GATES: frozenset[ProjectState] = frozenset(ROLLBACKS)


def coerce(state: ProjectState | str) -> ProjectState:
    """manifest 의 current_state 는 use_enum_values=True 때문에 str 일 수 있다."""
    if isinstance(state, ProjectState):
        return state
    return ProjectState(state)


def next_state(current: ProjectState | str) -> ProjectState | None:
    """앞 방향 다음 상태. DONE 이면 None."""
    idx = SEQUENCE.index(coerce(current))
    return SEQUENCE[idx + 1] if idx + 1 < len(SEQUENCE) else None


def allowed_next_states(current: ProjectState | str) -> set[ProjectState]:
    """현재 상태에서 전이 가능한 상태 집합(앞 1칸 + 역전이)."""
    cur = coerce(current)
    allowed: set[ProjectState] = set(ROLLBACKS.get(cur, frozenset()))
    nxt = next_state(cur)
    if nxt is not None:
        allowed.add(nxt)
    return allowed


def is_rollback(current: ProjectState | str, target: ProjectState | str) -> bool:
    return coerce(target) in ROLLBACKS.get(coerce(current), frozenset())


def validate_transition(current: ProjectState | str, target: ProjectState | str) -> None:
    """전이가 허용되지 않으면 ValueError 를 던집니다.

    raises
    ------
    ValueError : 동일 상태 전이, 또는 허용되지 않은 점프.
    """
    cur = coerce(current)
    tgt = coerce(target)

    if cur == tgt:
        raise ValueError(
            f"이미 '{cur.value}' 상태입니다. 동일 상태로의 전이는 허용되지 않습니다."
        )

    allowed = allowed_next_states(cur)
    if tgt not in allowed:
        allowed_str = ", ".join(sorted(s.value for s in allowed)) or "(없음)"
        raise ValueError(
            f"잘못된 상태 전이: '{cur.value}' → '{tgt.value}'. "
            f"허용된 다음 상태: {allowed_str}"
        )

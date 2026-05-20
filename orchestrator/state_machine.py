"""Project state machine.

`docs/02_SYSTEM_ARCHITECTURE.md` §4 의 상태 전이도를 코드로 강제합니다.

원칙
----
- 모든 전이는 `ALLOWED_TRANSITIONS` 표에 명시되어야 합니다.
- 표에 없는 전이는 `InvalidTransitionError` 로 거부됩니다 (SCHEMA-AP 카탈로그 부합).
- 본 모듈은 순수 함수만 노출합니다. 디스크 I/O 는 `project_manager` 가 담당.
"""

from __future__ import annotations

from schemas.models import ProjectState


class InvalidTransitionError(ValueError):
    """허용되지 않은 상태 전이 시도. ValueError 하위 클래스."""


# docs/02_SYSTEM_ARCHITECTURE.md §4 의 선형 흐름.
# Review Gate 의 revision_requested 분기는 Phase 11 에서 카탈로그로 추가.
_LINEAR_ORDER: list[ProjectState] = [
    ProjectState.CREATED,
    ProjectState.INTAKE_PLANNING,
    ProjectState.INTAKE_PENDING_USER,
    ProjectState.SOURCE_COLLECTING,
    ProjectState.SOURCE_COMPLETENESS_REVIEW,
    ProjectState.RESEARCH_IN_PROGRESS,
    ProjectState.BLUEPRINT_REVIEW,
    ProjectState.SCRIPT_WRITING,
    ProjectState.SCRIPT_REVIEW,
    ProjectState.SCENE_PLANNING,
    ProjectState.ASSET_PRODUCTION,
    ProjectState.SCENE_REVIEW,
    ProjectState.AUDIO_PRODUCTION,
    ProjectState.RENDER_DEBUG,
    ProjectState.DEBUG_REVIEW,
    ProjectState.RENDER_PREVIEW,
    ProjectState.PREVIEW_REVIEW,
    ProjectState.THUMBNAIL_PRODUCTION,
    ProjectState.THUMBNAIL_REVIEW,
    ProjectState.RENDER_FINAL,
    ProjectState.FINAL_REVIEW,
    ProjectState.PUBLISH_READY,
    ProjectState.PUBLISHED,
    ProjectState.ARCHIVED,
]


def _build_allowed() -> dict[ProjectState, frozenset[ProjectState]]:
    table: dict[ProjectState, set[ProjectState]] = {s: set() for s in ProjectState}
    # 선형 다음 단계.
    for i in range(len(_LINEAR_ORDER) - 1):
        table[_LINEAR_ORDER[i]].add(_LINEAR_ORDER[i + 1])
    # 어디서든 ARCHIVED 로 (사용자가 명시적으로 폐기).
    for s in ProjectState:
        if s is not ProjectState.ARCHIVED:
            table[s].add(ProjectState.ARCHIVED)
    return {k: frozenset(v) for k, v in table.items()}


ALLOWED_TRANSITIONS: dict[ProjectState, frozenset[ProjectState]] = _build_allowed()


def _coerce(state: ProjectState | str) -> ProjectState:
    if isinstance(state, ProjectState):
        return state
    try:
        return ProjectState(state)
    except ValueError as e:
        raise InvalidTransitionError(
            f"알 수 없는 상태값: {state!r}. ProjectState enum 멤버여야 합니다."
        ) from e


def is_allowed(current: ProjectState | str, target: ProjectState | str) -> bool:
    return _coerce(target) in ALLOWED_TRANSITIONS[_coerce(current)]


def validate_transition(current: ProjectState | str, target: ProjectState | str) -> None:
    """허용되지 않으면 InvalidTransitionError 를 던집니다.

    동일 상태로의 전이도 허용되지 않습니다 (no-op 호출자 책임).
    """
    cur = _coerce(current)
    tgt = _coerce(target)
    if tgt == cur:
        raise InvalidTransitionError(
            f"현재 상태와 동일한 상태로 전이할 수 없습니다: {cur.value}"
        )
    if tgt not in ALLOWED_TRANSITIONS[cur]:
        allowed = ", ".join(sorted(s.value for s in ALLOWED_TRANSITIONS[cur])) or "(없음)"
        raise InvalidTransitionError(
            f"허용되지 않은 상태 전이: {cur.value} → {tgt.value}. "
            f"현 상태에서 허용된 다음 상태: {allowed}."
        )


def next_linear_state(current: ProjectState | str) -> ProjectState | None:
    """선형 다음 상태. 마지막 상태(ARCHIVED)면 None."""
    cur = _coerce(current)
    try:
        idx = _LINEAR_ORDER.index(cur)
    except ValueError:
        return None
    if idx + 1 >= len(_LINEAR_ORDER):
        return None
    return _LINEAR_ORDER[idx + 1]

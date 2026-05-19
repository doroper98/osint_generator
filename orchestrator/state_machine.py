"""ProjectManifest 상태 전이 규칙.

docs/02_SYSTEM_ARCHITECTURE.md §4 의 선형 흐름을 정식 SSOT 로 따릅니다.
임의 점프는 금지됩니다 (SCHEMA-AP-001).

전이 규칙:
- 각 상태는 docs/02 §4 의 다음 상태로만 전이할 수 있다.
- 어떤 상태에서든 `archived` 로 종료할 수 있다 (사용자가 수동 폐기).
- 동일 상태로의 재전이는 허용하지 않는다 (no-op 은 transition 호출 자체를 하지 마라).

본 모듈은 순수 함수만 제공합니다. 디스크 I/O 는 project_manager.py 가 담당합니다.
"""

from __future__ import annotations

from schemas.models import ProjectState


# docs/02_SYSTEM_ARCHITECTURE.md §4 의 선형 시퀀스.
LINEAR_SEQUENCE: list[ProjectState] = [
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


def _coerce(state: ProjectState | str) -> ProjectState:
    """Pydantic use_enum_values=True 때문에 manifest 의 current_state 가
    str 로 들어올 수 있어 안전하게 enum 으로 변환합니다.
    """
    if isinstance(state, ProjectState):
        return state
    return ProjectState(state)


def allowed_next_states(current: ProjectState | str) -> set[ProjectState]:
    """현재 상태에서 전이 가능한 다음 상태 집합."""
    current = _coerce(current)
    if current == ProjectState.ARCHIVED:
        return set()

    allowed: set[ProjectState] = set()

    # 선형 시퀀스의 다음 상태
    try:
        idx = LINEAR_SEQUENCE.index(current)
        if idx + 1 < len(LINEAR_SEQUENCE):
            allowed.add(LINEAR_SEQUENCE[idx + 1])
    except ValueError:
        pass

    # 어디서든 archived 종료 허용 (이미 archived 인 경우는 위에서 차단)
    allowed.add(ProjectState.ARCHIVED)

    return allowed


def validate_transition(current: ProjectState | str, target: ProjectState | str) -> None:
    """전이가 허용되지 않으면 ValueError 를 던집니다.

    raises
    ------
    ValueError : 동일 상태 전이, 또는 허용되지 않은 점프.
    """
    current = _coerce(current)
    target = _coerce(target)

    if current == target:
        raise ValueError(
            f"이미 '{current.value}' 상태입니다. 동일 상태로의 전이는 허용되지 않습니다."
        )

    allowed = allowed_next_states(current)
    if target not in allowed:
        allowed_str = ", ".join(sorted(s.value for s in allowed)) or "(없음)"
        raise ValueError(
            f"잘못된 상태 전이: '{current.value}' → '{target.value}'. "
            f"허용된 다음 상태: {allowed_str}"
        )

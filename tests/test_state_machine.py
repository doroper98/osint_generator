"""SCHEMA-AP-001 회귀 테스트.

`orchestrator.state_machine.validate_transition` 의 다섯 가지 보호 조건을 회귀화:

1. 정상 선형 전이 — `LINEAR_SEQUENCE` 의 인접 페어는 허용된다.
2. 임의 점프 거부 — 인접하지 않은 상태 (예: created → render_final) 는 거부된다.
3. self-loop 거부 — 동일 상태로의 재전이 (예: created → created) 는 거부된다.
4. ARCHIVED 어디서든 도달 — 비-archived 상태에서 archived 로의 전이는 항상 허용된다.
5. ARCHIVED 에서 추가 전이 거부 — archived 는 종착이므로 어떤 상태로도 못 나간다.

실행:
    python -m unittest tests.test_state_machine
"""

from __future__ import annotations

import unittest

from orchestrator.state_machine import (
    LINEAR_SEQUENCE,
    allowed_next_states,
    validate_transition,
)
from schemas.models import ProjectState


class LinearSequenceTransitions(unittest.TestCase):
    """① 정상 선형 — LINEAR_SEQUENCE 의 모든 인접 페어는 ValueError 없이 통과."""

    def test_every_adjacent_pair_is_allowed(self) -> None:
        for current, target in zip(LINEAR_SEQUENCE, LINEAR_SEQUENCE[1:]):
            with self.subTest(current=current.value, target=target.value):
                # 예외 없이 통과해야 한다.
                validate_transition(current, target)

    def test_string_input_is_coerced(self) -> None:
        """manifest 의 current_state 가 use_enum_values=True 로 str 인 케이스도 허용."""
        validate_transition("created", "intake_planning")


class ArbitraryJumpRejected(unittest.TestCase):
    """② 임의 점프 거부 — 인접하지 않은 전이는 ValueError."""

    def test_created_to_render_final_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_transition(ProjectState.CREATED, ProjectState.RENDER_FINAL)
        self.assertIn("잘못된 상태 전이", str(ctx.exception))
        # 허용된 다음 상태 힌트가 메시지에 포함되어야 한다.
        self.assertIn("intake_planning", str(ctx.exception))

    def test_backwards_jump_is_rejected(self) -> None:
        # 역방향 전이도 인접 페어 룰을 깨므로 거부.
        with self.assertRaises(ValueError):
            validate_transition(
                ProjectState.SCRIPT_WRITING, ProjectState.INTAKE_PLANNING
            )


class SelfLoopRejected(unittest.TestCase):
    """③ self-loop 거부 — 동일 상태 재전이는 ValueError."""

    def test_same_state_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_transition(ProjectState.CREATED, ProjectState.CREATED)
        self.assertIn("동일 상태", str(ctx.exception))

    def test_archived_self_loop_is_also_rejected(self) -> None:
        # archived 의 self-loop 는 ②(allowed 빈 집합) 와 ③(동일 상태) 두 가드 모두에
        # 걸린다. 어느 메시지든 ValueError 면 OK.
        with self.assertRaises(ValueError):
            validate_transition(ProjectState.ARCHIVED, ProjectState.ARCHIVED)


class ArchivedReachableFromAnywhere(unittest.TestCase):
    """④ ARCHIVED 어디서든 도달 — 비-archived 의 모든 상태에서 archived 로 갈 수 있다."""

    def test_archived_is_always_in_allowed_set(self) -> None:
        for current in LINEAR_SEQUENCE:
            if current == ProjectState.ARCHIVED:
                continue
            with self.subTest(current=current.value):
                self.assertIn(ProjectState.ARCHIVED, allowed_next_states(current))

    def test_transition_to_archived_from_arbitrary_states(self) -> None:
        for current in [
            ProjectState.CREATED,
            ProjectState.SOURCE_COLLECTING,
            ProjectState.SCRIPT_WRITING,
            ProjectState.PUBLISH_READY,
        ]:
            with self.subTest(current=current.value):
                validate_transition(current, ProjectState.ARCHIVED)


class ArchivedIsTerminal(unittest.TestCase):
    """⑤ ARCHIVED 에서 추가 전이 거부 — archived 는 종착, 어떤 상태로도 못 나간다."""

    def test_allowed_next_states_is_empty(self) -> None:
        self.assertEqual(allowed_next_states(ProjectState.ARCHIVED), set())

    def test_archived_to_any_other_state_is_rejected(self) -> None:
        for target in [
            ProjectState.CREATED,
            ProjectState.INTAKE_PLANNING,
            ProjectState.PUBLISHED,
        ]:
            with self.subTest(target=target.value):
                with self.assertRaises(ValueError):
                    validate_transition(ProjectState.ARCHIVED, target)


if __name__ == "__main__":
    unittest.main()

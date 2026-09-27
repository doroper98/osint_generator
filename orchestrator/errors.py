"""오케스트레이터 공용 예외 (v2.0.0).

`docs/handoff/15` P6 — 옛 경로는 조용히 폴백하지 않고 시끄럽게 실패한다.
"""

from __future__ import annotations


class LegacyRemovedError(RuntimeError):
    """v2.0.0 에서 삭제된 옛 영상 경로(장면 1:1 빌더·옛 렌더러·옛 오디오)를 호출했을 때.

    대체 경로는 docs/handoff/16 §4 `engine_service` (Phase 6.8). 옛 코드는
    `archive/hyperframes-briefing` 브랜치에 보존돼 있다.
    """

    def __init__(self, command: str) -> None:
        self.command = command
        super().__init__(
            f"{command}는 v2.0.0에서 삭제됨 — 대체 경로는 docs/handoff/16 §4 engine_service "
            f"(Phase 6.8). archive/hyperframes-briefing 참조"
        )

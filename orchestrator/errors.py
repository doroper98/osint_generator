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


class ManifestError(RuntimeError):
    """project_manifest.json 을 믿을 수 없을 때의 공통 부모 (v3.0.0, 16 §3, 15 P6)."""


class ManifestCorruptError(ManifestError):
    """manifest 가 JSON 이 아니거나 스키마를 통과하지 못할 때. 'created' 로 폴백하지 않는다."""

    def __init__(self, path: object, detail: str) -> None:
        self.path = path
        super().__init__(f"project_manifest.json 손상: {path} — {detail}")


class ManifestVersionError(ManifestError):
    """schema_version 이 현재(2)와 다른 manifest. 변환하지 않고 재생성을 요구한다(19 §3.6)."""

    def __init__(self, path: object, found: object, expected: int) -> None:
        self.path = path
        self.found = found
        super().__init__(
            f"v{found} manifest — 재생성 필요: {path} (현재 schema_version {expected}, "
            f"상태 머신이 16 §2 로 바뀌었다. `python -m orchestrator.main new-project` 로 다시 만든다)"
        )

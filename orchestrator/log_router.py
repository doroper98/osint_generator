"""Log Router.

Worker subprocess 의 stdout/stderr 를 비동기로 읽어
TUI 패널 (콜백) 과 로그 파일에 동시에 기록합니다.

설계 의도
---------
- Worker 가 1줄 1이벤트 원칙으로 출력하면 패널이 깨끗합니다.
- 패널 버퍼 무한 증가를 막기 위해 ring buffer (config.command_center.log_panel_max_lines).
- 본 모듈은 TUI 에 의존하지 않습니다. 콜백만 호출합니다 (테스트 용이성).
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


LogCallback = Callable[[int, str, str], None]
"""콜백 시그니처: (slot_id, stream_kind, line)
   stream_kind ∈ {"stdout", "stderr", "system"}."""


@dataclass
class LogBuffer:
    """TUI 패널에 표시할 ring buffer."""

    max_lines: int = 500
    lines: deque[tuple[str, str]] = field(default_factory=deque)  # (kind, line)

    def append(self, kind: str, line: str) -> None:
        self.lines.append((kind, line))
        while len(self.lines) > self.max_lines:
            self.lines.popleft()

    def snapshot(self) -> list[tuple[str, str]]:
        return list(self.lines)


class LogRouter:
    """Worker 한 명당 LogRouter 인스턴스가 1:1 매핑됩니다.

    callback 은 main TUI 스레드 (asyncio loop) 안에서 호출되므로
    Textual 위젯을 직접 갱신해도 안전합니다.
    """

    def __init__(
        self,
        slot_id: int,
        task_id: str,
        log_file: Path,
        callback: Optional[LogCallback] = None,
        max_lines: int = 500,
    ) -> None:
        self.slot_id = slot_id
        self.task_id = task_id
        self.log_file = log_file
        self.callback = callback
        self.buffer = LogBuffer(max_lines=max_lines)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        # truncate 방지: 같은 task_id 가 재실행되면 append 로 이어 붙입니다.
        self._file = self.log_file.open("a", encoding="utf-8")

    def emit(self, kind: str, line: str) -> None:
        """system / heartbeat 등 명시적 1줄 emit."""
        self.buffer.append(kind, line)
        self._file.write(f"[{kind}] {line}\n")
        self._file.flush()
        if self.callback:
            self.callback(self.slot_id, kind, line)

    async def consume_stream(self, stream: asyncio.StreamReader | None, kind: str) -> None:
        """subprocess 의 stdout 또는 stderr StreamReader 를 끝까지 읽습니다."""
        if stream is None:
            return
        while True:
            line_bytes = await stream.readline()
            if not line_bytes:
                break
            try:
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            except Exception:
                line = repr(line_bytes)
            self.emit(kind, line)

    def close(self) -> None:
        try:
            self._file.close()
        except Exception:
            pass

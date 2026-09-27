"""렌더 컨텍스트 — v3 의 모듈 전역(RESERVED·SHIPS·_SC·SENT…)을 한 객체로 모았다 (v2.1.0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from engine.assets import Assets
from engine.credits import Credits
from engine.timebase import Timebase


@dataclass
class RenderCtx:
    assets: Assets
    tb: Timebase
    credits: Optional[Credits] = None
    reserved: list[tuple[float, float, float, float]] = field(default_factory=list)  # 프레임마다 비운다(라벨 충돌 회피)
    cache: dict[str, Any] = field(default_factory=dict)

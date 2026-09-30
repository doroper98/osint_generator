"""사진 배경 무대(BackdropStage) — 지도가 중심이 아닌 주제의 캔버스 (v5.1.0, back_and_forth D-0121 §B·D-0123 §1, 사용자 결정 D106·D108).

월드 좌표 = 화면 설계 px(854×480). 앵커 없음(카메라 `{}` — 이동 없음, `fixed_w` = 화면 폭). 무대 자체는 바탕색만 칠한다.
배경 사진은 `backdrop` 이벤트(engine/layers/backdrop.py)가 장면마다 블러·dim·채도 낮춤으로 깔고 crossfade 로 바꾼다.
사진은 미디어 레지스트리의 권리 기록 있는 실사진만(C9·G4-10) — 권리 게이트는 `engine.layers.backdrop.validate_backdrop`.
그 위의 내용물(차트·개념도·사진·기사·패널)은 아일랜드다(D-0123 §1). 수치는 전부 `rules stage_backdrop`(코드 리터럴 0).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import cairo

from engine.style import BACKDROP, H_OUT, W_OUT

if TYPE_CHECKING:
    from engine.assets import Assets
    from engine.projection import View


class BackdropError(ValueError):
    """backdrop 무대 구성·앵커 오류(15 P6)."""


class BackdropStage:
    """사진 배경 무대(20 §2.1 카탈로그 밖 — D-0123 신설). 앵커 = 없음."""

    name = "backdrop"
    anchor_keys: tuple[str, ...] = ()
    fixed_w: float = float(W_OUT)

    def __init__(self, assets: "Optional[Assets]" = None, *, out: object = None, config: Optional[dict] = None) -> None:
        if config:
            raise BackdropError(f"backdrop 무대에는 stage_config 가 없다(수치는 rules stage_backdrop): {sorted(config)}")
        self.assets = assets

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (0.0, 0.0, float(W_OUT) + 1.0, float(H_OUT) + 1.0)

    def to_world(self, **anchor: Any) -> tuple[float, float]:
        if anchor:
            raise BackdropError(f"backdrop 무대 카메라는 빈 카메라 {{}} — 앵커 {sorted(anchor)} 금지(이동 없음, D-0123)")
        return W_OUT / 2, H_OUT / 2

    def from_world(self, x: float, y: float) -> dict[str, Any]:
        return {}

    def render_base(self, ctx: cairo.Context, view: "View") -> None:
        ctx.set_source_rgb(*BACKDROP.bg_rgb)
        ctx.paint()

    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> None:
        """라벨 없음(사진 배경은 장식 — 캡션 바도 없다, D-0121 §B)."""

    def lod_rules(self) -> dict[str, Any]:
        return {}


__all__ = ["BackdropError", "BackdropStage"]

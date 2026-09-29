"""요소 한 개를 실제 엔진 렌더러로 그리는 공용 함수 (v4.2.0, back_and_forth D-0081 작업 5·6).

`tools/primitive_sketch.py`(새 요소 스케치 프리뷰, 20 §4.1-2)와 `tools/element_gallery.py`(등록 요소 전부)가 같이 쓴다.
목업이 아니다 — 레지스트리 렌더러(`engine.registry.resolve(e).render`)와 무대 배경(`stage.base_image`)·라벨(`draw_labels`)을
렌더 프레임과 같은 순서로 부른다(engine.render.render_frame 의 층 순서). 자막·날짜·전면 카드·전체 페이드는 그리지 않는다.
"""

from __future__ import annotations

import cairo
from PIL import Image

from engine import typography
from engine.projection import View
from engine.registry import MAP_LAYER_ORDER, resolve, validate_events
from engine.reserved import card_zones
from engine.stage import attach_world
from engine.style import H_OUT, W_OUT

SCREEN_STAGES = ("dip", "panel", "media", "card")


def prepare(P, raw: dict) -> dict:  # noqa: ANN001 — engine.project.Project
    """예제 이벤트(dict) → 검증된 렌더 이벤트(월드 좌표 포함). 레지스트리 밖·모델 불일치 = RegistryError(P6)."""
    ev = validate_events([raw])[0]
    attach_world([ev], P.R.stage)
    if ev["type"] == "post":
        from engine.project import _attach_posts  # noqa: PLC0415 — post 카드 상자는 소스 레코드로(18 §5)

        _attach_posts(P.root, P.R, [ev])
    return ev


def render_event(P, ev: dict, t: float, cam: tuple | None = None) -> tuple[Image.Image, list]:  # noqa: ANN001
    """(이미지, 그린 글자[(크기, 역할, 문자열)]). cam = (x, y, w) 월드 카메라(없으면 프로젝트 첫 카메라)."""
    R = P.R  # noqa: N806
    view = View(R.stage, cam if cam is not None else P.cams[0])
    im = R.stage.base_image(view)
    buf = bytearray(im.tobytes("raw", "BGRX"))
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W_OUT, H_OUT, W_OUT * 4)
    ctx = cairo.Context(surf)
    R.reserved.clear()
    R.zones = card_zones(ctx, [ev], t)
    entry = resolve(ev)
    typography.GLYPH_LOG = []
    try:
        if ev["type"] in MAP_LAYER_ORDER:
            entry.render(ctx, R, view, t, ev)
            R.stage.draw_labels(ctx, view, R.reserved, 1.0)
        elif entry.stage == "primitive":
            entry.render(ctx, R, view, t, ev)
        elif entry.stage in SCREEN_STAGES:
            entry.render(ctx, R, t, ev)
        else:
            raise ValueError(f"그릴 층을 모른다: {ev['type']} (registry stage {entry.stage})")
    finally:
        drawn, typography.GLYPH_LOG = typography.GLYPH_LOG, None
    surf.flush()
    return Image.frombuffer("RGBA", (W_OUT, H_OUT), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB"), list(drawn or [])


def set_genre(P, name: str) -> None:  # noqa: ANN001
    """이 렌더의 장르(색 의미)를 바꾼다 — 프리미티브 스타일 캐시도 비운다."""
    P.R.cache["genre"] = {**P.R.cache.get("genre", {}), "name": name}
    P.R.cache.pop("primitive_style", None)


__all__ = ["prepare", "render_event", "set_genre"]

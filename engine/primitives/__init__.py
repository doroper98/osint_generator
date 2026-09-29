"""프리미티브(새 시각 요소) 계약 (v4.2.0, docs/handoff/20 §4.2, back_and_forth D-0081 작업 4).

`engine/primitives/<id>.py` 모듈 하나 = 요소 하나. 모듈이 반드시 가진 것:

    SCHEMA          Pydantic 모델(extra="forbid") — 데이터 모양. 이벤트 필드는 이 모델 + (type: primitive, id, t0, t1)
    COLOR_KEYS      이 요소가 쓰는 색 의미 키(장르 프로필 color_semantics). 프로필에 없으면 렌더 전 오류(P6)
    draw(ctx, view, t, e, style) -> Reserved     그리고 예약 영역(x0, y0, x1, y1, 설계 px)을 돌려준다. 알파 0 이어도 상자는 돌려준다
    PREVIEW_FIXTURE 레지스트리 예제(이벤트 dict) — 갤러리·회귀 테스트. SCHEMA 를 그대로 통과해야 한다(P4)

등록: `rules registries.primitives` 에 id. 연출은 `{type: primitive, id: <id>, …}` 로만 부른다(20 §4.1-5).
등록 안 된 id(= planned 포함) = RegistryError, 등록됐는데 모듈·계약이 없음 = 오류(tests/anti_inertia/test_registry_complete).
색·크기는 `engine.style` 토큰(`PrimitiveStyle`)만 쓴다 — 모듈 안에 hex·px 숫자를 적지 않는다(AST 검사).
무대와 무관한 화면 오버레이다(카드 층, 카드와 같은 배치 슬롯 `card_right`).
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable, Literal

import cairo
from pydantic import BaseModel, create_model

from engine.events import _Primitive
from engine.style import C, Color, hexc

Reserved = tuple[float, float, float, float]   # x0, y0, x1, y1 (설계 px)
RGBA = tuple[float, float, float, float]
CONTRACT: tuple[str, ...] = ("SCHEMA", "COLOR_KEYS", "draw", "PREVIEW_FIXTURE")
_RGBA_RE = re.compile(r"^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)$")


class PrimitiveError(ValueError):
    """프리미티브 계약·색 의미 오류(15 P6·P10)."""


@dataclass(frozen=True)
class PrimitiveStyle:
    """draw 가 받는 스타일 — 레이아웃 토큰(rules primitives.<id>)·색 의미(장르 프로필)·팔레트(engine.style.C)."""

    layout: Any
    colors: dict[str, RGBA] = field(default_factory=dict)
    palette: dict[str, Color] = field(default_factory=lambda: dict(C))

    def color(self, key: str) -> RGBA:
        if key not in self.colors:
            raise PrimitiveError(f"색 의미 {key!r} 없음 — 장르 프로필 color_semantics: {sorted(self.colors)}")
        return self.colors[key]


def semantic_rgba(v: str) -> RGBA:
    """장르 프로필 색 값 → RGBA. 색 토큰 이름(C) · #rrggbb · rgba(r,g,b,a)."""
    if v in C:
        return (*C[v], 1.0)
    if v.startswith("#"):
        return (*hexc(v), 1.0)
    m = _RGBA_RE.match(v)
    if not m:
        raise PrimitiveError(f"색 값 해석 불가 {v!r}")
    return (int(m.group(1)) / 255, int(m.group(2)) / 255, int(m.group(3)) / 255, float(m.group(4)))


def module(pid: str) -> ModuleType:
    """id → 모듈(engine/primitives/<id>.py). 계약 속성이 빠지면 PrimitiveError."""
    try:
        mod = importlib.import_module(f"engine.primitives.{pid}")
    except ModuleNotFoundError as ex:
        raise PrimitiveError(f"프리미티브 {pid!r} 모듈 없음(engine/primitives/{pid}.py)") from ex
    missing = [a for a in CONTRACT if not hasattr(mod, a)]
    if missing:
        raise PrimitiveError(f"프리미티브 {pid!r} 계약 누락: {missing} (20 §4.2)")
    return mod


def event_model(pid: str, schema: type[BaseModel]) -> type[BaseModel]:
    """이벤트 모델 = 봉투(type: primitive, id, t0, t1) + SCHEMA 필드. SCHEMA 가 extra 를 막아야 한다."""
    if schema.model_config.get("extra") != "forbid":
        raise PrimitiveError(f"프리미티브 {pid!r} SCHEMA 는 extra='forbid' 여야 한다(P6)")
    return create_model(f"PrimitiveEvent_{pid}", __base__=(schema, _Primitive), id=(Literal[pid], ...))  # type: ignore[call-overload]


def style_for(pid: str, color_semantics: dict[str, str]) -> PrimitiveStyle:
    """장르 프로필 색 의미로 스타일을 만든다. 요소의 COLOR_KEYS 가 프로필에 없으면 오류(조용히 기본색으로 그리지 않는다, P6)."""
    from engine.style import PRIMITIVES  # noqa: PLC0415

    mod = module(pid)
    missing = [k for k in mod.COLOR_KEYS if k not in color_semantics]
    if missing:
        raise PrimitiveError(f"프리미티브 {pid!r} 색 의미 {missing} 가 장르 프로필 color_semantics 에 없다(20 §3)")
    return PrimitiveStyle(layout=PRIMITIVES[pid], colors={k: semantic_rgba(color_semantics[k]) for k in mod.COLOR_KEYS})


def measure_style(pid: str) -> PrimitiveStyle:
    """상자만 잴 때(예약 영역) — 색 없이 레이아웃만. draw 는 알파 0 이면 색을 읽지 않는다."""
    from engine.style import PRIMITIVES  # noqa: PLC0415

    return PrimitiveStyle(layout=PRIMITIVES[pid])


_MEASURE = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def primitive_box(e: dict) -> Reserved:
    """제자리 상자(그리지 않음) — 카드 예약 영역(engine.reserved.card_zones)."""
    return module(e["id"]).draw(_MEASURE, None, e["t1"] + 1, e, measure_style(e["id"]))


def make_renderer(pid: str) -> Callable[..., Reserved]:
    """레지스트리 렌더러 render(ctx, R, view, t, e) — 장르 프로필(R.cache genre)의 색 의미로 스타일을 만들어 draw 를 부른다."""
    mod = module(pid)

    def render(ctx: cairo.Context, R: Any, view: Any, t: float, e: dict) -> Reserved:  # noqa: N803
        cache = R.cache.setdefault("primitive_style", {})
        if pid not in cache:
            from genres.load import load_genre  # noqa: PLC0415

            cache[pid] = style_for(pid, load_genre(R.cache["genre"]["name"]).color_semantics)
        box = mod.draw(ctx, view, t, e, cache[pid])
        R.reserved.append(box)
        return box

    render.__name__ = f"primitive_{pid}"
    return render


__all__ = ["CONTRACT", "PrimitiveError", "PrimitiveStyle", "Reserved", "event_model", "make_renderer", "measure_style", "module",
           "primitive_box", "semantic_rgba", "style_for"]

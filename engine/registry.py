"""이벤트 레지스트리 — 타입 → (모델, 렌더러, 단계) (v2.1.0, 15 P10).

- 규칙 파일 `registries.event_types`·`panel_kinds`와 양방향으로 일치해야 한다(tests/anti_inertia/test_registry_complete).
- 레지스트리에 없는 타입은 렌더 전에 `RegistryError`다. `event_types_planned`도 등록하지 않는다(쓰면 오류).
- 패널은 `panel:<kind>` 키로 등록한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from pydantic import BaseModel, ValidationError

from engine import events as ev
from engine.cards import draw_card
from engine.layers.areas import draw_country
from engine.layers.badges import draw_badge
from engine.layers.dip import draw_dip
from engine.layers.effects import draw_boom, draw_ships
from engine.layers.markers import draw_marker
from engine.layers.media import draw_article, draw_clip, draw_cutout, draw_photo
from engine.layers.routes import draw_barrier, draw_route, draw_tanker_loop
from engine.panels import precedent, relation, statement, timeline, versus
from engine.panels.base import make_panel_renderer
from rules import load_rules

Stage = Literal["map", "dip", "panel", "media", "card"]


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    model: type[BaseModel]
    render: Callable[..., None]
    stage: Stage


REGISTRY: dict[str, Entry] = {
    # 지도 레이어 — render(ctx, R, view, t, e)
    "country": Entry(ev.CountryEvent, draw_country, "map"),
    "ships": Entry(ev.ShipsEvent, draw_ships, "map"),
    "route": Entry(ev.RouteEvent, draw_route, "map"),
    "tanker_loop": Entry(ev.TankerLoopEvent, draw_tanker_loop, "map"),
    "barrier": Entry(ev.BarrierEvent, draw_barrier, "map"),
    "boom": Entry(ev.BoomEvent, draw_boom, "map"),
    "cutout": Entry(ev.CutoutEvent, draw_cutout, "map"),
    "marker": Entry(ev.MarkerEvent, draw_marker, "map"),
    "badge": Entry(ev.BadgeEvent, draw_badge, "map"),
    # 화면 레이어 — render(ctx, R, t, e)
    "dip": Entry(ev.DipEvent, draw_dip, "dip"),
    "photo": Entry(ev.PhotoEvent, draw_photo, "media"),
    "clip": Entry(ev.ClipEvent, draw_clip, "media"),
    "card": Entry(ev.CardEvent, draw_card, "card"),
    "article": Entry(ev.ArticleEvent, draw_article, "card"),
    "panel": Entry(ev._Panel, lambda ctx, R, t, e: dispatch_panel(ctx, R, t, e), "panel"),  # kind 별 항목으로 위임
    "panel:relation": Entry(ev.PanelRelation, make_panel_renderer(relation.draw), "panel"),
    "panel:statement": Entry(ev.PanelStatement, make_panel_renderer(statement.draw), "panel"),
    "panel:timeline": Entry(ev.PanelTimeline, make_panel_renderer(timeline.draw), "panel"),
    "panel:precedent": Entry(ev.PanelPrecedent, make_panel_renderer(precedent.draw), "panel"),
    "panel:versus": Entry(ev.PanelVersus, make_panel_renderer(versus.draw), "panel"),
}

# v3 LAYER 순서(render3 L950) — 지도 레이어는 타입 순서대로, 같은 타입 안에서는 이벤트 순서대로 그린다.
MAP_LAYER_ORDER: tuple[str, ...] = ("country", "ships", "route", "tanker_loop", "barrier", "boom", "cutout", "marker", "badge")


def dispatch_panel(ctx: object, R: object, t: float, e: dict) -> None:  # noqa: N803
    """`panel` 타입의 렌더러 — `panel:<kind>` 항목으로 넘긴다(없으면 RegistryError)."""
    resolve(e).render(ctx, R, t, e)


def key_of(e: dict) -> str:
    typ = e.get("type")
    if not isinstance(typ, str):
        raise RegistryError(f"이벤트에 type 이 없다: {e!r}")
    if typ == "panel":
        kind = e.get("kind")
        if not isinstance(kind, str):
            raise RegistryError(f"panel 이벤트에 kind 가 없다: {e!r}")
        return f"panel:{kind}"
    return typ


def resolve(e: dict | str) -> Entry:
    """이벤트(dict) 또는 레지스트리 키(str, 예: "marker", "panel:timeline") → 항목. 없으면 RegistryError."""
    key = e if isinstance(e, str) else key_of(e)
    if key not in REGISTRY:
        rules = load_rules().registries
        planned = set(rules.event_types_planned) | {f"panel:{k}" for k in rules.panel_kinds_planned}
        why = "계획만 있고 구현 전(planned)" if key in planned else "레지스트리에 없음"
        raise RegistryError(f"이벤트 타입 {key!r}: {why} — rules/video_rules.yaml registries (15 P10)")
    return REGISTRY[key]


def validate_events(raw: list[dict]) -> list[dict]:
    """모든 이벤트를 모델로 검증하고, 렌더러가 읽을 dict 로 돌려준다. 하나라도 틀리면 전체 오류."""
    out: list[dict] = []
    errors: list[str] = []
    for i, e in enumerate(raw):
        try:
            entry = resolve(e)
            out.append(entry.model.model_validate(e).model_dump())
        except (RegistryError, ValidationError) as ex:
            errors.append(f"[{i}] {e.get('type')}: {ex}")
    if errors:
        raise RegistryError("이벤트 검증 실패(렌더 시작 전):\n" + "\n".join(errors))
    return out

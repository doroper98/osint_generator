"""이벤트 레지스트리 — 타입 → (모델, 렌더러, 단계) (v2.1.0, 15 P10).

- 규칙 파일 `registries.event_types`·`panel_kinds`와 양방향으로 일치해야 한다(tests/anti_inertia/test_registry_complete).
- 레지스트리에 없는 타입은 렌더 전에 `RegistryError`다. `event_types_planned`도 등록하지 않는다(쓰면 오류).
- 패널은 `panel:<kind>` 키로 등록한다.
- 프리미티브(v4.2.0 D-0081 작업 4, 20 §4.2)는 `primitive:<id>` 키 — `rules registries.primitives` 마다 engine/primitives/<id>.py 를 잇는다.
  렌더러는 지도 레이어처럼 view 를 받는다: render(ctx, R, view, t, e) → 예약 영역.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Optional

from pydantic import BaseModel, ValidationError

from engine import events as ev
from engine.cards import draw_card
from engine.cascade import draw_cascade
from engine.layers.areas import draw_country
from engine.island import draw_island
from engine.layers.backdrop import draw_backdrop
from engine.layers.badges import draw_badge, draw_over_panel
from engine.layers.dip import draw_dip
from engine.layers.effects import draw_boom, draw_ships
from engine.layers.markers import draw_marker
from engine.layers.article import draw_article
from engine.layers.media import draw_clip, draw_cutout, draw_photo
from engine.layers.post import draw_post
from engine.layers.routes import draw_barrier, draw_route, draw_tanker_loop
from engine.layers.series import draw_series
from engine.panels import checklist, dots, dual_line, fork, gantt, network, precedent, relation, statement, timeline, versus
from engine.panels.base import make_panel_renderer
from engine.primitives import event_model, make_renderer, module
from rules import load_rules

Stage = Literal["map", "dip", "panel", "media", "card", "primitive"]


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
    "series": Entry(ev.SeriesEvent, draw_series, "map"),     # v4.3.0 D-0084 작업 4 — 시간축 무대 전용(데이터 레코드에서 직접)
    "badge": Entry(ev.BadgeEvent, draw_badge, "map"),
    "backdrop": Entry(ev.BackdropEvent, draw_backdrop, "map"),   # v5.1.0 D-0123 — backdrop 무대 배경 사진(무대 바탕 바로 위, render_frame 이 먼저 그린다)
    "island": Entry(ev.IslandEvent, draw_island, "map"),         # v5.1.0 D-0126 Q1 A — 차트 아일랜드(backdrop 무대, 무대 레이어 맨 앞)
    # 화면 레이어 — render(ctx, R, t, e)
    "dip": Entry(ev.DipEvent, draw_dip, "dip"),
    "photo": Entry(ev.PhotoEvent, draw_photo, "media"),
    "clip": Entry(ev.ClipEvent, draw_clip, "media"),
    "card": Entry(ev.CardEvent, draw_card, "card"),
    "cascade": Entry(ev.CascadeEvent, draw_cascade, "card"),       # v5.2.0 겹침 카드(시안) — 패널 덮개 아래에 그린다(engine/render.py)
    "article": Entry(ev.ArticleEvent, draw_article, "card"),
    "post": Entry(ev.PostEvent, draw_post, "card"),          # v3.2.0 18 §5
    "panel": Entry(ev._Panel, lambda ctx, R, t, e: dispatch_panel(ctx, R, t, e), "panel"),  # kind 별 항목으로 위임
    "panel:relation": Entry(ev.PanelRelation, make_panel_renderer(relation.draw), "panel"),
    "panel:statement": Entry(ev.PanelStatement, make_panel_renderer(statement.draw), "panel"),
    "panel:timeline": Entry(ev.PanelTimeline, make_panel_renderer(timeline.draw), "panel"),
    "panel:precedent": Entry(ev.PanelPrecedent, make_panel_renderer(precedent.draw), "panel"),
    "panel:versus": Entry(ev.PanelVersus, make_panel_renderer(versus.draw), "panel"),
    # v2 번들 차트 이식(D-0032 작업 5, 08 §8)
    "panel:dots": Entry(ev.PanelDots, make_panel_renderer(dots.draw), "panel"),
    "panel:gantt": Entry(ev.PanelGantt, make_panel_renderer(gantt.draw), "panel"),
    "panel:dual_line": Entry(ev.PanelDualLine, make_panel_renderer(dual_line.draw), "panel"),
    "panel:fork": Entry(ev.PanelFork, make_panel_renderer(fork.draw), "panel"),
    "panel:checklist": Entry(ev.PanelChecklist, make_panel_renderer(checklist.draw), "panel"),
    "panel:network": Entry(ev.PanelNetwork, make_panel_renderer(network.draw), "panel"),
    # v4.2.0 D-0081 작업 4 — 프리미티브. id 별 항목은 아래에서 registries.primitives 로 채운다
    "primitive": Entry(ev._Primitive, lambda ctx, R, view, t, e: dispatch_primitive(ctx, R, view, t, e), "primitive"),
}
for _pid in load_rules().registries.primitives:
    REGISTRY[f"primitive:{_pid}"] = Entry(event_model(_pid, module(_pid).SCHEMA), make_renderer(_pid), "primitive")

# v3 LAYER 순서(render3 L950) — 지도 레이어는 타입 순서대로, 같은 타입 안에서는 이벤트 순서대로 그린다.
MAP_LAYER_ORDER: tuple[str, ...] = ("island", "country", "ships", "route", "tanker_loop", "barrier", "boom", "cutout", "series", "marker", "badge")


def dispatch_panel(ctx: object, R: object, t: float, e: dict) -> None:  # noqa: N803
    """`panel` 타입의 렌더러 — `panel:<kind>` 항목으로 넘긴다(없으면 RegistryError)."""
    resolve(e).render(ctx, R, t, e)


def dispatch_primitive(ctx: object, R: object, view: object, t: float, e: dict) -> object:  # noqa: N803
    """`primitive` 타입의 렌더러 — `primitive:<id>` 항목으로 넘긴다(없으면 RegistryError)."""
    return resolve(e).render(ctx, R, view, t, e)


def key_of(e: dict) -> str:
    typ = e.get("type")
    if not isinstance(typ, str):
        raise RegistryError(f"이벤트에 type 이 없다: {e!r}")
    if typ == "panel":
        kind = e.get("kind")
        if not isinstance(kind, str):
            raise RegistryError(f"panel 이벤트에 kind 가 없다: {e!r}")
        return f"panel:{kind}"
    if typ == "primitive":
        pid = e.get("id")
        if not isinstance(pid, str):
            raise RegistryError(f"primitive 이벤트에 id 가 없다: {e!r}")
        return f"primitive:{pid}"
    return typ


def resolve(e: dict | str) -> Entry:
    """이벤트(dict) 또는 레지스트리 키(str, 예: "marker", "panel:timeline") → 항목. 없으면 RegistryError."""
    key = e if isinstance(e, str) else key_of(e)
    if key not in REGISTRY:
        rules = load_rules().registries
        planned = (set(rules.event_types_planned) | {f"panel:{k}" for k in rules.panel_kinds_planned}
                   | {f"primitive:{k}" for k in rules.primitives_planned})
        why = "계획만 있고 구현 전(planned)" if key in planned else "레지스트리에 없음"
        raise RegistryError(f"이벤트 타입 {key!r}: {why} — rules/video_rules.yaml registries (15 P10)")
    return REGISTRY[key]


@dataclass(frozen=True)
class LayerSet:
    """렌더 한 벌의 레이어 선택(v4.9.0 back_and_forth D-0108) — render_frame 은 이 객체만 본다(플래그 분기 없음).
    resolve = 이벤트 → 항목, over_panel = 패널 위 인물 뱃지(D2(c)), overlay = 전체 페이드 뒤 맨 위 층(없으면 None).
    전편 = `FULL_LAYERS`, 콘티 판 = `engine.layers.animatic.ANIMATIC_LAYERS`(진입 = load_project(animatic=True) 한 곳)."""

    name: str
    resolve: Callable[[dict | str], Entry]
    over_panel: Callable[..., None]
    overlay: Optional[Callable[..., None]] = None


FULL_LAYERS = LayerSet("full", resolve, draw_over_panel)


def validate_events(raw: list[dict]) -> list[dict]:
    """모든 이벤트를 모델로 검증하고, 렌더러가 읽을 dict 로 돌려준다. 하나라도 틀리면 전체 오류."""
    out: list[dict] = []
    errors: list[str] = []
    for i, e in enumerate(raw):
        try:
            entry = resolve(e)
            d = entry.model.model_validate(e).model_dump()
            for k in getattr(entry.model, "DROP_NONE", ()):   # v4.3.0 — 선택 앵커 쌍(지도·시간축) 중 쓰지 않은 쪽
                if d.get(k) is None:
                    d.pop(k, None)
            out.append(d)
        except (RegistryError, ValidationError) as ex:
            errors.append(f"[{i}] {e.get('type')}: {ex}")
    if errors:
        raise RegistryError("이벤트 검증 실패(렌더 시작 전):\n" + "\n".join(errors))
    return out

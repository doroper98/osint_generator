"""배치 슬롯 → 좌표 (v3.1.0, docs/handoff/17 §2 `place:`, back_and_forth D-0047 작업 5).

연출(LLM·사람)은 픽셀·경위도 대신 슬롯 이름을 준다. 좌표 계산은 코드가 한다(15 P8).
- box 슬롯(사진·영상): x·y·w ← `rules placement.slots.<이름>.box`
- point 슬롯(뱃지·컷아웃·마커): 이벤트 시작 순간의 카메라 뷰로 화면 점을 경위도로 역투영 → lon·lat
- card 슬롯: 카드 y(null 이면 렌더러 기본)
- beside_panel 슬롯(사진·영상, v3.2.0 D-0050 NB9): 그 시각 활성 패널이 차지한 상자(`OCCUPIED[kind]`, 미디어가 떠 있는 동안
  등장하는 요소까지)·자막·날짜 예약 영역을 피하는 첫 후보 자리. 막히면 오류. 겹침 판정은 RESERVED 와 같은 `reserved._hits`
- 사진·영상에 place·x 가 둘 다 없으면 `placement.auto_media`(14 §10.3-5, v3 합격 좌표)
- 무대 종류별 자리(v4.4.0 D-0093): 그 무대의 `placement.stage_slots` 에 이벤트 종류가 있으면 지도 슬롯(map_*) 대신 그 슬롯
슬롯 이름이 없거나 그 종류에 쓸 수 없는 슬롯이면 오류(15 P6·P10).
"""

from __future__ import annotations

from collections.abc import Callable

import cairo

from engine.panels import timeline
from engine.reserved import _hits
from engine.hud import date_box
from engine.style import H_OUT, W_OUT
from rules import load_rules

_R = load_rules()
PL = _R.placement
SUB_Y = _R.layout_480p.reserved_zones.subtitle.y_from
Box = tuple[float, float, float, float]
# 패널 종류 → 차지 상자 함수(ctx, 패널 이벤트, t_until). 없는 종류에 beside_panel 슬롯 = 오류(P10)
OCCUPIED: dict[str, Callable[[cairo.Context, dict, float], list[Box]]] = {"timeline": timeline.occupied}


class PlacementError(ValueError):
    pass


def _panel_at(events: list[dict], t: float) -> bool:
    return any(e["type"] == "panel" and e["t0"] <= t <= e["t1"] for e in events)


def _beside_panel(e: dict, events: list[dict], slot, media_h: Callable[[dict, float], tuple[float, float]] | None) -> str | None:  # noqa: ANN001
    """패널 옆 자리 → e 에 x·y·w. 오류면 문구."""
    bp = slot.beside_panel
    panels = [p for p in events if p["type"] == "panel" and p["t0"] < e["t1"] and e["t0"] < p["t1"]]
    if not panels:
        return "활성 패널 없음 — 지도 위 미디어는 map_* 슬롯"
    if media_h is None:
        return "미디어 높이 계산기 없음(자산 레지스트리 필요)"
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    obst: list[Box] = [(0, SUB_Y, W_OUT, H_OUT), date_box()]
    for p in panels:
        fn = OCCUPIED.get(p["kind"])
        if fn is None:
            return f"패널 {p['kind']!r} 의 차지 상자 함수 없음 — engine.placement.OCCUPIED: {sorted(OCCUPIED)}"
        obst += fn(ctx, p, e["t1"])
    h, text_w = media_h(e, bp.w)
    for x, y in bp.candidates:
        b = (x, y, x + text_w, y + h)          # 캡션 글자가 바보다 길면 그 끝까지(출처 줄 잘림 금지)
        if b[0] >= 0 and b[1] >= 0 and b[2] <= W_OUT and not any(_hits(b, o, bp.gap_px) for o in obst):
            e["x"], e["y"], e["w"] = x, y, bp.w
            return None
    return f"후보 {len(bp.candidates)}곳 모두 패널·예약 영역과 겹치거나 화면 밖(폭 {bp.w:g}, 글자 폭 {text_w:.0f}, 높이 {h:.0f})"


PANEL_SCENE = "panel"   # stage_slots 의 '패널 장면' 키(v4.8.0 D-0104 D2(c)) — 무대 이름이 아니다


def _stage_slot(e: dict, slot_name: str, stage_name: str | None, in_panel: bool = False) -> str | None:
    """주 무대의 `placement.stage_slots` 자리. 연출이 그 무대 전용 슬롯이나 card·panel 슬롯을 골랐으면 그대로(None).
    지도 슬롯(map_*)·자동 슬롯만 바꾼다 — 시간축에서 지도 좌표 자리는 레인 이름·출처 줄을 가린다(D-0093).
    in_panel = 이벤트 시작 순간 패널이 떠 있다 → `stage_slots.panel` 먼저(D2(c) — 지도 층 뱃지는 패널에 가린다)."""
    if not slot_name.startswith("map_"):
        return None
    if in_panel and e["type"] in PL.stage_slots.get(PANEL_SCENE, {}):
        return PL.stage_slots[PANEL_SCENE][e["type"]]
    if stage_name is None:
        return None
    return PL.stage_slots.get(stage_name, {}).get(e["type"])


def _screen_point(e: dict, slot, taken: list[dict]) -> str | None:  # noqa: ANN001
    """화면 고정 슬롯(D2(c)) — 이 뱃지와 시간이 겹치는, 먼저 자리 잡은 뱃지 수 = 점 번호. 모자라면 문구."""
    busy = {tuple(o["screen"]) for o in taken if o["t0"] < e["t1"] and e["t0"] < o["t1"]}
    free = [p for p in slot.screen if tuple(p) not in busy]
    if not free:
        return f"동시에 떠 있는 패널 위 뱃지가 자리 {len(slot.screen)}곳보다 많다"
    e["screen"], e["over_panel"] = list(free[0]), True
    taken.append(e)
    return None


def resolve_places(events: list[dict], view_at: Callable[[float], object],
                   media_h: Callable[[dict, float], tuple[float, float]] | None = None, stage_name: str | None = None) -> dict[str, str]:
    """`place` 가 있는 이벤트를 좌표로 바꾸고(제자리) 기록을 돌려준다.
    기록: 미디어는 {mid: explicit | auto:<슬롯> | slot:<슬롯>}(provenance media.placement), 그 밖은 {타입:라벨: slot:<슬롯>}.
    view_at(t) → engine.projection.View(그 시각 카메라, 무대 포함). point 슬롯에만 쓴다.
    stage_name = 주 무대 이름(v4.4.0 — `placement.stage_slots` 조회, None 이면 바꾸지 않는다).
    media_h(e, w) → 폭 w 일 때 (미디어 상자 높이(캡션 바 포함), 캡션 글자까지의 폭). beside_panel 슬롯에만 쓴다."""
    rec: dict[str, str] = {}
    errs: list[str] = []
    on_screen: list[dict] = []
    for i, e in enumerate(events):
        slot_name = e.pop("place", None)
        media = e["type"] in PL.auto_media
        tag = e["mid"] if media else f"{e['type']}:{e.get('label') or i}"
        how = "slot"
        if slot_name is None:
            if media and e.get("x") is None:
                slot_name = PL.auto_media[e["type"]]["panel" if _panel_at(events, e["t0"]) else "map"]
                how = "auto"
            else:
                if media:
                    rec[tag] = "explicit"
                continue
        stage_slot = _stage_slot(e, slot_name, stage_name, _panel_at(events, e["t0"]))   # v4.4.0 D-0093 무대 자리 · v4.8.0 D2(c) 패널 장면
        if stage_slot is not None:
            slot_name, how = stage_slot, "stage"
        slot = PL.slots.get(slot_name)
        if slot is None:
            errs.append(f"[{i}] {tag}: 슬롯 {slot_name!r} 없음 — rules placement.slots: {sorted(PL.slots)}")
            continue
        if e["type"] not in slot.kinds:
            errs.append(f"[{i}] {tag}: 슬롯 {slot_name!r} 는 {slot.kinds} 용")
            continue
        if slot.beside_panel is not None:
            err = _beside_panel(e, events, slot, media_h)
            if err:
                errs.append(f"[{i}] {tag}: 슬롯 {slot_name!r} — {err}")
                continue
        elif slot.box is not None:
            e["x"], e["y"], e["w"] = slot.box
        elif slot.point is not None or slot.screen:
            if slot.screen:
                err = _screen_point(e, slot, on_screen)
                if err:
                    errs.append(f"[{i}] {tag}: 슬롯 {slot_name!r} — {err}")
                    continue
            if stage_name == "backdrop" and e["type"] == "badge" and slot.point is not None:
                e["screen"], e["over_panel"] = list(slot.point), True   # v5.1.0 D-0123 — backdrop 무대 뱃지 = 화면 고정(월드 앵커 없음)
                rec[tag] = f"{how}:{slot_name}"
                continue
            v = view_at(e["t0"])
            pt = slot.point if slot.point is not None else e["screen"]   # 화면 고정 뱃지도 앵커는 둔다(모델 검증) — 그리기는 screen
            e.update(v.stage.from_world(*v.to_world(*pt)))   # type: ignore[attr-defined] — 화면 점 → 월드 → 앵커(lon·lat)
        else:
            if slot.card is not None:
                e["y"] = slot.card
        rec[tag] = f"{how}:{slot_name}"
    if errs:
        raise PlacementError("배치 슬롯 오류:\n" + "\n".join(errs))
    return rec


__all__ = ["PlacementError", "resolve_places"]

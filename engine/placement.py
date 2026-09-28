"""배치 슬롯 → 좌표 (v3.1.0, docs/handoff/17 §2 `place:`, back_and_forth D-0047 작업 5).

연출(LLM·사람)은 픽셀·경위도 대신 슬롯 이름을 준다. 좌표 계산은 코드가 한다(15 P8).
- box 슬롯(사진·영상): x·y·w ← `rules placement.slots.<이름>.box`
- point 슬롯(뱃지·컷아웃·마커): 이벤트 시작 순간의 카메라 뷰로 화면 점을 경위도로 역투영 → lon·lat
- card 슬롯: 카드 y(null 이면 렌더러 기본)
- 사진·영상에 place·x 가 둘 다 없으면 `placement.auto_media`(14 §10.3-5, v3 합격 좌표)
슬롯 이름이 없거나 그 종류에 쓸 수 없는 슬롯이면 오류(15 P6·P10).
"""

from __future__ import annotations

from collections.abc import Callable

from engine.projection import lat_of
from rules import load_rules

PL = load_rules().placement


class PlacementError(ValueError):
    pass


def _panel_at(events: list[dict], t: float) -> bool:
    return any(e["type"] == "panel" and e["t0"] <= t <= e["t1"] for e in events)


def resolve_places(events: list[dict], view_at: Callable[[float], object]) -> dict[str, str]:
    """`place` 가 있는 이벤트를 좌표로 바꾸고(제자리) 기록을 돌려준다.
    기록: 미디어는 {mid: explicit | auto:<슬롯> | slot:<슬롯>}(provenance media.placement), 그 밖은 {타입:라벨: slot:<슬롯>}.
    view_at(t) → engine.projection.View(그 시각 카메라). point 슬롯에만 쓴다."""
    rec: dict[str, str] = {}
    errs: list[str] = []
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
        slot = PL.slots.get(slot_name)
        if slot is None:
            errs.append(f"[{i}] {tag}: 슬롯 {slot_name!r} 없음 — rules placement.slots: {sorted(PL.slots)}")
            continue
        if e["type"] not in slot.kinds:
            errs.append(f"[{i}] {tag}: 슬롯 {slot_name!r} 는 {slot.kinds} 용")
            continue
        if slot.box is not None:
            e["x"], e["y"], e["w"] = slot.box
        elif slot.point is not None:
            v = view_at(e["t0"])
            px, py = slot.point
            e["lon"] = v.u0 + px / v.s          # type: ignore[attr-defined] — View.xy 의 역
            e["lat"] = lat_of(v.v1 - py / v.s)  # type: ignore[attr-defined]
        else:
            if slot.card is not None:
                e["y"] = slot.card
        rec[tag] = f"{how}:{slot_name}"
    if errs:
        raise PlacementError("배치 슬롯 오류:\n" + "\n".join(errs))
    return rec


__all__ = ["PlacementError", "resolve_places"]

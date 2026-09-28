"""미디어 비트 배치·밀도 (v2.5.5, back_and_forth D-0036 작업 6, 14 §5·§10).

- 기본 배치·슬롯은 v3.1.0 부터 `engine/placement.py`(rules placement — 옛 media_beats.placement 를 옮김, D-0047 작업 5).
  패널이 떠 있으면 패널 자리, 아니면 지도 자리. 연출이 준 값은 그대로(P8).
- `placement_warnings()` — 예약 영역(카드·기사 카드가 떠 있는 동안, 하단 자막 y ≥ 410, 모서리 날짜)과 겹치면 경고(보고만, P8).
- `density_report()` — 14 §10.1 밀도(rules media.density, D-0037·D38): 전체 초당 개수, 장면당 개수(기사 예외),
  이웃 장면 같은 형태, 40초 창 몰림(기사 예외). 모두 경고(오류 아님).
"""

from __future__ import annotations

import math

import cairo

from engine.reserved import card_zones
from engine.style import DATE_BADGE, W_OUT
from engine.timebase import Timebase
from rules import load_rules

_R = load_rules()
MB = _R.media_beats
SUB_Y = _R.layout_480p.reserved_zones.subtitle.y_from
MEDIA_TYPES: tuple[str, ...] = ("photo", "clip", "cutout", "article")
_KIND = {"photo": "photo", "clip": "clip", "cutout": "cutout", "article": "article"}   # 14 §10 형태 이름(규칙 kinds)


def media_box(e: dict, assets: dict) -> tuple[float, float, float, float]:
    """사진·영상 상자(캡션 바 포함). 높이 비율은 레지스트리 가공 파라미터(크롭·스케일)에서."""
    prm = assets[e["mid"]].tool.params
    w_, h_ = prm.get("crop") or prm.get("scale")
    h = e["w"] * h_ / w_ + MB.caption_bar_px
    return e["x"], e["y"], e["x"] + e["w"], e["y"] + h


def _hit(a: tuple, b: tuple) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def placement_warnings(events: list[dict], assets: dict, step: float = 0.25) -> list[str]:
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    date_box = (W_OUT - DATE_BADGE.x_right - DATE_BADGE.size * 8, 0, W_OUT, DATE_BADGE.underline_y + 2)
    out: list[str] = []
    for e in events:
        if e["type"] not in ("photo", "clip"):
            continue
        box = media_box(e, assets)
        where = f"{e['type']} {e['mid']} t0={e['t0']:.2f}"
        if box[3] > SUB_Y:
            out.append(f"[media-over-subtitle] {where} 아래 끝 {box[3]:.0f} > 자막 영역 {SUB_Y} (14 §5-4)")
        if _hit(box, date_box):
            out.append(f"[media-over-date] {where} 모서리 날짜와 겹침 (14 §5-4)")
        n = max(1, int((e["t1"] - e["t0"]) / step))
        hits = {z.ref for k in range(n + 1) for z in card_zones(ctx, events, e["t0"] + k * (e["t1"] - e["t0"]) / n)
                if z.a > 1 / 2 and _hit(box, z.box)}
        if hits:
            out.append(f"[media-over-card] {where} 카드와 겹침 {sorted(hits)} (14 §5-4)")
    return out


def media_items(events: list[dict], tb: Timebase) -> list[dict]:
    out = []
    for e in sorted((e for e in events if e["type"] in MEDIA_TYPES), key=lambda e: e["t0"]):
        sc = next((s for s in reversed(tb.scenes) if tb.SC(s) <= e["t0"] + 1e-6), tb.scenes[0])
        out.append({"mid": e["mid"], "kind": _KIND[e["type"]], "t0": round(e["t0"], 2), "t1": round(e["t1"], 2), "scene": sc})
    return out


def density_report(events: list[dict], tb: Timebase, total: float) -> dict:
    """14 §10.1 밀도 경고 4종(D-0037): media-density-total · media-density-scene · media-kind-repeat · media-burst-window."""
    D = _R.media.density  # noqa: N806
    items = media_items(events, tb)
    lo, hi = D.per_item_sec
    warns: list[str] = []
    per = total / len(items) if items else math.inf
    if items and per < lo:
        warns.append(f"[media-density-total] 과밀 — {len(items)}개 / {total:.0f}초 = {per:.1f}초당 1개 < {lo:g}초 (14 §10.1)")
    if per > hi:
        warns.append(f"[media-density-total] 과소 — {len(items)}개 / {total:.0f}초 = {per:.1f}초당 1개 > {hi:g}초 (14 §10.1)")
    by_scene: dict[str, list[str]] = {}
    for i in items:
        if i["kind"] not in D.scene_exempt_kinds:
            by_scene.setdefault(i["scene"], []).append(i["mid"])
    for sc, mids in by_scene.items():
        if len(mids) > D.per_scene_max:
            warns.append(f"[media-density-scene] 장면 {sc}: {mids} > {D.per_scene_max} (14 §10.1, {D.scene_exempt_kinds} 제외)")
    if D.no_same_kind_adjacent_scenes:
        kinds = {s: {i["kind"] for i in items if i["scene"] == s} for s in tb.scenes}
        for s0, s1 in zip(tb.scenes, tb.scenes[1:]):
            same = kinds[s0] & kinds[s1]
            if same:
                warns.append(f"[media-kind-repeat] 이웃 장면 {s0}→{s1} 같은 형태 {sorted(same)} (14 §10.1)")
    win = [i for i in items if i["kind"] not in D.window_exempt_kinds]
    worst = {"t0": None, "count": 0, "mids": []}
    for k, a in enumerate(win):
        inside = [b for b in win[k:] if b["t0"] - a["t0"] < D.window_sec]
        if len(inside) > worst["count"]:
            worst = {"t0": a["t0"], "count": len(inside), "mids": [b["mid"] for b in inside]}
    if worst["count"] > D.window_max:
        warns.append(f"[media-burst-window] {worst['t0']}초부터 {D.window_sec:g}초 안 {worst['count']}개 {worst['mids']} > "
                     f"{D.window_max} (14 §10.1 하한, D38)")
    return {"schema_version": 1, "total_sec": round(total, 3), "items": items, "count": len(items),
            "sec_per_item": None if not items else round(per, 1), "target_sec_per_item": [lo, hi],
            "window": {"window_sec": D.window_sec, "window_max": D.window_max, "exempt": D.window_exempt_kinds, "max": worst},
            "per_scene": by_scene, "warnings": warns}

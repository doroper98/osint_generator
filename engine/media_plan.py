"""미디어 비트 배치·밀도 (v2.5.5, back_and_forth D-0036 작업 6, 14 §5·§10).

- 기본 배치·슬롯은 v3.1.0 부터 `engine/placement.py`(rules placement — 옛 media_beats.placement 를 옮김, D-0047 작업 5).
  패널이 떠 있으면 패널 자리, 아니면 지도 자리. 연출이 준 값은 그대로(P8).
- `placement_warnings()` — 예약 영역(카드·기사 카드가 떠 있는 동안, 하단 자막 y ≥ 410, 모서리 날짜)과 겹치면 경고(보고만, P8).
  v3.6.0 NB23: 카드·기사 카드·게시물 카드 자신도 날짜·자막 영역과 겹치면 같은 목록에 올린다(checks overlap = hard).
- `density_report()` — 14 §10.1 밀도(rules media.density, D-0037·D38): 전체 초당 개수, 장면당 개수(기사 예외),
  이웃 장면 같은 형태, 40초 창 몰림(기사 예외). 모두 경고(오류 아님).
"""

from __future__ import annotations

import math
from pathlib import Path

import cairo

from engine.hud import date_box as _date_box
from engine.reserved import card_box, card_zones
from engine.style import CARD
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


def card_zone_warnings(ctx: cairo.Context, events: list[dict]) -> list[str]:
    """카드 자신이 모서리 날짜·하단 자막 영역과 겹침(v3.6.0 NB23 — Phase 9 랫클리프 p_0191.86 카드 y 0.56 이 픽셀로 읽혀
    날짜 자리에 뜬 것을 검사기가 못 잡았다). 좌표는 480p 설계 픽셀이다."""
    date_box = _date_box()
    out: list[str] = []
    for e in events:
        if e["type"] not in ("card", "article", "post", "primitive") or (e["type"] == "post" and "post_box" not in e):   # primitive = v4.2.0
            continue
        box = card_box(ctx, e)
        where = f"{e['type']} {e.get('tag') or e.get('src') or e.get('mid') or ''} t0={e['t0']:.2f}"
        if _hit(box, date_box):
            out.append(f"[card-over-date] {where} 상자 {[round(v) for v in box]} 가 모서리 날짜 {[round(v) for v in date_box]} 와 겹침"
                       f" — y 는 480p 픽셀(비율 아님), 생략하면 기본 {CARD.y:g}")
        if box[3] > SUB_Y:
            out.append(f"[card-over-subtitle] {where} 아래 끝 {box[3]:.0f} > 자막 영역 {SUB_Y}")
    return out


def placement_warnings(events: list[dict], assets: dict, step: float = 0.25) -> list[str]:
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    date_box = _date_box()
    out: list[str] = card_zone_warnings(ctx, events)
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
    beats = [i for i in items if i["kind"] not in D.total_exempt_kinds]   # v5.19.0 D-0163 §2 — 기사는 미디어 비트 상한 밖(분당 상한 따로)
    lo, hi = D.per_item_sec
    warns: list[str] = []
    per = total / len(beats) if beats else math.inf
    if beats and per < lo:
        warns.append(f"[media-density-total] 과밀 — {len(beats)}개 / {total:.0f}초 = {per:.1f}초당 1개 < {lo:g}초 "
                     f"(14 §10.1, {D.total_exempt_kinds} 제외)")
    if per > hi:
        warns.append(f"[media-density-total] 과소 — {len(beats)}개 / {total:.0f}초 = {per:.1f}초당 1개 > {hi:g}초 "
                     f"(14 §10.1, {D.total_exempt_kinds} 제외)")
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
    # v7.3.0 사용자 결정 D232 U2 — 위성 인셋(flight.inset)은 미디어 비트 상한 밖, 자기 상한(장면당·간격)만
    insets = sorted(((e["t0"], e["inset"]["mid"]) for e in events if e["type"] == "flight" and e.get("inset")))
    by_scene_inset: dict[str, list[str]] = {}
    for t0, mid in insets:
        sc = next((s for s in reversed(tb.scenes) if tb.SC(s) <= t0 + 1e-6), tb.scenes[0])
        by_scene_inset.setdefault(sc, []).append(mid)
    for sc, mids in by_scene_inset.items():
        if len(mids) > D.inset_per_scene_max:
            warns.append(f"[inset-density] 장면 {sc}: 인셋 {mids} > {D.inset_per_scene_max} (D232 U2)")
    for (ta, ma), (tb_, mb) in zip(insets, insets[1:]):
        if tb_ - ta < D.inset_min_gap_sec:
            warns.append(f"[inset-density] {ma}({ta:.1f}초) → {mb}({tb_:.1f}초) 간격 < {D.inset_min_gap_sec:g}초 (D232 U2)")
    return {"schema_version": 1, "total_sec": round(total, 3), "items": items, "count": len(items), "beat_count": len(beats),
            "sec_per_item": None if not beats else round(per, 1), "target_sec_per_item": [lo, hi],
            "window": {"window_sec": D.window_sec, "window_max": D.window_max, "exempt": D.window_exempt_kinds, "max": worst},
            "per_scene": by_scene, "insets": [m for _, m in insets], "warnings": warns}


def article_candidate_usage(proj: Path, plan, events: list[dict]) -> dict:  # noqa: ANN001 — script.schema.Plan
    """v5.19.0 D-0163 §2 — 기사 카드 후보(확인된 기사 출처를 인용하고 그 기사가 등록된 문장, script.media_table)를 연출이 썼는가.

    60초 구간(문장 시작 기준)마다 기대 수 = min(후보 문장 수, rules media.density.article_per_min_max). 기사 이벤트가 문장 시간과
    겹치면 그 문장은 쓴 것이다. 모자라면 안 쓴 후보를 긴 문장 먼저 기대 수만큼 고르고, media_notes.yaml article 사유가 있으면 기록만,
    없으면 `[article-unused]` 경고. 구간에 기사 카드가 상한을 넘으면 `[article-density]` 경고. 원고·claims 가 없으면 후보 없음."""
    from script.media_table import article_candidates, load_notes  # noqa: PLC0415

    D = _R.media.density  # noqa: N806
    cands = article_candidates(proj)
    notes = load_notes(proj).sentences
    arts = [e for e in events if e["type"] == "article"]
    by_bucket: dict[int, list] = {}
    for s in plan.sentences:
        if s.sid in cands:
            by_bucket.setdefault(int(s.t0 // 60), []).append(s)
    warns: list[str] = []
    unused: list[dict] = []
    covered = 0
    for b, ss in sorted(by_bucket.items()):
        hit = [s for s in ss if any(e["t0"] < s.t1 and e["t1"] > s.t0 for e in arts)]
        covered += len(hit)
        need = min(len(ss), D.article_per_min_max) - len(hit)
        for s in sorted((s for s in ss if s not in hit), key=lambda s: -len(s.text))[:max(need, 0)]:
            why = notes[s.sid].article if s.sid in notes else None
            unused.append({"sid": s.sid, "t0": round(s.t0, 2), "mids": cands[s.sid], "reason": why})
            if why is None:
                warns.append(f"[article-unused] {s.sid} {s.t0:.1f}초 기사 카드 후보 {cands[s.sid]} — {b * 60}~{b * 60 + 60}초 구간 "
                             f"{len(hit)}/{min(len(ss), D.article_per_min_max)}개. 쓰거나 media_notes.yaml sentences.{s.sid}.article 에 사유")
    per_bucket: dict[int, int] = {}
    for e in arts:
        per_bucket[int(e["t0"] // 60)] = per_bucket.get(int(e["t0"] // 60), 0) + 1
    for b, n in sorted(per_bucket.items()):
        if n > D.article_per_min_max:
            warns.append(f"[article-density] {b * 60}~{b * 60 + 60}초 기사 카드 {n}개 > {D.article_per_min_max} (rules media.density.article_per_min_max)")
    return {"schema_version": 1, "candidates": len([s for ss in by_bucket.values() for s in ss]), "covered": covered,
            "used_events": len(arts), "per_min_max": D.article_per_min_max, "unused": unused, "warnings": warns}

"""카메라 제안 (v3.3.0, docs/handoff/05 §7, back_and_forth D-0056 작업 5) — **옵션이지 강제 아님**(19 §6, P8).

    python -m engine.camera_suggest <proj>   → prev/camera_suggest.json, 마지막 줄 StageResult JSON

direction.yaml 의 숏(카메라 키)마다 그 숏이 떠 있는 동안 보이는 장소(마커·뱃지·컷아웃·경로 끝점)를 모아
`engine.framing.frame_points` 로 최소 w·중심을, `engine.shots.choose_transition` 으로 들어오는 전환(move/dip)을 제안한다.
그 숏 동안 카드가 뜨면 카드 자리를 예약 영역에 넣는다. 전면 카드·패널이 화면을 덮는 동안만 있는 숏은 건너뛴다.
**direction.yaml 을 고치지 않는다** — 제안 파일만 쓴다. 적용은 연출가(LLM)·사람이 한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from engine.framing import FR, FramePoint, box_point, context_floor, default_reserve, frame_points, plain_point
from engine.projection import lat_of, ym
from engine.shots import SG, choose_transition, shot_issues

SUGGEST_FILE = "camera_suggest.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CamValue(_Strict):
    lon: float
    lat: float
    w: float


class ShotSuggest(_Strict):
    t: float                                   # 숏 시작(카메라 키 시각)
    t_end: float
    scene: str
    current: CamValue
    current_mode: Literal["move", "cut"]
    suggested: Optional[CamValue] = None       # None = 제안 없음(장소 없음·화면이 덮임)
    suggested_transition: Optional[Literal["move", "dip"]] = None
    fits: bool = False                         # 제안 카메라에서 장소 전부 안전 영역 안·예약 영역 밖
    current_fits: Optional[bool] = None        # 현재 카메라에서도 그런가
    points: list[str] = Field(default_factory=list)
    scale_class: Optional[str] = None          # 현재 카메라 w 의 shot_grammar.w_guide 분류(D-0058)
    context_w_min: Optional[float] = None      # 그 분류의 하한(camera.framing.context_w_min)
    w_before_context: Optional[float] = None   # 하한 적용 전 frame_points 최소 w(P5 — 하한이 바꾼 폭을 보인다)
    note: str = ""


class CameraSuggest(_Strict):
    schema_version: Literal[1] = 1
    direction_sha1: str = ""                   # 제안을 계산한 direction.yaml — provenance 가 '지금 연출에서 나온 제안인가'를 가린다
    shots: list[ShotSuggest]
    shot_issues_current: list[str] = Field(default_factory=list)   # engine.shots 검사(현재 연출)


def _points(events: list[dict], t0: float, t1: float, lead: float = 0.0) -> list[FramePoint]:
    """이 숏에서 **새로 등장하는** 장소(t0 가 숏 안) — 앞 장면에서 이어져 떠 있기만 한 마커·뱃지는 세지 않는다
    (v3 는 마커를 엔딩까지 남겨 두고 화면 밖이면 그리지 않는다). 상자는 렌더러 함수(marker_box·badge_box) 그대로."""
    import cairo  # noqa: PLC0415

    from engine.layers.badges import badge_box  # noqa: PLC0415
    from engine.layers.markers import marker_box  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[FramePoint] = []
    for e in events:
        if not (t0 - lead <= e["t0"] < t1):
            continue
        ref = f"{e['type']}:{e.get('label') or e.get('mid') or e.get('name') or ''}"
        if e["type"] == "marker":
            out.append(box_point(e["lon"], e["lat"], marker_box(ctx, e, 0.0, 0.0, with_sub=True), ref))
        elif e["type"] == "badge":
            out.append(box_point(e["lon"], e["lat"], badge_box(ctx, e, 0.0, 0.0), ref))
        elif e["type"] == "cutout":
            out.append(plain_point(e["lon"], e["lat"], ref))
        elif e["type"] in ("route", "tanker_loop") and e.get("pts"):
            for i in (0, -1):
                p = e["pts"][i]
                out.append(plain_point(p[0], p[1], f"{ref}#{i}", avoid_reserve=False))
    return out


def _covered(P, t0: float, t1: float) -> bool:  # noqa: ANN001, N803
    """숏 전체가 전면 카드·패널 뒤인가(그때 지도 카메라는 보이지 않는다)."""
    n = FR.cover_samples
    ts = [t0 + (t1 - t0) * i / (n - 1) for i in range(n)]
    return all(P.R.tb.in_fullcard(t) or any(e["type"] == "panel" and e["t0"] <= t <= e["t1"] for e in P.events) for t in ts)


def _frame(pts: list[FramePoint], card: bool, bounds: tuple, w_min: Optional[float]) -> tuple:  # noqa: ANN401
    """카드 자리까지 피하는 틀 → 안 되면 날짜만 피하는 틀(카드 겹침은 렌더 RESERVED 가 뱃지를 비킨다 — 적어 둔다)."""
    r = frame_points(pts, reserve=default_reserve(card=card), bounds=bounds, w_min=w_min)
    if r.ok or not card:
        return r, r.reason
    r2 = frame_points(pts, reserve=default_reserve(card=False), bounds=bounds, w_min=w_min)
    if r2.ok:
        return _not_ok(r2), f"카드 자리 회피 불가({r.reason}) — 날짜만 피한 틀, 카드 겹침은 렌더 RESERVED 가 비킴"
    return r, r.reason


def _not_ok(r):  # noqa: ANN001, ANN202
    r.ok = False
    return r


def _keys_for(P, sugs: list[Optional[tuple[float, float, float]]], trans: list[Optional[str]]) -> tuple[list, list[dict]]:  # noqa: ANN001, N803
    """제안값을 받아들였을 때의 카메라 키·암전 이벤트(engine.direction.build 와 같은 모양 — dip = 그 시각 cut + 1초 암전)."""
    from engine.camera import CamKey  # noqa: PLC0415
    from engine.direction import DIP_HALF_SEC  # noqa: PLC0415

    lo, hi = SG.move_dur_sec
    keys, dips = [], [e for e in P.events if e["type"] == "dip" and e.get("under")]
    others = [e for e in P.events if e["type"] != "dip"]
    old_dips = [e for e in P.events if e["type"] == "dip" and not e.get("under")]
    for k, sg, tr in zip(sorted(P.keys, key=lambda c: c.t), sugs, trans):
        x, y, w = sg if sg is not None else (k.x, k.y, k.w)
        if sg is None:
            keys.append(k)
            dips += [e for e in old_dips if abs((e["t0"] + e["t1"]) / 2 - k.t) < DIP_HALF_SEC]
        elif tr == "dip" or (tr is None and k.mode == "cut"):
            keys.append(CamKey(t=k.t, x=x, y=y, w=w, dur=0, mode="cut"))
            if tr == "dip" and not any(abs((e["t0"] + e["t1"]) / 2 - k.t) < DIP_HALF_SEC for e in dips):
                dips.append(dict(type="dip", t0=k.t - DIP_HALF_SEC, t1=k.t + DIP_HALF_SEC))
        else:
            keys.append(CamKey(t=k.t, x=x, y=y, w=w, dur=k.dur if k.mode == "move" else round((lo + hi) / 2, 2), mode="move"))
    return keys, others + dips


def suggest(P) -> CameraSuggest:  # noqa: ANN001, N803 — engine.project.Project
    """숏별 제안 → **실제 카메라 경로로 검증**(이동 중 등장·드리프트까지, engine.checks.offscreen_hits — 검사기 하나).
    화면 밖이 나온 숏은 w 를 camera.framing.path_w_step 배씩 키워 다시 틀을 잡는다(최대 verify_rounds 번)."""
    import dataclasses  # noqa: PLC0415

    from engine.camera import build_camera  # noqa: PLC0415
    from engine.checks import offscreen_hits  # noqa: PLC0415
    from engine.framing import place  # noqa: PLC0415
    from engine.shots import scene_at  # noqa: PLC0415
    from engine.style import FPS  # noqa: PLC0415

    keys = sorted(P.keys, key=lambda k: k.t)
    tiers = P.R.assets.tiers["W"]
    bounds = (tiers["lon0"], tiers["lat0"], tiers["lon1"], tiers["lat1"])
    ends = [keys[i + 1].t if i + 1 < len(keys) else P.plan.total for i in range(len(keys))]
    info: list[Optional[tuple[list[FramePoint], bool]]] = []
    floors: list[tuple[Optional[str], Optional[float]]] = []
    base: list[dict] = []
    notes: list[str] = []
    for k, t1 in zip(keys, ends):
        t0 = k.t + k.dur                       # 도착한 뒤부터 다음 키까지
        cur = CamValue(lon=round(k.x, 4), lat=round(lat_of(k.y), 4), w=round(k.w, 4))
        base.append(dict(t=round(k.t, 3), t_end=round(t1, 3), scene=scene_at(P.plan.sentences, max(k.t, 0.0)), current=cur,
                         current_mode=k.mode))
        pts = _points(P.events, k.t, t1)
        floors.append(context_floor(k.w))
        ep = SG.ending_pullback
        if k is keys[-1] and k.mode == "move" and ep.w_from <= k.w <= ep.w_to:
            info.append(None)
            notes.append("엔딩 풀백(shot_grammar.ending_pullback) — 문법 고정, 제안 없음")
        elif t1 <= t0 or _covered(P, t0, t1):
            info.append(None)
            notes.append("화면이 전면 카드·패널로 덮임 — 제안 없음")
        elif not pts:
            info.append(None)
            notes.append("장소 이벤트 없음 — 제안 없음")
        else:
            card = any(e["type"] in ("card", "article", "post") and e["t0"] <= t1 and e["t1"] >= t0 for e in P.events)
            info.append((pts, card))
            notes.append("")
    w_min: list[Optional[float]] = [f[1] for f in floors]   # 맥락 폭 하한 위에서 검증 라운드(D-0058 §3)
    before = [(_frame(inf[0], inf[1], bounds, None)[0].w if inf else None) for inf in info]
    left: list[str] = []
    for _ in range(FR.verify_rounds):
        res = [(_frame(inf[0], inf[1], bounds, w_min[i]) if inf else None) for i, inf in enumerate(info)]
        sugs = [(r.lon, ym(r.lat), r.w) if r else None for r, _ in (x if x else (None, "") for x in res)]
        trans: list[Optional[str]] = []
        prev: Optional[tuple[float, float, float]] = None
        for k, sg in zip(keys, sugs):
            here = sg if sg is not None else (k.x, k.y, k.w)
            trans.append(choose_transition(prev, sg) if sg is not None and prev is not None and k.t > 0 else None)
            prev = here
        nk, ev = _keys_for(P, sugs, trans)
        P2 = dataclasses.replace(P, keys=nk, events=ev, cams=build_camera(nk, P.n_frames, FPS))  # noqa: N806
        hits = offscreen_hits(P2)
        left = []
        grow = set()
        for e, t, over, _b in hits:
            i = max(j for j, k in enumerate(keys) if k.t <= t)
            if sugs[i] is None:
                continue                        # 제안 없는 숏(사람 카메라 그대로)의 문제는 제안 몫이 아니다
            left.append(f"{e['type']}:{e.get('label') or e.get('pid')} t={t:.1f} 화면 밖 {over:.0f}px")
            grow.add(i)
        grow = {i for i in grow if sugs[i][2] < FR.w_max}
        if not grow:
            break
        for i in grow:
            w_min[i] = min(FR.w_max, sugs[i][2] * FR.path_w_step)
    shots: list[ShotSuggest] = []
    for i, (k, b) in enumerate(zip(keys, base)):
        if res[i] is None:
            shots.append(ShotSuggest(**b, note=notes[i]))
            continue
        r, why = res[i]
        pts = info[i][0]
        cur_ok, _, _ = place(pts, b["current"].lon, b["current"].lat, b["current"].w, bounds=bounds, lenient=True)
        mine = [x for x in left if keys[i].t <= float(x.split(" t=")[1].split(" ")[0]) < ends[i]]
        unknown = "scale unknown — 맥락 폭 하한 없음" if floors[i][0] is None else ""
        note = "; ".join([n for n in (why, *mine, unknown) if n])
        shots.append(ShotSuggest(**b, suggested=CamValue(lon=r.lon, lat=r.lat, w=r.w), suggested_transition=trans[i],
                                 fits=r.ok and not mine, current_fits=cur_ok, points=[p.ref for p in pts],
                                 scale_class=floors[i][0], context_w_min=floors[i][1], w_before_context=before[i], note=note))
    dp = P.root / "direction.yaml"
    sha = hashlib.sha1(dp.read_bytes()).hexdigest() if dp.exists() else ""
    return CameraSuggest(direction_sha1=sha, shots=shots, shot_issues_current=shot_issues(P.keys, P.plan.sentences, P.events, P.plan.total))


def load_suggest(root: Path) -> Optional[CameraSuggest]:
    p = root / "prev" / SUGGEST_FILE
    return CameraSuggest.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


def main(argv: list[str] | None = None) -> int:
    from engine.project import ProjectError, load_project  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="engine.camera_suggest")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        cs = suggest(load_project(proj))
        out = proj / "prev" / SUGGEST_FILE
        out.parent.mkdir(exist_ok=True)
        out.write_text(cs.model_dump_json(indent=1), encoding="utf-8")
        n = sum(s.suggested is not None for s in cs.shots)
        res = StageResult(ok=True, stage="camera_suggest", artifacts={"camera_suggest": str(out)},
                          warnings=[f"제안 {n}/{len(cs.shots)}숏 · 현재 카메라가 장소를 다 못 담는 숏 "
                                    f"{sum(s.current_fits is False for s in cs.shots)}"])
    except (ProjectError, ValueError, OSError) as ex:
        res = StageResult(ok=False, stage="camera_suggest", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())

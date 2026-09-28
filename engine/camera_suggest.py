"""카메라 제안 (v3.3.0, docs/handoff/05 §7, back_and_forth D-0056 작업 5) — **옵션이지 강제 아님**(19 §6, P8).

    python -m engine.camera_suggest <proj>   → prev/camera_suggest.json, 마지막 줄 StageResult JSON

direction.yaml 의 숏(카메라 키)마다 그 숏이 떠 있는 동안 보이는 장소(마커·뱃지·컷아웃·경로 끝점)를 모아
`engine.framing.frame_points` 로 최소 w·중심을, `engine.shots.choose_transition` 으로 들어오는 전환(move/dip)을 제안한다.
그 숏 동안 카드가 뜨면 카드 자리를 예약 영역에 넣는다. 전면 카드·패널이 화면을 덮는 동안만 있는 숏은 건너뛴다.
**direction.yaml 을 고치지 않는다** — 제안 파일만 쓴다. 적용은 연출가(LLM)·사람이 한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from engine.framing import FR, FramePoint, box_point, default_reserve, frame_points, plain_point
from engine.projection import lat_of, ym
from engine.shots import choose_transition, shot_issues

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
    note: str = ""


class CameraSuggest(_Strict):
    schema_version: Literal[1] = 1
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


def suggest(P) -> CameraSuggest:  # noqa: ANN001, N803 — engine.project.Project
    from engine.framing import place  # noqa: PLC0415
    from engine.shots import scene_at  # noqa: PLC0415

    keys = sorted(P.keys, key=lambda k: k.t)
    tiers = P.R.assets.tiers["W"]
    bounds = (tiers["lon0"], tiers["lat0"], tiers["lon1"], tiers["lat1"])
    shots: list[ShotSuggest] = []
    prev: Optional[tuple[float, float, float]] = None
    for i, k in enumerate(keys):
        t0 = k.t + k.dur                       # 도착한 뒤부터 다음 키까지
        t1 = keys[i + 1].t if i + 1 < len(keys) else P.plan.total
        cur = CamValue(lon=round(k.x, 4), lat=round(lat_of(k.y), 4), w=round(k.w, 4))
        base = dict(t=round(k.t, 3), t_end=round(t1, 3), scene=scene_at(P.plan.sentences, max(k.t, 0.0)), current=cur,
                    current_mode=k.mode)
        if t1 <= t0 or _covered(P, t0, t1):
            shots.append(ShotSuggest(**base, note="화면이 전면 카드·패널로 덮임 — 제안 없음"))
            prev = (k.x, k.y, k.w)
            continue
        pts = _points(P.events, k.t, t1)
        if not pts:
            shots.append(ShotSuggest(**base, note="장소 이벤트 없음 — 제안 없음"))
            prev = (k.x, k.y, k.w)
            continue
        card = any(e["type"] in ("card", "article", "post") and e["t0"] <= t1 and e["t1"] >= t0 for e in P.events)
        res = default_reserve(card=card)
        r = frame_points(pts, reserve=res, bounds=bounds)
        cur_ok, _, _ = place(pts, cur.lon, cur.lat, cur.w, bounds=bounds, lenient=True)
        sug = (r.lon, ym(r.lat), r.w)
        trans = choose_transition(prev, sug) if prev is not None and k.t > 0 else None
        shots.append(ShotSuggest(**base, suggested=CamValue(lon=r.lon, lat=r.lat, w=r.w), suggested_transition=trans,
                                 fits=r.ok, current_fits=cur_ok, points=[p.ref for p in pts], note=r.reason))
        prev = sug
    return CameraSuggest(shots=shots, shot_issues_current=shot_issues(P.keys, P.plan.sentences, P.events, P.plan.total))


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

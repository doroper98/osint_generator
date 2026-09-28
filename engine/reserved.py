"""카드 RESERVED — 카드·기사 카드가 떠 있는 영역을 지도 뱃지·마커 라벨이 피한다 (v2.5.0, D-0033·D36, 08 §10·§11-4).

- 영역은 카드가 **떠 있는 시간 구간**에만 있다(알파 = 카드 알파). 카드가 사라지면 뱃지는 제자리로 돌아온다.
- 뱃지(`badge_strategy: push`): 카드 밖으로 나가는 최소 이동(방향 후보 `push_directions`)을 구해
  이동량 × 카드 알파만큼 옮긴다. 이동량이 `max_push_px` 를 넘으면 `hide`(뱃지 알파 × (1 − 카드 알파)).
- 마커(`marker_label_strategy: hide`): 점은 사실 위치라 그대로, 라벨만 카드 알파만큼 흐린다.
- 규칙 값은 `rules/video_rules.yaml panels.reserved`. 지도 레이어보다 카드가 나중에 그려지므로
  프레임 시작 때 `card_zones()` 로 영역을 먼저 계산해 `R.zones` 에 둔다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cairo

from engine.cards import card_geom
from engine.layers.media import article_geom, article_text
from engine.style import CARD
from engine.timebase import window
from rules import load_rules

RES = load_rules().panels.reserved
Box = tuple[float, float, float, float]   # x0, y0, x1, y1
_DIRS: dict[str, tuple[float, float]] = {"left": (-1, 0), "down": (0, 1), "left-down": (-math.sqrt(0.5), math.sqrt(0.5))}


@dataclass(frozen=True)
class Zone:
    box: Box
    a: float
    ref: str          # 무엇이 예약했나(provenance)


def presence(t: float, e: dict, fade_out: float) -> float:
    """영역 존재도 — 들어올 때는 카드보다 lead_sec 먼저 차오르고(뱃지가 미리 비킨다), 나갈 때는 카드 페이드와 같이 빠진다.
    그래서 한 카드가 나가며 다른 카드가 들어오는 순간(hormuz review 168.2초)에도 뱃지가 되돌아오지 않고,
    카드가 사라진 뒤(장면 컷 포함)에는 영역이 남지 않는다."""
    return window(t, e["t0"] - RES.lead_sec, e["t1"], RES.lead_sec, fade_out)


def card_box(ctx: cairo.Context, e: dict) -> Box:
    """카드·기사 카드·게시물 카드의 제자리 상자(x0, y0, x1, y1). 예약 영역과 checks overlap(NB23)이 같이 쓴다."""
    if e["type"] == "post":             # v3.2.0 — 상자는 load_project 가 소스 레코드로 미리 계산(post_box)
        x, y, w, h = e["post_box"]
    elif e["type"] == "card":
        x, y, w, h, _ = card_geom(ctx, e)
    else:
        x, y, w, h, _, _ = article_geom(ctx, e)
    return x, y, x + w, y + h


def card_zones(ctx: cairo.Context, events: list[dict], t: float) -> list[Zone]:
    out: list[Zone] = []
    for e in events:
        if e["type"] not in ("card", "article", "post"):
            continue
        a = presence(t, e, CARD.fade_sec)   # 기사·게시물 카드도 같은 0.45초 페이드(media.article_alpha, post.post_alpha)
        if a <= RES.min_zone_alpha:
            continue
        ref = (f"post:{e['src']}" if e["type"] == "post" else f"card:{e['tag']}" if e["type"] == "card"
               else f"article:{article_text(e)['pub']}")
        out.append(Zone(card_box(ctx, e), a, ref))
    return out


def _hits(b: Box, z: Box, g: float) -> bool:
    return b[0] < z[2] + g and z[0] < b[2] + g and b[1] < z[3] + g and z[1] < b[3] + g


def _shift(b: Box, d: tuple[float, float], s: float) -> Box:
    return (b[0] + d[0] * s, b[1] + d[1] * s, b[2] + d[0] * s, b[3] + d[1] * s)


def _need(b: Box, z: Box, d: tuple[float, float], g: float) -> float:
    """방향 d 로 몇 px 가야 영역 z(+간격 g) 밖인가. 이 방향으로 풀 수 없으면 inf."""
    cand = []
    if d[0] < 0:
        cand.append((b[2] - (z[0] - g)) / -d[0])
    if d[1] > 0:
        cand.append(((z[3] + g) - b[1]) / d[1])
    return max(0.0, min(cand)) if cand else math.inf


def push_vector(b: Box, zones: list[Zone]) -> tuple[float, float, str, float] | None:
    """(dx, dy, 방향, 이동량) — 모든 영역 밖으로 가는 최소 이동. 겹치지 않으면 None. 여러 영역이면 반복해서 민다."""
    live = [z for z in zones if _hits(b, z.box, RES.push_gap_px)]
    if not live:
        return None
    best: tuple[float, float, str, float] | None = None
    for name in RES.push_directions:
        d = _DIRS[name]
        s = 0.0
        for _ in range(len(zones) + 1):
            moved = _shift(b, d, s)
            hit = [z for z in zones if _hits(moved, z.box, RES.push_gap_px)]
            if not hit:
                break
            s += max(_need(moved, z.box, d, RES.push_gap_px) for z in hit)
        else:
            continue
        if best is None or s < best[3]:
            best = (d[0] * s, d[1] * s, name, s)
    return best


def avoid_badge(b: Box, zones: list[Zone]) -> tuple[float, float, float, dict | None]:
    """뱃지 상자 → (dx, dy, 알파 배율, 기록).

    이동 = ∫₀¹ push({영역: 존재도 ≥ s}) ds — 존재도 순으로 쌓은 층마다 그 층의 영역 전부를 피하는 이동을 두께만큼 더한다.
    영역이 하나면 push × 존재도. 두 카드가 교대할 때(한쪽 존재도가 내려가는 동안) 목표가 끊기지 않고 미끄러진다.
    층의 이동이 max_push_px 를 넘거나 방향이 없으면 그 두께만큼 흐린다(hide)."""
    live = sorted((z for z in zones if _hits(b, z.box, RES.push_gap_px)), key=lambda z: -z.a)
    if not live:
        return 0.0, 0.0, 1.0, None
    dx = dy = hidden = 0.0
    info: dict = {"strategy": "push", "direction": None, "px": 0.0, "zones": sorted({z.ref for z in live})}
    for k, z in enumerate(live):
        thick = z.a - (live[k + 1].a if k + 1 < len(live) else 0.0)
        level = [w for w in zones if w.a >= z.a]
        pv = push_vector(b, level) if RES.badge_strategy == "push" else None
        if pv is not None and pv[3] <= RES.max_push_px:
            dx += pv[0] * thick
            dy += pv[1] * thick
            if k == 0:
                info["direction"], info["px"] = pv[2], round(pv[3], 1)
        else:
            hidden += thick
            if k == 0:
                info = dict(info, strategy="hide", px=None if pv is None else round(pv[3], 1))
    return dx, dy, 1 - hidden, info


def marker_label_alpha(b: Box, zones: list[Zone]) -> float:
    if RES.marker_label_strategy == "none":
        return 1.0
    live = [z.a for z in zones if _hits(b, z.box, 0)]
    return 1 - max(live) if live else 1.0


def avoidance_report(P) -> list[dict]:  # noqa: ANN001 — engine.project.Project (순환 import 회피)
    """provenance `reserved.avoidance[]` — 지도 뱃지마다 카드 영역 때문에 비킨 기록(프레임 전수, 그리지 않고 계산만)."""
    from engine.layers.badges import badge_box  # noqa: PLC0415
    from engine.projection import View  # noqa: PLC0415
    from engine.style import FPS  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[dict] = []
    for e in P.events:
        if e["type"] != "badge":
            continue
        rec: dict | None = None
        for i in range(max(0, int(e["t0"] * FPS)), min(P.n_frames, int(e["t1"] * FPS) + 1)):
            t = i / FPS
            zones = card_zones(ctx, P.events, t)
            if not zones:
                continue
            x, y = View(P.R.stage, P.cams[i]).to_screen(*e["world"])
            dx, dy, ka, info = avoid_badge(badge_box(ctx, e, x, y), zones)
            if info is None:
                continue
            if rec is None:
                rec = {"badge": e["label"] or e.get("img") or e.get("flag"), "t0": round(t, 2), "t1": round(t, 2),
                       "strategy": set(), "direction": set(), "max_px": 0.0, "zones": set(), "frames": 0}
            rec["t1"] = round(t, 2)
            rec["frames"] += 1
            rec["strategy"].add(info["strategy"])
            if info.get("direction"):
                rec["direction"].add(info["direction"])
            rec["max_px"] = max(rec["max_px"], info["px"] or 0.0)
            rec["zones"] |= set(info["zones"])
        if rec is not None:
            out.append({k: sorted(v) if isinstance(v, set) else v for k, v in rec.items()})
    return out

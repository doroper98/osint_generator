"""Phase D1 스케치 — 미사일 발사·궤적·착탄, 탐지 자산 범위, EEZ(중첩 포함) 화면 시안.

실제 엔진(MercatorStage 지형·국경·지명, typography, 색 토큰)을 그대로 쓰고, 새 요소(EEZ 채움·빗금, 측지선 궤적,
탐지 부채꼴, 착탄 불확실성 원, 고도 단면 패널)만 이 파일에서 그린다. 레지스트리 등록 전 스케치(docs/handoff/20 §4.1-2).
자막·내레이션 없음(사용자 요청 2026-10-05 — 화면만 검토).

    python projects/d1_missile_sketch/sketch_d1.py            → out/d1_sketch.mp4 + out/d1_sheet.jpg
    python projects/d1_missile_sketch/sketch_d1.py --frames 30,95  → 해당 초의 정지 화면만
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import cairo
import numpy as np
from PIL import Image
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.assets import Assets, load_labels  # noqa: E402
from engine.projection import View  # noqa: E402
from engine.stage import MercatorStage, lat_of, ym  # noqa: E402
from engine.style import C, CARD_BG, DATE_BADGE, FPS, H_OUT, W_OUT, output_profile  # noqa: E402
from engine.timebase import clamp01, ease_io, ease_out, smooth, window  # noqa: E402
from engine.typography import rrect, text, tw  # noqa: E402
from engine.layers.routes import glow_line  # noqa: E402

PROJ = Path(__file__).resolve().parent
OUT = PROJ / "out"
TOTAL = 56.0
EARTH_KM = 6371.0

# ---------------------------------------------------------------- 사실 값(출처는 SOURCES 와 화면 출처 줄)
LAUNCH = (125.67, 39.20)          # 평양 순안 일대(합참 2022.11.18 "평양 순안 일대")
OSHIMA = (139.37, 41.51)          # 오시마오시마(渡島大島)
IMPACT_KM_WEST = 210              # 일본 방위성 "오시마오시마 서쪽 약 210km"
UNCERT_KM = 25                    # "약" 표현 → 점 대신 반경 표시(스케치 값, 규칙화 대상)
SOURCES = [
    "발사·비행: 합동참모본부 2022.11.18 발표(뉴시스 보도) · 일본 방위성 2022.11.18 발표",
    "EEZ: Marine Regions(VLIZ) EEZ 경계 · CC BY 4.0 · 한일·한중 미획정 구간은 등거리선 참고",
    "서해 남북: NLL 개략 재구성(공식 좌표 아님) · 북한 해상군사분계선 1999.9.2 발표 좌표(한국일보 1999.9.3)",
    "사드 AN/TPY-2 종말 모드 약 600km · 그린파인 블록-C 최대 약 800km(공개 사양·보도)",
    "화성-17형 도해: Geoarchive · Wikimedia Commons · CC BY-SA 4.0",
]

COL_EEZ = {"KR": "gold", "JP": "teal", "KP": "ru", "CN": "muted", "RU": "muted"}
OVERLAP_COLS = {"KR_KP": ("gold", "ru"), "KR_JP": ("gold", "teal"), "JP_RU": ("teal", "muted"), "TW_JP_CN": ("teal", "muted")}


# ---------------------------------------------------------------- 측지 계산(구면, R = 6371km)
def dest(lon: float, lat: float, brg_deg: float, km: float) -> tuple[float, float]:
    """출발점에서 방위각·거리만큼 간 점(대원)."""
    p1, l1, b, d = math.radians(lat), math.radians(lon), math.radians(brg_deg), km / EARTH_KM
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(l2), math.degrees(p2)


def bearing(a: tuple[float, float], b: tuple[float, float]) -> float:
    l1, p1, l2, p2 = math.radians(a[0]), math.radians(a[1]), math.radians(b[0]), math.radians(b[1])
    y = math.sin(l2 - l1) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(l2 - l1)
    return math.degrees(math.atan2(y, x)) % 360


def gc_dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    l1, p1, l2, p2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def gc_path(a: tuple[float, float], b: tuple[float, float], n: int = 120) -> np.ndarray:
    """두 점 사이 대원 경로(경위도)."""
    d, brg = gc_dist(a, b), bearing(a, b)
    return np.array([dest(a[0], a[1], brg, d * i / (n - 1)) for i in range(n)])


def world(ll: np.ndarray) -> np.ndarray:
    return np.column_stack([ll[:, 0], [ym(v) for v in ll[:, 1]]])


IMPACT = dest(*OSHIMA, 270, IMPACT_KM_WEST)
TRACK_LL = gc_path(LAUNCH, IMPACT, 160)
TRACK_KM = gc_dist(LAUNCH, IMPACT)


# ---------------------------------------------------------------- 카메라(숏 4개, 이동은 장면 전환에서만)
SHOTS = [  # (시작, 이동 끝, 중심 lon, lat, w)
    (0.0, 0.0, 132.6, 36.6, 37.0),     # 광역 — EEZ
    (8.6, 10.4, 126.9, 38.15, 9.5),    # 한반도 — 발사 지점·서해 남북 경계·미사일
    (17.0, 18.8, 132.0, 38.6, 25.0),   # 탐지 자산
    (28.0, 29.8, 132.9, 40.3, 19.5),   # 궤적·착탄
]


def camera(t: float) -> tuple[float, float, float]:
    cur = SHOTS[0]
    prev = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            prev, cur = cur, s
    if cur is SHOTS[0]:
        prev = cur
    k = ease_io(clamp01((t - cur[0]) / max(1e-6, cur[1] - cur[0]))) if cur[1] > cur[0] else 1.0
    x = prev[2] + (cur[2] - prev[2]) * k
    y = ym(prev[3]) + (ym(cur[3]) - ym(prev[3])) * k
    w = math.exp(math.log(prev[4]) + (math.log(cur[4]) - math.log(prev[4])) * k)
    nxt = next((s[0] for s in SHOTS if s[0] > t), TOTAL)
    hold = clamp01((t - cur[1]) / max(1.0, nxt - cur[1]))
    w *= 1 - 0.035 * smooth(hold)       # 숏 안 느린 푸시인(줌 범프 없음)
    return x, y, w


# ---------------------------------------------------------------- 그리기 도우미
def path_ll(ctx: cairo.Context, view: View, rings: list) -> None:
    for ring in rings:
        S = view.to_screen_arr(world(np.array(ring)))
        ctx.move_to(*S[0])
        for p in S[1:]:
            ctx.line_to(*p)
        ctx.close_path()


def hatch(ctx: cairo.Context, cols: tuple[str, str], a: float, gap: float = 5.0, wd: float = 1.6) -> None:
    """현재 클립 안을 두 색이 번갈아 드는 사선으로 채운다(중첩 주장 = 양쪽 색이 같은 무게)."""
    x0, y0, x1, y1 = ctx.clip_extents()
    span = (x1 - x0) + (y1 - y0)
    i = 0
    s = x0 - (y1 - y0)
    while s < x0 + span:
        ctx.move_to(s, y1)
        ctx.line_to(s + (y1 - y0), y0)
        ctx.set_source_rgba(*C[cols[i % 2]], a)
        ctx.set_line_width(wd)
        ctx.stroke()
        s += gap
        i += 1


def crosshatch_dots(ctx: cairo.Context, col: str, a: float, gap: float = 6.0) -> None:
    x0, y0, x1, y1 = ctx.clip_extents()
    y = y0
    row = 0
    while y < y1:
        x = x0 + (gap / 2 if row % 2 else 0)
        while x < x1:
            ctx.arc(x, y, 0.95, 0, 2 * math.pi)
            ctx.new_sub_path()
            x += gap
        y += gap * 0.8
        row += 1
    ctx.set_source_rgba(*C[col], a)
    ctx.fill()


RES: list = []      # 이번 프레임 새 라벨의 예약 상자 — 엔진 지명 라벨(draw_labels)이 피한다
DEFER: list = []    # 지명 라벨 뒤에 그릴 새 라벨(맨 위)


def _box(x: float, w: float, anchor: str) -> tuple[float, float]:
    return (x - w / 2, x + w / 2) if anchor == "c" else ((x - w, x) if anchor == "r" else (x, x + w))


def tag(ctx: cairo.Context, s: str, x: float, y: float, col: str, a: float, anchor: str = "l") -> float:
    """작은 글자 태그(추정·개념 표시). 상자 + 글자. 예약 상자에 올리고 지명 라벨 뒤에 그린다."""
    size = 10
    w = tw(ctx, s, size, "sansb") + 10
    xx = x - w / 2 if anchor == "c" else (x - w if anchor == "r" else x)
    if a > 0.05:
        RES.append((xx - 2, y - 13, xx + w + 2, y + 6))
    DEFER.append(lambda: _tag_draw(ctx, s, xx, y, w, col, a, size))
    return w


def _tag_draw(ctx: cairo.Context, s: str, xx: float, y: float, w: float, col: str, a: float, size: float) -> None:
    rrect(ctx, xx, y - 11, w, 15, 3)
    ctx.set_source_rgba(*C[col], 0.22 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*C[col], 0.9 * a)
    ctx.set_line_width(0.8)
    ctx.stroke()
    text(ctx, s, xx + 5, y, size, "sansb", C[col], a, 2.0, "l", role="tag")


def label2(ctx: cairo.Context, x: float, y: float, a: float, main: str, sub: str | None = None,
           col: tuple = (1, 1, 1), sub_col: str = "gold", anchor: str = "l") -> None:
    w = max(tw(ctx, main, 13, "sansb"), tw(ctx, sub, 11.5, "sansm") if sub else 0)
    x0, x1 = _box(x, w, anchor)
    shift = max(0.0, 8 - x0) - max(0.0, x1 - (W_OUT - 8))   # 화면 밖으로 나가면 안쪽으로 민다
    x, x0, x1 = x + shift, x0 + shift, x1 + shift
    if a > 0.05:
        RES.append((x0 - 4, y - 14, x1 + 4, y + (20 if sub else 5)))

    def draw() -> None:
        text(ctx, main, x, y, 13, "sansb", col, a, 3.2, anchor)
        if sub:
            text(ctx, sub, x, y + 16, 11.5, "sansm", C[sub_col], a, 3, anchor)
    DEFER.append(draw)


# ---------------------------------------------------------------- 층 1: EEZ
EEZ_TIMES = {"KR": 0.9, "JP": 1.7, "KP": 2.5, "CN": 3.1, "RU": 3.5,
             ("KR_JP", "overlap"): 4.7, ("KR_JP", "joint"): 5.6, ("JP_RU", "overlap"): 6.4,
             ("NLL", "claim_line"): 10.6, ("NK1999", "claim_line"): 11.8, ("KR_KP", "overlap"): 4.2}
WEST_KEYS = {("NLL", "claim_line"), ("NK1999", "claim_line"), ("KR_KP", "overlap")}   # 서해 남북 — 숏 2(한반도)에서 강조
CLAIM_STYLE = {"NLL": ("gold", None), "NK1999": ("ru", [6, 4])}
CLAIM_TXT = {   # (이름, 부제, 위치, 기준)
    "NLL": ("NLL · 1953", "유엔군사령부 설정 · 화면 선은 개략", (123.15, 38.32), "l"),
    "NK1999": ("북한 주장 해상군사분계선 · 1999", "1999.9.2 발표 좌표", (125.6, 37.05), "l"),
}
EEZ_NAME = {"KR": "한국 EEZ", "JP": "일본 EEZ", "KP": "북한 EEZ", "CN": "중국 EEZ", "RU": "러시아 EEZ"}
EEZ_LABEL_AT = {"KR": (124.4, 35.4), "JP": (146.5, 33.5), "KP": (130.6, 40.4), "CN": (122.6, 29.0), "RU": (137.2, 44.4)}
OVERLAP_TXT = {
    ("KR_JP", "overlap"): ("독도 주변 수역", "일본이 영유권 주장 · 대한민국 실효 지배", (133.6, 38.6), "l"),
    ("KR_JP", "joint"): ("한일 공동개발구역", "1974년 협정 · 경계 미획정 수역", (125.0, 31.2), "r"),
    ("JP_RU", "overlap"): ("쿠릴 남단 4개 섬", "러·일 중첩 주장", (146.4, 41.0), "r"),
    ("KR_KP", "overlap"): ("남북 주장 중첩 수역", "법적 경계 미획정", (123.15, 37.55), "l"),
}
OVERLAP_END = {("KR_KP", "overlap"): 17.6}   # 기본 9.0
OVERLAP_LABEL_AT = {("KR_KP", "overlap"): 13.0}   # 빗금은 처음부터, 설명 라벨은 서해 장면에서


class EEZ:
    def __init__(self) -> None:
        d = json.loads((PROJ / "eez.json").read_text(encoding="utf-8"))
        self.src = d["source"]
        self.feat = d["features"]
        self.label_ll = {}
        for f in self.feat:
            if f["kind"] == "eez" and f["code"] in EEZ_LABEL_AT:
                geo = shape({"type": "MultiPolygon", "coordinates": f["polys"]})
                p = EEZ_LABEL_AT[f["code"]]
                self.label_ll[f["code"]] = p if geo.contains(Point(p)) else tuple(f["rep"])

    def draw(self, ctx: cairo.Context, view: View, t: float, dim: float, jp_pulse: float) -> None:
        for f in self.feat:
            key = f["code"] if f["kind"] == "eez" else (f["code"], f["kind"])
            if key not in EEZ_TIMES:
                continue
            d_ = max(dim, window(t, 8.6, 18.2, 0.6, 0.8)) if key in WEST_KEYS else dim
            a = smooth((t - EEZ_TIMES[key]) / 0.7) * d_
            if a <= 0.01:
                continue
            if f["kind"] == "claim_line":
                col, dash = CLAIM_STYLE[f["code"]]
                grow = ease_io(clamp01((t - EEZ_TIMES[key]) / 1.2))
                for i, ln in enumerate(f["lines"]):
                    S = view.to_screen_arr(world(np.array(ln)))
                    dense = np.concatenate([np.linspace(S[j], S[j + 1], 12, endpoint=False) for j in range(len(S) - 1)] + [S[-1:]])
                    n = max(2, int(len(dense) * grow))
                    glow_line(ctx, dense[:n], C[col], a * (0.45 if i else 1.0), 1.5 if i == 0 else 1.0,
                              dash=[2, 3] if i else dash)
                if f["code"] == "NK1999":   # 발표 꼭짓점(북한 발표 좌표) 표시
                    for lon, lat in f["lines"][0][:-1]:
                        x, y = view.to_screen(lon, ym(lat))
                        ctx.rectangle(x - 2.2, y - 2.2, 4.4, 4.4)
                        ctx.set_source_rgba(*C[col], a * grow)
                        ctx.fill()
                continue
            ctx.save()
            ctx.new_path()
            path_ll(ctx, view, [r for poly in f["polys"] for r in poly])
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            if f["kind"] == "eez":
                col = COL_EEZ[f["code"]]
                boost = jp_pulse if f["code"] == "JP" else 0.0
                ctx.set_source_rgba(*C[col], (0.10 + 0.14 * boost) * a)
                ctx.fill()
                for ln in f["lines"]:   # 바다 쪽 경계만(해안선과 겹치는 구간은 eez.json 준비 때 뺐다)
                    if len(ln) < 2 or math.dist(ln[0], ln[-1]) + len(ln) * 0.01 < 0.15:
                        continue
                    S = view.to_screen_arr(world(np.array(ln)))
                    ctx.move_to(*S[0])
                    for q in S[1:]:
                        ctx.line_to(*q)
                ctx.set_source_rgba(*C[col], (0.6 + 0.4 * boost) * a)
                ctx.set_line_width(1.0 + boost)
                ctx.set_dash([4, 3])
                ctx.stroke()
                ctx.set_dash([])
            else:
                ctx.clip_preserve()
                ctx.new_path()
                if f["kind"] == "joint":
                    crosshatch_dots(ctx, "green", 0.8 * a)
                    col_line = "green"
                else:
                    hatch(ctx, OVERLAP_COLS[f["code"]], 0.75 * a)
                    col_line = OVERLAP_COLS[f["code"]][0]
                ctx.reset_clip()
                if key not in WEST_KEYS:   # 서해 남북 중첩은 테두리 대신 두 주장선(NLL·북한선)이 경계를 그린다
                    path_ll(ctx, view, [r for poly in f["polys"] for r in poly])
                    ctx.set_source_rgba(*C[col_line], 0.95 * a)
                    ctx.set_line_width(1.3)
                    ctx.stroke()
            ctx.restore()

    def labels(self, ctx: cairo.Context, view: View, t: float, dim: float) -> None:
        for code, (lon, lat) in self.label_ll.items():
            a = smooth((t - EEZ_TIMES[code] - 0.3) / 0.6) * dim * (1 - smooth((t - 8.6) / 0.6))
            x, y = view.to_screen(lon, ym(lat))
            if 0 < x < W_OUT and 0 < y < H_OUT:
                text(ctx, EEZ_NAME[code], x, y, 11.5, "sansb", C[COL_EEZ[code]], 0.95 * a, 3, "c")
        for key, (main, sub, (lon, lat), anc) in OVERLAP_TXT.items():
            d_ = max(dim, window(t, 8.6, 18.2, 0.6, 0.8)) if key in WEST_KEYS else dim
            a = window(t, OVERLAP_LABEL_AT.get(key, EEZ_TIMES[key]) + 0.3, OVERLAP_END.get(key, 9.0), 0.5, 0.6) * d_
            if a <= 0.01:
                continue
            f = next(f for f in self.feat if (f["code"], f["kind"]) == key)
            tx, ty = view.to_screen(lon, ym(lat))
            px, py = view.to_screen(f["rep"][0], ym(f["rep"][1]))
            ctx.move_to(px, py)
            ctx.line_to(tx + (6 if anc == "l" else -6), ty - 4)
            ctx.set_source_rgba(1, 1, 1, 0.55 * a)
            ctx.set_line_width(0.8)
            ctx.stroke()
            label2(ctx, tx, ty, a, main, sub, sub_col="muted", anchor=anc)
        for code, (main, sub, (lon, lat), anc) in CLAIM_TXT.items():
            key = (code, "claim_line")
            a = window(t, EEZ_TIMES[key] + 0.9, 17.6, 0.5, 0.6)
            if a <= 0.01:
                continue
            tx, ty = view.to_screen(lon, ym(lat))
            label2(ctx, tx, ty, a, main, sub, sub_col=CLAIM_STYLE[code][0], anchor=anc)
        f = next(f for f in self.feat if f["code"] == "NK1999")
        a = window(t, EEZ_TIMES[("NK1999", "claim_line")] + 1.4, 17.6, 0.5, 0.6)
        if a > 0.01:
            lon, lat = f["lines"][1][-1]
            x, y = view.to_screen(lon, ym(lat))
            tag(ctx, "이후 '중국과의 경계까지' · 방향 미발표 — 점선은 같은 방향 연장", x + 10, y + 4, "amber", a)
        a = window(t, 10.2, 17.6, 0.5, 0.6)
        for name, (lon, lat), dx in (("백령도", (124.67, 37.96), -6), ("연평도", (125.70, 37.66), 6)):
            if a <= 0.01:
                break
            x, y = view.to_screen(lon, ym(lat))
            ctx.arc(x, y, 2.4, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, a)
            ctx.fill()
            RES.append((x - 40, y + 4, x + 40, y + 20))
            DEFER.append(lambda x=x, y=y, name=name, dx=dx, a=a: text(ctx, name, x + dx * 0, y + 16, 11.5, "sansb", (1, 1, 1), a, 3, "c"))


# ---------------------------------------------------------------- 층 2: 탐지 자산
SENSORS = [  # (이름, 부제, 위치 lon/lat, 방위, 폭(도), 거리 km, 색, 등장, 위치 공개?, 태그)
    dict(name="사드 AN/TPY-2 · 성주", sub="종말 모드 탐지 약 600km", at=(128.28, 35.99), brg=None, width=120, km=600,
         col="us", t=19.0, exact=True, tag=None, side="r", lab=(129.4, 35.25)),
    dict(name="그린파인 레이더", sub="블록-C 최대 약 800km", at=(127.5, 36.7), brg=None, width=120, km=800,
         col="gold", t=21.0, exact=False, tag="위치 비공개 · 범위는 개념도", side="l", lab=(125.2, 36.0)),
    dict(name="AN/TPY-2 · 샤리키", sub="전진배치 모드", at=(140.32, 40.89), brg=None, width=120, km=1000,
         col="teal", t=23.0, exact=True, tag="거리 공개 추정치", side="l", lab=(141.0, 41.9)),
    dict(name="AN/TPY-2 · 교가미사키", sub="전진배치 모드", at=(135.22, 35.76), brg=None, width=120, km=1000,
         col="teal", t=24.4, exact=True, tag=None, side="l", lab=(135.6, 35.0)),
]
AEGIS = dict(name="이지스 구축함", sub="SPY-1D · 동해 작전", at=(130.3, 36.5), t=25.8)


def sector_ll(at: tuple[float, float], brg: float, width: float, km: float, n: int = 48) -> np.ndarray:
    pts = [at] + [dest(at[0], at[1], brg - width / 2 + width * i / (n - 1), km) for i in range(n)]
    return np.array(pts + [at])


def draw_sensor(ctx: cairo.Context, view: View, t: float, s: dict, dim: float) -> None:
    lt = t - s["t"]
    if lt <= 0:
        return
    grow = ease_out(clamp01(lt / 1.3))
    a = smooth(lt / 0.5) * dim
    brg = s["brg"] if s["brg"] is not None else bearing(s["at"], LAUNCH)
    col = C[s["col"]]
    km = s["km"] * grow
    if s["exact"]:
        poly = view.to_screen_arr(world(sector_ll(s["at"], brg, s["width"], km)))
        ctx.new_path()
        ctx.move_to(*poly[0])
        for p in poly[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        cx, cy = view.to_screen(s["at"][0], ym(s["at"][1]))
        rmax = max(np.hypot(poly[:, 0] - cx, poly[:, 1] - cy))
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, max(rmax, 1))
        g.add_color_stop_rgba(0, *col, 0.30 * a)
        g.add_color_stop_rgba(1, *col, 0.05 * a)
        ctx.set_source(g)
        ctx.fill_preserve()
        ctx.set_source_rgba(*col, 0.7 * a)
        ctx.set_line_width(1.1)
        ctx.stroke()
        for frac in (0.5,):   # 거리 눈금 호(절반)
            arc = view.to_screen_arr(world(np.array([dest(s["at"][0], s["at"][1], brg - s["width"] / 2 + s["width"] * i / 31, km * frac)
                                                     for i in range(32)])))
            glow_line(ctx, arc, col, 0.35 * a, 0.7, dash=[2, 3])
        # 스캔 빔: 부채꼴 안을 천천히 쓸고 지나간다(영상미, 사실 정보 아님)
        sweep = brg - s["width"] / 2 + s["width"] * (0.5 + 0.5 * math.sin(lt * 1.1))
        tip = view.to_screen(*world(np.array([dest(s["at"][0], s["at"][1], sweep, km)]))[0])
        ctx.move_to(cx, cy)
        ctx.line_to(*tip)
        ctx.set_source_rgba(*col, 0.45 * a)
        ctx.set_line_width(1.2)
        ctx.stroke()
        ctx.arc(cx, cy, 3.4, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*col, a)
        ctx.set_line_width(1.4)
        ctx.stroke()
    else:
        # 위치 비공개 — 기준점을 찍지 않는다. 시작점을 흐린 여러 겹으로 그려 "어딘가"임을 보인다
        offs = [(-0.6, -0.3), (0.5, 0.2), (0.0, 0.5), (-0.2, -0.6), (0.6, -0.4)]
        for dx, dy in offs:
            at = (s["at"][0] + dx, s["at"][1] + dy)
            poly = view.to_screen_arr(world(sector_ll(at, brg, s["width"], km)))
            ctx.new_path()
            ctx.move_to(*poly[0])
            for p in poly[1:]:
                ctx.line_to(*p)
            ctx.close_path()
            ctx.set_source_rgba(*col, 0.06 * a)
            ctx.fill()
        poly = view.to_screen_arr(world(sector_ll(s["at"], brg, s["width"], km)))
        glow_line(ctx, poly[1:-1], col, 0.6 * a, 0.9, dash=[5, 4])
        cx, cy = view.to_screen(s["at"][0], ym(s["at"][1]))
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, 26)
        g.add_color_stop_rgba(0, *col, 0.55 * a)
        g.add_color_stop_rgba(1, *col, 0.0)
        ctx.set_source(g)
        ctx.arc(cx, cy, 26, 0, 2 * math.pi)
        ctx.fill()
    la = smooth((lt - 0.6) / 0.5) * dim * (1 - smooth((t - 27.6) / 0.6))
    lx, ly = view.to_screen(s["lab"][0], ym(s["lab"][1]))
    anc = "l" if s["side"] == "r" else "r"
    nxt = min([o["t"] for o in SENSORS if o["t"] > s["t"]] + [AEGIS["t"]])
    full = 1 - smooth((t - nxt) / 0.5)          # 다음 자산이 나오면 부제·태그는 물러나고 이름만 남는다
    if full > 0.02:
        label2(ctx, lx, ly, la * full, s["name"], s["sub"], sub_col=s["col"], anchor=anc)
        if s["tag"]:
            tag(ctx, s["tag"], lx, ly + 34, "amber", la * full, anchor=anc)
    if full < 0.98:
        label2(ctx, lx, ly, la * (1 - full) * 0.8, s["name"], None, anchor=anc)


def draw_aegis(ctx: cairo.Context, view: View, t: float, dim: float) -> None:
    lt = t - AEGIS["t"]
    if lt <= 0:
        return
    a = smooth(lt / 0.5) * dim
    x, y = view.to_screen(AEGIS["at"][0], ym(AEGIS["at"][1]))
    for k in range(2):
        f = ((lt * 0.45) + k / 2) % 1.0
        ctx.arc(x, y, 5 + 26 * ease_out(f), 0, 2 * math.pi)
        ctx.set_source_rgba(*C["gold"], 0.5 * (1 - f) * a)
        ctx.set_line_width(1.2)
        ctx.stroke()
    # 함정 실루엣(벡터 기호)
    ctx.save()
    ctx.translate(x, y)
    ctx.move_to(-11, -2)
    ctx.line_to(9, -2)
    ctx.line_to(13, 0)
    ctx.line_to(9, 3)
    ctx.line_to(-10, 3)
    ctx.close_path()
    ctx.rectangle(-4, -6, 6, 4)
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill()
    ctx.restore()
    la = smooth((lt - 0.5) / 0.5) * dim * (1 - smooth((t - 27.6) / 0.6))
    label2(ctx, x + 16, y + 4, la, AEGIS["name"], AEGIS["sub"], sub_col="gold")
    tag(ctx, "함정 위치는 예시 · 탐지 거리 비공개", x + 16, y + 38, "amber", la)


# ---------------------------------------------------------------- 층 3: 발사·궤적·착탄
T_LAUNCH_MK = 10.8
T_TRACK0, T_TRACK1 = 30.4, 38.0
T_IMPACT = T_TRACK1
FLIGHT_SEC = 4135          # 일본 방위성


def draw_launch(ctx: cairo.Context, view: View, t: float, dim: float) -> None:
    lt = t - T_LAUNCH_MK
    if lt <= 0:
        return
    a = smooth(lt / 0.4) * dim
    x, y = view.to_screen(*world(np.array([LAUNCH]))[0])
    for k in range(2):
        f = ((lt * 0.5) + k / 2) % 1.0
        ctx.arc(x, y, 4 + 20 * ease_out(f), 0, 2 * math.pi)
        ctx.set_source_rgba(*C["ru"], 0.6 * (1 - f) * a)
        ctx.set_line_width(1.4)
        ctx.stroke()
    # 발사 기호: 위로 향한 삼각형
    ctx.move_to(x, y - 6)
    ctx.line_to(x + 5, y + 4)
    ctx.line_to(x - 5, y + 4)
    ctx.close_path()
    ctx.set_source_rgba(*C["ru"], a)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.set_line_width(1)
    ctx.stroke()
    la = smooth((lt - 0.3) / 0.4) * dim
    main, sub = "평양 순안 일대", "발사 · 오전 10시 15분"
    w = max(tw(ctx, main, 13, "sansb"), tw(ctx, sub, 11.5, "sansm"))
    if x - 12 - w < 8:   # 왼쪽 공간이 모자라면 점 오른쪽으로(라벨이 기호를 덮지 않게)
        label2(ctx, x + 14, y + 22, la, main, sub, sub_col="ru", anchor="l")
    else:
        label2(ctx, x - 12, y + 4, la, main, sub, sub_col="ru", anchor="r")


def draw_track(ctx: cairo.Context, view: View, t: float, dim: float) -> None:
    if t < T_TRACK0:
        return
    prog = ease_io(clamp01((t - T_TRACK0) / (T_TRACK1 - T_TRACK0)))
    S = view.to_screen_arr(world(TRACK_LL))
    n = max(2, int(round(1 + (len(S) - 1) * prog)))
    glow_line(ctx, S[:n], C["ru"], dim, 2.0)
    if prog < 1:
        hx, hy = S[n - 1]
        g = cairo.RadialGradient(hx, hy, 0, hx, hy, 14)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.95 * dim)
        g.add_color_stop_rgba(0.3, *C["ru"], 0.6 * dim)
        g.add_color_stop_rgba(1, *C["ru"], 0)
        ctx.set_source(g)
        ctx.arc(hx, hy, 14, 0, 2 * math.pi)
        ctx.fill()
    # 비행 시간 계기(지상 궤적 아래쪽, 화면 고정)
    a = window(t, T_TRACK0, T_TRACK1 + 3.5, 0.4, 0.6) * dim
    sec = int(FLIGHT_SEC * prog)
    text(ctx, "비행 경과", 32, 404, 11.5, "sansm", C["muted"], a, 3, role="hud")
    text(ctx, f"+{sec // 60:02d}:{sec % 60:02d}", 32, 432, 26, "mono", (1, 1, 1), a, 3.5)
    # 거리는 계산값을 보이지 않는다(발사·착탄 좌표가 근사라 발표값과 어긋남) — 착탄 뒤 발표값만
    text(ctx, "비행거리 약 1,000km · 합참 발표", 32, 452, 12, "sansm", C["gold"], a * smooth((t - T_TRACK1) / 0.5), 3)
    text(ctx, "궤적선은 발사점·착탄점을 잇는 지상 투영(대원) · 실제 비행은 고각", 32, 470, 9.5, "sans", C["muted"], 0.85 * a, 2, role="source")


def draw_impact(ctx: cairo.Context, view: View, t: float, dim: float) -> float:
    lt = t - T_IMPACT
    if lt <= 0:
        return 0.0
    a = smooth(lt / 0.3) * dim
    ix, iy = view.to_screen(*world(np.array([IMPACT]))[0])
    # 번쩍임(한 번)
    fl = math.exp(-lt * 3.0)
    if fl > 0.02:
        g = cairo.RadialGradient(ix, iy, 0, ix, iy, 40)
        g.add_color_stop_rgba(0, 1, 0.9, 0.7, 0.85 * fl * dim)
        g.add_color_stop_rgba(1, *C["amber"], 0)
        ctx.set_source(g)
        ctx.arc(ix, iy, 40, 0, 2 * math.pi)
        ctx.fill()
    # 불확실성 원: "약 210km" → 점이 아니라 영역
    ring = view.to_screen_arr(world(np.array([dest(IMPACT[0], IMPACT[1], b, UNCERT_KM * ease_out(clamp01(lt / 0.8)))
                                              for b in range(0, 361, 6)])))
    ctx.new_path()
    ctx.move_to(*ring[0])
    for p in ring[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*C["amber"], 0.22 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*C["amber"], 0.95 * a)
    ctx.set_dash([3, 2.5])
    ctx.set_line_width(1.3)
    ctx.stroke()
    ctx.set_dash([])
    # 오시마오시마 기준점과 거리선
    ma = smooth((lt - 0.8) / 0.5) * dim
    ox, oy = view.to_screen(*world(np.array([OSHIMA]))[0])
    seg = view.to_screen_arr(world(gc_path(IMPACT, OSHIMA, 30)))
    k = int(2 + 28 * ease_io(clamp01((lt - 0.8) / 1.0)))
    glow_line(ctx, seg[:k], (1, 1, 1), 0.8 * ma, 0.8, dash=[3, 3])
    ctx.arc(ox, oy, 2.8, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 1, 1, ma)
    ctx.fill()
    text(ctx, "오시마오시마", ox + 6, oy - 6, 11.5, "sansm", (1, 1, 1), ma, 3)
    mx, my = seg[15]
    text(ctx, "약 210km", mx, my - 7, 12, "sansb", C["gold"], smooth((lt - 1.6) / 0.4) * dim, 3, "c")
    la = smooth((lt - 0.4) / 0.5) * dim
    label2(ctx, ix - 2, iy + 34, la, "착탄 추정 영역", "일본 방위성 · 오시마오시마 서쪽 약 210km", sub_col="amber", anchor="c")
    jp = smooth((lt - 2.2) / 0.5) * dim
    if jp > 0.01:
        tag(ctx, "일본 EEZ 안쪽", ix, iy + 66, "teal", jp, anchor="c")
    return clamp01((lt - 2.0) / 0.6) * (1 - clamp01((lt - 5.5) / 1.0))


# ---------------------------------------------------------------- 층 4: 미사일 도해 카드
T_CARD0, T_CARD1 = 12.0, 17.6
_IMG: dict = {}


def missile_img() -> cairo.ImageSurface | None:
    if "s" in _IMG:
        return _IMG["s"]
    p = PROJ / "media" / "hwasong17_diagram.png"
    if not p.exists():
        _IMG["s"] = None
        return None
    im = Image.open(p).convert("RGBA")
    im = im.crop((im.width // 2, 0, im.width, im.height))          # 오른쪽 = 2022.11 발사형
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    im = im.rotate(-90, expand=True)                                  # 가로로 눕힘(탄두가 오른쪽)
    arr = np.asarray(im, dtype=np.float32)
    al = arr[:, :, 3:4] / 255.0
    pm = np.concatenate([arr[:, :, [2, 1, 0]] * al, arr[:, :, 3:4]], axis=2).round().astype(np.uint8)   # cairo ARGB32 = 미리 곱한 BGRA
    s = cairo.ImageSurface.create_for_data(bytearray(pm.tobytes()), cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
    _IMG["s"] = s
    return s


def draw_missile_card(ctx: cairo.Context, t: float) -> None:
    a = window(t, T_CARD0, T_CARD1, 0.55, 0.55)
    if a <= 0.01:
        return
    s = missile_img()
    x, y, w, h = 452, 64, 376, 168
    slide = (1 - ease_out(clamp01((t - T_CARD0) / 0.55))) * 24
    x += slide
    rrect(ctx, x, y, w, h, 8)
    ctx.set_source_rgba(*CARD_BG[:3], CARD_BG[3] * a)
    ctx.fill()
    inner = (x + 12, y + 12, w - 24, h - 82)
    rrect(ctx, *inner, 5)
    ctx.set_source_rgba(0.93, 0.93, 0.91, 0.96 * a)
    ctx.fill()
    if s is not None:
        sc = min((inner[2] - 16) / s.get_width(), (inner[3] - 16) / s.get_height())
        ctx.save()
        ctx.translate(inner[0] + inner[2] / 2 - s.get_width() * sc / 2, inner[1] + inner[3] / 2 - s.get_height() * sc / 2)
        ctx.scale(sc, sc)
        ctx.set_source_surface(s, 0, 0)
        ctx.paint_with_alpha(a)
        ctx.restore()
    else:
        text(ctx, "도해 이미지 받는 중", inner[0] + inner[2] / 2, inner[1] + inner[3] / 2, 12, "sansm", (0.3, 0.3, 0.3), a, 0, "c")
    text(ctx, "화성-17형", x + 14, y + h - 50, 17, "disp", (1, 1, 1), a, 0)
    text(ctx, "2022년 11월 발사형 · 개념 도해", x + 14, y + h - 31, 11.5, "sansm", C["gold"], a, 0)
    text(ctx, "도해 · Geoarchive · CC BY-SA 4.0", x + 14, y + h - 14, 9.5, "sans", C["muted"], a, 0, role="credit")


# ---------------------------------------------------------------- 층 5: 고도 단면 패널
T_PROF0, T_PROF1 = 43.0, 51.2
APOGEE_JP, APOGEE_JCS = 6040.9, 6100
RANGE_JP = 999.2


def loft(u: np.ndarray) -> np.ndarray:
    """고각 궤적 모양(개념): 거리 비율 u → 고도 비율. 정점 부근이 완만한 포물선."""
    return 4 * u * (1 - u)


def draw_profile(ctx: cairo.Context, t: float) -> None:
    a = window(t, T_PROF0, T_PROF1, 0.6, 0.6)
    if a <= 0.01:
        return
    ctx.set_source_rgba(0.02, 0.025, 0.04, 0.55 * a)
    ctx.paint()
    x, y, w, h = 436, 64, 392, 362
    slide = (1 - ease_out(clamp01((t - T_PROF0) / 0.6))) * 30
    x += slide
    rrect(ctx, x, y, w, h, 8)
    ctx.set_source_rgba(0.07, 0.08, 0.12, 0.94 * a)
    ctx.fill()
    text(ctx, "고도 단면", x + 16, y + 28, 17, "disp", (1, 1, 1), a, 0)
    text(ctx, "고각 발사 · 위로 높이 솟아 짧게 떨어짐", x + 16, y + 47, 11.5, "sansm", C["muted"], a, 0)
    # 축
    gx0, gy0, gx1, gy1 = x + 58, y + 70, x + w - 24, y + 262
    alt_max = 7000.0
    ctx.set_line_width(0.8)
    for alt in (0, 2000, 4000, 6000):
        yy = gy1 - (gy1 - gy0) * alt / alt_max
        ctx.move_to(gx0, yy)
        ctx.line_to(gx1, yy)
        ctx.set_source_rgba(1, 1, 1, (0.35 if alt == 0 else 0.12) * a)
        ctx.stroke()
        text(ctx, f"{alt:,}", gx0 - 6, yy + 4, 10, "mono", C["muted"], a, 0, "r")
    text(ctx, "고도 km", gx0 - 6, gy0 - 8, 10, "sansm", C["muted"], a, 0, "r")
    for rng in (0, 500, 1000):
        xx = gx0 + (gx1 - gx0) * rng / 1000
        text(ctx, f"{rng:,}", xx, gy1 + 15, 10, "mono", C["muted"], a, 0, "c")
    text(ctx, "지상 거리 km", gx1, gy1 + 30, 10, "sansm", C["muted"], a, 0, "r")
    # 국제우주정거장 고도(약 400km) 기준선
    yy = gy1 - (gy1 - gy0) * 400 / alt_max
    ctx.move_to(gx0, yy)
    ctx.line_to(gx1, yy)
    ctx.set_dash([3, 3])
    ctx.set_source_rgba(*C["teal"], 0.8 * a)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "국제우주정거장 약 400km", gx1 - 2, yy - 4, 10, "sansm", C["teal"], a, 2, "r")
    # 궤적
    prog = ease_io(clamp01((t - T_PROF0 - 0.6) / 2.6))
    u = np.linspace(0, 1, 120)[: max(2, int(120 * prog))]
    pts = np.column_stack([gx0 + (gx1 - gx0) * u * RANGE_JP / 1000, gy1 - (gy1 - gy0) * loft(u) * APOGEE_JP / alt_max])
    glow_line(ctx, pts, C["ru"], a, 2.0)
    pa = smooth((t - T_PROF0 - 2.4) / 0.5) * a
    ax, ay = gx0 + (gx1 - gx0) * 0.5 * RANGE_JP / 1000, gy1 - (gy1 - gy0) * APOGEE_JP / alt_max
    ctx.arc(ax, ay, 3, 0, 2 * math.pi)
    ctx.set_source_rgba(*C["gold"], pa)
    ctx.fill()
    text(ctx, "정점", ax + 8, ay + 4, 11.5, "sansb", C["gold"], pa, 2.5)
    text(ctx, "가로·세로 축척 다름 · 궤적 모양은 개념", x + 16, gy1 + 30, 9.5, "sans", C["muted"], a, 0, role="source")
    # 두 출처 나란히(같은 무게)
    ta = smooth((t - T_PROF0 - 3.0) / 0.5) * a
    ty = y + 312
    cols = [("합동참모본부", ["거리 약 1,000km", "고도 약 6,100km", "속도 약 마하 22"]),
            ("일본 방위성", ["거리 999.2km", "고도 6,040.9km", "비행 4,135초(약 69분)"])]
    for i, (who, rows) in enumerate(cols):
        cx = x + 16 + i * (w - 32) / 2
        text(ctx, who, cx, ty, 12, "sansb", C["gold"] if i == 0 else C["teal"], ta, 0)
        for j, r in enumerate(rows):
            text(ctx, r, cx, ty + 16 + j * 14, 11, "sansm", (1, 1, 1), ta, 0)


# ---------------------------------------------------------------- 출처 줄·날짜·엔딩
def draw_date(ctx: cairo.Context, t: float) -> None:
    B = DATE_BADGE
    k = smooth((t - 0.4) / B.slide_sec)
    a = 0.95 * k * (1 - smooth((t - (TOTAL - 4.6)) / 0.5))
    txt = "2022. 11. 18"
    w = text(ctx, txt, W_OUT - B.x_right, B.y - (1 - k) * B.slide_px, B.size, B.font, (1, 1, 1), a, 3, "r")
    ctx.set_source_rgba(*C["gold"], 0.9 * a)
    ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
    ctx.fill()


def draw_source_line(ctx: cairo.Context, t: float) -> None:
    a = window(t, 1.0, 9.6, 0.6, 0.6)
    text(ctx, "EEZ 경계: Marine Regions(VLIZ) · CC BY 4.0 · 미획정 구간은 등거리선 참고", 14, 470, 9.5, "sans", C["muted"], 0.9 * a, 2, role="source")
    a3 = window(t, 10.8, 17.6, 0.6, 0.6)
    text(ctx, "NLL: 서해 5도와 북측 해안의 중간점 원칙으로 개략 재구성(공식 좌표 아님) · 북한선: 1999.9.2 발표 좌표(한국일보 보도)", 14, 470, 9.5, "sans", C["muted"], 0.9 * a3, 2, role="source")
    a2 = window(t, 19.4, 28.4, 0.6, 0.6)
    text(ctx, "탐지 거리: 공개 사양·언론 보도 기준 · 실제 운용 범위는 비공개", 14, 470, 9.5, "sans", C["muted"], 0.9 * a2, 2, role="source")


def draw_end(ctx: cairo.Context, t: float) -> None:
    a = smooth((t - (TOTAL - 4.4)) / 0.6)
    if a <= 0.01:
        return
    ctx.set_source_rgba(0.02, 0.025, 0.04, 0.92 * a)
    ctx.paint()
    text(ctx, "자료", 60, 170, 17, "disp", (1, 1, 1), a, 0)
    for i, s in enumerate(SOURCES):
        text(ctx, s, 60, 200 + i * 20, 11, "sansm", C["muted"], a, 0, role="credit")
    text(ctx, "Phase D1 화면 스케치 · 자막·내레이션 없음", 60, 300, 10, "sans", C["muted"], 0.8 * a, 0, role="credit")


# ---------------------------------------------------------------- 프레임
def build_stage() -> MercatorStage:
    out = output_profile("720p")
    assets = Assets(PROJ, load_labels(PROJ / "labels.yaml"), "720p")
    st = MercatorStage(assets, out=out)
    st.out_profile = out
    return st


def render(stage: MercatorStage, eez: EEZ, t: float) -> tuple[bytearray, cairo.ImageSurface]:
    OP = stage.out_profile
    view = View(stage, np.array(camera(t)))
    buf = bytearray(OP.width * OP.height * 4)
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * 4)
    ctx = cairo.Context(surf)
    ctx.translate(OP.pad_x, 0)
    ctx.scale(OP.k, OP.k)
    stage.render_base(ctx, view)
    # 장면별 초점: 지금 이야기하는 층이 밝고 나머지는 물러난다
    eez_dim = 1.0 - 0.55 * smooth((t - 9.0) / 1.0) + 0.25 * smooth((t - 30.0) / 1.0)
    sens_dim = 1.0 - 0.6 * smooth((t - 29.0) / 1.0)
    jp_pulse = 0.0
    if t >= T_IMPACT:
        jp_pulse = clamp01((t - T_IMPACT - 2.0) / 0.6) * (1 - clamp01((t - T_IMPACT - 5.5) / 1.0))
    eez.draw(ctx, view, t, eez_dim, jp_pulse)
    for s in SENSORS:
        own = 1.0 if t < s["t"] + 1.6 or t > 26.8 else 1.0
        later = [o for o in SENSORS if o["t"] > s["t"] and t > o["t"]]
        focus = 0.55 if later and t < 27.2 else 1.0
        draw_sensor(ctx, view, t, s, sens_dim * focus * own)
    draw_aegis(ctx, view, t, sens_dim)
    draw_launch(ctx, view, t, 1.0)
    draw_track(ctx, view, t, 1.0)
    eez.labels(ctx, view, t, eez_dim if t < 30 else 0.0)
    draw_impact(ctx, view, t, 1.0)
    stage.draw_labels(ctx, view, list(RES), 1.0)
    for fn in DEFER:
        fn()
    RES.clear()
    DEFER.clear()
    draw_missile_card(ctx, t)
    draw_profile(ctx, t)
    draw_source_line(ctx, t)
    draw_date(ctx, t)
    draw_end(ctx, t)
    fa = 1 - min(smooth(t / 1.0), smooth((TOTAL - t) / 1.2))
    if fa > 0.001:
        ctx.set_source_rgba(0, 0, 0, fa)
        ctx.paint()
    surf.flush()
    return buf, surf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default=None, help="쉼표로 구분한 초 — 정지 화면만")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    stage = build_stage()
    eez = EEZ()
    OP = stage.out_profile
    if args.frames:
        for s in args.frames.split(","):
            _, surf = render(stage, eez, float(s))
            surf.write_to_png(str(OUT / f"frame_{float(s):05.1f}.png"))
            print(OUT / f"frame_{float(s):05.1f}.png")
        return 0
    sheet_t = [5.0, 8.4, 14.0, 20.5, 27.0, 34.0, 41.0, 48.0, 54.0]
    cells = []
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{OP.width}x{OP.height}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(OUT / "d1_sketch.mp4")], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        t = i / FPS
        buf, surf = render(stage, eez, t)
        ff.stdin.write(bytes(buf))
        if any(abs(t - s) < 0.5 / FPS for s in sheet_t):
            im = Image.frombuffer("RGBA", (OP.width, OP.height), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB")
            cells.append((im.resize((854, 480)), f"t={t:.1f}s"))
        if i % 120 == 0:
            print(f"{i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    from engine.sheet import grid
    grid(cells, 2, OUT / "d1_sheet.jpg", cell=(854, 480))
    print(OUT / "d1_sketch.mp4", OUT / "d1_sheet.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

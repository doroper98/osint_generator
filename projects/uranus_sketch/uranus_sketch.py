"""천왕성 작전(1942.11.19~30) 전황 화면 스케치 — 국가·제대별 배치, 공격 화살표, 날짜별 전선, 포위망.

    python projects/uranus_sketch/uranus_sketch.py              → out/uranus_sketch.mp4 + out/uranus_sheet.jpg
    python projects/uranus_sketch/uranus_sketch.py --frames 6,20 → 정지 화면

엔진 지형(MercatorStage.base_image, 현대 국경·행정구역선·현대 지명은 그리지 않는다 — 1942년 소련 영토)과 typography·색 토큰을 쓰고,
새 요소(부대 부호·제대 표시, 진격 화살표, 전선 그리기, 포위망 빗금)는 이 파일에서 그린다. 레지스트리 등록 전 스케치.
전선 좌표는 prep_uranus.py 가 참고 작전도(SVG)에서 경위도로 옮긴 것(개략). 부대 위치·화살표 경로는 군 단위 개략(참고 지도 2종 대조).
자막·내레이션 없음.
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

PROJ = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ.parents[1]))

from engine.assets import Assets, load_labels  # noqa: E402
from engine.layers.routes import catmull, glow_line  # noqa: E402
from engine.projection import View  # noqa: E402
from engine.stage import MercatorStage, ym  # noqa: E402
from engine.style import C, CARD_BG, DATE_BADGE, FPS, H_OUT, W_OUT, output_profile  # noqa: E402
from engine.timebase import clamp01, ease_io, ease_out, smooth, window  # noqa: E402
from engine.typography import rrect, text, tw  # noqa: E402

OUT = PROJ / "out"
TOTAL = 58.0
D = json.loads((PROJ / "uranus.json").read_text(encoding="utf-8"))

NATION = {  # 색 = 엔진 강조 토큰(rules registries.accents)
    "su": ("ru", "소련"), "de": ("us", "독일"), "ro": ("amber", "루마니아"), "it": ("green", "이탈리아"),
}
WATER = (0.42, 0.66, 0.86)


# ---------------------------------------------------------------- 데이터(개략)
def piece(date: str, idx: int, side: str = "axis") -> np.ndarray:
    return np.array(D["fronts"][date][side][idx])


F19 = [piece("1119", 0), piece("1119", 1)]                       # 11.19 개시선(추축 쪽 선)
NORTH = F19[1]                                                     # 돈강 따라 서 → 동(볼가 북쪽)까지. 저장 순서 동 → 서
RING10 = piece("1123", 10)                                         # 11.23 포위망 서·남 고리(돈강 큰 굴곡 → 스탈린그라드 남쪽)
ARC8 = piece("1123", 8)                                            # 11.30 포위망 북서 호
RASP = piece("1123", 12)                                           # 라스포핀스카야 루마니아군 포위 고리
F23_OTHER = [piece("1123", 2), piece("1123", 6), piece("1123", 4)]  # 11.23 바깥 선(서쪽 루마니아군 잔존·치르·남쪽)
F30_OUT = [piece("1130", 0)] + [np.array(x) for x in D["fronts"]["1130"]["soviet"][:2]]


def pocket_1123() -> np.ndarray:
    north = NORTH[NORTH[:, 0] >= RING10[0, 0]]                    # 동 → 서
    city = np.array([[44.61, 48.79], [44.67, 48.92]])
    return np.vstack([RING10, city, north])


def pocket_1130() -> np.ndarray:
    i0 = int(np.argmin(np.linalg.norm(RING10 - ARC8[-1], axis=1)))   # ARC8 서쪽 끝(칼라치 동쪽)과 만나는 고리 점
    north = NORTH[NORTH[:, 0] >= ARC8[0, 0]]
    city = np.array([[44.61, 48.79], [44.67, 48.92]])
    return np.vstack([RING10[i0:], city, north, ARC8])


POCKET23, POCKET30 = pocket_1123(), pocket_1130()

# 부대(11.18 배치, 군·군단 단위 개략) — (국가, 제대, 병종, 이름, 경도, 위도, 등장 초)
UNITS = [
    ("it", "XXXX", "inf", "이탈리아 제8군", 40.75, 49.78, 3.6),
    ("ro", "XXXX", "inf", "루마니아 제3군", 42.15, 49.33, 4.2),
    ("de", "XXX", "arm", "독일 제48기갑군단", 42.42, 49.03, 4.8),
    ("de", "XXXX", "inf", "독일 제6군", 44.05, 49.02, 5.4),
    ("de", "XXXX", "arm", "독일 제4기갑군", 44.22, 48.42, 6.0),
    ("ro", "XXXX", "inf", "루마니아 제4군", 44.25, 47.95, 6.6),
    ("su", "XXXX", "arm", "제5전차군", 42.72, 49.72, 8.4),
    ("su", "XXXX", "inf", "제21군", 43.18, 49.52, 8.9),
    ("su", "XXXX", "inf", "제65군", 43.62, 49.42, 9.4),
    ("su", "XXXX", "inf", "제24군", 44.05, 49.30, 9.8),
    ("su", "XXXX", "inf", "제66군", 44.55, 49.18, 10.2),
    ("su", "XXXX", "inf", "제62군", 44.72, 48.80, 10.6),
    ("su", "XXXX", "inf", "제64군", 44.78, 48.52, 11.0),
    ("su", "XXXX", "inf", "제57군", 44.88, 48.27, 11.4),
    ("su", "XXXX", "inf", "제51군", 44.98, 47.98, 11.8),
]
FRONT_GROUPS = [  # 소련 전선군(방면군) 이름 — 등장 초
    ("남서전선군 · 바투틴", 42.95, 50.02, 12.2), ("돈 전선군 · 로코솝스키", 44.05, 49.66, 12.5),
    ("스탈린그라드 전선군 · 예료멘코", 45.2, 48.55, 12.8),
]
# 진격 화살표 — (이름, 경유점, 시작, 끝, 날짜 설명)
ARROWS = [
    ("제5전차군 · 제26·제1전차군단", [(42.76, 49.50), (42.62, 49.22), (42.85, 48.98), (43.25, 48.80), (43.52, 48.72)], 16.0, 31.0),
    ("제21군 · 제4전차군단", [(43.08, 49.28), (43.22, 49.07), (43.45, 48.88), (43.62, 48.64)], 16.6, 37.0),
    ("제65군", [(43.30, 49.30), (43.55, 49.17), (43.72, 49.02)], 17.2, 26.0),
    ("제51군 · 제4기계화군단", [(44.55, 48.10), (44.20, 48.08), (43.95, 48.25), (43.78, 48.45), (43.66, 48.60)], 26.8, 37.0),
    ("제57군 · 제13전차군단", [(44.55, 48.42), (44.30, 48.42), (44.05, 48.50), (43.85, 48.57)], 27.4, 36.0),
    ("제4기병군단", [(44.45, 47.98), (44.15, 47.88), (43.85, 47.80)], 28.0, 34.0),
]
SOVETSKY = (43.64, 48.60)
PLACES = [  # 1942년 지명(현재 이름)
    ("스탈린그라드", "현 볼고그라드", 44.51, 48.71), ("칼라치", None, 43.53, 48.69), ("세라피모비치", None, 42.74, 49.58),
    ("클레츠카야", None, 43.06, 49.32), ("수로비키노", None, 42.85, 48.61), ("코텔니코보", None, 43.14, 47.63),
    ("소베츠키", None, 43.64, 48.60), ("모로좁스크", None, 41.81, 48.35),
]
RIVER_LABELS = [("돈강", 42.35, 49.66), ("볼가강", 45.05, 48.62), ("치르강", 42.30, 48.80), ("돈강", 43.0, 48.05)]
DATES = [(0.0, "1942. 11. 18"), (15.4, "1942. 11. 19"), (26.4, "1942. 11. 20"), (35.0, "1942. 11. 23"), (46.0, "1942. 11. 30")]
SHOTS = [  # (시작, 이동 끝, 중심 경도, 위도, w)
    (0.0, 0.0, 42.75, 48.85, 6.6),
    (13.0, 15.6, 43.05, 49.22, 2.7),
    (24.0, 26.6, 44.05, 48.22, 2.7),
    (32.6, 35.2, 43.98, 48.74, 2.3),
    (43.5, 46.2, 43.35, 48.55, 4.4),
]
PUSH = 0.03
SOURCES = [
    "전선(11.19·23·30): 러시아 국방부 지도 023 재작도 'Operation Uranus'(Lưu Ly, Wikimedia Commons, CC BY 3.0) — 경위도 눈금으로 정합한 개략선",
    "11.18 배치: 'Stalingrad – Preparations for Operation Uranus'(J. O'Sullivan, Commons, CC BY-SA 3.0) 대조 · 군 단위 개략",
    "포위 병력 추정은 사료마다 크게 다름(약 25만~30만 명대 제시가 많음)",
]


# ---------------------------------------------------------------- 카메라(앞 숏 끝 상태에서 이어 간다 — D1 멈칫 교훈)
def camera(t: float) -> tuple[float, float, float]:
    i = max(j for j, s in enumerate(SHOTS) if t >= s[0])
    cur = SHOTS[i]
    if i == 0:
        px, py, pw = cur[2], ym(cur[3]), cur[4]
    else:
        pv = SHOTS[i - 1]
        px, py, pw = pv[2], ym(pv[3]), pv[4] * (1 - PUSH)
    k = ease_io(clamp01((t - cur[0]) / max(1e-6, cur[1] - cur[0]))) if cur[1] > cur[0] else 1.0
    x, y = px + (cur[2] - px) * k, py + (ym(cur[3]) - py) * k
    w = math.exp(math.log(pw) + (math.log(cur[4]) - math.log(pw)) * k)
    nxt = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else TOTAL
    w *= 1 - PUSH * smooth(clamp01((t - cur[1]) / max(1.0, nxt - cur[1])))
    return x, y, w


def W_(ll: np.ndarray) -> np.ndarray:
    ll = np.asarray(ll, float)
    return np.column_stack([ll[:, 0], [ym(v) for v in ll[:, 1]]])


# ---------------------------------------------------------------- 그리기 요소
def draw_rivers(ctx: cairo.Context, view: View) -> None:
    for kind, wd, al in (("minor", 0.8, 0.55), ("major", 2.0, 0.85)):
        for r in D["rivers"][kind]:
            S = view.to_screen_arr(W_(r))
            ctx.new_path()
            ctx.move_to(*S[0])
            for p in S[1:]:
                ctx.line_to(*p)
            ctx.set_source_rgba(*WATER, al)
            ctx.set_line_width(wd)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()


def front_line(ctx: cairo.Context, view: View, P: np.ndarray, prog: float, a: float, dashed: bool = False,
               col_axis: tuple = C["us"]) -> None:
    """전선 = 추축(파랑)·소련(빨강) 이중선. 소련 선은 추축 선을 화면에서 2px 옮겨 같은 모양으로(원 지도 범례 방식)."""
    if a <= 0.01 or prog <= 0:
        return
    S = view.to_screen_arr(W_(P))
    n = max(2, int(len(S) * prog))
    S = S[:n]
    d = np.gradient(S, axis=0)
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
    glow_line(ctx, S, col_axis, a, 1.6, dash=[5, 3] if dashed else None)
    glow_line(ctx, S + nrm * 2.6, C["ru"], a, 1.2, dash=[5, 3] if dashed else None)


def poly_path(ctx: cairo.Context, view: View, P: np.ndarray) -> None:
    S = view.to_screen_arr(W_(P))
    ctx.new_path()
    ctx.move_to(*S[0])
    for p in S[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def hatch_fill(ctx: cairo.Context, col: tuple, a: float, gap: float = 5.0) -> None:
    x0, y0, x1, y1 = ctx.clip_extents()
    s = x0 - (y1 - y0)
    while s < x1:
        ctx.move_to(s, y1)
        ctx.line_to(s + (y1 - y0), y0)
        s += gap
    ctx.set_source_rgba(*col, a)
    ctx.set_line_width(1.1)
    ctx.stroke()


def draw_pocket(ctx: cairo.Context, view: View, P: np.ndarray, a: float) -> None:
    if a <= 0.01:
        return
    ctx.save()
    poly_path(ctx, view, P)
    ctx.set_source_rgba(*C["us"], 0.16 * a)
    ctx.fill_preserve()
    ctx.clip()
    hatch_fill(ctx, C["us"], 0.45 * a)
    ctx.restore()


def unit_symbol(ctx: cairo.Context, x: float, y: float, nation: str, ech: str, kind: str, a: float, scale: float = 1.0) -> None:
    """부대 부호(나토식 단순화): 사각 틀 + 병종(보병 X, 기갑 타원) + 위에 제대 표시. 색 = 국가."""
    col = C[NATION[nation][0]]
    w, h = 26 * scale, 17 * scale
    x0, y0 = x - w / 2, y - h / 2
    ctx.rectangle(x0, y0, w, h)
    ctx.set_source_rgba(*col, 0.88 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.95 * a)
    ctx.set_line_width(1.2)
    ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.95 * a)
    ctx.set_line_width(1.1)
    if kind == "inf":
        ctx.move_to(x0, y0)
        ctx.line_to(x0 + w, y0 + h)
        ctx.move_to(x0 + w, y0)
        ctx.line_to(x0, y0 + h)
        ctx.stroke()
    else:
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(w * 0.34, h * 0.26)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.stroke()
    text(ctx, ech, x, y0 - 3, 9.5, "mono", (1, 1, 1), a, 2.4, "c", role="echelon")


def draw_units(ctx: cairo.Context, view: View, t: float, res: list) -> None:
    for nat, ech, kind, name, lon, lat, t0 in UNITS:
        a = smooth((t - t0) / 0.5)
        if nat == "ro" and name.endswith("제3군"):          # 북쪽 돌파 뒤 무너짐 — 흐려진다
            a *= 1 - 0.65 * smooth((t - 21.0) / 2.0)
        if nat == "ro" and name.endswith("제4군"):
            a *= 1 - 0.65 * smooth((t - 31.0) / 2.0)
        if name == "독일 제48기갑군단":
            a *= 1 - 0.65 * smooth((t - 23.0) / 2.0)
        if a <= 0.01:
            continue
        x, y = view.to_screen(lon, ym(lat))
        if not (-40 < x < W_OUT + 40 and -40 < y < H_OUT + 40):
            continue
        pop = 1 + 0.25 * (1 - ease_out(clamp01((t - t0) / 0.4)))
        unit_symbol(ctx, x, y, nat, ech, kind, a, pop)
        text(ctx, name, x, y + 22, 11.5, "sansb", C[NATION[nat][0]] if nat != "su" else (1, 0.82, 0.82), a, 3, "c")
        wd = tw(ctx, name, 11.5, "sansb")
        res.append((x - max(wd, 26) / 2 - 3, y - 22, x + max(wd, 26) / 2 + 3, y + 26))


def arrow(ctx: cairo.Context, view: View, pts: list, prog: float, a: float, col: tuple) -> tuple[float, float] | None:
    """진격 화살표: 꼬리가 가늘고 머리 쪽이 굵은 반투명 띠 + 화살촉. prog = 자란 비율."""
    if a <= 0.01 or prog <= 0.001:
        return None
    S = view.to_screen_arr(catmull(W_(pts).tolist(), 16))
    seg = np.linalg.norm(np.diff(S, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    end = L[-1] * prog
    k = int(np.searchsorted(L, end))
    if k < 2:
        return None
    P = S[:k]
    d = np.gradient(P, axis=0)
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
    u = np.linspace(0, 1, len(P))
    half = 2.5 + 6.5 * u
    left, right = P + nrm * half[:, None], P - nrm * half[:, None]
    tip_dir = (P[-1] - P[-2]) / max(np.linalg.norm(P[-1] - P[-2]), 1e-6)
    tip = P[-1] + tip_dir * 16
    wing = 14.0
    ctx.new_path()
    ctx.move_to(*left[0])
    for p in left[1:]:
        ctx.line_to(*p)
    ctx.line_to(*(P[-1] + nrm[-1] * wing))
    ctx.line_to(*tip)
    ctx.line_to(*(P[-1] - nrm[-1] * wing))
    for p in right[::-1]:
        ctx.line_to(*p)
    ctx.close_path()
    g = cairo.LinearGradient(*P[0], *tip)
    g.add_color_stop_rgba(0, *col, 0.15 * a)
    g.add_color_stop_rgba(1, *col, 0.78 * a)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 0.85, 0.85, 0.55 * a)
    ctx.set_line_width(0.8)
    ctx.stroke()
    return float(P[len(P) // 2][0]), float(P[len(P) // 2][1])


def draw_arrows(ctx: cairo.Context, view: View, t: float, res: list, labels: list) -> None:
    for name, pts, t0, t1 in ARROWS:
        prog = ease_io(clamp01((t - t0) / (t1 - t0)))
        a = smooth((t - t0) / 0.4) * (1 - 0.72 * smooth((t - 44.0) / 1.5))
        mid = arrow(ctx, view, pts, prog, a, C["ru"])
        if mid and prog > 0.35:
            la = smooth((t - t0 - (t1 - t0) * 0.35) / 0.6) * (1 - smooth((t - 43.0) / 0.8))
            labels.append((name, mid, la))


def place_labels(ctx: cairo.Context, view: View, t: float, res: list) -> None:
    a = smooth((t - 1.0) / 0.8)
    for name, sub, lon, lat in PLACES:
        x, y = view.to_screen(lon, ym(lat))
        if not (0 < x < W_OUT and 0 < y < H_OUT):
            continue
        if any(b[0] < x + 60 and b[2] > x and b[1] < y and b[3] > y - 14 for b in res):
            continue
        ctx.arc(x, y, 2.6, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.fill()
        text(ctx, name, x + 6, y + 4, 11.5, "sansm", (1, 1, 1), 0.9 * a, 3)
        if sub:
            text(ctx, sub, x + 6, y + 18, 9.5, "sans", C["muted"], 0.9 * a, 2.5)
    for name, lon, lat in RIVER_LABELS:
        x, y = view.to_screen(lon, ym(lat))
        if 0 < x < W_OUT and 0 < y < H_OUT:
            text(ctx, name, x, y, 11, "serif", WATER, 0.75 * a, 0, "c", spacing=2.0)


def tag(ctx: cairo.Context, s: str, x: float, y: float, col: str, a: float, anchor: str = "c") -> None:
    size = 10.5
    w = tw(ctx, s, size, "sansb") + 12
    xx = x - w / 2 if anchor == "c" else (x - w if anchor == "r" else x)
    rrect(ctx, xx, y - 12, w, 17, 3)
    ctx.set_source_rgba(0.05, 0.06, 0.09, 0.75 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*C[col], 0.95 * a)
    ctx.set_line_width(0.9)
    ctx.stroke()
    text(ctx, s, xx + 6, y + 1, size, "sansb", C[col], a, 0)


def draw_date(ctx: cairo.Context, t: float) -> None:
    B = DATE_BADGE
    cur = [d for d in DATES if t >= d[0]][-1]
    k = smooth((t - cur[0] - 0.2) / B.slide_sec)
    a = 0.95 * k * (1 - smooth((t - (TOTAL - 5.2)) / 0.5))
    w = text(ctx, cur[1], W_OUT - B.x_right, B.y - (1 - k) * B.slide_px, B.size, B.font, (1, 1, 1), a, 3, "r")
    ctx.set_source_rgba(*C["gold"], 0.9 * a)
    ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
    ctx.fill()


def legend(ctx: cairo.Context, t: float) -> None:
    a = window(t, 3.4, 13.5, 0.6, 0.6)
    if a <= 0.01:
        return
    x, y = 18, 392
    rrect(ctx, x - 8, y - 18, 214, 70, 6)
    ctx.set_source_rgba(*CARD_BG[:3], 0.8 * a)
    ctx.fill()
    for i, nat in enumerate(("su", "de", "ro", "it")):
        cx = x + 10 + (i % 2) * 104
        cy = y + (i // 2) * 22
        unit_symbol(ctx, cx, cy - 4, nat, "", "inf", a, 0.62)
        text(ctx, NATION[nat][1], cx + 14, cy, 11.5, "sansm", (1, 1, 1), a, 0)
    text(ctx, "XXXX 군 · XXX 군단 · 사선 보병 · 타원 기갑", x, y + 42, 10, "sansm", C["muted"], a, 0)


def source_line(ctx: cairo.Context, t: float) -> None:
    a = window(t, 1.0, TOTAL - 6.0, 0.6, 0.6)
    text(ctx, "전선·부대 위치는 개략(참고 작전도 정합 · 군 단위) — 출처는 끝 화면", 14, 470, 9.5, "sans", C["muted"], 0.85 * a, 2,
         role="source")


def end_card(ctx: cairo.Context, t: float) -> None:
    a = smooth((t - (TOTAL - 5.0)) / 0.6)
    if a <= 0.01:
        return
    ctx.set_source_rgba(0.02, 0.025, 0.04, 0.92 * a)
    ctx.paint()
    text(ctx, "자료", 50, 170, 17, "disp", (1, 1, 1), a, 0)
    for i, s in enumerate(SOURCES):
        text(ctx, s, 50, 200 + i * 20, 10.5, "sansm", C["muted"], a, 0, role="credit")
    text(ctx, "천왕성 작전 화면 스케치 · 자막·내레이션 없음", 50, 280, 10, "sans", C["muted"], 0.8 * a, 0, role="credit")


# ---------------------------------------------------------------- 프레임
class Scene:
    def __init__(self) -> None:
        self.out = output_profile("720p")
        self.stage = MercatorStage(Assets(PROJ, load_labels(PROJ / "labels.yaml"), "720p"), out=self.out)

    def render(self, t: float) -> bytearray:
        OP = self.out
        view = View(self.stage, np.array(camera(t)))
        im = self.stage.base_image(view, OP)            # 지형만 — 현대 국경·행정구역선은 그리지 않는다
        buf = bytearray(im.tobytes("raw", "BGRX"))
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * 4)
        ctx = cairo.Context(surf)
        ctx.translate(OP.pad_x, 0)
        ctx.scale(OP.k, OP.k)
        ctx.set_source_rgba(0.02, 0.03, 0.05, 0.28)      # 지형을 한 단계 눌러 부호·선이 앞으로
        ctx.paint()
        draw_rivers(ctx, view)
        res: list = []
        labels: list = []
        # 포위망: 11.23 생성 → 11.30 축소(교차 전환)
        pa = smooth((t - 38.2) / 1.2)
        p30 = smooth((t - 47.0) / 1.5)
        draw_pocket(ctx, view, POCKET23, pa * (1 - p30))
        draw_pocket(ctx, view, POCKET30, pa * p30)
        # 전선
        f19a = 1 - 0.7 * smooth((t - 36.0) / 1.5)
        for P in F19:
            front_line(ctx, view, P, ease_io(clamp01((t - 0.6) / 2.8)), f19a)
        g23 = ease_io(clamp01((t - 36.6) / 2.4))
        f23a = 1 - 0.55 * smooth((t - 46.5) / 1.5)
        front_line(ctx, view, RING10, g23, f23a)
        for P in F23_OTHER:
            front_line(ctx, view, P, g23, f23a)
        front_line(ctx, view, RASP, ease_io(clamp01((t - 21.5) / 1.6)), 1.0)
        g30 = ease_io(clamp01((t - 46.8) / 3.0))
        for P in F30_OUT:
            front_line(ctx, view, P, g30, 1.0, dashed=True)
        front_line(ctx, view, ARC8, g30, 1.0, dashed=True)
        draw_arrows(ctx, view, t, res, labels)
        draw_units(ctx, view, t, res)
        # 집게가 닫히는 순간(11.23 소베츠키)
        lt = t - 37.2
        if lt > 0:
            x, y = view.to_screen(SOVETSKY[0], ym(SOVETSKY[1]))
            fl = math.exp(-lt * 2.2)
            g = cairo.RadialGradient(x, y, 0, x, y, 46)
            g.add_color_stop_rgba(0, 1, 0.9, 0.75, 0.9 * fl)
            g.add_color_stop_rgba(1, *C["ru"], 0)
            ctx.set_source(g)
            ctx.arc(x, y, 46, 0, 2 * math.pi)
            ctx.fill()
            for k in range(2):
                f = ((lt * 0.5) + k / 2) % 1.0
                ctx.arc(x, y, 5 + 24 * ease_out(f), 0, 2 * math.pi)
                ctx.set_source_rgba(*C["gold"], 0.6 * (1 - f) * window(t, 37.2, 45.0, 0.3, 0.6))
                ctx.set_line_width(1.3)
                ctx.stroke()
            ta = window(t, 37.6, 45.0, 0.4, 0.6)
            tag(ctx, "11.23 소베츠키 — 남북 집게가 만남", x, y + 36, "gold", ta)
            res.append((x - 110, y + 20, x + 110, y + 40))
        place_labels(ctx, view, t, res)
        for name, (x, y), la in labels:
            text(ctx, name, x, y - 13, 11.5, "sansb", (1, 0.86, 0.86), la, 3.2, "c")
        # 국면 태그
        a = window(t, 6.0, 13.0, 0.5, 0.6)
        if a > 0.01:
            for lon, lat in ((42.15, 49.33), (44.25, 47.95)):
                x, y = view.to_screen(lon, ym(lat))
                tag(ctx, "약한 측면", x, y - 30, "amber", a)
        a = window(t, 22.4, 31.0, 0.5, 0.6)
        if a > 0.01:
            x, y = view.to_screen(43.0, ym(49.38))
            tag(ctx, "라스포핀스카야 — 루마니아군 포위", x, y - 22, "amber", a)
        a = window(t, 39.6, TOTAL - 5.0, 0.6, 0.6)
        if a > 0.01:
            x, y = view.to_screen(44.15, ym(48.80))
            tag(ctx, "포위망 — 독일 제6군·제4기갑군 일부", x, y, "us", a)
        a = window(t, 48.6, TOTAL - 5.0, 0.6, 0.6)
        if a > 0.01:
            x, y = view.to_screen(42.55, ym(48.40))
            tag(ctx, "11.30 외곽 포위선(치르강·악사이 방면)", x, y, "ru", a)
        legend(ctx, t)
        source_line(ctx, t)
        draw_date(ctx, t)
        end_card(ctx, t)
        fa = 1 - min(smooth(t / 1.0), smooth((TOTAL - t) / 1.2))
        if fa > 0.001:
            ctx.set_source_rgba(0, 0, 0, fa)
            ctx.paint()
        surf.flush()
        return buf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default=None)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    sc = Scene()
    OP = sc.out
    to_img = lambda b: Image.frombuffer("RGBA", (OP.width, OP.height), bytes(b), "raw", "BGRA", 0, 1).convert("RGB")  # noqa: E731
    if args.frames:
        for s in args.frames.split(","):
            to_img(sc.render(float(s))).save(OUT / f"frame_{float(s):05.1f}.png")
            print(OUT / f"frame_{float(s):05.1f}.png", flush=True)
        return 0
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{OP.width}x{OP.height}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(OUT / "uranus_sketch.mp4")], stdin=subprocess.PIPE)
    marks = [11.5, 20.0, 30.5, 38.5, 42.0, 51.0, 55.5]
    cells = []
    for i in range(int(TOTAL * FPS)):
        t = i / FPS
        b = sc.render(t)
        ff.stdin.write(bytes(b))
        if any(abs(t - m) < 0.5 / FPS for m in marks):
            cells.append((to_img(b).resize((854, 480)), f"t={t:.1f}s"))
        if i % 240 == 0:
            print(f"{i}/{int(TOTAL * FPS)}", flush=True)
    ff.stdin.close()
    ff.wait()
    from engine.sheet import grid
    grid(cells, 2, OUT / "uranus_sheet.jpg", cell=(854, 480))
    print(OUT / "uranus_sketch.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

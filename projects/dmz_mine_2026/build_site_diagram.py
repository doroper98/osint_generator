"""『DMZ 지뢰 폭발』 사건 현장 개념도 — 코드 조판(사실 텍스트는 코드 렌더, C9·G4-10).

    python projects/dmz_mine_2026/build_site_diagram.py   → media/site_diagram_{1,2,3}.png (1440×900)

형식은 사용자가 보여 준 2015년 목함지뢰 사건 보도 그래픽(군사분계선·남북방한계선·사고 지점 개념도)을 참고했다.
그림 자체와 2015년 수치는 쓰지 않는다. 넣는 수치는 2026년 사건 공식 발표·복수 보도로 확인된 것만:
- 군사분계선 남쪽 약 10m(합참 9.28), 폭발 2회(합참 9.23), 1차 폭발 지점 약 1m 미폭발 지뢰 목격(장병 진술, 합참 9.28),
  9.29 합동조사 북한군 수지반보병지뢰 1발 추가 발견(합참 9.29), 비무장지대 폭 약 4km(남북 각 2km).
정확한 좌표·GP/OP 거리는 비공개 → 그리지 않는다. 축척 아님을 그림에 적는다.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import cairo

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from engine.style import C  # noqa: E402
from engine.typography import text  # noqa: E402

W, H, K = 720, 450, 2          # 설계 좌표 720×450, 2배 해상도로 저장
OUT = Path(__file__).resolve().parent / "media"

BG = (0.043, 0.052, 0.07)
NORTH = (0.20, 0.13, 0.12)
SOUTH = (0.075, 0.095, 0.12)
RED = (0.87, 0.27, 0.27)
WHITE = (0.93, 0.93, 0.92)
MUTED = (0.62, 0.66, 0.72)
GOLD = C["gold"]
TEAL = C["teal"]


def mdl_y(x: float) -> float:
    return 170 + 10 * math.sin(x / 70) + 5 * math.sin(x / 23)


def curve(ctx: cairo.Context, f, x0: float = 0, x1: float = W, step: float = 4) -> None:  # noqa: ANN001
    ctx.move_to(x0, f(x0))
    x = x0
    while x < x1:
        x = min(x1, x + step)
        ctx.line_to(x, f(x))


def burst(ctx: cairo.Context, x: float, y: float, r: float, col: tuple) -> None:
    n = 10
    ctx.move_to(x + r, y)
    for i in range(1, 2 * n + 1):
        rr = r if i % 2 == 0 else r * 0.48
        a = math.pi * i / n
        ctx.line_to(x + rr * math.cos(a), y + rr * math.sin(a))
    ctx.close_path()
    ctx.set_source_rgb(*col)
    ctx.fill_preserve()
    ctx.set_source_rgb(1, 0.95, 0.6)
    ctx.set_line_width(1.2)
    ctx.stroke()


def dotted(ctx: cairo.Context, f, col: tuple, dash: tuple = (2.5, 4), w: float = 1.4) -> None:  # noqa: ANN001
    ctx.save()
    ctx.set_dash(list(dash))
    ctx.set_source_rgb(*col)
    ctx.set_line_width(w)
    curve(ctx, f)
    ctx.stroke()
    ctx.restore()


def draw(step: int) -> cairo.ImageSurface:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W * K, H * K)
    ctx = cairo.Context(surf)
    ctx.scale(K, K)
    ctx.set_source_rgb(*BG)
    ctx.paint()

    # 남북 면
    ctx.set_source_rgb(*NORTH)
    curve(ctx, mdl_y)
    ctx.line_to(W, 0)
    ctx.line_to(0, 0)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*SOUTH)
    curve(ctx, mdl_y)
    ctx.line_to(W, 408)
    ctx.line_to(0, 408)
    ctx.close_path()
    ctx.fill()

    nll = lambda x: mdl_y(x) - 110   # noqa: E731 — 북방한계선(개념상 2km)
    sll = lambda x: mdl_y(x) + 170  # noqa: E731 — 남방한계선(개념상 2km, 사고 지점을 크게 보이려 남측을 넓게)
    dotted(ctx, nll, MUTED)
    dotted(ctx, sll, MUTED)
    ctx.set_source_rgb(*RED)
    ctx.set_line_width(3.2)
    curve(ctx, mdl_y)
    ctx.stroke()

    # 머리
    # 제목은 넣지 않는다 — 화면 캡션(미디어 레지스트리)이 제목, 사진 위 PHOTO 태그·상단 그라데이션 자리(왼쪽 위)를 비운다
    text(ctx, "2026. 9. 21  ·  경기 파주 서부전선  ·  육군 25사단 관할", 696, 30, 13, "sansm", (0.85, 0.75, 0.72), 1, 0, "r")
    text(ctx, "북측", 690, 98, 17, "sansb", (0.85, 0.62, 0.58), 1, 0, "r")
    text(ctx, "남측", 690, 396, 17, "sansb", (0.62, 0.74, 0.88), 1, 0, "r")
    text(ctx, "북방한계선", 30, nll(30) - 8, 14, "sansm", MUTED, 1, 0)
    text(ctx, "군사분계선(MDL)", 30, mdl_y(30) - 10, 16, "sansb", RED, 1, 0)
    text(ctx, "남방한계선", 30, sll(30) - 8, 14, "sansm", MUTED, 1, 0)
    text(ctx, "비무장지대 폭 약 4km", 690, 124, 13, "sansm", MUTED, 0.9, 0, "r")

    sx = 360
    sy = mdl_y(sx) + 9          # 사고 지점(개념상 MDL 바로 남쪽)
    # 새 수색로(남방한계선 → MDL 방향)
    ctx.save()
    ctx.set_dash([6, 4])
    ctx.set_source_rgb(*WHITE)
    ctx.set_line_width(2)
    ctx.move_to(300, sll(300) + 2)
    ctx.curve_to(305, 300, 345, 240, sx, sy + 6)
    ctx.stroke()
    ctx.restore()
    text(ctx, "새 수색로 개척 중(18명 투입)", 322, 300, 15, "sansm", WHITE, 1, 2, "l")

    if step == 1:
        ctx.set_source_rgb(*GOLD)
        ctx.arc(sx, sy, 6.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*GOLD, 0.35)
        ctx.arc(sx, sy, 15, 0, 2 * math.pi)
        ctx.fill()
    # MDL 남쪽 약 10m 표시(괄호선)
    bx = sx + 34
    ctx.set_source_rgb(*GOLD)
    ctx.set_line_width(1.3)
    ctx.move_to(bx, mdl_y(bx))
    ctx.line_to(bx, sy)
    ctx.move_to(bx - 4, mdl_y(bx))
    ctx.line_to(bx + 4, mdl_y(bx))
    ctx.move_to(bx - 4, sy)
    ctx.line_to(bx + 4, sy)
    ctx.stroke()
    ctx.move_to(bx + 5, (mdl_y(bx) + sy) / 2)
    ctx.line_to(bx + 26, mdl_y(bx) - 30)
    ctx.stroke()
    text(ctx, "MDL 남쪽 약 10m", bx + 30, mdl_y(bx) - 40, 20, "sansb", GOLD, 1, 2.5)
    text(ctx, "합참 발표(9.28)", bx + 30, mdl_y(bx) - 20, 13, "sansm", MUTED, 1, 2)

    if step >= 2:
        burst(ctx, sx - 8, sy + 2, 13, (0.95, 0.45, 0.15))
        burst(ctx, sx - 28, sy + 30, 11, (0.95, 0.45, 0.15))
        text(ctx, "① 1차 폭발 — 앞장선 공병 중사 부상", 30, 224, 15, "sansb", WHITE, 1, 2.5, "l")
        text(ctx, "② 2차 폭발 — 구조 나선 수색대대장 부상", 30, 250, 15, "sansb", WHITE, 1, 2.5, "l")
        ctx.set_source_rgba(*WHITE, 0.55)
        ctx.set_line_width(0.8)
        ctx.move_to(268, 219)
        ctx.line_to(sx - 20, sy + 2)
        ctx.move_to(292, 245)
        ctx.line_to(sx - 38, sy + 30)
        ctx.stroke()
    if step >= 3:
        mx, my = sx + 14, sy + 6
        ctx.set_source_rgb(0.55, 0.38, 0.22)
        ctx.rectangle(mx - 5, my - 3.5, 10, 7)
        ctx.fill()
        ctx.set_source_rgb(*WHITE)
        ctx.set_line_width(0.8)
        ctx.rectangle(mx - 5, my - 3.5, 10, 7)
        ctx.stroke()
        text(ctx, "미폭발 갈색 지뢰 목격 — 1차 폭발 지점 약 1m", 402, 224, 14, "sansm", WHITE, 1, 2.5, "l")
        text(ctx, "9.29 합동조사: 수지반보병지뢰 1발 추가 발견", 402, 250, 14, "sansb", TEAL, 1, 2.5, "l")
        ctx.set_source_rgba(*WHITE, 0.55)
        ctx.move_to(400, 219)
        ctx.line_to(mx + 6, my)
        ctx.stroke()

    text(ctx, "축척·실제 지형 아님 · 정확한 좌표 비공개", 24, 432, 12, "sansm", MUTED, 0.95, 0)
    text(ctx, "자료: 합참 발표(9.23·9.28·9.29) 보도 종합", 696, 432, 12, "sansm", MUTED, 0.95, 0, "r")
    return surf


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for step in (1, 2, 3):
        p = OUT / f"site_diagram_{step}.png"
        draw(step).write_to_png(str(p))
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
